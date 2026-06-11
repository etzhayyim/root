//! Binding-coverage smoke component (ADR-2606031600 §D3).
//!
//! HONEST: this is NOT a realistic controller — it is a completeness check that
//! every `kotoba:os` device interface compiles into a working WASM import. The
//! `scan` touches one function from each of io-{digital,analog,gpio} and
//! fieldbus-{modbus,opcua,ethercat,canopen} plus datom, so the component's
//! tree-shaken imports cover the entire device surface. If any interface failed
//! to bind, this would not compile.

wit_bindgen::generate!({
    world: "plc-control",
    path: "wit",
});

use kotoba::os::{
    datom, fieldbus_canopen, fieldbus_ethercat, fieldbus_modbus, fieldbus_opcua, io_analog,
    io_digital, io_gpio,
};

struct Component;

impl Guest for Component {
    fn scan(cycle: u64) -> Result<ScanReport, String> {
        // io-analog + io-digital
        let pv = io_analog::read_input(0)?;
        io_digital::write_output(10, pv < 10.0)?;
        // io-gpio
        io_gpio::configure(0, io_gpio::Direction::Output)?;
        io_gpio::write(0, true)?;
        // fieldbus-modbus
        let _m = fieldbus_modbus::read_holding(1, 0, 1)?;
        // fieldbus-opcua
        let _o = fieldbus_opcua::read_node("ns=1;i=1")?;
        // fieldbus-ethercat
        let _e = fieldbus_ethercat::read_pdo(0)?;
        // fieldbus-canopen
        let _c = fieldbus_canopen::read_sdo(1, 0x6040, 0)?;
        // datom
        datom::assert_facts(&[datom::Fact {
            graph: "plc".to_string(),
            entity: "coverage".to_string(),
            attribute: ":coverage/all-buses".to_string(),
            value_cbor: vec![1u8],
        }])?;
        Ok(ScanReport {
            cycle,
            inputs_read: 5,
            outputs_staged: 2,
            facts_asserted: 1,
            duration_us: 0,
        })
    }
}

export!(Component);
