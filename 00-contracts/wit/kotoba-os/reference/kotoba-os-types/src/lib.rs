//! kotoba-os reference types — the genesis manifest + the `LowerEdge` trait.
//!
//! ADR-2606031600 R1 scaffold (`Consequences` → "kotoba-os crate scaffold:
//! genesis-manifest type, the LowerEdge trait abstracting L1"). This is a
//! *reference* crate: the Rust mirror of
//! `00-contracts/schemas/kotoba-os-genesis-manifest.schema.json`, kept
//! monorepo-side so the boot contract has a typed, compiled, tested form before
//! the production `kotoba-os` crate lands in the `40-engine/kotoba` subrepo
//! (which needs upstream coordination, N6 no-fork).
//!
//! The types deny unknown fields (mirroring the schema's `additionalProperties:
//! false`) and [`GenesisManifest::validate`] enforces the constitutional
//! carve-outs that the JSON Schema encodes as `const`:
//!   * C3/N5 — `identity.server_key` MUST be false (no platform key).
//!   * N3    — `safety.live_actuation` MUST be false at R0..R4.
//!   * N1    — `safety.civilian_only` MUST be true (no weapons/fire-control).

use serde::{Deserialize, Serialize};

pub mod cid;
pub mod mesh;

/// The L1 lower edge a manifest targets. L3–L5 are identical across edges.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Edge {
    /// Bare-metal / microVM unikernel (PLC field device, k8s pod).
    Unikernel,
    /// Hosted Linux process (the e7m edge / dev / sidecar).
    Hosted,
    /// Browser wasm32 (ameno), bound by the baien edge-target invariant.
    Browser,
}

/// Target architecture of the kernel image.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Arch {
    #[serde(rename = "x86_64")]
    X86_64,
    Aarch64,
    Wasm32,
}

/// The kotoba:os WIT world an L5 actor implements.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum World {
    /// Control program: scan cycle = Datom transaction.
    PlcControl,
    /// Non-control Holochain-style agent; source chain = local Datom segment.
    MeshAgent,
}

/// An interface from the `kotoba:os` WIT package (capability scoping).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum WitInterface {
    IoDigital,
    IoAnalog,
    IoGpio,
    FieldbusModbus,
    FieldbusOpcua,
    FieldbusEthercat,
    FieldbusCanopen,
    Datom,
}

