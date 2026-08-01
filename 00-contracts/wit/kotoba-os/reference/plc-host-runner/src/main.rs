//! End-to-end host run of the real plc-control WASM component (ADR-2606031600).
//!
//! Instantiates `../plc-control-guest/plc-control.component.wasm` under wasmtime,
//! provides the host imports (io-analog read / io-digital write / datom assert)
//! over an immutable Datom log, drives a sequence of scan cycles, and asserts:
//!   * scan cycle = Datom transaction — each committed cycle appends Datoms at
//!     T = cycle, and `as-of` reconstructs the control decision;
//!   * N3 fault-atomicity — a cycle whose sensor read faults makes the guest
//!     return Err, and nothing from that cycle is committed.
//! Self-asserting: panics (nonzero exit) on any mismatch, prints `E2E OK` on pass.

use anyhow::{anyhow, Result};
use wasmtime::component::{Component, HasSelf, Linker};
use wasmtime::{Config, Engine, Store};

mod bindings {
    wasmtime::component::bindgen!({
        world: "plc-host",
        path: "wit",
    });
}
use bindings::kotoba::os::{datom, io_analog, io_digital};
use bindings::PlcHost;

#[derive(Default)]
struct HostState {
    input_pv: f32,
    fail_read: bool,
    staged_outputs: Vec<(u32, bool)>,
    // neutral (graph, entity, attribute, value-cbor) so BOTH worlds' datom::Host
    // impls can stage into one shared log (one OS node, many actors).
    staged_facts: Vec<(String, String, String, Vec<u8>)>,
    // committed Datom log: (T, entity, attribute, value-string)
    log: Vec<(u64, String, String, String)>,
    outputs: std::collections::BTreeMap<u32, bool>,
}

impl HostState {
    /// Atomic commit of one scan cycle's staged outputs + facts as a Datom txn.
    fn commit(&mut self, t: u64) {
        for (ch, v) in self.staged_outputs.drain(..) {
            self.outputs.insert(ch, v);
            self.log.push((t, format!("out:{ch}"), ":io/output".into(), v.to_string()));
        }
        for (_graph, entity, attribute, value_cbor) in self.staged_facts.drain(..) {
            let val = if attribute == ":ctrl/command" {
                if value_cbor.first() == Some(&1) { "ON" } else { "OFF" }.to_string()
            } else {
                format!("{value_cbor:?}")
            };
            self.log.push((t, entity, attribute, val));
        }
    }

    /// Discard a faulted cycle's staging (N3): nothing reaches the log.
    fn rollback(&mut self) {
        self.staged_outputs.clear();
        self.staged_facts.clear();
    }

    /// Datomic as-of: latest :ctrl/command value as of cycle t.
    fn as_of_cmd(&self, t: u64) -> Option<String> {
        self.log
            .iter()
            .filter(|(tt, _, a, _)| *tt <= t && a == ":ctrl/command")
            .last()
            .map(|(_, _, _, v)| v.clone())
    }
}

impl io_analog::Host for HostState {
    fn read_input(&mut self, _ch: u32) -> Result<f32, String> {
        if self.fail_read {
            Err("sensor fault".into())
        } else {
            Ok(self.input_pv)
        }
    }
}

impl io_digital::Host for HostState {
    fn write_output(&mut self, ch: u32, value: bool) -> Result<(), String> {
        self.staged_outputs.push((ch, value)); // staged; applied on commit (N3)
        Ok(())
    }
}

impl datom::Host for HostState {
    fn assert_facts(&mut self, facts: Vec<datom::Fact>) -> Result<(), String> {
        self.staged_facts.extend(
            facts.into_iter().map(|f| (f.graph, f.entity, f.attribute, f.value_cbor)),
        );
        Ok(())
    }
}

// Second world: the mesh-agent. Same kotoba:os/datom import, distinct bindgen
// types, shared HostState — this is "one OS node, many WASM actors, one log".
mod mesh_bindings {
    wasmtime::component::bindgen!({
        world: "mesh-host",
        path: "wit",
    });
}
use mesh_bindings::MeshHost;

impl mesh_bindings::kotoba::os::datom::Host for HostState {
    fn assert_facts(
        &mut self,
        facts: Vec<mesh_bindings::kotoba::os::datom::Fact>,
    ) -> Result<(), String> {
        self.staged_facts.extend(
            facts.into_iter().map(|f| (f.graph, f.entity, f.attribute, f.value_cbor)),
        );
        Ok(())
    }
}

