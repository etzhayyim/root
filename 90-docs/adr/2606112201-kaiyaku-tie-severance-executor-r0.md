---
id: adr-2606112201-kaiyaku-tie-severance-executor-r0
title: "ADR-2606112201: kaiyaku 解約 — 縁切り (tie-severance) executor, Tier-B actor R0"
status: proposed
doc_type: adr
topic: kaiyaku-tie-severance-executor
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "closes the organizer subscription-pipeline executor gap (kaiyaku was referenced since organizer's design but never existed)"
authoritative_for:
  - kaiyaku-actor-charter
  - enkiri-ledger-ontology
depends_on:
  - adr-2606039200 # karakuri ServiceOp tiers + ToS stances
  - adr-2606072400 # organizer kotoba-native (subscription-discovery upstream)
  - adr-2605231525 # no-server-key
  - adr-2605215000 # Murakumo-only inference
  - adr-2605312345 # kotoba Datom log = canonical state
related:
  - adr-2605312500 # kurashimori 暮らし守 (クーリングオフ/返金 — adjacent, NOT 解約)
  - adr-2605312030 # toritsugi 取次 (default-self-submit pattern)
  - adr-2605302130 # himotoki 繙き (own-data-only prior art)
  - adr-2605263700 # kokoro 心 (human-relationship support — kaiyaku N1 routes there)
  - adr-2605181100 # encrypted consent envelope
supersedes: []
superseded_by: []
---

# ADR-2606112201: kaiyaku 解約 — 縁切り (tie-severance) executor, Tier-B actor R0

**Status**: proposed
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

The founder asked whether etzhayyim is designed to **identify and sever 有毒な繋がり・
依存・不要なアカウント・クレジットカードの継続支払い** (harmful ties, dependencies,
unneeded accounts, recurring card payments) — 縁切り. A repo survey (2026-06-11) found:

- **Designed but unbuilt executor.** organizer's Subscription Discovery Pipeline
  (`20-actors/organizer/CLAUDE.md`) detects billing mail via mailer, scores usage
  monthly (usageScore < 20 ∧ cost > ¥500 → "cancel"), gets member approval over yoro
  convo chat, then `Invoke("did:web:kaiyaku.etzhayyim.com", "start-cancellation", …)`.
  **kaiyaku did not exist** — no ADR, no directory. The pipeline's last leg was a
  dangling reference.
- **Live primitives, no domain actor.** kotoba `EdgeDelete` can remove graph ties;
  wellbecoming `separation_delta` tracks degrading connections; karakuri
  (ADR-2606039200) already solved the safe-execution problem generically (T1 official
  API > T2 ToS-permitted browser-use > T3 export; evasion unrepresentable).
- **Scope gaps.** Dormant-account inventory (退会), unrecognized recurring card
  charges, and dependency-aware severance (an account that is the SSO / payment root
  of other services) had no owner. kurashimori explicitly excludes 解約 (it owns
  クーリングオフ/返金 rights); tsumugi excludes personal ties by constitutional gate.

# Decision

Create **kaiyaku 解約** (`20-actors/kaiyaku/`, `did:web:etzhayyim.com:actor:kaiyaku`,
aka legacy `did:web:kaiyaku.etzhayyim.com`), the Tier-B **縁切り executor** for the
member's OWN service ties. R0 ships pure-stdlib pywasm-ready methods + synthetic seed +
17 tests green.

## 1. 縁-ledger ontology (edge-primary)

Nodes `:svc/*` (`:svc/kind` ∈ {`:subscription`, `:account`, `:card-merchant`}; cancel
stances `{:api :available|:none, :browser :permitted|:prohibited|:unknown,
:self-submit}`; `:svc/notice-days`, `:svc/penalty-jpy`) + one `:member/*` node. Ties are
`:en/*` edges: member→service (`:subscribes` / `:holds-account` / `:recurring-charge`
with cost, usage-score, last-used-days) and service→service (`:depends-on` — SSO /
payment-method dependency). Lexicons: `com.etzhayyim.apps.kaiyaku.{tieRecord,
enkiriReadout, severancePlan, severanceJob}`.

