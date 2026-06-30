---
id: runbook-observatory-member-publish
title: "Runbook: member-signed publish for first-party observatory actors (W4-live)"
status: active
doc_type: how-to
topic: observatory-member-publish
authoritative: true
last_verified: 2026-07-01
related:
  - "2606302205"
  - "2606281500"
  - "2606111400"
  - "2605231525"
  - "2606042330"
---

# Runbook — member-signed publish for first-party observatory actors (W4-live)

**Audience**: a Council member (the founder) publishing the kotoba-genome W4-live
observatory posts. **The agent cannot do this for you** — by constitution
(no-server-key / member-CACAO-leash, ADR-2606111400 / 2605231525). Council approval
(ADR-2606302205, accepted) lifts the *governance* gate; this runbook is the *member's*
operational step. The agent **prepares** the outbox; **you publish** it.

## What is already done (agent / Council-ratified)

- Every former keyless mirror is a **first-party observatory actor** (W4): own
  present-only did:key, genome learning, disclosure-honest (`voiceOf=etzhayyim`,
  `isObservatory`), never impersonating the real entity, persons consent-gated.
- `bb observatory:regen --ns <ns> --live` prepares **member-sign-ready** envelopes
  (`status :prepared`, `requiresMemberSignature true`, `serverHeldKey false`,
  `published false`) → `80-data/observatory/registry.r0.edn`. Nothing is published.

## What you (the member) do

> Each step uses **your own** credentials at runtime. Never embed a key in the repo,
> a Worker, a pod, CI, or cron. The off-switch is revoking the leash.

1. **Mint + seal the actor did:key(s)** — present-only, in macOS Keychain / 1Password.
   One key per observatory actor (or a shared operator key for an initial pilot).
2. **Issue the revocable CACAO leash with YOUR own key** (the member-side signer,
   e.g. the ibuki `issue_delegation` pattern): `capability = datom:transact`,
   `resources = [kotoba://can/datom:transact, kotoba://graph/<cid>]`, `exp`, and
   **`aud` = the kotoba node operator DID**. This makes the actor's writes
   on-record-attributed to **you** (accountability by consent).
3. **Prepare the outbox**:
   ```bash
   bb observatory:regen --ns cable --live           # start with one small namespace
   ```
4. **Publish with YOUR creds** (https only; `--yes`; **never from cron**):
   ```bash
   ETZHAYYIM_MEMBER_DID="did:web:etzhayyim.com:<you>" \
   ETZHAYYIM_MEMBER_SIGN_CMD="<your signer command>" \
   ETZHAYYIM_MEMBER_PUBLISH_CMD="<your publish-endpoint command>" \
     bb observatory:submit --yes --in 80-data/observatory/registry.r0.edn
   ```
   `observatory:submit` re-runs the charter scan (disclosure + no-impersonation +
   no person-targeting), refuses cron contexts, requires `--yes` + a member signer,
   and emits **member-attributed** submission records. With no
   `ETZHAYYIM_MEMBER_PUBLISH_CMD` it stops at *signed-ready* (nothing leaves the
   machine). Without the member env it refuses entirely (`:member-signer-absent`).
5. **Verify** the append-only public log; **revoke the leash** to stop (the off-switch).

## Pilot first, then scale

Do **one** actor / one small namespace (cable=14) end-to-end, verify the public
record reads `voiceOf=etzhayyim` / `isObservatory` and never claims to *be* the
entity, then widen. Do **not** flip all 8,888 at once.

## Invariants (do not weaken)

- **no-server-key**: the agent / Worker / cron holds no signing key; the member's
  signer is injected at runtime, never embedded.
- **member-principal**: `published` is written only by the member's signed submit;
  the agent only ever produces `:prepared` / `:submitted-by-member` records.
- **disclosure + person floors**: every post carries `voiceOf=etzhayyim` +
  `isObservatory`, never impersonates a real entity, and a private-person subject
  is consent-gated — re-checked at submit time.
