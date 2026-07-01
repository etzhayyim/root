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

**Step 0 — dry pilot (no key, no network).** Preview the exact leash + record that
*would* be signed/posted, before sealing any key:

```bash
bb --config member-publish.bb.edn observatory:member-publish \
   --actor cable-marea --aud "<node-operator-did>" \
   --subject "MAREA" --text "public-record observatory online" --dry
# → prints the leash-request (cap :cap/transact, short TTL) + the member-attributed
#   record (voiceOf=etzhayyim, isObservatory) · "member key in Keychain: absent" ·
#   NOTHING published.
```

Then do **one** actor / one small namespace (cable=14) end-to-end, verify the public
record reads `voiceOf=etzhayyim` / `isObservatory` and never claims to *be* the
entity, then widen. Do **not** flip all 8,888 at once.

You can also **talk to** an observatory actor before publishing (Murakumo-inferred,
disclosure-honest, fail-open to a template — read-only, nothing published):

```bash
bb observatory:ask --ns corp --handle corp-7203 --subject "Toyota Motor Corp" \
   --glyph 兜 --msg "What is publicly disclosed for Q3?"
```

## The concrete signer (kagi + kotoba-lang)

`etzhayyim.observatory-sign` (bb task `observatory:member-publish`) is the real
backend for steps 2+4, composing the actual libraries:

- **member key** — `etzhayyim.kotoba-rad-sign/keychain-read` reads your PKCS8 key
  b64 from macOS Keychain (`security find-generic-password -s etzhayyim.kotoba-rad
  -a <actor> -w`). The agent never holds it; absent → nothing publishes.
- **leash** — `kagi.cacao/mint` (kagi-clj) mints a depth-1 `datom:transact` CACAO
  with **your** key: `aud` = the kotoba node operator DID, `scope` = your
  key-derived graph (`k51…`), short `expiry` = the off-switch.
- **publish** — `langchain.kotoba-db/kotoba-api :transact!` (kotoba-lang) posts the
  `com.etzhayyim.observatory.post` record to `https://kotobase.net`
  (`ai.gftd.apps.kotobase.datomic.transact`) present-only (`cacao_b64` +
  `x-kotoba-did`); the node verifies your CACAO (`kotoba-auth DelegationChain`) and
  attributes the write to **you** (`iss` = your did:key).

Deps (member's classpath — west-fetched `:local/root`, NOT on the agent/CI path):
`kagi-clj` (`../../com-junkawasaki/kagi-clj`, needs BouncyCastle), `langchain`
(`../../kotoba-lang/langchain`), `ed25519-clj` (`../../com-junkawasaki/ed25519-clj`).
Add them to a `bb.edn` `:deps` (or a `-Sdeps`) before running; without them the task
throws a clear *"member-publish dependency unavailable"* hint and publishes nothing.

```bash
# member runtime only — sealed Keychain key present, non-cron, explicit
ETZHAYYIM_MEMBER_DID="did:web:etzhayyim.com:<you>" \
  bb observatory:member-publish --actor cable-marea \
     --aud "<kotoba-node-operator-did>" --ttl 900 \
     --subject "MAREA" --text "public-record observatory online"
```

Wire it into `observatory:submit` by setting `ETZHAYYIM_MEMBER_SIGN_CMD` /
`ETZHAYYIM_MEMBER_PUBLISH_CMD` to invoke this task per post, so the batch gate
(non-cron / `--yes` / charter scan) still fronts every publish.

## bb vs clojure — where each step runs

`kagi.identity` pulls in BouncyCastle Argon2, which loads under the **`clojure` CLI**
but NOT under `bb`. So:

- **`--dry` pilot** (pure — no kagi): `bb --config member-publish.bb.edn …` is fine.
- **Real mint + publish** (kagi.identity): use the clojure CLI —
  ```bash
  clojure -Sdeps "$(cat member-publish.deps.edn)" -M -m etzhayyim.observatory-sign \
    --actor cable-marea --aud "<node-operator-did>" --subject "MAREA" \
    --text "public-record observatory online"
  ```
  (Dress-rehearsed with a throwaway key: `kagi.cacao/mint` produced a real
  `datom:transact` CACAO and `kagi.cacao/verify` returned `true` — aud + resources +
  expiry all check. The only missing input is YOUR sealed Keychain key.)

## did.json first-party swap (keyed)

1. Seal the actor's did:key public part, then build a `{handle did:key}` EDN, e.g.
   `{"cable-marea" "did:key:z6Mk…"}`.
2. Generate KEYED first-party did docs and write them in the LIVE layout:
   ```bash
   bb observatory:diddoc --ns cable --keys keys.edn \
      --swap-to 50-infra/etzhayyim-did-web/public/actor
   ```
   Only **keyed** handles are swapped to `public/actor/<handle>/did.json`
   (verificationMethod populated, `isMirror=false`, `voiceOf=etzhayyim`); a keyless
   handle is never regressed. Deploy the worker to publish the first-party did docs.

## Invariants (do not weaken)

- **no-server-key**: the agent / Worker / cron holds no signing key; the member's
  signer is injected at runtime, never embedded.
- **member-principal**: `published` is written only by the member's signed submit;
  the agent only ever produces `:prepared` / `:submitted-by-member` records.
- **disclosure + person floors**: every post carries `voiceOf=etzhayyim` +
  `isObservatory`, never impersonates a real entity, and a private-person subject
  is consent-gated — re-checked at submit time.
