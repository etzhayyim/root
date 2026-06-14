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
- **Second landed step (same wave).** `danjo/methods/analyze.py` → `analyze.clj` (+ `test_analyze.clj`):
  the non-adjudicating discrepancy analyzer. `method_cid` is byte-identical (golden
  `method:single-bidder-streak:955ade7944f2`); the full `render_edn` output is **byte-for-byte**
  equal to the Python (golden-string test); G4 (no verdict field representable, structural
  self-check) + G5 (≥2 source CIDs, raises) enforced in code (13/13 green). Note `method_cid`
  uses Python's DEFAULT `ensure_ascii=True` (non-ASCII → `\uXXXX`), so it needs a *distinct*
  canonical encoder from budget_ledger's `ensure_ascii=False` — both now live in the danjo clj
  tree, a reminder that "canonical JSON" is encoder-specific and parity must be proven per call
  site. The `.py` shim is retained (D2.2): `autorun.py` still imports `from analyze import …`.
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
