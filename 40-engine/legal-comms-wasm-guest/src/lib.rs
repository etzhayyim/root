//! chigiri legal-comms G18 gate — kotoba WASM Component guest.
//!
//! The counsel-operated comms gate (ADR-2605302345 §D2) running INSIDE the
//! kotoba node. It enforces G18 in WASM and, on a valid actuation, asserts an
//! `outboundLegalAct` quad into the EAVT graph + publishes an "authorized"
//! event. Actual transport egress (fax/email/e-filing) happens OUTSIDE the
//! sandboxed guest, keyed off that event — the guest never performs the act
//! itself, it only authorizes + records it.
//!
//! G18: every legal act MUST be actuated and signed by a human lawyer LICENSED
//! in the destination jurisdiction, using their OWN credential. etzhayyim holds
//! no legal-act signing key; a missing/mismatched counselActuation is refused.

use serde::{Deserialize, Serialize};

/// Reserved-activity artifact classes — each may be performed ONLY by licensed
/// counsel. Anything in this set must carry a counselActuation.
const ARTIFACT_CLASSES: &[&str] = &[
    "court-filing",
    "pleading",
    "formal-notice",
    "demand-letter",
    "representation-letter",
    "appeal-document",
];

#[derive(Serialize, Deserialize, Debug)]
struct InvokeContext {
    graph: String,
    #[allow(dead_code)]
    session_cid: Option<String>,
    args_cbor: Vec<u8>,
}

