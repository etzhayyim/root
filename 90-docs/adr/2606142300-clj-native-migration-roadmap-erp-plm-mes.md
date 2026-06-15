---
id: adr-2606142300-clj-native-migration-roadmap-erp-plm-mes
title: "ADR-2606142300: clj-native migration roadmap for ERP / PLM / MES actors (kotoba Datom-log + langgraph-clj)"
status: accepted
doc_type: adr
topic: clj-native-migration-roadmap-erp-plm-mes
authoritative: true
last_verified: 2026-06-14
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - clj-native migration priority/order for the ERP / PLM / MES actor families
  - the "logic-core to Clojure, UI to TS, physics to Rust" partition rule
  - byte-identical port discipline + dependency-ordered (additive) migration rule
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2606141200-matsurigoto-tax-collect-jp-withholding-remittance
  - adr-2606037200-open-kyber-kotoba-datomic-erp-isic-productivity
supersedes: []
superseded_by: []
---

# ADR-2606142300: clj-native migration roadmap for ERP / PLM / MES actors

**Status**: accepted
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

The substrate question ("on what do ERP / PLM / MES state live?") is **already
answered and largely shipped**: every ERP / PLM / MES actor uses the **kotoba
Datom log (EAVT, content-addressed, append-only)** as canonical state, with
RisingWave / Postgres / Kysely / SQL structurally excluded (ADR-2605262130 +
ADR-2605312345). The remaining question is the *implementation language* of the
actor **logic**.

`bb.edn` already declares the migration vehicle: "actor code ported off Python/TS
onto the kotoba Datom-log + **langgraph-clj / langchain-clj** stack." The Clojure
substrate primitives needed to land there already exist:

