//! chigiri legal-aid intake — kotoba WASM Component guest.
//!
//! The free legal-aid intake gate, running INSIDE the kotoba node (not a
//! Cloudflare Worker). It enforces the constitutional gates in WASM and, on a
//! valid intake, asserts a `legalAidMatter` quad into the kotoba EAVT graph via
//! the KQE host ABI and publishes a KSE event.
//!
//! Gates (ADR-2605302200 / 2605302330 / 2605302345):
//!   G14 — this guest produces NO legal advice; it only routes + asserts.
//!   G15 — zero_compensation MUST be true; any consideration is rejected.
//!   G16 — an in-jurisdiction (license == matter) supervising counsel is
//!         required, and the jurisdiction MUST be `enabled` (not verify-required).
//!
//! InvokeContext (CBOR): { graph, session_cid, args_cbor }; args_cbor is the
//! CBOR-encoded IntakeArgs. Output CBOR: IntakeResult.

#![allow(clippy::needless_return)]

use serde::{Deserialize, Serialize};

/// Jurisdictions whose legal-aid lane is `enabled` (ADR-2605302200 §D4
/// compensation + advice-unreserved families). AT and US-state granularity are
/// `verify-required` and therefore intentionally ABSENT here.
const ENABLED_JURISDICTIONS: &[&str] =
    &["jpn", "deu", "fra", "gbr", "kor", "aus", "ca-on", "che"];

const LANES: &[&str] = &["advice", "certified-mediation"];

#[derive(Serialize, Deserialize, Debug)]
struct InvokeContext {
    graph: String,
    #[allow(dead_code)]
    session_cid: Option<String>,
    args_cbor: Vec<u8>,
}

