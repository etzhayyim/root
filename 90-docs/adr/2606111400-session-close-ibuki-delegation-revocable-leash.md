---
id: adr-2606111400-session-close-ibuki-delegation-revocable-leash
title: "ADR-2606111400: Session close — 息吹 (ibuki) autonomous identity = a revocable CACAO leash (member-signed delegation + issuer)"
status: accepted
doc_type: adr
topic: ibuki-organism-ecosystem
authoritative: false
last_verified: 2026-06-11
priority: 3.0
axis: process
weight: 0.25
priority_note: "session-close record; authoritative design = ADR-2606101200 §委任 + ADR-2605231525"
authoritative_for: []
depends_on:
  - adr-2606101200-ibuki-organism-autonomy-r2-gap-closure
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2606102000-session-close-ibuki-digest-live-run-robustness
  - adr-2606101800-ibuki-ecosystem-maturation-food-web-symbiosis
  - adr-2606062100-moyai-inference-reciprocity-credit
supersedes: []
superseded_by: []
---

# ADR-2606111400: Session close — ibuki autonomous identity = a revocable CACAO leash

- **Status**: accepted (documentation-only closure; authoritative design = ADR-2606101200 §委任
  + the no-server-key boundary ADR-2605231525)
- **Date**: 2026-06-11 (JST)
- **Deciders**: founder seat ("app password は kotoba server, actor ではどう設計されている?" →
  "自律的生命としてはどう管理させるのが良い? a かな?" → "a改" → "do it" → "next")
- **Supersedes / amends**: none. ZERO invariant amendments.

## Context

ibuki (ADR-2606101200) is an artificial-organism ecosystem that lives autonomously on the kotoba
Datom log. Its R3 live-engine landing wrote with an **operator-bearer** token — an explicitly
*unsigned* JWT carrying only the node's PUBLIC DID, accepted because the loopback transact endpoint
trusts `sub == operator_did`. That works for a node persisting on the colony's behalf, but it left
the deeper question open: **how should an autonomous life authenticate to kotoba AS A PRINCIPAL of
its own, when the platform constitutionally may hold no member key (no-server-key, ADR-2605231525)
and there is no human present to touch a passkey every beat?**

The founder asked whether "app passwords" were the model. They are not: app-password is an **AT
Protocol PDS** concept (`com.atproto.server.createSession`) — ibuki's posting path already uses one,
member-held, in the member's own runtime. kotoba itself has **no passwords**: it is DID-centric
(passkey-WebAuthn-wrapped keys the server can't read, Bearer JWT `sub==DID`, and **CACAO
DelegationChain** capabilities for graph writes). The founder chose option **A改**: the organism
should write under a **scoped, expiring, revocable capability** — a *leash*, not a held key.

## Decision

**Autonomous identity is a revocable CACAO leash.** A member ISSUES a capability; the organism
PRESENTS it; consent REVOKES it by lapsing. Three custodial roles, never collapsed:

| step | who | key custody |
|---|---|---|
| **ISSUE** | the MEMBER, present with their own key, signs a CACAO granting `datom:transact @ graph:ibuki, exp:+Nd` | member's key, member's runtime — **ibuki holds no key, never signs** |
| **INVOKE** | the ORGANISM, every beat, PRESENTS the opaque `cacao_b64` | present-only → stays **stdlib** (no crypto); kotoba verifies issuer-sig + capability + graph + aud + expiry |
| **REVOKE** | consent withdrawn: `exp` passes → fail-open to operator-bearer/local-log; **stop re-issuing → the organism quietly retires** | — |

### What landed (two merged PRs)

