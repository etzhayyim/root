//! Reference `plc-control` WASM Component guest (ADR-2606031600 §D2/§D3).
//!
//! A trivial IEC-61131-3-style bang-bang controller compiled to a real WASM
//! Component-Model component implementing the `kotoba:os` `plc-control` world:
//! it imports the capability-scoped device + Datom host interfaces and exports
//! `scan(cycle) -> scan-report`. Each scan reads a granted analog input, stages a
//! discrete output, and asserts a Datom fact — the host commits the cycle as one
//! Datom transaction (scan cycle = Datom transaction; the Rust/Python reference
//! models pin those host-side semantics, this is the guest side made real).
//!
//! N3: the guest only *stages* the output via the host; live actuation is gated.

wit_bindgen::generate!({
    world: "plc-control",
    path: "wit",
});

use kotoba::os::{datom, io_analog, io_digital};

struct Component;

impl Guest for Component {
    fn scan(cycle: u64) -> Result<ScanReport, String> {
        // read the granted analog process value on channel 0
        let pv = io_analog::read_input(0)?;
        // bang-bang: command output ON below setpoint, OFF at/above
        let on = pv < 10.0;
        // stage the discrete output on channel 10 (host defers to commit; N3)
        io_digital::write_output(10, on)?;
        // record the control decision as a Datom fact for the cycle transaction
        let fact = datom::Fact {
            graph: "plc".to_string(),
            entity: "ctrl".to_string(),
            attribute: ":ctrl/command".to_string(),
            value_cbor: vec![if on { 1u8 } else { 0u8 }],
        };
        datom::assert_facts(&[fact])?;
        Ok(ScanReport {
            cycle,
            inputs_read: 1,
            outputs_staged: 1,
            facts_asserted: 1,
            duration_us: 0,
        })
    }
}

export!(Component);
