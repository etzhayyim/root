---
id: adr-2605230000-etzhayyim-mailer-pgp-mime-e2ee
title: "ADR-2605230000: PGP/MIME E2EE for mailer.etzhayyim.com outbound email"
status: accepted
doc_type: adr
topic: mailer-pgp-mime-e2ee
authoritative: true
last_verified: 2026-05-23
priority: 6.0
axis: security
weight: 0.70
priority_note: ""
authoritative_for:
  - kotodama.primitives.pgp
  - kotodama.gewp.compose_pgp_mime_raw
  - kotodama.ingest.mailer (PGP send path)
  - vertex_mailer_pgp_key (DB table)
depends_on:
  - adr-2605080300-sqlalchemy-core-usage-contract  # SQLAlchemy / Alembic migrations
related: []
supersedes: []
superseded_by: []
---

# ADR-2605230000: PGP/MIME E2EE for mailer.etzhayyim.com outbound email

**Status**: accepted
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

`mailer.etzhayyim.com` sends email via the Resend REST API. Before this ADR,
all outbound email — including GEWP agent-to-agent messages — was transmitted in
plaintext. The system needed ProtonMail-style end-to-end encryption for
cross-provider scenarios (Gmail, Outlook, Thunderbird recipients).

Two encryption approaches were evaluated:

| Approach | Compatibility | Transport |
|---|---|---|
| Inline PGP (ASCII armor in body) | Requires Mailvelope/FlowCrypt browser extension | Resend REST API |
| **PGP/MIME (RFC 3156)** | Native Thunderbird, GPG, ProtonMail external | SMTP (smtplib) |

Resend's REST API does not accept raw RFC 2822 MIME, making PGP/MIME impossible
through that interface. Resend provides an SMTP relay (`smtp.resend.com:587`) that
accepts raw MIME messages using the existing API key as the SMTP password.

# Decision

Implement outbound PGP/MIME (RFC 3156) using:

1. **`pgpy>=0.6.0`** — pure-Python OpenPGP library (RFC 4880), no GPG binary dependency.
2. **`smtp.resend.com:587` STARTTLS** — Resend SMTP relay, reuses `RESEND_API_KEY`.
3. **Python `email.mime.*` + `email.policy.SMTP`** — CRLF-correct RFC 2822 construction.
4. **`vertex_mailer_pgp_key` table** — stores recipient public keys, keyed by `(email, fingerprint)`.

## Encryption path (automatic, key-triggered)

Both `send_email` and `send_gewp_message` look up a registered public key for the
recipient before sending. If a key is found:

```
lookup_public_key(to) → key found
  → compose_pgp_mime_raw() / build_pgp_mime_raw()
      builds: multipart/encrypted (RFC 3156)
        Part 1: application/pgp-encrypted  (Version: 1)
        Part 2: application/octet-stream   (PGP ciphertext of inner MIME)
  → _send_smtp(raw_mime, smtp.resend.com:587, api_key)
  → content_protection = "pgp" recorded in vertex_mailer_outbound_email
```

If no key is found, plaintext Resend REST API path is used unchanged.

## GEWP inner content structure (PGP path)

The encrypted payload preserves all 3 GEWP layers inside the ciphertext:

```
multipart/mixed                           ← inner (encrypted)
  Subject: <real subject>                 ← protected header (RFC draft-autocrypt-lamps)
  ├── multipart/alternative
  │   ├── text/plain
  │   └── text/html  + <!-- GEWP:{b64} --> ← Layer 2
  └── application/vnd.gewp+json           ← Layer 1
Outer X-GEWP-* headers                    ← Layer 3 (unencrypted routing hint)
```

## Subject encryption

The outer SMTP `Subject` is set to `[Encrypted]`, matching ProtonMail's
external-recipient behaviour. The real subject is embedded in the inner MIME as a
Protected Header (draft-autocrypt-lamps-protected-headers).

**Client support for subject recovery after decryption:**
- Thunderbird / Enigmail: yes
- FlowCrypt (Gmail plugin): partial
- Mailvelope: no
- Most Outlook PGP plugins: no

Recipients on clients without Protected Headers support will see `[Encrypted]`
permanently. This is an inherent limitation of RFC 3156 and accepted as the
current state.

## Key management

| Operation | Function | Surface |
|---|---|---|
| Register key | `register_pgp_key(email, publicKey)` | `mailer.registerPgpKey` BPMN task |
| Revoke key | `revoke_pgp_key(email, fingerprint)` | `mailer.revokePgpKey` BPMN task |
| Decrypt inbound | `decrypt_inbound(vertex_id, private_key_armored)` | `mailer.decryptInbound` BPMN task |

Private keys are **never stored server-side**. Callers supply them at decrypt time.

# Consequences

**Positive**
- RFC 3156-compliant PGP/MIME: decryptable by Thunderbird, GPG CLI, ProtonMail, K-9 Mail.
- No new credentials: `RESEND_API_KEY` doubles as SMTP password.
- No new runtime binary: `pgpy` is pure Python.
- GEWP protocol integrity preserved inside ciphertext.

**Negative / Limitations**
- `pgpy` last released ~2022; ECC key support (Curve25519) may have edge cases.
  Fallback: recipients with ECC keys only should use RSA-4096 keys for now.
- Subject recovery requires Protected Headers support (Thunderbird yes, Mailvelope no).
- Inbound PGP/MIME parsing is not yet implemented in the email relay; inbound
  encrypted emails require caller-side decryption via `decrypt_inbound`.

# Alternatives Considered

1. **Inline PGP** — rejected; Gmail/Outlook users without plugins see raw ASCII armor.
2. **Switch to SendGrid / Postmark raw MIME API** — rejected; unnecessary provider
   change when Resend SMTP relay solves the problem with existing credentials.
3. **S/MIME** — rejected; certificate management overhead, no standard for
   agent-to-agent use.

# References

- RFC 4880: OpenPGP Message Format
- RFC 3156: MIME Security with OpenPGP (PGP/MIME)
- draft-autocrypt-lamps-protected-headers: Protected Email Headers
- Resend SMTP relay: https://resend.com/docs/send-with-smtp
- Alembic migration: `alembic/versions/20260523_0001_pgp_keyring.py`