fn main() -> Result<()> {
    let comp_path = "../plc-control-guest/plc-control.component.wasm";
    let engine = Engine::default();
    let component = Component::from_file(&engine, comp_path)
        .map_err(|e| anyhow!("load {comp_path}: {e} (run plc-control-guest/build.sh first)"))?;

    let mut linker: Linker<HostState> = Linker::new(&engine);
    PlcHost::add_to_linker::<_, HasSelf<_>>(&mut linker, |s: &mut HostState| s)?;

    let mut store = Store::new(&engine, HostState::default());
    let bindings = PlcHost::instantiate(&mut store, &component, &linker)?;

    // --- normal cycles: pv below setpoint(10) -> ON, else OFF ---
    for (cycle, pv) in [(0u64, 3.0f32), (1, 20.0), (2, 8.0)] {
        store.data_mut().input_pv = pv;
        let report = bindings
            .call_scan(&mut store, cycle)?
            .map_err(|e| anyhow!("guest scan err: {e}"))?;
        assert_eq!(report.cycle, cycle);
        assert_eq!(report.outputs_staged, 1);
        assert_eq!(report.facts_asserted, 1);
        store.data_mut().commit(cycle);
        let cmd = store.data().as_of_cmd(cycle).unwrap();
        println!("CYCLE {cycle} pv={pv} cmd={cmd} out10={:?}", store.data().outputs.get(&10));
    }

    // --- faulted cycle (N3): sensor read errors -> guest returns Err -> no commit ---
    let before = store.data().log.len();
    store.data_mut().fail_read = true;
    store.data_mut().input_pv = 5.0;
    let faulted = bindings.call_scan(&mut store, 3)?;
    assert!(faulted.is_err(), "faulted cycle must surface guest Err");
    store.data_mut().rollback();
    assert_eq!(store.data().log.len(), before, "faulted cycle must not commit (N3)");
    println!("CYCLE 3 FAULTED -> Err({}), no commit", faulted.err().unwrap());

    // --- assertions: control history + as-of ---
    let st = store.data();
    assert_eq!(st.as_of_cmd(0).as_deref(), Some("ON"));
    assert_eq!(st.as_of_cmd(1).as_deref(), Some("OFF"));
    assert_eq!(st.as_of_cmd(2).as_deref(), Some("ON"));
    // as-of(0) must not leak cycle-1's OFF
    assert_eq!(st.as_of_cmd(0).as_deref(), Some("ON"));
    // 3 committed cycles x (1 output + 1 command) = 6 datoms
    assert_eq!(st.log.len(), 6, "expected 6 committed datoms, got {}", st.log.len());

    println!("DATOMS={}", st.log.len());
    println!("E2E OK");

    fuel_demo(comp_path)?;
    let mesh = "../mesh-agent-guest/mesh-agent.component.wasm";
    multi_actor_demo(comp_path, mesh)?;
    source_chain_demo(mesh)?;
    Ok(())
}

/// ADR §D5: a mesh agent's source chain IS its local Datom-log segment —
/// append-only, monotonically growing. Runs the real mesh-agent component for N
/// steps and asserts each committed step appends exactly one heartbeat (the chain
/// only ever grows; nothing is overwritten).
fn source_chain_demo(comp_mesh: &str) -> Result<()> {
    let engine = Engine::default();
    let mesh = Component::from_file(&engine, comp_mesh)?;
    let mut linker: Linker<HostState> = Linker::new(&engine);
    MeshHost::add_to_linker::<_, HasSelf<_>>(&mut linker, |s: &mut HostState| s)?;
    let mut store = Store::new(&engine, HostState::default());
    let agent = MeshHost::instantiate(&mut store, &mesh, &linker)?;

    let mut prev = 0usize;
    for step in 1..=5u64 {
        agent.call_step(&mut store)?.map_err(|e| anyhow!("step: {e}"))?;
        store.data_mut().commit(step);
        let beats = store
            .data()
            .log
            .iter()
            .filter(|(_, _, a, _)| a == ":agent/heartbeat")
            .count();
        assert_eq!(beats, step as usize, "source chain must grow by 1 per step");
        assert!(beats > prev, "source chain is append-only / monotone");
        prev = beats;
    }
    println!("CHAIN heartbeats={prev} (monotone over 5 steps)");
    println!("CHAIN OK");
    Ok(())
}