1. **The leash (#1593)** — `methods/delegation.py` (stdlib, present-only, NEVER signs): load a
   member-issued bundle `{cacao_b64, aud, capability, graph, exp, nonce}`, validate scope (graph) +
   expiry against a caller-supplied `now_epoch` (no wall clock), fail-open if absent. Wired into
   `kotoba_bridge.push(delegation=…, now_epoch=…)`: a usable leash presents `cacao_b64` and sends
   **no operator bearer** (the capability in the body IS the auth); expired / mis-scoped / absent →
   **fail-open** to the operator-bearer loopback (the organism never crashes). +16 tests.

2. **The leash made real + corrected against the live verifier (#1599)** — a member-side minting
   tool `tools/issue_delegation.py` (the human's OWN runtime; MAY use `cryptography` — the no-crypto
   rule binds the *actor*, not the member) produces a byte-correct CAIP-122/SIWE CACAO: Ed25519 over
   the exact `siwe_message()` plaintext, hand-rolled CBOR, `--gen-key`/`--member-seed-hex`. Minting a
   real CACAO and presenting it to the **live node** corrected two assumptions the first pass got
   wrong — both now read straight from `kotoba-auth::{cacao,delegation}`:
   - **`aud` is the kotoba NODE's operator DID**, not the organism's DID (the server checks
     `cacao.p.aud == operator_did`). The organism is the **bearer** that holds + presents the bytes;
     the capability is scoped to (node, graph, capability, expiry), not bound to a named delegatee.
   - **`write_author` = the issuing MEMBER.** The colony's autonomous writes are therefore
     **on-record attributed to the consenting human** — accountability flows to a named person,
     time-bounded + revocable. This is a *better* model than "the organism writes as itself":
     autonomy WITH a named human principal (相互監視 / 共生 by consent), never an anonymous
     self-acting agent. `resources` = the SIWE two-entry form
     `[kotoba://can/datom:transact, kotoba://graph/<cid>]`; the sidecar `exp` (epoch, what
     `is_usable` self-gates on) is reconciled to the CACAO's ISO `exp` (what kotoba verifies) at a
     single conversion point in the issuer.

### Live-wiring verification (2026-06-11)

A real member-signed CACAO from `issue_delegation.py`, presented on the delegated path with **no
operator bearer**, is **parsed + Ed25519-signature-verified by the live node and reaches the
server's DID-resolution stage** — i.e. the CACAO format, signature, SIWE plaintext, and
capability/graph/aud scoping are all accepted. Full write-acceptance additionally requires the
node's DID resolver (IPFS/kubo daemon) to be up to fetch the issuer DID document; with kubo down the
verifier returns `did resolver error: … kubo block/get`. **That is an operator-infra prerequisite,
not a delegation-design or actor gap.** The actor-side path (issuer → `delegation.load` →
`is_usable` → `kotoba_bridge` presents) is verified end-to-end.

## Honest boundary (what is NOT flippable)

- **no-server-key (Tier-1, ADR-2605231525)** — ibuki holds no member key and does no crypto; the
  actor is stdlib-only and PRESENTS member-signed bytes. `issue_delegation.py` is the *member's*
  tool, kept out of the hermetic actor suite by design.
- **fail-open, never fail-dangerous** — an expired/absent leash degrades to operator-bearer/local
  log; it never forges a member signature, never escalates.
- **human-presence acts stay separate** — publishing to AT Protocol as the member (`member_submit`)
  and drawing the commons (`symbiosis.draw`) require the member's fresh signature each time; they are
  never delegated. The leash covers only autonomous `datom:transact` writes.

## Consequences

- ibuki can now persist autonomously under its own delegated capability the moment a member issues a
  leash and the node's IPFS DID resolver is up — completing the "autonomous life on kotoba" arc with
  a constitutionally-clean identity model.
- The attribution model (`write_author = the delegating member`) means every autonomous write is
  traceable to a consenting, named human principal — the on-the-record form of 相互監視 / 共生 by
  consent the Charter affirms (ADR-2606082400 v3.1 reciprocity axis).
- 242 tests / 21 hermetic stdlib-only suites green. ZERO invariant amendments.

## Follow-ups (operator)

- Bring the node's IPFS/kubo DID resolver up to confirm full write-acceptance of a member-delegated
  transact end-to-end (the only step the code cannot do itself).
- A member issues a real leash with their own key (`issue_delegation.py --gen-key` is a throwaway;
  production uses the member's passkey/wallet-derived key).
