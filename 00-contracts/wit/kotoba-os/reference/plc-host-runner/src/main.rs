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
use wasmtime::component::{Component, Linker};
use wasmtime::{Engine, Store};

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
    staged_facts: Vec<datom::Fact>,
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
        for f in self.staged_facts.drain(..) {
            let val = if f.attribute == ":ctrl/command" {
                if f.value_cbor.first() == Some(&1) { "ON" } else { "OFF" }.to_string()
            } else {
                format!("{:?}", f.value_cbor)
            };
            self.log.push((t, f.entity, f.attribute, val));
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
        self.staged_facts.extend(facts);
        Ok(())
    }
}

fn main() -> Result<()> {
    let comp_path = "../plc-control-guest/plc-control.component.wasm";
    let engine = Engine::default();
    let component = Component::from_file(&engine, comp_path)
        .map_err(|e| anyhow!("load {comp_path}: {e} (run plc-control-guest/build.sh first)"))?;

    let mut linker: Linker<HostState> = Linker::new(&engine);
    PlcHost::add_to_linker(&mut linker, |s: &mut HostState| s)?;

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
    Ok(())
}