#[derive(Serialize, Deserialize, Debug)]
struct IntakeArgs {
    adherent_did: String,
    jurisdiction: String,
    lane: String,
    /// G15 — MUST be true. There is no fee/consideration field by construction.
    zero_compensation: bool,
    /// G16 — required to advance past intake.
    supervising_counsel_did: Option<String>,
    counsel_license_jurisdiction: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct IntakeResult {
    status: String,        // "counsel-assigned" | "rejected"
    intake_state: String,
    quads_asserted: u32,
    agent_did: String,
    rejection_reason: Option<String>,
}

/// Pure gate logic — shared by the wasm entry and the native test path.
/// Returns Ok(matter_record_cbor) when the intake passes all gates, or
/// Err(reason) when a gate rejects it.
fn evaluate_intake(args: &IntakeArgs) -> Result<Vec<u8>, String> {
    // G15 — zero compensation, no exceptions.
    if !args.zero_compensation {
        return Err("G15: legal aid is gratuitous; zero_compensation must be true".into());
    }
    // lane must be known.
    if !LANES.contains(&args.lane.as_str()) {
        return Err(format!("unknown lane {:?}", args.lane));
    }
    // G16 — jurisdiction must be enabled (not verify-required).
    if !ENABLED_JURISDICTIONS.contains(&args.jurisdiction.as_str()) {
        return Err(format!(
            "G16: jurisdiction {:?} is not enabled (verify-required)",
            args.jurisdiction
        ));
    }
    // G16 — in-jurisdiction supervising counsel required.
    let counsel = args
        .supervising_counsel_did
        .as_deref()
        .filter(|s| !s.is_empty())
        .ok_or("G16: no supervising counsel; matter held at intake")?;
    let lic = args
        .counsel_license_jurisdiction
        .as_deref()
        .unwrap_or("");
    if lic != args.jurisdiction {
        return Err(format!(
            "G16: counsel licensed in {:?} but matter targets {:?}",
            lic, args.jurisdiction
        ));
    }

    // Passed — build the legalAidMatter record (G15 pinned, no fee field).
    let matter = MatterRecord {
        adherent_did: args.adherent_did.clone(),
        jurisdiction: args.jurisdiction.clone(),
        lane: args.lane.clone(),
        zero_compensation: true,
        supervising_counsel_did: counsel.to_string(),
        counsel_license_jurisdiction: lic.to_string(),
        intake_state: "counsel-assigned".to_string(),
    };
    let mut buf = Vec::new();
    ciborium::into_writer(&matter, &mut buf).map_err(|e| format!("cbor: {e}"))?;
    Ok(buf)
}

#[derive(Serialize, Deserialize, Debug)]
struct MatterRecord {
    adherent_did: String,
    jurisdiction: String,
    lane: String,
    zero_compensation: bool,
    supervising_counsel_did: String,
    counsel_license_jurisdiction: String,
    intake_state: String,
}

// ── WASM Component entry ──────────────────────────────────────────────────

#[cfg(target_arch = "wasm32")]
mod bindings {
    wit_bindgen::generate!({ world: "kotoba-node", path: "wit" });
}

#[cfg(target_arch = "wasm32")]
use bindings::{
    kotoba::kais::{
        auth,
        kqe::{self, Quad},
        kse,
    },
    Guest,
};

#[cfg(target_arch = "wasm32")]
struct LegalAidGuest;

#[cfg(target_arch = "wasm32")]
impl Guest for LegalAidGuest {
    fn run(ctx_cbor: Vec<u8>) -> Result<Vec<u8>, String> {
        let ctx: InvokeContext =
            ciborium::from_reader(ctx_cbor.as_slice()).map_err(|e| format!("ctx cbor: {e}"))?;
        let args: IntakeArgs =
            ciborium::from_reader(ctx.args_cbor.as_slice()).map_err(|e| format!("args cbor: {e}"))?;
        let agent_did = auth::current_did();

        let result = match evaluate_intake(&args) {
            Ok(matter_cbor) => {
                // Assert the legalAidMatter quad into the EAVT graph.
                let subject = format!("matter/{}", args.adherent_did);
                kqe::assert_quad(&Quad {
                    graph: ctx.graph.clone(),
                    subject,
                    predicate: "com.etzhayyim.chigiri/legalAidMatter".to_string(),
                    object_cbor: matter_cbor.clone(),
                })
                .map_err(|e| format!("assert-quad: {e}"))?;
                let _ = kse::publish(
                    &format!("chigiri/{}/legalAid/counsel-assigned", ctx.graph),
                    &matter_cbor,
                );
                IntakeResult {
                    status: "counsel-assigned".to_string(),
                    intake_state: "counsel-assigned".to_string(),
                    quads_asserted: 1,
                    agent_did,
                    rejection_reason: None,
                }
            }
            Err(reason) => IntakeResult {
                status: "rejected".to_string(),
                intake_state: "rejected".to_string(),
                quads_asserted: 0,
                agent_did,
                rejection_reason: Some(reason),
            },
        };

        let mut out = Vec::new();
        ciborium::into_writer(&result, &mut out).map_err(|e| format!("out cbor: {e}"))?;
        Ok(out)
    }
}

#[cfg(target_arch = "wasm32")]
bindings::export!(LegalAidGuest with_types_in bindings);

// ── Native path (IDE + `cargo test`) ──────────────────────────────────────

#[cfg(not(target_arch = "wasm32"))]
pub fn evaluate_native(args_cbor: &[u8]) -> Result<Vec<u8>, String> {
    let args: IntakeArgs =
        ciborium::from_reader(args_cbor).map_err(|e| format!("args cbor: {e}"))?;
    evaluate_intake(&args)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cbor(args: &IntakeArgs) -> Vec<u8> {
        let mut b = Vec::new();
        ciborium::into_writer(args, &mut b).unwrap();
        b
    }

    fn base(jx: &str, counsel_jx: Option<&str>, zero: bool) -> IntakeArgs {
        IntakeArgs {
            adherent_did: "did:web:a".into(),
            jurisdiction: jx.into(),
            lane: "advice".into(),
            zero_compensation: zero,
            supervising_counsel_did: counsel_jx.map(|_| "did:web:lawyer".into()),
            counsel_license_jurisdiction: counsel_jx.map(|s| s.into()),
        }
    }

    #[test]
    fn g15_rejects_non_zero_compensation() {
        assert!(evaluate_native(&cbor(&base("jpn", Some("jpn"), false))).is_err());
    }

    #[test]
    fn g16_rejects_verify_required_jurisdiction() {
        let e = evaluate_native(&cbor(&base("aut", Some("aut"), true))).unwrap_err();
        assert!(e.contains("G16"));
    }

    #[test]
    fn g16_rejects_missing_counsel() {
        let e = evaluate_native(&cbor(&base("jpn", None, true))).unwrap_err();
        assert!(e.contains("G16"));
    }

    #[test]
    fn g16_rejects_license_jurisdiction_mismatch() {
        let e = evaluate_native(&cbor(&base("jpn", Some("usa"), true))).unwrap_err();
        assert!(e.contains("G16"));
    }

    #[test]
    fn valid_intake_passes() {
        let ok = evaluate_native(&cbor(&base("jpn", Some("jpn"), true))).unwrap();
        let m: MatterRecord = ciborium::from_reader(ok.as_slice()).unwrap();
        assert_eq!(m.intake_state, "counsel-assigned");
        assert!(m.zero_compensation);
    }
}