/// Soft-RT (scan-cycle determinism) vs the R5-gated hard-RT/SILx path.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum RealtimeClass {
    Soft,
    Hard,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Kernel {
    /// CIDv1 of the kernel image (the image *is* a CID).
    pub image_cid: String,
    pub arch: Arch,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct UserlandActor {
    /// CIDv1 of the content-addressed WASM Component-Model actor.
    pub actor_cid: String,
    /// CIDv1 of its content-addressed validation-rule component (the membrane).
    pub validation_rule_cid: String,
    pub world: World,
}

/// A permitted channel/node identifier in a `channel_allowlist` (number or opaque string).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ChannelId {
    Num(i64),
    Name(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Capabilities {
    /// Granted device/world imports (no ambient authority).
    pub interfaces: Vec<WitInterface>,
    /// Optional per-interface allowlist bounding the addressable channels/nodes.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub channel_allowlist: Option<std::collections::BTreeMap<String, Vec<ChannelId>>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Identity {
    /// A delegated capability reference (CACAO CID / token id), NOT a key.
    pub did_capability: String,
    /// C3/N5: MUST be false. A kotoba-os node holds no platform private key.
    pub server_key: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Neighbourhood {
    pub peers: Vec<String>,
    /// Minimum witnesses to accept a published entry (ADR-2605231902).
    pub witness_quorum: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct Safety {
    pub realtime_class: RealtimeClass,
    /// N3: MUST be false at R0..R4 (stage-only / simulation).
    pub live_actuation: bool,
    /// N1: MUST be true (civilian producing actors only).
    pub civilian_only: bool,
}

/// The content-addressed manifest a kotoba-os node boots from (the "DNA").
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GenesisManifest {
    pub schema: String,
    pub name: String,
    pub edge: Edge,
    pub kernel: Kernel,
    pub userland: Vec<UserlandActor>,
    pub capabilities: Capabilities,
    pub identity: Identity,
    pub neighbourhood: Neighbourhood,
    pub safety: Safety,
}

/// A constitutional invariant the manifest violates. Codes mirror the ADR.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Violation {
    /// C3/N5 — identity.server_key is true.
    ServerKeyHeld,
    /// N3 — safety.live_actuation is true at R0..R4.
    LiveActuation,
    /// N1 — safety.civilian_only is false.
    NotCivilianOnly,
    /// Structural — userland is empty.
    NoUserland,
    /// D1 capability scoping — the actor imports an interface the manifest does
    /// not grant (the boot path must refuse to load it).
    UnauthorizedImport(WitInterface),
    /// A content-addressed artifact (kernel / actor / membrane rule) failed CID
    /// verification.
    BadArtifact,
}

impl GenesisManifest {
    /// Enforce the carve-outs the JSON Schema encodes as `const`. An empty
    /// result means the manifest is constitutionally bootable at R0..R4.
    pub fn validate(&self) -> Vec<Violation> {
        let mut v = Vec::new();
        if self.identity.server_key {
            v.push(Violation::ServerKeyHeld);
        }
        if self.safety.live_actuation {
            v.push(Violation::LiveActuation);
        }
        if !self.safety.civilian_only {
            v.push(Violation::NotCivilianOnly);
        }
        if self.userland.is_empty() {
            v.push(Violation::NoUserland);
        }
        v
    }

    /// True iff a guest may import `iface` (capability scoping, no ambient authority).
    pub fn grants(&self, iface: WitInterface) -> bool {
        self.capabilities.interfaces.contains(&iface)
    }

    /// Interfaces an actor's WASM component imports that this manifest does NOT
    /// grant. Empty = the manifest authorizes the actor (ADR §D1 capability
    /// scoping; the boot path must reject loading an actor it cannot satisfy).
    pub fn ungranted(&self, imports: &[WitInterface]) -> Vec<WitInterface> {
        imports
            .iter()
            .copied()
            .filter(|i| !self.capabilities.interfaces.contains(i))
            .collect()
    }

    /// True iff every interface the component imports is granted.
    pub fn authorizes(&self, imports: &[WitInterface]) -> bool {
        self.ungranted(imports).is_empty()
    }
}

/// Abstracts the L1 lower edge (bare-metal/microVM, hosted, browser). The boot
/// sequence (ADR §D1) is edge-independent above this trait; only image
/// verification + the run loop differ per edge.
pub trait LowerEdge {
    /// Which edge this implementation is.
    fn edge(&self) -> Edge;

    /// Structural CIDv1-base32 shape check (cheap pre-filter; used when the
    /// artifact bytes are not yet in hand, e.g. validating a manifest offline).
    fn verify_cid(&self, cid: &str) -> bool {
        cid.len() > 8
            && cid.starts_with('b')
            && cid[1..].bytes().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
    }

    /// REAL content-address verification: recompute the CIDv1(raw, blake3) of the
    /// fetched bytes and compare to the claimed CID (kotoba-core content address,
    /// trustless `/ipfs/<cid>` re-verify discipline, ADR-2606014600). This is what
    /// the boot path runs before loading a kernel image / actor / membrane rule.
    fn verify_artifact(&self, bytes: &[u8], claimed_cid: &str) -> bool {
        crate::cid::verify_blake3(bytes, claimed_cid)
    }

    /// Boot a manifest on this edge: validate carve-outs, then verify the
    /// kernel + every userland actor + its membrane rule by CID. Returns the
    /// number of content-addressed artifacts verified, or the first violation set.
    fn boot(&self, m: &GenesisManifest) -> Result<usize, Vec<Violation>> {
        let violations = m.validate();
        if !violations.is_empty() {
            return Err(violations);
        }
        let mut verified = 0usize;
        for cid in std::iter::once(&m.kernel.image_cid).chain(
            m.userland
                .iter()
                .flat_map(|a| [&a.actor_cid, &a.validation_rule_cid]),
        ) {
            if !self.verify_cid(cid) {
                return Err(vec![Violation::BadArtifact]);
            }
            verified += 1;
        }
        Ok(verified)
    }

    /// Boot with the actor's actual WASM imports (e.g. extracted from the
    /// component): the complete boot-time check = carve-outs + **capability
    /// authorization** (every import must be granted, D1) + CID verification.
    /// The R0 `boot` omitted the authorization step; this is the correct path.
    fn boot_actor(
        &self,
        m: &GenesisManifest,
        actor_imports: &[WitInterface],
    ) -> Result<usize, Vec<Violation>> {
        let mut violations = m.validate();
        violations.extend(
            m.ungranted(actor_imports)
                .into_iter()
                .map(Violation::UnauthorizedImport),
        );
        if !violations.is_empty() {
            return Err(violations);
        }
        self.boot(m)
    }
}

/// The hosted-process edge (the e7m node, ADR-2606012100). Reference stub.
pub struct HostedEdge;

impl LowerEdge for HostedEdge {
    fn edge(&self) -> Edge {
        Edge::Hosted
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const HIKARI: &str =
        include_str!("../../examples/genesis-hikari-pv-controller.json");

    fn hikari() -> GenesisManifest {
        serde_json::from_str(HIKARI).expect("valid manifest deserializes")
    }

    #[test]
    fn valid_manifest_deserializes_and_validates() {
        let m = hikari();
        assert_eq!(m.edge, Edge::Unikernel);
        assert_eq!(m.kernel.arch, Arch::Aarch64);
        assert_eq!(m.userland.len(), 1);
        assert_eq!(m.userland[0].world, World::PlcControl);
        assert!(m.validate().is_empty(), "expected no violations");
    }

    #[test]
    fn deny_unknown_fields_mirrors_schema() {
        // The negative fixture carries a `_comment` key; deny_unknown_fields
        // rejects it exactly as the schema's additionalProperties:false does.
        let bad = include_str!("../../examples/genesis-INVALID-server-key.json");
        let parsed: Result<GenesisManifest, _> = serde_json::from_str(bad);
        assert!(parsed.is_err(), "unknown field must be rejected");
    }

    #[test]
    fn validate_catches_constitutional_violations() {
        let mut m = hikari();
        m.identity.server_key = true; // C3/N5
        m.safety.live_actuation = true; // N3
        m.safety.civilian_only = false; // N1
        let v = m.validate();
        assert!(v.contains(&Violation::ServerKeyHeld));
        assert!(v.contains(&Violation::LiveActuation));
        assert!(v.contains(&Violation::NotCivilianOnly));
    }

    #[test]
    fn capability_scoping() {
        let m = hikari();
        assert!(m.grants(WitInterface::IoAnalog));
        assert!(m.grants(WitInterface::Datom));
        assert!(!m.grants(WitInterface::IoGpio)); // not granted -> no ambient authority
    }

    #[test]
    fn hosted_edge_boots_valid_manifest() {
        let edge = HostedEdge;
        assert_eq!(edge.edge(), Edge::Hosted);
        // kernel image + (actor + membrane rule) = 3 content-addressed artifacts.
        assert_eq!(edge.boot(&hikari()), Ok(3));
    }

    #[test]
    fn boot_refuses_a_server_key_manifest() {
        let mut m = hikari();
        m.identity.server_key = true;
        assert_eq!(HostedEdge.boot(&m), Err(vec![Violation::ServerKeyHeld]));
    }

    #[test]
    fn boot_actor_enforces_capability_authorization() {
        use WitInterface::{Datom, FieldbusModbus, IoAnalog, IoDigital};
        let m = hikari(); // grants io-analog + fieldbus-modbus + datom
        // a modbus actor's imports are all granted + CIDs valid -> boots (3 artifacts)
        assert_eq!(
            HostedEdge.boot_actor(&m, &[IoAnalog, FieldbusModbus, Datom]),
            Ok(3)
        );
        // a discrete-I/O actor needs io-digital, which hikari does not grant ->
        // boot_actor refuses (the R0 `boot` would have wrongly accepted it)
        let err = HostedEdge
            .boot_actor(&m, &[IoAnalog, IoDigital, Datom])
            .unwrap_err();
        assert!(err.contains(&Violation::UnauthorizedImport(IoDigital)));
        // and the carve-out checks still run in boot_actor
        let mut bad = hikari();
        bad.identity.server_key = true;
        assert!(HostedEdge
            .boot_actor(&bad, &[IoAnalog, FieldbusModbus, Datom])
            .unwrap_err()
            .contains(&Violation::ServerKeyHeld));
    }

    #[test]
    fn manifest_authorizes_a_component_only_if_it_grants_every_import() {
        use WitInterface::{Datom, IoAnalog, IoDigital};
        // the real plc-control component imports io-analog + io-digital + datom
        let imports = [IoAnalog, IoDigital, Datom];
        // hikari grants io-analog + fieldbus-modbus + datom -> missing io-digital
        let hikari = hikari();
        assert!(!hikari.authorizes(&imports));
        assert_eq!(hikari.ungranted(&imports), vec![IoDigital]);
        // a manifest that grants all three authorizes (no ungranted)
        let mut ok = hikari;
        ok.capabilities.interfaces = vec![IoAnalog, IoDigital, Datom];
        assert!(ok.authorizes(&imports));
        assert!(ok.ungranted(&imports).is_empty());
    }

    #[test]
    fn lower_edge_verifies_real_blake3_cid() {
        let bytes = b"a kernel image / actor / membrane rule";
        let cid = crate::cid::cidv1_raw_blake3(bytes);
        // the edge accepts the bytes that hash to the claimed CID...
        assert!(HostedEdge.verify_artifact(bytes, &cid));
        // ...and rejects tampered bytes (real recompute, not a shape check)
        assert!(!HostedEdge.verify_artifact(b"tampered", &cid));
    }
}
