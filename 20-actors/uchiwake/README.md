# uchiwake 内訳

**World product bill-of-materials / GTIN knowledge graph** — the product-level layer beneath
kabuto 兜. Tier-B religious-corp actor, R0 design-only. ADR-2606081800.

kabuto wires **company → company** supply edges. uchiwake goes one level **down** — to the
**trade item itself**, keyed on the GS1 **GTIN**, decomposed into its bill of materials
(**product → part → raw material**), plus the **process** steps that make it, the **logistics**
legs that move it, and the **design/standard** refs that specify it — and one level **up**, via
**ownership** edges that roll a brand-owning **subsidiary** to its **ultimate parent** (子会社,
GLEIF Level-2 relationship records).

The lens is the kabuto lens: **supply-chain resilience + corporate-power transparency**. Where a
product's material inputs, processing, or transport concentrate onto a single source or a single
jurisdiction, that concentration is surfaced — routed to **redundancy + accountability**, never a
target-list and never a clone/counterfeit recipe (G2).

## Worldwide-coverage design

| Dimension | Public source (R1 ingest target, G7-gated) |
|---|---|
| Product identity (GTIN) | GS1 GDSN + GS1 Verified; open mirrors Open Food/Beauty/Products Facts |
| Classification | GS1 GPC brick + UNSPSC (existing 18,342 codes) + HS code (WCO) |
| Brand-owner → company | GS1 prefix licensee → GLEIF LEI (kabuto `org.corp.*`) |
| Subsidiary → parent (子会社) | GLEIF Level-2 Relationship Records (RR) |
| BOM / materials | public teardowns, ingredient labels, supplier-list filings, EU DPP |
| Process / logistics | public origin declarations, UN Comtrade HS flows, factory-list pledges |
| Design / standards | cited IEC/ISO/JEDEC/USB-IF specs, public regulatory monographs |

R0 ships a **bounded real seed**; full-universe ingest (hundreds of millions of GTINs) is **R1**
and Council + operator gated (G7).

## Run

```bash
python3 methods/ingest.py            # offline bridge + seed (live = G7-gated)
python3 methods/analyze.py            # resilience report + derived concentration datoms
python3 methods/crosscheck.py         # measured uchiwake ⇄ kabuto coverage linkage
python3 -m unittest tests.test_uchiwake -v
```

## Honesty (R0)

7 products (3 real GTINs; 2 `:authoritative`), 10 parts, 23 materials, 33 BOM edges, 8 process
steps, 5 logistics legs, 4 design refs, 3 ownership edges. `:representative` decompositions, GS1
check-digit-validated GTINs, bounded criticality estimates — never an authoritative recipe or a
contract figure. Company refs wire to REAL kabuto companies; `crosscheck.py` measures the linkage
(~71%) and honestly reports the not-yet-ingested gap. See `CLAUDE.md` for the full gate list.
