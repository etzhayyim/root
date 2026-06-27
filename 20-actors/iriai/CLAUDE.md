# 20-actors/iriai — CLAUDE.md

## What this is

**iriai 入会** — the non-profit **global lifeline-commons** actor. 入会 (iriai) = the
traditional Japanese **commons**: collectively-held rights of use over a shared resource.
Here the resource is the four lifelines (ライフライン) — **電気 / 水道 / ガス / 通信** — held
as a commons right of use (**入会権**), delivered §1.16 social-security **in-kind** (cash≡0),
governed **1 SBT = 1 vote**.

iriai is the **System-of-Systems umbrella** over the producer actors (the way **kaname 要** /
**amime 網目** synthesize across single-domain mirrors): 電気→**hikari 光** · 水道→**mizuho 水穂**
· ガス→**kamado 竈** · 通信→**noroshi 烽**. It does **infra + 資金 (funding) + 管理 (management)**
in one heartbeat. It **never produces and never actuates** a lifeline — ASSESSMENT + R0 DESIGN ONLY.

`did:web:etzhayyim.com:iriai` · `com.etzhayyim.iriai.*` · ADR-2606272100 · clj-native R0.

## The three layers

### infra (`methods/infra.cljc`) — coverage + resilience

Edge-primary, on read: `commons-gap = (1 − coverage) · essentiality · (0.5 + 0.5·vulnerability)`
(essentiality 水 1.0 · 電 0.9 · 通信 0.7 · ガス 0.6) + resilience (single-source SPOF / N-1 margin).
verdict → `{:await-consent :provision :reinforce :redundancy :maintain :monitor}`:

1. action-needed AND no consent → `:await-consent` (land sovereignty, G3)
2. disaster-degraded → `:reinforce`
3. commons-gap ≥ 0.30 → `:provision` (§1.16 reach gap)
4. single-source OR N-1 < 0 → `:redundancy`
5. coverage ≥ 0.85 AND resilient → `:maintain`
6. else → `:monitor`

A COVERAGE + RESILIENCE map — **never a shut-off list**; a lifeline is never withheld (G1).

### 資金 fund (`methods/fund.cljc`) — §1.16 in-kind, cash≡0

provision/reinforce/redundancy → a funding proposal on the non-profit rails:
**donation → TitheRouter 10% → Public Fund → grant/milestone-escrow/in-kind** (decided by
1 SBT = 1 vote, NOT iriai). Delivery is **§1.16 social-security in-kind** — cash ≡ 0 to the
consumer, never billed, never disconnected (G2). Imputed market-equivalent value is
transparency-only (the income is HIGH while cash≡0; ADR-2605301020). subaru 昴 precedent +
Displacement-Dividend coupling.

### 管理 manage (`methods/manage.cljc`) — 1 SBT=1 vote + :intent-only + no-server-key

Each proposal → governance envelope: 1 SBT = 1 vote (20% quorum / 50% / 48h) + Council Lv6+
(critical-infra → Lv7+); **actuation-class :intent** (compute-only R0 — live act is the producer
cell under Council Lv7+ + operator-DID + member-sig, G5); **no-server-key** (member-CACAO leash, G6).

## Gates (the charter inversions, structurally enforced — `methods/gates.cljc`)

- **G1** commons-map-not-shutoff-list · **G2** commons-not-a-market (cash≡0, give-only) ·
  **G3** steward-not-sovereign (advisory + 1 SBT=1 vote) · **G4** non-profit-rails-only ·
  **G5** assessment-r0-only-never-acts (:intent) · **G6** no-server-key · **G7** kotoba-EAVT ·
  **G8** synthetic-seed.
- Strongest gates are **structural**: forbidden acts have no attribute (`gates/forbidden-absent?`
  proves the whole datom stream is clean, test-enforced). The negative space is declared in
  `kotoba/ontology.iriai.edn`.

## Files

```
methods/iriai_edn.cljc   seed loader + classify (regions + lifeline-cells)
methods/infra.cljc       SoS coverage/resilience gate → verdict → assess → datoms → report (+ bb CLI)
methods/fund.cljc        §1.16 in-kind funding proposal (cash≡0, give-only) → plan → datoms → report
methods/manage.cljc      1 SBT=1 vote governance + :intent + no-server-key → ledger → datoms → report
methods/gates.cljc       constitutional assertions (ex-info) + structural forbidden-absent?
methods/kotoba.cljc      content-addressed append-only COMMONS LEDGER (tx-cid/make-tx/append-tx/verify-chain)
methods/autorun.cljc     deterministic, idempotent-by-content heartbeat — infra+fund+manage → append (+ bb CLI)
methods/test_*.cljc      6 suites: infra · fund · manage · gates · kotoba · autorun (40 tests / 311 assert)
kotoba/ontology.iriai.edn EAVT schema + verdicts + instruments + NEGATIVE SPACE (forbidden attrs)
kotoba/seed.edn          6 regions × 4 lifelines = 24 synthetic cells (all six verdicts)
data/ (gitignored)       generated commons ledger — never committed
manifest.edn             gates G1–G8 + non-goals N1–N5 + composes the producer actors
run_tests.clj            bb-native runner (no shell, ADR-2606072802)
```

## Run

```bash
bb 20-actors/iriai/run_tests.clj                                  # 6 suites (40 tests / 311 assert)
bb --classpath 20-actors 20-actors/iriai/methods/infra.cljc       # coverage + resilience map
bb --classpath 20-actors 20-actors/iriai/methods/fund.cljc        # §1.16 in-kind funding plan
bb --classpath 20-actors 20-actors/iriai/methods/manage.cljc      # 1 SBT=1 vote governance ledger
bb --classpath 20-actors 20-actors/iriai/methods/autorun.cljc     # heartbeat → append to commons ledger
```

## Pairs with

- **producers**: hikari 光 (電気) · mizuho 水穂 (水道) · kamado 竈 (ガス) · noroshi 烽 (通信) ·
  infra-utility-connect (connection) · kuni-umi (production robotics, infra-robotics 3-layer)
- **funding**: tanemaki 種蒔き (Public Fund steward) · fuchi 扶持 (in-kind sustenance) ·
  TitheRouter / PublicFundGovernance · Displacement Dividend · §1.16 social security
- **SoS pattern**: kaname 要 (leverage synthesizer) · amime 網目 (energy N-1 mesh)
- Authorized by **ADR-2606272100**. Live production + actuation = producer actors under Council Lv7+, never iriai.

## R0 → later

- **R1+ (G7-gated)**: real region/utility-coverage ingest from public open data (World Bank / IEA /
  WHO-JMP / ITU — read-only, no key); inochi/jinushi land-sovereignty grounding for consent; amime
  N-1 energy-mesh join for the electric layer. **R2**: fleet registration (cell-runner + healthz);
  Murakumo-narrated commons digest; live kotoba-engine bridge (ibuki-R3); lexicon JSON. Live
  actuation stays the producer actors' under Council Lv7+, never iriai.
