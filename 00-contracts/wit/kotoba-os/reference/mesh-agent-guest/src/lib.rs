//! Reference `mesh-agent` WASM Component guest (ADR-2606031600 §D2/§D5).
//!
//! A non-control Holochain-style mesh agent: on each `step` it appends one fact
//! to its source chain (= its local Datom-log segment) via the host's `datom`
//! surface, and returns how many facts it asserted. Unlike `plc-control`, it
//! imports NO device worlds — an agent has zero ambient device authority; its
//! only capability is the Datom log. Same artifact KIND as plc-control-guest
//! (content-addressed component), different world.

wit_bindgen::generate!({
    world: "mesh-agent",
    path: "wit",
});

use kotoba::os::datom;

struct Component;

impl Guest for Component {
    fn step() -> Result<u32, String> {
        // append one heartbeat fact to the agent's source chain (local Datom seg)
        let fact = datom::Fact {
            graph: "mesh".to_string(),
            entity: "agent".to_string(),
            attribute: ":agent/heartbeat".to_string(),
            value_cbor: vec![1u8], // minimal CBOR unsigned 1
        };
        datom::assert_facts(&[fact])?;
        Ok(1)
    }
}

export!(Component);
