//! Postage verification (ADR-2605172200 §4, `Postage.sol`).
//!
//! Outbound to external recipients is gated on a paid postage receipt. This module
//! is the pure verification core: it computes the canonical `messageHash` that binds
//! one payment to one message, checks a receipt covers the external recipient count
//! and amount, and builds the `eth_getLogs` filter that finds the on-chain `Paid`
//! event. The actual RPC call is the daemon edge.

use serde_json::{json, Value};
use sha3::{Digest, Keccak256};

/// The `Paid` event signature from `Postage.sol`.
pub const PAID_EVENT_SIGNATURE: &str = "Paid(address,bytes32,uint16,uint256,uint64)";

/// Canonical identity of an outbound message, used to derive `messageHash`. Binding
/// the payment to these fields prevents replaying one postage tx across messages.
#[derive(Debug, Clone)]
pub struct MessageIdentity {
    pub from: String,
    /// All recipients (order-independent — sorted before hashing).
    pub to: Vec<String>,
    pub subject: String,
    pub created_at: String,
    /// The message body hash (e.g. the DKIM `bh=`), binding content too.
    pub body_hash_b64: String,
}

/// keccak256 of the canonical preimage → `0x`-prefixed 32-byte hex. This is the
/// `messageHash` a member passes to `Postage.payPostage` and that the gateway
/// recomputes to verify the receipt binds to *this* message.
pub fn message_hash(id: &MessageIdentity) -> String {
    let mut to = id.to.clone();
    to.sort();
    let preimage = format!(
        "openmail-postage:v1\nfrom={}\nto={}\nsubject={}\ncreatedAt={}\nbody={}",
        id.from,
        to.join(","),
        id.subject,
        id.created_at,
        id.body_hash_b64,
    );
    keccak_hex(preimage.as_bytes())
}

