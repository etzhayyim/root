# kaiyaku 解約 — 縁切り (tie-severance) executor

**DID**: `did:web:etzhayyim.com:actor:kaiyaku` (aka legacy `did:web:kaiyaku.etzhayyim.com`) ·
**Tier**: B · **Status**: 🟡 R0 · **ADR**: 2606112200 · **depends**: 2606039200 (karakuri
ServiceOp tiers) · 2606072400 (organizer upstream) · 2605231525 (no-server-key) ·
2605215000 (Murakumo-only) · 2605312345 (Datom = canonical state)

## What this is

The actor that **severs the member's own unwanted service ties** — the missing executor
the organizer subscription-discovery pipeline has pointed at since its design
(`mailer → organizer → kaiyaku`, organizer CLAUDE.md). 縁切り here is the member releasing
their OWN accumulated digital ties: **unused subscriptions (解約), dormant accounts (退会),
unrecognized recurring card charges, and the SSO / payment-method dependencies** that make
severing them risky.

Three legs:

1. **縁-ledger** — the member's service ties as `:en/*` edges over `:svc/*` nodes in the
   kotoba Datom log (R0 = synthetic demo seed; live ingest from mailer/organizer/card-export
   is G7-gated).
2. **enkiri analyze** (`methods/analyze.py`) — per-TIE burden (cost × unused fraction +
   dormancy) routed to `:keep / :review / :sever`, using the **disclosed organizer
   thresholds** (usage<20 ∧ cost>¥500 → sever; <50 → review; cost-free account dormant
   ≥365d → sever) + a **dependency cascade-guard**: a severable service that other ties
   stand on (SSO / payment-method) downgrades to `:review-cascade` and plans a
   `rehome-dependency` step first — 依存 is detected, never blindly cut.
3. **severance plan** (`methods/plan.py`) — an approved `:sever` becomes a dry-run plan
   through the safest adapter tier (karakuri pattern): **T1 official-API cancel > T2
   ToS-permitted browser-use > T3 self-submit 解約/退会 procedure** (toritsugi/kurashimori
   default-self-submit). Every plan exports the member's own data before closure and ends
   with a closure confirmation step.

## Hard gates (constitutional — read before any change)

- **G1 member-principal, own ties only.** The ledger is the member's OWN service ties,
  consent-bound; live member facts ship encrypted (`com.etzhayyim.encrypted.*`). R0 seed
  is fully `:synthetic`. Never a third party's accounts.
- **G2 edge-primary, no score-of-member.** Burden / recommendation live ONLY on ties,
  computed on READ (emitted as `:bond/is-transient` datoms). There is no per-member
  score and **no "toxic person" rating** (反個人主義).
- **G3 ToS-honest, no detection-evasion.** T2 only where the service browser stance
  permits; `:prohibited` / `:unknown` refuses T2 **by construction** (`select_tier`);
  evasion verbs (captcha-solve / proxy-rotate / stealth / rate-limit-bypass /
  fingerprint-spoof) are **unrepresentable** — `_make_step` raises.
- **G5/G6 destructive-gated.** 解約/退会 is destructive: member-sig + explicit dry-run
  confirm required on every plan; **live execution is Council Lv6+ + operator gated** —
  `execute()` raises at R0.
- **G8 cost-of-severance honesty.** Notice period / 違約金 are carried into every readout
  and plan and **never planned around**; thresholds are the disclosed organizer rules.
- **G9 kotoba-EAVT audit.** Every readout + plan is a Datom; the member can audit
  exactly what kaiyaku touched.

## Non-goals

**N1 — NOT a human-relationship severance tool.** A tie target is always a SERVICE
(`:svc/*`), never a person (enforced by test). No contact-blocking, no relationship
scoring; a member dealing with a harmful human relationship routes to **kokoro 心**
(mental-health support, ADR-2605263700). · N2 no retention-flow trickery / anti-bot
circumvention · N3 no debt evasion / 取立 / chargeback abuse (kurashimori owns
クーリングオフ/返金 **rights**; kaiyaku owns 解約/退会 **execution**) · N4 no third-party
account operation / credential custody · N5 not a mass-unsubscribe bot · N6 no financial
advice.

## Boundaries (who owns what)

| Concern | Owner |
|---|---|
| Detect subscriptions from billing mail, monthly usage scoring | **organizer** (upstream; Follow on mailer inboundEmail) |
| クーリングオフ / 返金 / 消費者庁 escalation (rights) | **kurashimori** |
| Generic web-service ServiceOp adapters (T1/T2 engine, ToS stances) | **karakuri** (kaiyaku composes; never re-implements) |
| 解約 / 退会 decision-ledger + severance plan + (gated) execution | **kaiyaku** (this actor) |
| Harmful human relationships | **kokoro** (support; kaiyaku N1 refuses the domain) |

## Layout

```
20-actors/kaiyaku/
├── CLAUDE.md                          # this file
├── manifest.edn                       # actor manifest (5 cells, 9 gates, 6 non-goals)
├── data/
│   └── seed-en-ledger.kotoba.edn      # SYNTHETIC demo 縁-ledger (no real PII — G1)
├── methods/                           # pure-stdlib → kotoba pywasm-runnable
│   ├── analyze.py                     # edge-primary tie-burden analyzer + cascade-guard
│   ├── plan.py                        # T1/T2/T3 severance-plan builder (dry-run only)
│   └── datom_emit.py                  # kotoba Datom-log (EAVT) emitter — canonical state
├── tests/                             # 17 tests, pure stdlib
│   ├── test_analyze.py
│   └── test_plan.py
└── out/                               # GENERATED — do not hand-edit
    ├── enkiri-readout.md
    ├── severance-plans.md
    └── enkiri-datoms.kotoba.edn
```

## Run

```bash
cd 20-actors/kaiyaku
python3 methods/analyze.py            # → out/enkiri-readout.md
python3 methods/plan.py               # → out/severance-plans.md (dry-run)
python3 methods/datom_emit.py         # → out/enkiri-datoms.kotoba.edn (EAVT)
python3 tests/test_analyze.py && python3 tests/test_plan.py   # 17 green
```

## Do not

- Do not add a person / contact / relationship node kind to the ledger, or any
  per-member aggregate score — N1 / G2 (tests enforce both).
- Do not return T2 for a `:prohibited` or `:unknown` browser stance, and never add an
  evasion verb — G3 (`_make_step` raises; tests enforce).
- Do not let any code path execute a live cancellation — `execute()` raises at R0;
  live legs are Council Lv6+ + operator + member-sig gated (G5/G6).
- Do not plan around a notice period / 違約金, and do not absorb kurashimori's
  クーリングオフ/返金 scope — G8 / N3.
- Do not ingest real member data into `data/` — the committed seed stays `:synthetic`;
  live ingest is consent- + G7-gated and encrypted (ADR-2605181100).
