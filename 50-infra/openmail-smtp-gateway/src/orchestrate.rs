//! Outbound pipeline planner — composes the whole bridge outbound path (ADR-2605172200
//! §3.2 + ADR-2606022800).
//!
//! `plan_outbound` is the pure, testable orchestration core: given one native message
//! + the member's DKIM keys + a postage receipt, it
//!   1. partitions recipients (local DID vs external SMTP vs invalid),
//!   2. gates external delivery on a valid postage receipt bound to this message,
//!   3. dual-signs (ed25519 + rsa) the rendered RFC 5322,
//!   4. groups external recipients per destination domain into ready [`OutboundMessage`]s.
//!
//! The result is a [`OutboundPlan`] the daemon executes against live MX DNS + TCP
//! (`daemon::relay_to_mx`). All network/clock is out of this function, so the entire
//! decision flow is unit-tested offline.

use ed25519_dalek::SigningKey;
use rsa::RsaPrivateKey;

use crate::dkim::{self, SignParams};
use crate::outbound::render_and_dual_sign;
use crate::outbound_route::{group_by_domain, partition};
use crate::postage::{self, MessageIdentity, PostageReceipt, PostageVerdict};
use crate::render::{MimeMessage, RenderError};
use crate::smtp_out::OutboundMessage;

/// Disposition of a planned outbound message.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OutboundStatus {
    /// No external recipients — nothing for the SMTP bridge to relay (local copies
    /// go via `email.send`).
    NoExternal,
    /// External recipients present and postage is valid — `deliveries` are ready.
    Planned,
    /// External recipients present but postage is missing/invalid — held, not relayed.
    Held(PostageVerdict),
}

/// One destination domain's ready-to-send job.
#[derive(Debug, Clone)]
pub struct DomainDelivery {
    pub domain: String,
    pub message: OutboundMessage,
}

/// The full plan for one outbound message.
#[derive(Debug, Clone)]
pub struct OutboundPlan {
    pub status: OutboundStatus,
    /// Local members — delivered in-substrate (not by this gateway).
    pub local_dids: Vec<String>,
    /// Unusable recipient addresses.
    pub invalid: Vec<String>,
    /// Per-domain SMTP jobs (empty unless `status == Planned`).
    pub deliveries: Vec<DomainDelivery>,
    /// The dual-signed RFC 5322 bytes (present once `status == Planned`).
    pub signed_message: Option<Vec<u8>>,
    /// The canonical message hash bound by postage.
    pub message_hash: String,
}

/// Inputs to plan one outbound message.
pub struct OutboundJob {
    /// Envelope reverse-path (`MAIL FROM`) — e.g. the member's bounce address.
    pub mail_from: String,
    /// The composed message (decrypted content; `to` is the visible header set).
    pub message: MimeMessage,
    /// Creation time bound into the postage hash (often == `message.date`).
    pub created_at: String,
    /// DKIM params for each algorithm (selectors differ).
    pub ed_params: SignParams,
    pub rsa_params: SignParams,
    /// Postage receipt covering the external recipients (None ⇒ held if any external).
    pub postage: Option<PostageReceipt>,
    /// Per-recipient postage rate (USDC 6-dp) the receipt must meet.
    pub rate_per_recipient_6dp: u128,
}