/// A postage receipt as read from the message record / chain event.
#[derive(Debug, Clone)]
pub struct PostageReceipt {
    /// `0x`-prefixed messageHash the payment was bound to.
    pub message_hash: String,
    pub recipient_count: u16,
    /// Amount in USDC base units (6 decimals), e.g. 20_000 = 0.02 USDC.
    pub amount_6dp: u128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PostageVerdict {
    Valid,
    HashMismatch,
    CountTooLow { need: u16, got: u16 },
    Underpaid { need: u128, got: u128 },
}

/// Verify a receipt covers `external_count` external recipients at `rate_per_recipient_6dp`,
/// and is bound to `expected_hash` (the recomputed [`message_hash`]).
pub fn verify_receipt(
    receipt: &PostageReceipt,
    expected_hash: &str,
    external_count: u16,
    rate_per_recipient_6dp: u128,
) -> PostageVerdict {
    if !receipt.message_hash.eq_ignore_ascii_case(expected_hash) {
        return PostageVerdict::HashMismatch;
    }
    if receipt.recipient_count < external_count {
        return PostageVerdict::CountTooLow {
            need: external_count,
            got: receipt.recipient_count,
        };
    }
    let need = rate_per_recipient_6dp.saturating_mul(external_count as u128);
    if receipt.amount_6dp < need {
        return PostageVerdict::Underpaid { need, got: receipt.amount_6dp };
    }
    PostageVerdict::Valid
}

/// keccak256 topic0 for the `Paid` event (`0x`-prefixed 32-byte hex).
pub fn paid_event_topic0() -> String {
    keccak_hex(PAID_EVENT_SIGNATURE.as_bytes())
}

/// Build the `eth_getLogs` filter that finds the `Paid` event binding `message_hash`
/// on `contract` from `from_block`. `messageHash` is the 2nd indexed topic.
pub fn paid_log_filter(contract: &str, message_hash_hex: &str, from_block: &str) -> Value {
    json!({
        "address": contract,
        "fromBlock": from_block,
        "toBlock": "latest",
        // topics: [event sig, sender (any), messageHash]
        "topics": [paid_event_topic0(), Value::Null, normalize_topic(message_hash_hex)],
    })
}

/// Decode a `Paid` event log into a [`PostageReceipt`]. `topics[2]` is the indexed
/// `messageHash`; `data` ABI-encodes the non-indexed `(uint16 recipientCount,
/// uint256 amount, uint64 paidAtMs)` as three 32-byte words.
pub fn decode_paid_log(topics: &[String], data_hex: &str) -> Result<PostageReceipt, String> {
    if topics.len() < 3 {
        return Err("Paid log needs 3 topics (sig, sender, messageHash)".into());
    }
    let data = hex_decode(data_hex.trim_start_matches("0x"))?;
    if data.len() < 96 {
        return Err(format!("Paid data too short: {} bytes", data.len()));
    }
    // word 0: uint16 recipientCount (right-aligned in 32 bytes)
    let recipient_count = u16::from_be_bytes([data[30], data[31]]);
    // word 1: uint256 amount — lower 16 bytes are ample for USDC 6-dp amounts.
    let amount_6dp = u128::from_be_bytes(data[48..64].try_into().unwrap());
    Ok(PostageReceipt {
        message_hash: normalize_topic(&topics[2]),
        recipient_count,
        amount_6dp,
    })
}

/// Find and decode the first `Paid` log in an `eth_getLogs` JSON-RPC result array.
pub fn receipt_from_logs(result: &Value) -> Option<PostageReceipt> {
    let logs = result.as_array()?;
    for log in logs {
        let topics: Vec<String> = log
            .get("topics")?
            .as_array()?
            .iter()
            .filter_map(|t| t.as_str().map(String::from))
            .collect();
        let data = log.get("data")?.as_str()?;
        if let Ok(r) = decode_paid_log(&topics, data) {
            return Some(r);
        }
    }
    None
}

// ── helpers ────────────────────────────────────────────────────────────────────

fn hex_decode(s: &str) -> Result<Vec<u8>, String> {
    if !s.len().is_multiple_of(2) {
        return Err("odd-length hex".into());
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(|_| "bad hex".to_string()))
        .collect()
}

fn keccak_hex(bytes: &[u8]) -> String {
    let digest = Keccak256::digest(bytes);
    let mut s = String::with_capacity(2 + 64);
    s.push_str("0x");
    for b in digest {
        s.push(HEX[(b >> 4) as usize] as char);
        s.push(HEX[(b & 0x0f) as usize] as char);
    }
    s
}

const HEX: &[u8; 16] = b"0123456789abcdef";

/// Left-pad a hex topic to 32 bytes (64 hex chars) with a `0x` prefix.
fn normalize_topic(hex: &str) -> String {
    let h = hex.trim_start_matches("0x");
    format!("0x{:0>64}", h.to_ascii_lowercase())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn identity() -> MessageIdentity {
        MessageIdentity {
            from: "alice@etzhayyim.com".into(),
            to: vec!["carol@yahoo.com".into(), "bob@gmail.com".into()],
            subject: "hi".into(),
            created_at: "2026-06-02T00:00:00Z".into(),
            body_hash_b64: "2jUSOH9NhtVGCQWNr9BrIAPreKQjO6Sn7XIkfJVOzv8=".into(),
        }
    }

    #[test]
    fn message_hash_is_deterministic_and_0x32() {
        let h1 = message_hash(&identity());
        let h2 = message_hash(&identity());
        assert_eq!(h1, h2);
        assert!(h1.starts_with("0x"));
        assert_eq!(h1.len(), 66); // 0x + 64 hex
    }

    #[test]
    fn message_hash_is_recipient_order_independent() {
        let mut a = identity();
        let mut b = identity();
        a.to = vec!["carol@yahoo.com".into(), "bob@gmail.com".into()];
        b.to = vec!["bob@gmail.com".into(), "carol@yahoo.com".into()];
        assert_eq!(message_hash(&a), message_hash(&b));
    }

    #[test]
    fn message_hash_changes_with_content() {
        let mut other = identity();
        other.subject = "different".into();
        assert_ne!(message_hash(&identity()), message_hash(&other));
    }

    #[test]
    fn keccak_matches_known_empty_vector() {
        // keccak256("") = c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
        assert_eq!(
            keccak_hex(b""),
            "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        );
    }

    #[test]
    fn paid_topic0_matches_known_keccak() {
        // keccak256("Paid(address,bytes32,uint16,uint256,uint64)")
        let t = paid_event_topic0();
        assert!(t.starts_with("0x") && t.len() == 66);
        // Recompute independently to guard against regression in the signature string.
        assert_eq!(t, keccak_hex(b"Paid(address,bytes32,uint16,uint256,uint64)"));
    }

    #[test]
    fn valid_receipt_passes() {
        let h = message_hash(&identity());
        let r = PostageReceipt { message_hash: h.clone(), recipient_count: 2, amount_6dp: 40_000 };
        assert_eq!(verify_receipt(&r, &h, 2, 20_000), PostageVerdict::Valid);
    }

    #[test]
    fn hash_mismatch_rejected() {
        let r = PostageReceipt { message_hash: "0xdead".into(), recipient_count: 2, amount_6dp: 40_000 };
        let h = message_hash(&identity());
        assert_eq!(verify_receipt(&r, &h, 2, 20_000), PostageVerdict::HashMismatch);
    }

    #[test]
    fn undercount_rejected() {
        let h = message_hash(&identity());
        let r = PostageReceipt { message_hash: h.clone(), recipient_count: 1, amount_6dp: 40_000 };
        assert_eq!(
            verify_receipt(&r, &h, 2, 20_000),
            PostageVerdict::CountTooLow { need: 2, got: 1 }
        );
    }

    #[test]
    fn underpayment_rejected() {
        let h = message_hash(&identity());
        let r = PostageReceipt { message_hash: h.clone(), recipient_count: 2, amount_6dp: 30_000 };
        assert_eq!(
            verify_receipt(&r, &h, 2, 20_000),
            PostageVerdict::Underpaid { need: 40_000, got: 30_000 }
        );
    }

    /// Build a Paid-log `data` field: recipientCount=2, amount=40000, paidAt=123.
    fn paid_data(count: u16, amount: u128, paid_at: u64) -> String {
        let mut data = Vec::new();
        let mut w0 = [0u8; 32];
        w0[30..32].copy_from_slice(&count.to_be_bytes());
        data.extend_from_slice(&w0);
        let mut w1 = [0u8; 32];
        w1[16..32].copy_from_slice(&amount.to_be_bytes());
        data.extend_from_slice(&w1);
        let mut w2 = [0u8; 32];
        w2[24..32].copy_from_slice(&paid_at.to_be_bytes());
        data.extend_from_slice(&w2);
        let mut s = String::from("0x");
        for b in data {
            s.push_str(&format!("{b:02x}"));
        }
        s
    }

    #[test]
    fn decode_paid_log_recovers_fields() {
        let topics = vec![
            paid_event_topic0(),
            "0x000000000000000000000000aabbccddeeff00112233445566778899aabbccdd".into(),
            "0x1234000000000000000000000000000000000000000000000000000000000000".into(),
        ];
        let r = decode_paid_log(&topics, &paid_data(2, 40_000, 123)).unwrap();
        assert_eq!(r.recipient_count, 2);
        assert_eq!(r.amount_6dp, 40_000);
        assert_eq!(
            r.message_hash,
            "0x1234000000000000000000000000000000000000000000000000000000000000"
        );
    }

    #[test]
    fn receipt_from_logs_picks_first_paid_log() {
        let result = json!([{
            "topics": [
                paid_event_topic0(),
                "0x00000000000000000000000000000000000000000000000000000000000000aa",
                "0xdeadbeef00000000000000000000000000000000000000000000000000000000"
            ],
            "data": paid_data(1, 20_000, 9),
        }]);
        let r = receipt_from_logs(&result).unwrap();
        assert_eq!(r.recipient_count, 1);
        assert_eq!(r.amount_6dp, 20_000);
    }

    #[test]
    fn decode_rejects_short_data() {
        let topics = vec!["0xsig".into(), "0xsender".into(), "0xhash".into()];
        assert!(decode_paid_log(&topics, "0x1234").is_err());
    }

    /// End-to-end: an on-chain log decodes to a receipt that then verifies against a
    /// recomputed message hash — the full postage read+verify path.
    #[test]
    fn decoded_receipt_verifies_against_recomputed_hash() {
        let h = message_hash(&identity());
        let topics = vec![paid_event_topic0(), "0x00".into(), h.clone()];
        let r = decode_paid_log(&topics, &paid_data(2, 40_000, 1)).unwrap();
        assert_eq!(verify_receipt(&r, &h, 2, 20_000), PostageVerdict::Valid);
    }

    #[test]
    fn log_filter_has_three_topics_and_padded_hash() {
        let f = paid_log_filter("0xContract", "0xabc", "0x100");
        assert_eq!(f["address"], "0xContract");
        assert_eq!(f["fromBlock"], "0x100");
        let topics = f["topics"].as_array().unwrap();
        assert_eq!(topics.len(), 3);
        assert_eq!(topics[0], paid_event_topic0());
        assert!(topics[1].is_null());
        // messageHash padded to 32 bytes.
        assert_eq!(topics[2].as_str().unwrap().len(), 66);
        assert!(topics[2].as_str().unwrap().ends_with("abc"));
    }
}
