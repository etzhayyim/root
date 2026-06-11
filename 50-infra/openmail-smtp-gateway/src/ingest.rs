//! Build the kotoba-server `email.ingest` request (ADR-2605172200 §3.1 inbound).
//!
//! The gateway hands raw RFC 5322 bytes to `com.etzhayyim.apps.kotoba.email.ingest`,
//! which parses + at-rest-encrypts them into the recipient's inbox graph. The
//! request body shape mirrors `EmailIngestBody` in kotoba-server (snake_case keys,
//! base64-STANDARD raw). Kept pure so the body is unit-tested without a network.

use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use serde_json::{json, Value};

/// XRPC path (appended to the kotoba-server base URL).
pub const INGEST_NSID: &str = "com.etzhayyim.apps.kotoba.email.ingest";

/// Build the JSON body for one `email.ingest` call delivering `raw` to `owner_did`.
pub fn ingest_request_body(raw: &[u8], owner_did: &str, thread_id: Option<&str>) -> Value {
    let mut body = json!({
        "raw_b64": B64.encode(raw),
        "owner_did": owner_did,
    });
    if let Some(tid) = thread_id {
        body["thread_id"] = Value::String(tid.to_string());
    }
    body
}

/// Full XRPC URL for a kotoba-server base (e.g. `http://127.0.0.1:8077`).
pub fn ingest_url(base: &str) -> String {
    format!("{}/xrpc/{}", base.trim_end_matches('/'), INGEST_NSID)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn body_has_snake_case_keys_and_b64_raw() {
        let raw = b"From: a@b\r\nSubject: hi\r\n\r\nbody";
        let body = ingest_request_body(raw, "did:web:etzhayyim.com:actor:bob", Some("t-1"));
        assert_eq!(body["owner_did"], "did:web:etzhayyim.com:actor:bob");
        assert_eq!(body["thread_id"], "t-1");
        assert_eq!(body["raw_b64"], B64.encode(raw));
    }

    #[test]
    fn thread_id_omitted_when_none() {
        let body = ingest_request_body(b"x", "did:plc:bob", None);
        assert!(body.get("thread_id").is_none());
    }

    #[test]
    fn url_joins_without_double_slash() {
        assert_eq!(
            ingest_url("http://127.0.0.1:8077/"),
            "http://127.0.0.1:8077/xrpc/com.etzhayyim.apps.kotoba.email.ingest"
        );
        assert_eq!(
            ingest_url("http://127.0.0.1:8077"),
            "http://127.0.0.1:8077/xrpc/com.etzhayyim.apps.kotoba.email.ingest"
        );
    }
}
