---
id: adr-2606022800-openmail-per-member-dkim-no-server-key
title: "ADR-2606022800: openmail outbound — per-member self-signed DKIM (no platform signing key)"
status: proposed
status_note: "Session close 2026-06-02: ADR registered after implementation landed in commit 2ad240504. openmail-smtp-gateway now carries Ed25519 DKIM sign/verify + RFC 8463 Appendix A KAT, per-member DNS helpers, outbound signing assembly, and README custody notes. Remaining follow-ups stay unchanged: client-side ARK signing surface, rsa-sha256 compatibility co-signature, SMTP-out transport/postage orchestration, and live DNS enrollment automation."
doc_type: adr
topic: openmail-outbound-dkim
authoritative: true
last_verified: 2026-06-02
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Refines ADR-2605172200 §3.2: outbound SMTP uses per-member Ed25519 DKIM keys held in the member ARK (client-side), not a single platform-held etzhayyim.com DKIM key. Resolves the only collision between openmail outbound and the no-server-key invariant."
authoritative_for:
  - openmail outbound DKIM key model (per-member, client-held)
  - DKIM ed25519-sha256 signing/verification in 50-infra/openmail-smtp-gateway
  - per-member DKIM DNS publication convention (<selector>._domainkey.etzhayyim.com)
depends_on:
  - adr-2605172200-openmail-atproto-mst-smtp-bridge
  - adr-2606014000-kotoba-passkey-rooted-secrecy
  - adr-2605231525-no-platform-held-signing-key
related:
supersedes: []
superseded_by: []
---

# ADR-2606022800: openmail outbound — per-member self-signed DKIM (no platform signing key)

**Status**: proposed
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

ADR-2605172200 §3.2 (openmail outbound bridge) renders an openmail message to RFC
5322 and **DKIM-signs it with an `etzhayyim.com` selector** before SMTP relay. That
single domain-wide DKIM private key is a **platform-held signing key** — exactly
what the no-server-key invariant (substrate boundary table; ADR-2605231525) forbids
in etzhayyim-operated infrastructure. It is also the worst-case blast radius: a leak
lets an attacker forge outbound mail for *every* member.

The current canonical mail path is kotoba-server's `com.etzhayyim.apps.kotoba.email.*`
(native E2E `email.send` via Signal; bridged ingest via `email.ingest`). The SMTP
gateway (`50-infra/openmail-smtp-gateway/`) is the legacy edge. Its inbound path is
fine (read-only ingress). Its **outbound** path needs DKIM, and DKIM is where the
key-custody question must be answered.

Two options were considered (see Alternatives):

- **(a)** keep a single `etzhayyim.com` DKIM key as a documented infra exception.
- **(b)** give each member their own DKIM key, held in their passkey ARK hierarchy,
  signing client-side; the gateway becomes a dumb relay holding no key.

# Decision

Adopt **option (b): per-member self-signed DKIM.**

## 1. Key custody

- The DKIM **private key** is an Ed25519 purpose-key in the member's ARK hierarchy
  (ADR-2606014000), derived and held **client-side**. The gateway never receives it.
- Signing runs where the key lives. `50-infra/openmail-smtp-gateway/src/{dkim,outbound}.rs`
  is pure and `wasm32`-compilable so the identical canonicalization runs in the
  member's browser.
- The gateway holds **no signing key**. Outbound, it relays already-signed bytes and
  may only prepend unsigned trace headers (`Received:`). It must not alter any signed
  header or the body (byte-exact relay).

## 2. Public key distribution

- The **public key** is published in DNS at `<selector>._domainkey.etzhayyim.com`
  as `v=DKIM1; k=ed25519; p=<base64>` (`dkim::txt_record` / `dkim::dns_record_name`).
  Public material only — automated at member enrollment, no secret custody.
- `<selector>` is a per-member key id, allowing multiple/rotated keys per member.

## 3. Alignment

- `d=etzhayyim.com` aligns with the `From: <localpart>@etzhayyim.com` domain →
  **DMARC passes on DKIM alignment**, while the authorising key is the member's, not
  the platform's.
- SPF stays a domain-level config (the relay IP in the `etzhayyim.com` SPF record);
  it is about the sending IP, not a signing key, so it raises no custody issue.

## 4. Algorithm

- R0 implements `ed25519-sha256` (RFC 8463) with `relaxed/relaxed` canonicalization.
  Correctness is pinned to the **RFC 8463 Appendix A known-answer vector**: the test
  suite verifies the RFC's authoritative signature against the RFC's public key, so
  the signature-base construction is byte-exact and interop-correct.
