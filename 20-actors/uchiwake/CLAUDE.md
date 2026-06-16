# uchiwake 内訳 — agent reference

> World product bill-of-materials / GTIN knowledge graph. Tier-B, R0 design-only. ADR-2606081800.
> The product-level layer beneath kabuto 兜. Read the repo-root `CLAUDE.md` first; this file only
> adds actor-local rules.

## Identity

- **DID**: `did:web:etzhayyim.com:actor:uchiwake`.
- **Glyph**: 内訳 — "itemized breakdown" — a finished good resolved into its constituent parts,
  materials, processes, transport, and design refs, made a first-class graph.
- **Role**: the *product-level* face of the observation upper layer. kabuto 兜 wires
  COMPANY → COMPANY supply edges; uchiwake goes one level down to PRODUCT → PART → raw MATERIAL,
  and one level up (ownership) to roll a brand-owning subsidiary to its ultimate parent. Brand /
  supplier / carrier / operator ids reuse kabuto's `org.corp.*` space; commodity codes reuse the
  existing UNSPSC space (entity-as-actor).

## Hard rules (constitutional — do not weaken)

1. **Resilience + transparency, not interdiction or cloning (G2).** Output is framed toward
   material/supplier diversification and corporate-power accountability. NEVER a "who to hit" map
   AND never a clone/counterfeit recipe. Quantities are bounded public estimates, never a
   manufacturer's confidential formulation. Mirrors Charter Rider §2(d) + the kabuto lineage.
2. **Public trade items, public-record data only (G1).** GTIN, brand, brand-owner, GS1 prefix,
   GPC/UNSPSC/HS classification, published material/ingredient labels, public teardown findings,
   disclosed supplier relationships. **Forbidden inputs**: confidential recipes/formulations,
   non-public commercial terms, trade secrets, consumer purchase/PII data.
3. **No adjudication (G4).** uchiwake states public facts + computed concentration. It does not
   rule on legality, safety/conformity compliance, or country-of-origin claims.
4. **Sourcing honesty (G5).** Every node/edge carries `:*/sourcing` ∈
   `:authoritative | :representative | :synthesized`. GTINs marked `:authoritative` are REAL
   public identifiers (validated by GS1 mod-10 check digit on ingest). BOM decompositions are
   `:representative` (public teardown/label, NOT an exhaustive authoritative bill of materials).
   Absence ≠ non-existence — it means "not yet ingested".
5. **kotoba-native (substrate boundary).** State = kotoba Datom log. No SQL / RisingWave / Lance.
6. **Murakumo-only (G6).** Any LLM narration routes through the Murakumo fleet (ADR-2605215000).
7. **Outward-gated INGEST (G7).** Live full-universe fetch (GS1 GDSN / GLEIF RR / Open Product
   Data — hundreds of millions of GTINs) requires `UCHIWAKE_OPERATOR_GATE=1` + Council. R0 ships
   a bounded real seed only.
8. **no-server-key + read-only (G12).** uchiwake never holds a GS1/GLEIF write credential and
   never mutates an upstream record.

## Vocabulary

`00-contracts/schemas/product-bom-ontology.kotoba.edn`:
- `:product/*` — a trade item keyed on the GTIN (normalized GTIN-14), brand, brand-owner
  (→ kabuto `:company/id`), GS1 prefix + prefix-country, GPC/UNSPSC/HS classification.
- `:part/*` — a sub-assembly / component / ingredient / packaging node.
- `:material/*` — a raw / refined material input (metal/mineral/polymer/agricultural/chemical/…).
- `:bom.edge/*` — first-class directed BOM edge: parent CONTAINS child, with qty + tier +
  disclosed supplier + bounded criticality.
- `:process.step/*` — a transformation step (extraction → refining → fab → assembly → …).
- `:logistics.leg/*` — a transport leg (origin → dest, mode, carrier).
- `:design.ref/*` — a design/standard/spec reference (IEC/ISO/JEDEC/USB-IF/regulatory).
- `:company.ownership/*` — SUBSIDIARY edge (子会社): child → parent, GLEIF Level-2 RR.
- derived `:concentration/*` — computed by `analyze.py`, flagged `:concentration/derived true`,
  **never re-ingested as fact**.

## Cells

- `cell:uchiwake.ingest` → `methods/ingest.py` — public product source → kotoba EAVT bridge
  (offline default; live G7-gated). Documents the GS1 GDSN / GLEIF RR / Open Product Data path.
  Validates the GS1 check digit before admitting any product datom.
- `cell:uchiwake.analyze` → `methods/analyze.py` (stdlib). recursive BOM material-closure →
  material dependence → processing-jurisdiction load → ultimate-parent rollup (子会社) →
  single-source/high-criticality edges. Aggregate-first. Idempotent.
- `cell:uchiwake.crosscheck` → `methods/crosscheck.py` (stdlib). resolves every uchiwake company
  reference (brand-owner/supplier/operator/carrier/ownership) against kabuto's ingested company
  universe → MEASURED linkage % + 子会社 rollup recovery + honest not-yet-ingested gap. Measures
  cross-actor supply-chain integration; does not assert it.