## 2. enkiri analyze (`methods/analyze.py`)

Per-TIE burden = monthly cost × unused fraction + dormancy, computed **on read**
(emitted as `:bond/is-transient` datoms — G2). Recommendations reuse the **disclosed
organizer thresholds** (usage<20 ∧ cost>¥500 → `:sever`; usage<50 → `:review`;
cost-free account dormant ≥365d → `:sever` 退会候補, ≥180d → `:review`; live
unrecognized `:recurring-charge` → `:sever`). **Cascade-guard (依存 detection)**: a
severable service with `:depends-on` dependents downgrades to `:review-cascade`; its
plan opens with `rehome-dependency` steps. Aggregates stop at totals (`recoverable
¥/mo`); there is **no per-member score** (反個人主義).

## 3. severance plan (`methods/plan.py`) — karakuri composition

Approved `:sever` → dry-run plan through the safest tier (karakuri ADR-2606039200,
composed not re-implemented): **T1** official-API cancel > **T2** ToS-permitted
browser-use over the member's OWN session (`:prohibited`/`:unknown` stance refuses T2
**by construction**) > **T3** generated 解約/退会 self-submit procedure
(toritsugi/kurashimori default-self-submit; always available). Every plan:
`export-own-data` before closure + `confirm-closure`; carries notice-days + 違約金
verbatim (G8); requires `{member_sig, dry_run_confirm, council_lv6_operator_gate}`;
`execute()` **raises at R0** (G5/G6). Evasion verbs (captcha-solve / proxy-rotate /
stealth / rate-limit-bypass / fingerprint-spoof) are structurally unrepresentable.

## 4. Gates G1–G9 / non-goals N1–N6

As in `manifest.edn`. Load-bearing ones: **G1** member-principal own-ties-only
(R0 seed fully `:synthetic`; live facts encrypted per ADR-2605181100); **G2**
edge-primary no-score-of-member; **G3** ToS-honest no-detection-evasion; **G5/G6**
destructive member-sig + dry-run + Council-gated live legs; **G7** ingest
consent-gated (mailer Follow / organizer subscriptionItem / card-statement export);
**G8** cost-of-severance honesty; **G9** kotoba-EAVT audit. **N1: human relationships
are structurally out of scope** — a tie target is always a service (test-enforced);
harmful human relationships route to kokoro 心 (support), never to an executor.

## 5. Pipeline closure

organizer's `CANCELLATION_REQUESTED` edge + `Invoke(…, "start-cancellation", …)` now
lands on a real actor: severanceJob `pending → approved (member-sig) → executed
(Council-gated) → confirmed`, with kaiyaku notifying organizer on completion
(`AppBskyFeedPost` agent mention → subscriptionItem archived), as organizer's
cross-actor table already specified.

## R0 scope (this ADR)

`manifest.edn` + `CLAUDE.md` + synthetic seed + `analyze.py` / `plan.py` /
`datom_emit.py` + 17 tests green. Cells are manifest-declared (langgraph→WASM,
`.solve()` raises) — coded scaffolds, live ingest (G7), member-approval convo leg, and
any live execution (G6) are R1+ follow-ups, each behind its gate.

## R1 — capability-gated severance driver (added 2026-06-21)

R0 left exactly one gap between a member-approved dry-run plan and an actual
cancellation: `plan/execute` raised unconditionally, with no designed path to ever
say *yes*. R1 closes that gap as an **authorization boundary, not live I/O** — the
karakuri `adapter_live` / fuchi `live_gate` pattern, ported into kaiyaku:

- **`methods/cap.cljc` — the revocable leash.** A severance is destructive, so the
  credential is neither a platform-held key (prohibited, no-server-key ADR-2605231525)
  nor a per-tie passkey touch. It is a **scoped, expiring, revocable kotoba CACAO
  capability** the MEMBER signs in their OWN runtime and hands kaiyaku to PRESENT
  (kaiyaku holds no key, never signs — present-only, mirrors ibuki `delegation.cljc`,
  ADR-2606111400). kaiyaku **tightens** the ibuki leash: the bundle carries an
  `approved` svc-id ALLOWLIST = the exact set the member approved at the G5
  human-in-the-loop interrupt, so the member-sig gate and the capability scope become
  ONE artifact. `usable?` is a pure fn of bundle metadata against a caller-supplied
  `:now-epoch` (no wall clock); `aud` is the kotoba NODE DID; `write_author` resolves
  to the issuing member (severance attributed on-record to the consenting human).