/// "One OS node, many WASM actors, one Datom log" (ADR §D2). Instantiates BOTH
/// the plc-control and mesh-agent components into ONE store (one HostState =
/// one Datom log) and runs them interleaved — the control program's commands and
/// the agent's heartbeats land in the same content-addressed log.
fn multi_actor_demo(comp_plc: &str, comp_mesh: &str) -> Result<()> {
    let engine = Engine::default();
    let plc = Component::from_file(&engine, comp_plc)?;
    let mesh = Component::from_file(&engine, comp_mesh)
        .map_err(|e| anyhow!("load {comp_mesh}: {e} (run mesh-agent-guest/build.sh first)"))?;

    let mut lk_plc: Linker<HostState> = Linker::new(&engine);
    PlcHost::add_to_linker::<_, HasSelf<_>>(&mut lk_plc, |s: &mut HostState| s)?;
    let mut lk_mesh: Linker<HostState> = Linker::new(&engine);
    MeshHost::add_to_linker::<_, HasSelf<_>>(&mut lk_mesh, |s: &mut HostState| s)?;

    let mut store = Store::new(&engine, HostState::default());
    let plc_b = PlcHost::instantiate(&mut store, &plc, &lk_plc)?;
    let mesh_b = MeshHost::instantiate(&mut store, &mesh, &lk_mesh)?;

    // interleave: control scan, agent step, control scan, agent step ...
    let mut t = 0u64;
    for pv in [3.0f32, 20.0] {
        store.data_mut().input_pv = pv;
        plc_b.call_scan(&mut store, t)?.map_err(|e| anyhow!("scan: {e}"))?;
        store.data_mut().commit(t);
        t += 1;
        mesh_b.call_step(&mut store)?.map_err(|e| anyhow!("step: {e}"))?;
        store.data_mut().commit(t);
        t += 1;
    }

    let st = store.data();
    let control = st.log.iter().filter(|(_, _, a, _)| a == ":ctrl/command").count();
    let beats = st.log.iter().filter(|(_, _, a, _)| a == ":agent/heartbeat").count();
    println!("MULTI control_facts={control} heartbeats={beats} total_datoms={}", st.log.len());
    assert_eq!(control, 2, "expected 2 control commands");
    assert_eq!(beats, 2, "expected 2 agent heartbeats");
    assert!(st.log.len() >= control + beats, "both actors share one log");
    println!("MULTI OK");
    Ok(())
}

/// Soft-RT (N2) demonstration: wasmtime fuel metering makes per-scan execution
/// MEASURABLE (a WCET-estimation input) and BOUNDED (a misbehaving control
/// program is trapped at its fuel budget, not allowed to run unbounded). This is
/// the honest soft-RT primitive — not hard-RT/SIL (R5), but enforceable bounds.
fn fuel_demo(comp_path: &str) -> Result<()> {
    let mut cfg = Config::new();
    cfg.consume_fuel(true);
    let engine = Engine::new(&cfg)?;
    let component = Component::from_file(&engine, comp_path)?;
    let mut linker: Linker<HostState> = Linker::new(&engine);
    PlcHost::add_to_linker::<_, HasSelf<_>>(&mut linker, |s: &mut HostState| s)?;

    let mut store = Store::new(&engine, HostState::default());
    store.set_fuel(10_000_000)?; // ample for instantiation + scans
    let bindings = PlcHost::instantiate(&mut store, &component, &linker)?;

    // measure fuel per scan across cycles -> an observed WCET bound
    let mut max_used = 0u64;
    for (c, pv) in [(0u64, 3.0f32), (1, 20.0), (2, 8.0)] {
        store.set_fuel(10_000_000)?;
        store.data_mut().input_pv = pv;
        let before = store.get_fuel()?;
        bindings.call_scan(&mut store, c)?.map_err(|e| anyhow!("scan: {e}"))?;
        let used = before - store.get_fuel()?;
        max_used = max_used.max(used);
        println!("FUEL scan{c} consumed={used}");
    }
    println!("FUEL wcet_observed={max_used}");
    assert!(max_used > 0, "a real scan must consume fuel");

    // bounded execution (N2): a budget below the per-scan cost TRAPS the guest.
    let mut starved = Store::new(&engine, HostState::default());
    starved.set_fuel(10_000_000)?;
    let b2 = PlcHost::instantiate(&mut starved, &component, &linker)?;
    starved.set_fuel(max_used / 2)?; // deliberately below the observed cost
    starved.data_mut().input_pv = 3.0;
    let trapped = b2.call_scan(&mut starved, 0);
    assert!(trapped.is_err(), "a starved fuel budget must trap (bounded execution)");
    println!("FUEL starved trapped=yes");
    println!("FUEL OK");
    Ok(())
}