- `etzhayyim.kotoba.*` — the clj Datom-log commit-DAG binding + encrypted-record envelope;
- `kotoba.datom` (`20-actors/kotodama/src`), `moyai.ledger` (reciprocity-credit primitive);
- `langgraph-clj` Pregel cells + `langchain-clj`;
- a **clj → WASM cell** path via the `kotoba-clj` CLI (landed shape: ISCO/APQC, PR #1739).

clj-native test suites are already green for `kotoba`, `mimamori`, `yobel`, `ibuki`,
and the recent wave (`danjo` revenue-ledger family #1742, `matsurigoto` tax-collect
#1743, `umisachi` + `funadaiku`/`ainori` ports #1745, the `kuramori`/`soma`/`madomori`/
`kudamori` robotics-gap actors #1740).

**Survey snapshot (2026-06-14).** Across the three families:

| Family | Canonical actor(s) | substrate | impl language today | maturity |
|---|---|---|---|---|
| **ERP** | open-kyber (core), iryo, toritate, matsurigoto, danjo, fuchi | kotoba ✓ | open-kyber **100% TS**; iryo/matsurigoto **Py**; danjo/fuchi **Py+clj**; toritate scaffold | open-kyber 🟢 R1+R2; fuchi 🟢 R2; rest 🟡 R0 |
| **PLM** | uchiwake (BOM/GTIN), kabuto (SC), sumitsubo (CAD), giemon (SBOM), kami-engine | kotoba ✓ | uchiwake/kabuto/giemon **Py**; sumitsubo **TS**; kami-engine **Rust** | kabuto/giemon/kami 🟢; uchiwake/sumitsubo R0 |
| **MES** | giemon-factory, sarutahiko, niyaku, kuni-umi, open-ot, sanae/hataori/kiyome, tatekata | kotoba ✓ / kami-genesis | physics **Rust**; orchestration cells **Py LangGraph** (a few FSMs clj) | kuni-umi 🟢 R0+R1; niyaku/giemon-factory/sarutahiko 🟢 R0; rest 🟡 R0 |

So: the **floor is built (kotoba), the language migration has begun at the edges,
but the basal ERP/PLM/MES logic is still Python/TS/Rust.** A migration that tries
to rewrite everything (incl. open-kyber's 70-file TS UI or kami-genesis's Rust
physics) into Clojure would be expensive and value-destroying. We need a partition
rule and a priority order.

# Decision

## D1 — Partition rule (what becomes Clojure, what does not)

Migrate to clj **only the correctness-critical logic core**; leave UI/transport in
TS and numeric/real-time in Rust.

- **→ Clojure**: exact-arithmetic + invariant + datalog/graph logic — accounting
  postings, tax computation, BOM/supply-chain graphs, policy/charter invariants,
  Pregel orchestration cells. This is Clojure's sweet spot and the kotoba Datom log
  is already its native home.
- **stays TypeScript**: large UI + XRPC Worker shells (open-kyber app, sumitsubo
  geometry kernel). Extract the *logic core* out of these into clj libs; keep the
  shell.
- **stays Rust**: kami-engine / kami-genesis physics, and any tight (≥100 Hz) /
  real-time control loop or field function-block (open-ot, kuni-umi numeric control).
  Determinism + performance, not Clojure's job.

## D2 — Migration discipline (how each port is done)

1. **Byte-identical port.** A clj port of a Python/TS method MUST reproduce its
   externally observable outputs bit-for-bit where those outputs are content-addressed
   (CIDs / hashes). Prove it with a golden-value parity test against the original
   (the repo's established "port" bar: funadaiku, umisachi).
2. **Dependency-ordered + additive.** Port in consumer-dependency order. If a method
   has a live downstream consumer in another language, the port is **additive** — the
   original-language shim stays until the consumer is also ported. Byte-identical CIDs
   make the eventual swap transparent.
3. **Charter discipline preserved in code.** Every actor's gates (G-numbers in its
   ADR/CLAUDE.md) must remain enforced *in the clj code* and proven by tests, never
   merely documented (e.g. danjo non-adjudication G4: a verdict token is unrepresentable).
4. **Murakumo-only inference** (ADR-2605215000) and **no-server-key** (ADR-2605231525)
   carry over unchanged.

## D3 — Priority order (waves)

**Wave 1 — accounting / tax / allocation core** (highest ROI: correctness-critical,
pure-stdlib, already part-clj):
- `matsurigoto` — finish the remaining Py modules (assess / civil / corp) in clj (税 already clj, #1743).
- `danjo` — finish in clj: `budget_ledger` (this ADR's landed first step), then `analyze` / `autorun` / `kotoba`.
- `fuchi` — consolidate the Py(38)+clj(10) split fully onto clj (currency≡0 invariants).
- `toritate` (R0 scaffold) — stand up as the **clj ERP accounting engine**: extract
  open-kyber's GL / double-entry (as-of) / ISIC-COA / tax rules into a clj lib on
  `etzhayyim.kotoba`, leaving open-kyber's TS as the UI/XRPC shell (per D1).

**Wave 2 — PLM graph / policy layer** (datalog-shaped, pure-stdlib Py today):
- `uchiwake` (BOM/GTIN graph) and `kabuto` (supply-chain HHI/centrality) → clj over
  EAVT + kotoba-kqe; `kabuto` live-ingest may stay Py during phased cutover.
- `giemon` SBOM↔kotoba bridge (CycloneDX → EAVT, purl↔CVE) → clj.

**Wave 3 — MES orchestration cells** (the explicit `langgraph-clj` target):
- Port the Python LangGraph Pregel cells (`niyaku`, `sarutahiko`, `sanae`/`hataori`/
  `kiyome`, `tatekata`) to `langgraph-clj`, each compiled clj → WASM via `kotoba-clj`.
  The `kuramori`/`soma`/`madomori`/`kudamori` robotics-gap actors (#1740) are the
  precedent. kami-genesis physics + tight control loops stay Rust/WASM (D1).

## D4 — Explicit non-goals
Whole-actor rewrites of open-kyber's UI, kami-engine/kami-genesis physics, open-ot
field function-blocks, or the sumitsubo geometry kernel. These stay in their current
language by D1.

# Consequences

- **Positive.** Correctness-critical logic gains Clojure's data/invariant ergonomics
  and lives natively on the kotoba Datom log; charter gates become code-enforced;
  the clj → WASM cell path unifies actor execution. Byte-identical discipline makes
  the migration reversible/verifiable at every step.
- **Cost.** A transitional period of mixed-language actors (Py shim + clj core) until
  downstream consumers are ported. This is accepted and made safe by D2.2 (additive)
  + D2.1 (byte parity).
- **First landed step (this ADR).** `danjo/methods/budget_ledger.py` → `budget_ledger.clj`
  (+ `test_budget_ledger.clj`, wired into `run_tests_clj.sh`): a Python-compatible
  canonical-JSON encoder reproduces `record_cid` **byte-for-byte** (golden CIDs proven
  on synthetic *and* real seed data), normalize/group logic ported, G4 non-adjudication
  + G5 provenance enforced in tests (17/17 green; full danjo clj suite green). Per
  D2.2 the `.py` shim is **retained** because kanae's Python pipeline
  (`assemble_flows.py` / `test_pipeline.py` / `project_yoro.py`) still imports
  `danjo.methods.budget_ledger`; it will be removed when kanae is ported (Wave 2-adjacent).
- **Second step — already done (correction).** `danjo/methods/analyze.py` was **already ported**
  to `analyze.cljc` (ns `danjo.methods.analyze`, classpath-wired into `bb test:actors` via
  `test_analyze.cljc`) before this wave. An earlier iteration mistakenly re-ported it to a
  redundant `analyze.clj` (ns `root.danjo.methods.analyze`), which **shadowed** the canonical
  `.cljc` on the classpath and broke `(require 'danjo.methods.test-analyze)`. The duplicate
  `analyze.clj`/`test_analyze.clj` were **removed**; `autorun.clj` + `test_kotoba.clj` now
  `load-file` the canonical `analyze.cljc`, and `kotoba.clj`'s `derived-datoms` reads the
  observation map tolerant of the canonical **string** keys (`"sourceRecordCids"` …, matching
  Python/`.cljc`) as well as keyword keys (`oget` helper). Lesson for Waves 2/3: **check for an
  existing `.cljc` before porting** (uchiwake, asobi, hoshimori, inochi, … are already `.cljc`),
  and never let a load-file `.clj` shadow a classpath-wired `.cljc` at the same path.
- **Tooling hardening — `bb test:actors` made robust.** Surfacing the above also exposed that the
  test auto-discovery (`etzhayyim.tools.discovery`, ADR-2606131500) derives a test's ns from its
  PATH and `require`s it, which **crashes** on `run_tests_clj.sh`-style suites that declare a
  non-path ns (`root.danjo.methods.*`) and load deps via cwd-relative `(load-file …)` — danjo (and
  #1742's danjo tests on `origin/main`) hit this. Fix: `actor-test-nss` now includes a file **only
  if its DECLARED ns equals the path-derived ns** (new `declared-ns` reads the `(ns …)` form with
  `:read-cond :allow`), cleanly skipping the externally-run suites while keeping every classpath-safe
  `.cljc`/`.clj` test. `bb test:actors` goes from an immediate `FileNotFoundException` to green
  (21 deftests / 73 assertions across 156 discovered nss, 0 failures); danjo's own
  `run_tests_clj.sh` (10 suites / 201 checks) is unaffected. Covered by a new
  `etzhayyim.tools.test-discovery` (2 tests / 9 assertions) wired into `bb test:tools`.
- **Third landed step (same wave).** `danjo/methods/kotoba.py` → `kotoba.clj` (+ `test_kotoba.clj`):
  the local content-addressed commit-DAG log writer (`graph-datoms` / `derived-datoms` /
  `tx-cid` / `make-tx` / `append-tx` / `read-log` / `head-cid` / `verify-chain`). The
  content-bearing derived-observation transaction is **byte-identical** with kotoba.py
  (golden `tx_cid b028f0f845c1…`), with commit-DAG round-trip + tamper-detection proven
  (16/16). Datoms are modelled with idiomatic Clojure keywords (`:db/add`, `:danjo.obs/*`)
  whose canonical-JSON rendering equals kotoba.py's `":"`-prefixed string literals, so the
  CID matches without giving up clj ergonomics; `read-log` uses native `clojure.edn`.
  `graph-datoms` emission order is canonicalized (sorted by attr) for parser-independent
  determinism — bb's cheshire does not preserve JSON key order, and a deterministic order is
  the resume-safety property that matters; the constitutionally-meaningful derived tx is
  order-independent and byte-exact. After this, danjo's data layer is clj-native; only the
  thin `autorun.py` orchestrator remains Python (imports `analyze`/`kotoba`; next step).
  *Cleanup noted*: budget_ledger / analyze / kotoba each carry a small canonical-JSON encoder
  (two `ensure_ascii=False`, one `=True`) — a shared `danjo` clj util is a future tidy.
- **Fourth landed step — danjo pipeline complete.** `danjo/methods/autorun.py` → `autorun.clj`
  (+ `test_autorun.clj`): the autonomous observe→detect→persist heartbeat over `analyze.clj` +
  `kotoba.clj`. Per D1 this is thin orchestration, so the meaningful guarantees are behavioral
  not byte-CID (the combined per-cycle tx mixes graph-datoms, whose order is canonicalized
  differently from kotoba.py): **deterministic / resume-safe** (two fresh runs → identical
  per-cycle CIDs), append-only (re-run extends the DAG, never rewrites), commit-DAG verifies,
  and **G4** (no verdict attr in the persisted log) + **G5** (≥2 source CIDs) hold over the
  actual persisted EDN (14/14). With this, **all four danjo core methods are clj-native**
  (budget_ledger / analyze / kotoba / autorun) — 11 danjo clj suites / 188 checks green. The
  Python files are retained as D2.2 shims (kanae still imports `budget_ledger`; `autorun.py`
  is a fleet cron entry point) and retire when those consumers port. danjo is the **worked
  reference** for Wave 1; matsurigoto (finish assess/civil/corp) and fuchi follow.
- **Wave 1 — matsurigoto begins.** `matsurigoto/methods/modules/tax_assess.py` → `tax_assess.clj`
  (+ `test_tax_assess.clj`): the progressive marginal-bracket assessment engine + VAT + unsigned
  receipt (G1). Reference liabilities are reproduced **exactly** against the published JP 速算表
  (golden e.g. taxable 5,000,000 → 572,500 JPY; 9,000,000 → 1,434,000; eff-rate half-to-even
  matches Python `round`); per-jurisdiction rate tables load natively via `clojure.edn` (7 tables
  incl. USA/DEU/GBR/IND/KOR). G1 (signs nothing — `:proof nil`, `server-held-authority false`) +
  the live-filing Council/operator gate (`solve` raises) enforced (7 tests / 37 assertions; full
  matsurigoto clj suite 53 tests / 205 assertions green). Follows the cleaner `clojure.test` +
  classpath pattern (ns `matsurigoto.*`, `bb test:matsurigoto`) the tax-collect module established
  (#1743). Remaining matsurigoto modules to port: `civil_registry` / `corp_registry` /
  `credential_issue` / `datoms` / `sign_capability` / `standard`.
- **Wave 1 — matsurigoto `corp-registry`.** `corp_registry.py` → `corp_registry.clj`
  (+ `test_corp_registry.clj`): 法人登記 — ISO 17442 LEI issuance with a real **ISO 7064
  MOD 97-10** check-digit (BigInteger), append-only registry records, unsigned VC certificate.
  LEI checksums are **byte-equivalent** with the Python (golden `EZHY0000000000000168`,
  `549300ACME0000000169`; corruption rejected with prob 96/97); G1 (unsigned cert) + G5
  (append-only amendment, never overwrite) + live-registration Council/operator gate enforced
  (7 tests / 35 assertions; full matsurigoto clj suite **60 tests / 240 assertions green**).
  matsurigoto now **2/7** reference modules clj-native (tax-assess + corp-registry); remaining:
  `civil_registry` / `credential_issue` / `datoms` / `sign_capability` / `standard`.
- **Wave 1 — matsurigoto `civil-registry`.** `civil_registry.py` → `civil_registry.clj`
  (+ `test_civil_registry.clj`): the CRVS engine (戸籍・住所管理) for birth/death/marriage/
  residency — UN CRVS + OpenCRVS validation (birth needs child+≥1 parent+non-future; marriage
  needs two distinct, monogamous partners; partners stored sorted), append-only records +
  unsigned VC certificates, `current-address` = latest residency by occurred-at (非終末論).
  G1 (unsigned) + G5 (append-only — prior address retained, never overwritten) + G6
  (data-minimization — no `:cause` unless given) + live-registration gate enforced (6 tests /
  28 assertions; full matsurigoto clj suite **66 tests / 268 assertions green**). matsurigoto
  now **3/7** reference modules clj-native; remaining: `credential_issue` / `datoms` /
  `sign_capability` / `standard`.
- **Wave 1 — matsurigoto `credential-issue`.** `credential_issue.py` → `credential_issue.clj`
  (+ `test_credential_issue.clj`): パスポート発行 — ICAO Doc 9303 **TD3 MRZ** builder with the
  real **7-3-1 weighted check-digit**. The canonical ICAO worked example (`L898902C3`→`6`,
  `740812`→`2`) and the full ERIKSSON specimen line 2 (`L898902C36UTO7408122F1204159ZE184226B<<<<<10`)
  are **byte-identical** with the Python. G1 (SOD + proof unsigned — issuing state signs via
  ICAO-PKD) + G6 (MRZ fields only) + live-issuance Council/operator gate enforced (5 tests /
  25 assertions; full matsurigoto clj suite **71 tests / 293 assertions green**). matsurigoto
  now **4/7** reference modules clj-native; remaining: `datoms` / `sign_capability` / `standard`.
- **Wave 1 — matsurigoto `datoms` (the substrate membrane).** `datoms.py` → `datoms.clj`
  (+ `test_datoms.clj`): the EAVT bridge that ties the four ported reference modules into the
  kotoba Datom log — converts each module's clj output into append-only `egov-exec-v1` datoms +
  a `kg.ingest_batch` body. Enforced in code: **G1** (`:egov.tx/server-held-authority false`,
  cert `:egov.cert/proof` nil, `assert-unsigned!` rejects a signed artifact), **G3** (`:operated-by`
  / `:authority-mode` allow-lists), **G5** (`:egov.record/immutable true`), **G8** (`kg-ingest-batch`
  `:published true` RAISES — live ingest Council/operator-gated). Golden count parity with
  datoms.py (tax-assess → 17 datoms) + correct per-module cert kinds (4 tests / 25 assertions;
  full matsurigoto clj suite **75 tests / 318 assertions green**). matsurigoto now **5/7**
  clj-native (the four verticals + the substrate membrane); remaining `sign_capability` /
  `standard` are capability/COFOG glue.
- **Wave 1 — matsurigoto `sign-capability` (no-server-key layer).** `sign_capability.py` →
  `sign_capability.clj` (+ `test_sign_capability.clj`): the verify-only sign/authority layer
  (ADR-2605231525). matsurigoto holds NO key — `signer-held-private-key` false, `sign-server-side`
  always RAISES; it only emits the canonical payload and ATTACHES an externally-produced signature
  after checking the signer is legitimate for the principal (**A** = Council `did:web:etzhayyim.com:council:*`;
  **B** = the adopting state's OWN non-etzhayyim did). `verify-proof` is structural (legitimate
  signer + sha256 payload integrity over content minus proof/status); tamper after signing breaks
  it. The payload digest is an INTERNAL integrity hash (not a cross-system content address), so no
  byte-parity with Python is claimed (the one place in this wave where parity is behavioral, not
  byte-exact). 6 tests / 16 assertions; full matsurigoto clj suite **81 tests / 334 assertions
  green**. matsurigoto now **6/7** clj-native; only `standard` (COFOG service catalogue) remains.
- **Wave 1 — matsurigoto `standard` → matsurigoto COMPLETE (7/7).** `standard.py` →
  `standard.clj` (+ `test_standard.clj`): the COFOG e-gov service-standard loader / validator /
  coverage reporter. clojure.edn reads the standard + per-country profiles natively (merge +
  dedup by iso3). `validate` enforces the charter invariants structurally (G1 every service
  `{:server-held-authority false}`, G2 non-empty `:spec-basis`, G3 every profile a legitimate
  `:operated-by`/`:authority-mode` — polities Council/sovereign, adopters state/supplied) + COFOG
  backbone (10 divisions) + known module/class references; `coverage` figures match standard.py
  goldens exactly (0 errors, **3/10** divisions, **6/69** groups, **22** services, all 4 required
  domains, 8 country adopters). A porting subtlety surfaced + tested: this EDN stores keyword-like
  enum *values* as `":"`-prefixed STRINGS (matching the Python `_edn` representation) while
  structural keys + the `:invariants` map use real keywords/booleans — the clj port matches
  strings for the enums (5 tests / 18 assertions). **matsurigoto clj suite now 86 tests / 352
  assertions green — matsurigoto is fully clj-native (7/7 modules).** Wave 1 actors: danjo ✅,
  matsurigoto ✅; **fuchi** (consolidate the Py(38)+clj(10) split) is the remaining Wave-1 actor.
- **Wave 1 — fuchi begins (`allocate`).** `fuchi/methods/allocate.py` → `allocate.clj`
  (+ `test_allocate.clj`, new `bb test:fuchi` task) — THE HEART of fuchi: tenure-weighted in-kind
  sustenance allocation, the charter-clean inverse of an investment fund's cap-table. The
  Displacement-Dividend curve `w = ln(1+min(tenure,40))×hazard` is byte-equivalent with the Python
  (golden tw=7.427144133408616; shares 0.805643/0.194357; ranks/floors exact; `round`/`int(round)`
  mirror half-to-even). The invariants are enforced **in code + tests**: **cash≡0** structurally on
  every allocation (N1), instrument ∈ {in-kind-grant/sustenance/tooling/compute} — equity/debt/
  carry/dividend/… **RAISE** (G1, Charter-Rider §2(b)), **G5** owns-payoff raises (work product is
  commons), **G9** no-server-key. The covenant gate (vowed → tenure-weighted share; outreach →
  minimal 0.25× floor, share 0) holds (6 tests / 41 assertions green). fuchi is the start of the
  third Wave-1 actor; remaining fuchi methods: `analyze` / `book` / `couple` / `provision` /
  `route` / `vote` / `live_gate`.
- **Wave 1 — fuchi `vote` + `live_gate`.** `vote.py` → `vote.clj` + `live_gate.py` → `live_gate.clj`
  (+ `test_vote.clj`): real **1 SBT = 1 vote** governance with a **48h timelock** + quorum.
  Enforced in code + tests: a duplicate voter DID is rejected at cast time (1 SBT = 1 vote), a
  ballot has weight 1 (no token-plutocracy), a `:server`/`:anon` voter is unrepresentable (G9),
  ballots outside `[opened-at, opened-at+48h]` don't count, a tally is `pending` until the window
  closes, a thin vote (< quorum) is `rejected` never auto-accepted, and `finalize`/`finalize-binding`
  RAISE before the timelock (the autonomous R2 gate cannot short-circuit it). Golden parity with
  vote.py (4-in-window → yes 2/no 1/abstain 1 → accepted; thin → rejected; binding council-level 7).
  `live_gate` is the shared R2 autonomous gate (per-leg policy retained as metadata; unknown leg
  raises). 8 tests / 28 assertions (vote) — full fuchi clj suite **14 tests / 69 assertions green**.
  fuchi now **3/8** methods clj-native (allocate + vote + live_gate); remaining: `analyze` /
  `book` / `couple` / `provision` / `route`.
- **Wave 1 — fuchi `route`.** `route.py` → `route.clj` (+ `test_route.clj`): in-kind rail
  decomposition + the governance gate. `route-envelope` decomposes a sustenance envelope into
  delivery rails over the EXISTING producing actors (housing→commons-land, food→mitsuho,
  energy→hikari, compute→murakumo, tooling→okaimono, care→iyashi, liquidity→warifu as
  MEMBER-PRINCIPAL qard-ḥasan) — a `:cash`/`:stipend` rail RAISES (cash≡0, 扶持 never pays);
  `in-kind-coverage` (round 4) is the honesty metric (golden 0.9). `gov-route` is a PURE function
  of (imputed total, invariant-touch, rider) → {refused/council-lv7/sbt-vote/auto} — a Charter-Rider
  hit refuses, a constitutional-invariant touch goes Council Lv7+, above the ceiling goes 1 SBT=1
  vote, else auto — 扶持 ROUTES, never DECIDES (非裁定, ake G2). Golden parity with route.py
  (5 tests / 25 assertions — full fuchi clj suite **19 tests / 89 assertions green**). fuchi now
  **4/8** methods clj-native; remaining: `analyze` / `book` / `couple` / `provision`.
- **Wave 1 — fuchi `book`.** `book.py` → `book.clj` (+ `test_book.clj`): the two cross-actor
  projections of an accepted allocation. `book-toritate` projects each IN-KIND rail into a toritate
  `ledgerEntry` using toritate's own category enum (housing/food/energy → subsistence-flow,
  compute/tooling → vocation-flow, care → care-flow) — `:payroll`/`:salary`/`:wage` unrepresentable,
  cash≡0, and the **MEMBER-PRINCIPAL liquidity rail is NOT booked as income** (it's the member's own
  warifu 0% loan — honest accounting). `flow-graph` emits a kanae-renderable Sankey (Public Fund →
  扶持 → provider → maintainer) where the funding leg covers only the in-kind value and the
  liquidity legs are flagged in-kind false. Golden parity with book.py (2 ledger entries, 7 flow
  edges, 18e9 funding leg). 4 tests / 21 assertions — full fuchi clj suite **23 tests / 112
  assertions green**. fuchi now **5/8** methods clj-native; remaining: `analyze` / `couple` /
  `provision`.
- **Wave 1 — fuchi `provision`.** `provision.py` → `provision.clj` (+ `test_provision.clj`): wires
  in-kind rails to the REAL producing actors (mitsuho/hikari/okaimono/iyashi/commons-land/Murakumo;
  liquidity→warifu MEMBER-PRINCIPAL) as DRY-RUN provisioning intents — `published` structurally
  false (G10, live provisioning Council Lv6+/operator gated), cash≡0 (G2), no-server-key (G9), all
  enforced in code. Honours the **abaki 暴 Anti-Monopoly routing policy**: a provider matched in
  `abaki/out/routing-policy.json` raises a route-around (robust load — missing/parse-error → no
  blocks). `dispatch-live` authorizes via the R2 gate without overriding the structural invariants.
  Golden parity with provision.py (3 intents to the right providers). 4 tests / 17 assertions —
  full fuchi clj suite **27 tests / 129 assertions green**. fuchi now **6/8** methods clj-native;
  remaining: `analyze` / `couple`.
- **Wave 1 — fuchi `couple`.** `couple.py` → `couple.clj` (+ `test_couple.clj`): the
  Displacement-Dividend cohort coupling (ADR-2606032130 G2). `earmark-from-surplus` applies the
  10% TitheRouter split as an **exact integer split** (gross = tithe + earmark, no rounding leak —
  golden 100M→10M/90M, odd 12345→1234/11111). The **G2 coupling gate** is the structural heart:
  a displacement is admissible iff its cohort earmark is FUNDED *and* the committed in-kind floor
  ≤ the earmark — **no live displacement without a funded cohort** (the actor may not shed human
  toil faster than the Public Fund can sustain the people affected). `commit-live` stacks two
  refusals (R2 gate Lv7 + the G2 gate). Golden parity with couple.py. 4 tests / 19 assertions —
  full fuchi clj suite **31 tests / 148 assertions green**. fuchi now **7/8** methods clj-native;
  only `analyze` (the R0 orchestrator, ~300 lines) remains to complete Wave 1.
- **Wave 1 — fuchi `analyze` → fuchi COMPLETE (8/8) → WAVE 1 COMPLETE.** `analyze.py run` →
  `analyze.clj` (+ `test_analyze.clj`): the end-to-end allocation membrane that drives every other
  fuchi method over the `:representative` seed (covenant → envelope → tenure-weighted allocation →
  rail decomposition → governance gate → provisioning intents → toritate booking + kanae flow graph
  → Displacement-Dividend coupling). The pipeline reproduces analyze.py `run()` **exactly**: 5
  maintainers route as `abel→auto/accepted`, `seth→sbt-vote 5-1/48h✓/accepted` (real 1 SBT=1 vote
  tally), `eve→council-lv7/pending`, `noah→auto/accepted` (outreach), `cain→refused/refused`; 14
  provisioning intents / 13 ledger entries / 32 flow edges / 4 derived datoms; coupling
  cohort-sanae-2026 admissible (funded) + cohort-hataori-2026 refused (unfunded); all 4 live legs
  admissible (R2). cash≡0 holds across every projection. (analyze.py's `_report`/`main` Markdown
  renderer is intentionally NOT ported — it reads live-gate condition keys the R2 autonomous gate no
  longer emits, i.e. dead code against the current `live_gate`; a clean `scorecard` replaces it.) 5
  tests / 28 assertions — full fuchi clj suite **36 tests / 176 assertions green**.

## STATUS — Wave 1 (accounting / tax / allocation core) is COMPLETE

All three Wave-1 actors are now fully clj-native, every port byte-/behaviour-parity-verified
against its Python original with the discipline of D2 (charter gates enforced in code + tests):

| Actor | Methods clj-native | Tests |
|---|---|---|
| **danjo** | 4/4 (budget_ledger · kotoba · autorun new this wave; analyze pre-existing `.cljc`) | 10 run_tests_clj suites / 201 checks (+ analyze.cljc in `test:actors`) |
| **matsurigoto** | 7/7 (tax-assess · corp · civil · credential · datoms · sign-capability · standard) | 86 tests / 352 assertions |
| **fuchi** | 8/8 (allocate · vote · live_gate · route · book · provision · couple · analyze) | 36 tests / 176 assertions |

The Python files are retained as D2.2 shims where live downstream consumers still import them
(kanae ← danjo budget_ledger; matsurigoto/fuchi cells + abaki policy reader) and retire when those
consumers port. **Next: Wave 2** (PLM graph layer — uchiwake / kabuto / giemon-SBOM), then Wave 3
(MES Pregel cells → langgraph-clj). The roadmap's worked references (danjo for load-file methods,
matsurigoto/fuchi for the clojure.test + classpath pattern) are now established for those waves.

## Wave 2 (PLM graph) — kicked off

Checking-for-existing-`.cljc`-first (the danjo lesson), much of the PLM/observatory layer is found
to be **already `.cljc`**: uchiwake (`uchiwake-edn` + `analyze`), kabuto (`kabuto-edn` + `analyze`),
and the mirror lineage (asobi/hoshimori/inochi/hokorobi/tsugite/shiori/rasen/keizu/kosatsu/watari/…)
all ship `.cljc` ports already. So Wave 2 is **finishing the unported tail**, not greenfield.

- **uchiwake `crosscheck`.** `crosscheck.py` → `crosscheck.clj` (+ `test_crosscheck.clj`): the
  headline uchiwake⇄kabuto coverage-linkage measurement, reusing the canonical `.cljc`
  `uchiwake.methods.uchiwake-edn` (load-edn + classify). **Byte-identical** with crosscheck.py on
  every metric: 1719 kabuto companies, 26 distinct refs → 21 resolved = **80.8% linkage**; per-kind
  totals; the 子会社 ownership-rollup (sony-semicon→sony recovered on two edge-kinds); the honest
  unresolved gap (5, G5 — "not yet ingested" not "nonexistent"); and reverse coverage (233 supply
  cos, **6.438%** with product detail, **1.163%** across all kabuto). Written `.clj` (a clj-side
  disk-reading data tool, not browser), path-matching ns → auto-discovered by `bb test:actors`
  (4 tests / 20 assertions; worklist tie-order is impl-specific so asserted by length + max
  out-degree, not exact order). Remaining uchiwake tail: `ingest` / `adapters/openfoodfacts`.

# Alternatives Considered

- **Full clj rewrite of every actor.** Rejected (D4): rewrites open-kyber UI + Rust
  physics for no correctness gain; enormous cost.
- **Stay Python/TS, rely only on the kotoba substrate.** Rejected: forgoes
  code-enforced invariants + the declared `langgraph-clj` cell/WASM execution path
  that bb.edn already commits to.
- **Big-bang swap (delete Py at port time).** Rejected (D2.2): breaks live downstream
  consumers (e.g. kanae ← danjo budget_ledger). Additive + byte-parity is safe.

# References

- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605262130 — kotoba storage substrate unification (no RisingWave)
- ADR-2605215000 — Murakumo-only inference
- ADR-2605231525 — no-server-key discipline
- ADR-2605301600 — danjo (this roadmap's Wave-1 first port)
- ADR-2606141200 — matsurigoto tax-collect (clj precedent)
- ADR-2606037200 — open-kyber kotoba-Datomic ERP (TS core whose logic Wave 1 extracts)
- `bb.edn` — the clj-side runner; langgraph-clj / langchain-clj deps