#[derive(Serialize, Deserialize, Debug)]
struct LegalActArgs {
    destination_jurisdiction: String,
    artifact_class: String,
    transport: String,
    payload_cid: String,
    destination_endpoint: String,
    /// G18 — the actuating lawyer's own credential. Absent → refused.
    counsel_did: Option<String>,
    counsel_license_jurisdiction: Option<String>,
    counsel_signature_ref: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct TransmitRecord {
    artifact_class: String,
    transport: String,
    destination_jurisdiction: String,
    destination_endpoint: String,
    payload_cid: String,
    counsel_did: String,
    counsel_signature_ref: String,
    status: String, // "authorized"
}

#[derive(Serialize, Deserialize, Debug)]
struct GateResult {
    status: String, // "authorized" | "refused"
    quads_asserted: u32,
    agent_did: String,
    rejection_reason: Option<String>,
}

/// Pure G18 gate — shared by the wasm entry and native tests.
fn evaluate_legal_act(a: &LegalActArgs) -> Result<Vec<u8>, String> {
    if !ARTIFACT_CLASSES.contains(&a.artifact_class.as_str()) {
        return Err(format!("unknown artifact_class {:?}", a.artifact_class));
    }
    // (1) counsel actuation must be present.
    let did = a
        .counsel_did
        .as_deref()
        .filter(|s| !s.is_empty())
        .ok_or("G18: legal act has no counselActuation (counsel_did missing)")?;
    // (2) the lawyer's OWN signature reference must be present.
    let sig = a
        .counsel_signature_ref
        .as_deref()
        .filter(|s| !s.is_empty())
        .ok_or("G18: counselActuation missing counsel_signature_ref (corp holds no key)")?;
    // (3) the lawyer must be licensed in the DESTINATION jurisdiction.
    let lic = a.counsel_license_jurisdiction.as_deref().unwrap_or("");
    if lic != a.destination_jurisdiction {
        return Err(format!(
            "G18: counsel licensed in {:?} but act targets {:?}",
            lic, a.destination_jurisdiction
        ));
    }

    let rec = TransmitRecord {
        artifact_class: a.artifact_class.clone(),
        transport: a.transport.clone(),
        destination_jurisdiction: a.destination_jurisdiction.clone(),
        destination_endpoint: a.destination_endpoint.clone(),
        payload_cid: a.payload_cid.clone(),
        counsel_did: did.to_string(),
        counsel_signature_ref: sig.to_string(),
        status: "authorized".to_string(),
    };
    let mut buf = Vec::new();
    ciborium::into_writer(&rec, &mut buf).map_err(|e| format!("cbor: {e}"))?;
    Ok(buf)
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
struct LegalCommsGuest;

#[cfg(target_arch = "wasm32")]
impl Guest for LegalCommsGuest {
    fn run(ctx_cbor: Vec<u8>) -> Result<Vec<u8>, String> {
        let ctx: InvokeContext =
            ciborium::from_reader(ctx_cbor.as_slice()).map_err(|e| format!("ctx cbor: {e}"))?;
        let args: LegalActArgs =
            ciborium::from_reader(ctx.args_cbor.as_slice()).map_err(|e| format!("args cbor: {e}"))?;
        let agent_did = auth::current_did();

        let result = match evaluate_legal_act(&args) {
            Ok(rec_cbor) => {
                kqe::assert_quad(&Quad {
                    graph: ctx.graph.clone(),
                    subject: format!("legalAct/{}", args.payload_cid),
                    predicate: "com.etzhayyim.legal/outboundLegalAct".to_string(),
                    object_cbor: rec_cbor.clone(),
                })
                .map_err(|e| format!("assert-quad: {e}"))?;
                // downstream egress transport subscribes to this topic and
                // performs the actual fax/email/e-filing send.
                let _ = kse::publish(
                    &format!("chigiri/{}/legalAct/authorized", ctx.graph),
                    &rec_cbor,
                );
                GateResult {
                    status: "authorized".to_string(),
                    quads_asserted: 1,
                    agent_did,
                    rejection_reason: None,
                }
            }
            Err(reason) => GateResult {
                status: "refused".to_string(),
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
bindings::export!(LegalCommsGuest with_types_in bindings);

// ── Native path (IDE + `cargo test`) ──────────────────────────────────────

#[cfg(not(target_arch = "wasm32"))]
pub fn evaluate_native(args_cbor: &[u8]) -> Result<Vec<u8>, String> {
    let args: LegalActArgs =
        ciborium::from_reader(args_cbor).map_err(|e| format!("args cbor: {e}"))?;
    evaluate_legal_act(&args)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cbor(a: &LegalActArgs) -> Vec<u8> {
        let mut b = Vec::new();
        ciborium::into_writer(a, &mut b).unwrap();
        b
    }
    fn act(counsel: Option<&str>, lic: Option<&str>, sig: Option<&str>) -> LegalActArgs {
        LegalActArgs {
            destination_jurisdiction: "jpn".into(),
            artifact_class: "court-filing".into(),
            transport: "fax".into(),
            payload_cid: "bafy".into(),
            destination_endpoint: "fax:+81".into(),
            counsel_did: counsel.map(|s| s.into()),
            counsel_license_jurisdiction: lic.map(|s| s.into()),
            counsel_signature_ref: sig.map(|s| s.into()),
        }
    }

    #[test]
    fn g18_refuses_without_actuation() {
        assert!(evaluate_native(&cbor(&act(None, None, None))).is_err());
    }
    #[test]
    fn g18_refuses_wrong_jurisdiction() {
        let e = evaluate_native(&cbor(&act(Some("did:l"), Some("usa"), Some("sig")))).unwrap_err();
        assert!(e.contains("G18"));
    }
    #[test]
    fn g18_refuses_missing_signature() {
        let e = evaluate_native(&cbor(&act(Some("did:l"), Some("jpn"), None))).unwrap_err();
        assert!(e.contains("G18"));
    }
    #[test]
    fn g18_authorizes_valid_actuation() {
        let ok = evaluate_native(&cbor(&act(Some("did:l"), Some("jpn"), Some("sig")))).unwrap();
        let r: TransmitRecord = ciborium::from_reader(ok.as_slice()).unwrap();
        assert_eq!(r.status, "authorized");
        assert_eq!(r.counsel_did, "did:l");
    }
}