- **`methods/driver.cljc` — authorize, never execute.** `dispatch` / `dispatch-batch`
  verify the capability and return an authorization DESCRIPTOR with `executed:false` /
  `server_signed:false`; the actual T1-API / T2-browser / T3-handoff driver remains a
  separate post-R1 component. Four invariants, each test-enforced:
  1. **G3 no-server-key** — absent/expired/wrong-graph/not-approved capability →
     `:refused` (the batch never throws, so one bad tie can't abort the rest).
  2. **G5-in-the-leash** — a tie not in `approved` is never severable, even under a
     valid unexpired bundle.
  3. **cascade ordering (依存)** — a `:review-cascade` plan is never live-dispatched
     (dependents must be re-homed first); for a `:sever` plan, `assert-cascade-order`
     structurally guarantees every `rehome-dependency` step precedes the irreversible
     cancel step.
  4. **exactly-once (冪等)** — `dispatch-batch` threads an `already-severed` cursor;
     a re-run / resume of the same batch is a no-op (no double cancellation).
  T3 self-submit is **never sent** — the descriptor says the member submits it.

`plan/execute` still raises (R0 contract untouched): no code path performs a live
cancellation. R1 is the *design* of the authorized path + its gates, proven green
(`run_tests.sh`: 41 tests / 254 assertions, +10 `test_driver` deftests), with live
network I/O still gated to a post-R1 driver behind G6 (Council Lv6+ + operator +
member-presented capability). Still-open R1 data gap: the real-service cancellation
procedure catalog (R0 seed is 9 synthetic `:representative` ties).

# Consequences

- The 縁切り question now has a designed, test-enforced answer: subscriptions, dormant
  accounts, recurring card charges, and their dependencies are identified and routed
  to release — while human-relationship severance is *explicitly refused* rather than
  silently absent.
- organizer's pipeline stops dangling; the executor exists with stricter gates than
  the upstream detector (destructive = member-sig + Council).
- kaiyaku takes a dependency on karakuri's adapter substrate; karakuri stance-registry
  growth directly widens kaiyaku's T1/T2 coverage.
- A new actor must be maintained; until R1+ live legs land, members get readouts +
  dry-run plans + self-submit procedures only (honest about it — G6).

# Alternatives Considered

1. **Extend organizer with an execution leg.** Rejected: detection (confidential,
   reactive) and destructive execution (member-sig + Council) want different gate
   profiles; organizer's note already deferred the pipeline as a follow-up.
2. **Make kaiyaku a karakuri verb (`cancel`) instead of an actor.** Rejected: the
   縁-ledger, dormancy/dependency analysis, severanceJob lifecycle, and 解約-specific
   honesty gates (notice/違約金) are a domain, not a verb. karakuri stays the execution
   substrate.
3. **Include human-relationship 縁切り.** Rejected (N1): scoring persons violates the
   edge-primary / no-score-of-soul line (tsumugi G1 precedent) and Wellbecoming;
   support belongs to kokoro 心.
4. **Real seed data.** Rejected (G1): committed ledgers stay synthetic; live member
   facts are consent-gated and encrypted.

# References

- `20-actors/kaiyaku/` (this actor) · `20-actors/organizer/CLAUDE.md` (upstream
  pipeline + thresholds) · ADR-2606039200 (karakuri) · ADR-2605312500 (kurashimori
  boundary) · ADR-2605263700 (kokoro) · ADR-2605312345 (Datom canonical state) ·
  ADR-2605231525 (no-server-key) · ADR-2605215000 (Murakumo-only) · ADR-2605181100
  (encrypted envelope)
