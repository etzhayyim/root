//! Reference Modbus control component (ADR-2606031600 §D3, fieldbus coverage).
//!
//! Same `plc-control` world as the bang-bang guest, but it reads its setpoint
//! from and writes its command to a **Modbus** device (holding registers) rather
//! than discrete I/O. Tree-shaken imports: {io-analog, fieldbus-modbus, datom} —
//! exactly the capability set the hikari grid-edge manifest grants, so that
//! manifest authorizes this actor. N3: writes are staged by the host.

wit_bindgen::generate!({
    world: "plc-control",
    path: "wit",
});

use kotoba::os::{datom, fieldbus_modbus, io_analog};

struct Component;

impl Guest for Component {
    fn scan(cycle: u64) -> Result<ScanReport, String> {
        // process value from an analog input
        let pv = io_analog::read_input(0)?;
        // setpoint from a Modbus holding register (unit 1, addr 0)
        let setpoint = fieldbus_modbus::read_holding(1, 0, 1)?
            .first()
            .copied()
            .unwrap_or(10) as f32;
        let on = pv < setpoint;
        // command to a Modbus holding register (unit 1, addr 10) — staged (N3)
        fieldbus_modbus::write_holding(1, 10, &[u16::from(on)])?;
        let fact = datom::Fact {
            graph: "plc".to_string(),
            entity: "ctrl".to_string(),
            attribute: ":ctrl/command".to_string(),
            value_cbor: vec![u8::from(on)],
        };
        datom::assert_facts(&[fact])?;
        Ok(ScanReport {
            cycle,
            inputs_read: 2,
            outputs_staged: 1,
            facts_asserted: 1,
            duration_us: 0,
        })
    }
}

export!(Component);