- RFC 8463 recommends *also* emitting an `rsa-sha256` signature for receivers that do
  not yet accept ed25519 (Gmail today). That co-signature drops in behind the same
  canonicalization, with the RSA key likewise client-held. It is the documented
  compat follow-up, not an architectural change.

## 5. Boundary with the native path

DID/Signal cannot cross the SMTP boundary — the world's MTAs do not resolve
`did:web`. So: **inside** etzhayyim, member↔member mail is DID-addressed + Signal-E2E
(`email.send`); **at** the SMTP boundary, the member speaks standard per-member DKIM.
The DKIM key and the Signal/DID keys are distinct purpose-keys off the same ARK.

# Consequences

## 正の効果

- **No platform-held signing key** — outbound openmail now satisfies the no-server-key
  invariant with no infra exception.
- **Minimal blast radius** — a compromised key forges one member; revocation is a
  single TXT delete. (Compare option (a): one key compromises all outbound.)
- **Member sovereignty** — each member cryptographically owns their outbound identity.
- **Inbound DKIM verify falls out for free** — `dkim::verify` also closes the inbound
  DKIM-check gap (ADR-2605172200 §3.1 attestation).
- **Interop-proven** — pinned to RFC 8463 Appendix A; not a hand-wave.

## 負の効果 / コスト

- **DNS management surface** — one TXT record per member key (thousands are fine on
  Cloudflare; a registry-synthesized authoritative `_domainkey` zone is the escape
  hatch if it grows).
- **Onboarding step** — a member must generate a keypair + publish DNS before first
  outbound send (automated off the ARK-enrollment hook).
- **ed25519-only until RSA co-sign lands** — some legacy receivers will not validate
  DKIM until the `rsa-sha256` co-signature is added (deliverability, not security).
- **Byte-exact relay constraint** — the gateway must not rewrite signed headers/body;
  this constrains future "helpful" gateway transforms.

## Out of scope

- `rsa-sha256` co-signature (compat follow-up).
- Firehose/inbox poller driving outbound, SMTP-out transport, Postage verification.
- ARC sealing for forwarded mail; BIMI.

# Session Close (2026-06-02)

Implementation landed before this registration pass in commit `2ad240504`.
The shipped surface covers the R0 cryptographic core and gateway assembly:

- `50-infra/openmail-smtp-gateway/src/dkim.rs` implements Ed25519 DKIM
  sign/verify, relaxed canonicalization, DNS TXT/name helpers, and the RFC 8463
  Appendix A known-answer test.
- `50-infra/openmail-smtp-gateway/src/outbound.rs` wires render + sign assembly
  while preserving the no-platform-key custody model.
- `50-infra/openmail-smtp-gateway/README.md` documents the per-member key posture
  and inbound DKIM verification reuse.

The ADR remains `proposed` because Council/process ratification and operational
enrollment automation are still pending. The code state is no longer just a
design sketch: R0 sign/verify correctness is implemented and test-pinned.

# Alternatives Considered

## A. Single `etzhayyim.com` DKIM key as a documented infra exception

Keep ADR-2605172200 §3.2 as-is; mark the domain DKIM key as an allowed exception with
a zero-misuse audit window.

却下理由: it is a platform-held signing key — the exact thing the substrate boundary
forbids — and carries all-member forge blast radius. An "exception" normalises the
anti-pattern. Option (b) removes the key entirely at comparable engineering cost.

## B. did:web-based verification instead of DNS DKIM

Have receivers verify the member's DID key via `did:web` rather than DNS DKIM.

却下理由: external MTAs (Gmail, corp, gov) only speak standard DKIM over DNS TXT. They
will never resolve `did:web`. DNS DKIM is the only language the legacy edge accepts;
did:web stays the *internal* (native-path) mechanism.

## C. Gateway signs on the member's behalf with a per-member key it custodies

Gateway holds each member's DKIM private key and signs server-side.

却下理由: still a server-held signing key (many, in fact) — strictly worse custody
than (a). Defeats the entire purpose.

# References

- ADR-2605172200 — Open Email: atproto MST-native mail + SMTP bridge + postage (refined here, §3.2)
- ADR-2606014000 — kotoba passkey-rooted secrecy (ARK purpose-key hierarchy)
- ADR-2605231525 — no platform-held signing key invariant
- RFC 6376 — DKIM Signatures
- RFC 8463 — Ed25519 signing algorithm for DKIM (Appendix A test vector pinned in code)
- RFC 7489 — DMARC
- `50-infra/openmail-smtp-gateway/src/dkim.rs` — sign/verify + RFC 8463 KAT
- `50-infra/openmail-smtp-gateway/src/outbound.rs` — render + sign assembly
- `40-engine/kotoba/crates/kotoba-server/src/email_xrpc.rs` — `email.{list,read,ingest,send}`