/// Plan the outbound delivery. Pure: no network, no clock.
pub fn plan_outbound(
    job: &OutboundJob,
    ed_key: &SigningKey,
    rsa_key: &RsaPrivateKey,
) -> Result<OutboundPlan, RenderError> {
    let (local_dids, external, invalid) = partition(&job.message.to);

    // Canonical hash bound by postage (over all recipients + content).
    let identity = MessageIdentity {
        from: job.message.from.clone(),
        to: job.message.to.clone(),
        subject: job.message.subject.clone(),
        created_at: job.created_at.clone(),
        body_hash_b64: dkim::body_hash(&job.message.body),
    };
    let message_hash = postage::message_hash(&identity);

    // No external recipients → nothing to relay.
    if external.is_empty() {
        return Ok(OutboundPlan {
            status: OutboundStatus::NoExternal,
            local_dids,
            invalid,
            deliveries: Vec::new(),
            signed_message: None,
            message_hash,
        });
    }

    // Postage gate for external recipients.
    let external_count = external.len() as u16;
    let verdict = match &job.postage {
        None => PostageVerdict::HashMismatch, // treat absent receipt as a failure to bind
        Some(receipt) => postage::verify_receipt(
            receipt,
            &message_hash,
            external_count,
            job.rate_per_recipient_6dp,
        ),
    };
    if verdict != PostageVerdict::Valid {
        return Ok(OutboundPlan {
            status: OutboundStatus::Held(verdict),
            local_dids,
            invalid,
            deliveries: Vec::new(),
            signed_message: None,
            message_hash,
        });
    }

    // Dual-sign once; the same bytes go to every destination MX.
    let signed = render_and_dual_sign(&job.message, &job.ed_params, &job.rsa_params, ed_key, rsa_key)?;

    let deliveries = group_by_domain(&external)
        .into_iter()
        .map(|(domain, rcpts)| DomainDelivery {
            domain,
            message: OutboundMessage {
                mail_from: job.mail_from.clone(),
                rcpts,
                data: signed.clone(),
            },
        })
        .collect();

    Ok(OutboundPlan {
        status: OutboundStatus::Planned,
        local_dids,
        invalid,
        deliveries,
        signed_message: Some(signed),
        message_hash,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dkim;
    use crate::outbound::default_signed_headers;
    use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
    use rsa::pkcs1::DecodeRsaPrivateKey;

    fn ed_key() -> SigningKey {
        SigningKey::from_bytes(&[9u8; 32])
    }

    fn rsa_key() -> RsaPrivateKey {
        let pem = "-----BEGIN RSA PRIVATE KEY-----\n\
MIICXQIBAAKBgQDkHlOQoBTzWRiGs5V6NpP3idY6Wk08a5qhdR6wy5bdOKb2jLQi\n\
Y/J16JYi0Qvx/byYzCNb3W91y3FutACDfzwQ/BC/e/8uBsCR+yz1Lxj+PL6lHvqM\n\
KrM3rG4hstT5QjvHO9PzoxZyVYLzBfO2EeC3Ip3G+2kryOTIKT+l/K4w3QIDAQAB\n\
AoGAH0cxOhFZDgzXWhDhnAJDw5s4roOXN4OhjiXa8W7Y3rhX3FJqmJSPuC8N9vQm\n\
6SVbaLAE4SG5mLMueHlh4KXffEpuLEiNp9Ss3O4YfLiQpbRqE7Tm5SxKjvvQoZZe\n\
zHorimOaChRL2it47iuWxzxSiRMv4c+j70GiWdxXnxe4UoECQQDzJB/0U58W7RZy\n\
6enGVj2kWF732CoWFZWzi1FicudrBFoy63QwcowpoCazKtvZGMNlPWnC7x/6o8Gc\n\
uSe0ga2xAkEA8C7PipPm1/1fTRQvj1o/dDmZp243044ZNyxjg+/OPN0oWCbXIGxy\n\
WvmZbXriOWoSALJTjExEgraHEgnXssuk7QJBALl5ICsYMu6hMxO73gnfNayNgPxd\n\
WFV6Z7ULnKyV7HSVYF0hgYOHjeYe9gaMtiJYoo0zGN+L3AAtNP9huqkWlzECQE1a\n\
licIeVlo1e+qJ6Mgqr0Q7Aa7falZ448ccbSFYEPD6oFxiOl9Y9se9iYHZKKfIcst\n\
o7DUw1/hz2Ck4N5JrgUCQQCyKveNvjzkkd8HjYs0SwM0fPjK16//5qDZ2UiDGnOe\n\
uEzxBDAr518Z8VFbR41in3W4Y3yCDgQlLlcETrS+zYcL\n\
-----END RSA PRIVATE KEY-----\n";
        RsaPrivateKey::from_pkcs1_pem(pem).unwrap()
    }

    fn params(selector: &str) -> SignParams {
        SignParams {
            domain: "etzhayyim.com".into(),
            selector: selector.into(),
            signed_headers: default_signed_headers(),
            auid: Some("@etzhayyim.com".into()),
            timestamp: Some(1_780_000_000),
        }
    }

    fn job(to: Vec<&str>, postage: Option<PostageReceipt>) -> OutboundJob {
        OutboundJob {
            mail_from: "alice@etzhayyim.com".into(),
            message: MimeMessage {
                from: "Alice <alice@etzhayyim.com>".into(),
                to: to.iter().map(|s| s.to_string()).collect(),
                subject: "Hello".into(),
                date: "Mon, 02 Jun 2026 00:00:00 +0000".into(),
                message_id: "<rk1@openmail.etzhayyim.com>".into(),
                body: "Hi there.\n".into(),
                extra_headers: vec![],
            },
            created_at: "2026-06-02T00:00:00Z".into(),
            ed_params: params("alice-ed25519"),
            rsa_params: params("alice-rsa"),
            postage,
            rate_per_recipient_6dp: 20_000,
        }
    }

    /// Compute the hash a correct receipt must carry for a given recipient set.
    fn hash_for(to: &[&str]) -> String {
        let id = MessageIdentity {
            from: "Alice <alice@etzhayyim.com>".into(),
            to: to.iter().map(|s| s.to_string()).collect(),
            subject: "Hello".into(),
            created_at: "2026-06-02T00:00:00Z".into(),
            body_hash_b64: dkim::body_hash("Hi there.\n"),
        };
        postage::message_hash(&id)
    }

    #[test]
    fn only_local_recipients_is_no_external() {
        let plan = plan_outbound(&job(vec!["bob@etzhayyim.com"], None), &ed_key(), &rsa_key()).unwrap();
        assert_eq!(plan.status, OutboundStatus::NoExternal);
        assert_eq!(plan.local_dids, vec!["did:web:etzhayyim.com:actor:bob"]);
        assert!(plan.deliveries.is_empty());
    }

    #[test]
    fn external_without_postage_is_held() {
        let plan = plan_outbound(&job(vec!["carol@yahoo.com"], None), &ed_key(), &rsa_key()).unwrap();
        assert!(matches!(plan.status, OutboundStatus::Held(_)));
        assert!(plan.deliveries.is_empty());
        assert!(plan.signed_message.is_none());
    }

    #[test]
    fn external_with_underpaid_postage_is_held() {
        let to = vec!["carol@yahoo.com"];
        let receipt = PostageReceipt {
            message_hash: hash_for(&to),
            recipient_count: 1,
            amount_6dp: 10_000, // below 20_000 rate
        };
        let plan = plan_outbound(&job(to, Some(receipt)), &ed_key(), &rsa_key()).unwrap();
        assert_eq!(
            plan.status,
            OutboundStatus::Held(PostageVerdict::Underpaid { need: 20_000, got: 10_000 })
        );
    }

    #[test]
    fn valid_postage_plans_signed_delivery_that_verifies() {
        let to = vec!["carol@yahoo.com"];
        let receipt = PostageReceipt {
            message_hash: hash_for(&to),
            recipient_count: 1,
            amount_6dp: 20_000,
        };
        let plan = plan_outbound(&job(to, Some(receipt)), &ed_key(), &rsa_key()).unwrap();
        assert_eq!(plan.status, OutboundStatus::Planned);
        assert_eq!(plan.deliveries.len(), 1);
        assert_eq!(plan.deliveries[0].domain, "yahoo.com");
        assert_eq!(plan.deliveries[0].message.rcpts, vec!["carol@yahoo.com"]);

        // The signed bytes the relay will transmit actually verify (ed25519).
        let signed = String::from_utf8(plan.signed_message.clone().unwrap()).unwrap();
        let ed_pub = B64.encode(ed_key().verifying_key().to_bytes());
        assert_eq!(dkim::verify(&signed, &ed_pub), Ok(true));
    }

    #[test]
    fn mixed_recipients_partition_and_group_by_domain() {
        let to = vec![
            "bob@etzhayyim.com",     // local
            "carol@yahoo.com",       // external
            "dave@yahoo.com",        // external, same MX
            "erin@gmail.com",        // external, other MX
            "garbage",               // invalid
        ];
        let receipt = PostageReceipt {
            message_hash: hash_for(&to),
            recipient_count: 3,
            amount_6dp: 60_000,
        };
        let plan = plan_outbound(&job(to, Some(receipt)), &ed_key(), &rsa_key()).unwrap();
        assert_eq!(plan.status, OutboundStatus::Planned);
        assert_eq!(plan.local_dids.len(), 1);
        assert_eq!(plan.invalid, vec!["garbage"]);
        // Two destination MXs.
        assert_eq!(plan.deliveries.len(), 2);
        let yahoo = plan.deliveries.iter().find(|d| d.domain == "yahoo.com").unwrap();
        assert_eq!(yahoo.message.rcpts, vec!["carol@yahoo.com", "dave@yahoo.com"]);
        let gmail = plan.deliveries.iter().find(|d| d.domain == "gmail.com").unwrap();
        assert_eq!(gmail.message.rcpts, vec!["erin@gmail.com"]);
    }

    #[test]
    fn postage_count_must_cover_external_recipients() {
        // 2 external recipients but receipt paid for 1 → held.
        let to = vec!["carol@yahoo.com", "erin@gmail.com"];
        let receipt = PostageReceipt {
            message_hash: hash_for(&to),
            recipient_count: 1,
            amount_6dp: 40_000,
        };
        let plan = plan_outbound(&job(to, Some(receipt)), &ed_key(), &rsa_key()).unwrap();
        assert_eq!(
            plan.status,
            OutboundStatus::Held(PostageVerdict::CountTooLow { need: 2, got: 1 })
        );
    }
}