- `cell:uchiwake.autorun` → `methods/autorun.py` (+ `methods/kotoba.py`). The autonomous
  Murakumo-fleet heartbeat — the same shape kanjō/shionome/ipaddress/watatsuna/watari/kabuto use.
  Each cycle observes the OFFLINE merged product graph → recursive BOM material-closure → material
  dependence + processing-jurisdiction load + ultimate-parent rollup (子会社) → **persists a
  content-addressed transaction** (graph datoms + derived `:concentration`) to the append-only
  **local** kotoba Datom log (`methods/kotoba.py`), linking the previous tx's CID into a verifiable
  commit-DAG. Deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs; derived sorted
  by id → independent of PYTHONHASHSEED set-iteration order); NO external I/O. **G2/G4/G5 hold by
  construction**: only public trade-item facts + transparent concentration are representable — every
  derived `:concentration/*` carries `:sourcing :synthesized` + `:derived true` and is never
  re-ingested as an authoritative product fact; no target-list / clone / recipe attr exists. Live
  universe ingest + the live-node push stay Council + operator gated (G7). Invariants guarded by
  `methods/test_autorun.py` (commit-DAG verify, tamper-detect, determinism, append-only, G5
  derived-:synthesized, G2/G4 not-target/not-recipe, no-external-I/O, G7 gate-refusal,
  exactly-once cursor).
- `cell:uchiwake.bridge` → `methods/bridge.py`. LOCAL→LIVE kotoba-node push leg (ibuki pattern):
  replays an exactly-once `:bridge/*` cursor off the local log, pushes only un-pushed heartbeat
  txs to the live `datomic.transact` node with `:uchiwake.tx/*` provenance, then appends ONE
  checkpoint. Gated by `UCHIWAKE_KOTOBA_LIVE=1` (Council + operator); the cursor/replay logic is
  pure and runs offline (`--status`). no-server-key (unsigned public-DID operator bearer, G12).

### Clojure port (datomic + clojure substrate parity)

`methods/kotoba.cljc` + `methods/autorun.cljc` are 1:1 Clojure ports of the heartbeat (alongside
the existing `uchiwake_edn.cljc` + `analyze.cljc`). The canonical-JSON tx-CID encoder in
`kotoba.cljc` reproduces Python's `json.dumps(…, sort_keys=True, separators=(",",":"))` **byte for
byte**, so a Clojure heartbeat and the Python heartbeat build the **identical commit-DAG**
(`graph_datoms` seed CID + all 3 beat CIDs verified equal — see
`tests/test_autorun.cljc cid-byte-parity-with-python`). The cljc EDN reader now tracks `::order`
meta so >8-key datom maps reproduce Python dict insertion order. DEFERRED as separate units
(inochi/rasen precedent): `ingest`/`crosscheck`/`bridge` + the OFF adapter (network/adapter legs).

## Run

```bash
cd 20-actors/uchiwake
python3 methods/ingest.py            # offline: bridge data/ingest/*.json + seed (default)
python3 methods/analyze.py            # → out/intel-report.md + out/product-criticality.kotoba.edn
python3 methods/autorun.py --cycles 3 --fresh   # AUTONOMOUS heartbeat → LOCAL kotoba Datom log
python3 methods/bridge.py --status    # inspect the exactly-once push cursor (offline)
python3 methods/test_autorun.py       # heartbeat + log + gate invariants
python3 -m unittest tests.test_uchiwake -v   # 21 tests
# live (G7-gated):
UCHIWAKE_OPERATOR_GATE=1 python3 methods/ingest.py --live --gtin 3017620422003  # OFF fetch (Nutella)
UCHIWAKE_KOTOBA_LIVE=1   python3 methods/bridge.py --push                        # push to live node

# Clojure heartbeat (byte-identical commit-DAG):
bb -cp 20-actors -e "(require 'uchiwake.tests.test-autorun 'clojure.test) \
  (clojure.test/run-tests 'uchiwake.tests.test-autorun)"
```

`python3 methods/analyze.py` with no argument runs the **seed** graph alone.

## Honesty (R0)

Bounded illustrative seed of **11 products** (real public GTINs: Coca-Cola 330ml `5449000000996`,
Nutella 750g `3017620422003` `:authoritative`; KitKat `7613035044289` `:representative`), **18
parts**, **26 materials**, **46 BOM edges**, **10 process steps** (incl. `:design` activity), **5
logistics legs**, **7 design refs**, **3 ownership edges** — **not** exhaustive coverage and **not**
an authoritative recipe. Brand-owners / suppliers / operators / carriers wire to REAL kabuto
companies (Apple, Foxconn, BYD, CATL, Maersk, Nestlé, Fast Retailing, TSMC, SK hynix, Kioxia, Sony,
NVIDIA, Ericsson, Boeing, ARM, SMIC, Denso, Magna, Glencore, ADM). `crosscheck.py` measures linkage
(**80.8%** of distinct refs resolve) AND reverse coverage (**6.4%** of kabuto's 233 supply-chain
companies / **1.16%** of all 1,719 have product-BOM detail) with a prioritized ingest worklist —
each `/loop` iteration ingests worklist suppliers to raise it (2.6%→6.4% this iteration). GTINs are validated by GS1 mod-10 check
digit; decompositions are `:representative` public-teardown/label estimates. "Register ALL trade
items" is the **R1** goal — full GS1 GDSN / GLEIF-RR / Open Product Data universe ingest (hundreds
of millions of GTINs) is **G7** Council + operator gated. Live atproto posting is **G11** (later).
