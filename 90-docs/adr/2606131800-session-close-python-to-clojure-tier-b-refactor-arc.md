---
id: adr-2606131800-session-close-python-to-clojure-tier-b-refactor-arc
title: "ADR-2606131800: Session close — Python→Clojure Tier-B byte-identical refactor arc (PRs #1706–#1730) + bb test-discovery"
status: accepted
doc_type: adr
topic: session-close-python-to-clojure-tier-b-refactor-arc
authoritative: false
last_verified: 2026-06-13
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "non-authoritative process record; authoritative design = ADR-2606120500 (fleet/refactor harness) + ADR-2606131300 (verification policy)"
authoritative_for: []
depends_on:
  - adr-2606120500-fleet-clojure-refactor-and-gemma4-cpt
  - adr-2606131300-clj-port-determinism-golden-file-first-class
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606131800: Session close — Python→Clojure Tier-B byte-identical refactor arc + bb test-discovery

**Status**: accepted (process record — non-authoritative)
**Date**: 2026-06-13

## Context

Non-authoritative process record of the multi-session Python→Clojure (.cljc, pywasm-ready
on the kotoba Datom-log + langgraph-clj/langchain-clj substrate) refactor of the etzhayyim
Tier-B actor corpus. Authoritative design lives in ADR-2606120500 (fleet/refactor harness +
gemma4 CPT investigation) and ADR-2606131300 (verification policy). This ADR records what
landed, the reusable technique, and the honest boundaries — so a later session resumes
without re-deriving.

## What landed (merged to `origin/main`)

| PR | Scope | Headline |
|---|---|---|
| #1706 | mimamori/yobel/ibuki(19 mod) + KG-mirror/accountability analyzers ×11 + 14 stub replacements + fleet investigation | first wave |
| #1714 | pywasm-ready analyzers (kaiyaku/kadode/tanemaki/watatsuna/hinagata/itonami/shionome) + 4 datom_emit + tsumugi banner | analyzers |
| #1716/#1718 | hotaru/mitooshi/nusa/ake/kawaraban/tasuke/shomei/fuchi/kasa/uchiwake/sukashi/suji/kamado/abaki/tate/hakoniwa (+rasen-cov/hinagata-datom) — #1718 was the cycle-6 recovery cherry-pick after #1716 merged a commit short | Tier-B analyzers |
| #1719/#1720/#1721 | compute methods: kadode/kaiyaku/hinagata · itonami/keizu/funadaiku · infra-robotics control hikari/mizuho + photonics noroshi | compute + control |
| #1723 | **bb test-discovery refactor** — `etzhayyim.tools.discovery` auto-globs actor test nss; deletes the hand-maintained test:stubs/test:pywasm lists | tooling |
| #1725 | noroshi active_alignment/fibre_loop + kamado decommission_robot (+ per-actor substrate) | robotics |
| #1727 | noroshi isac_sim/cable_endpoint/kami_isac_bridge (noroshi 7/7 complete) + mitooshi forecast_quantile/horizon | open at close |
| #1730 | matsurigoto standard/sign_capability/datoms | open at close |

`bb test:actors` (discovered suite) at session close ≈ **1265 tests / 18,732 assertions, 0
failures** (plus the merged mimamori/yobel/ibuki/tools suites). Every ported method's report /
datoms / CID is **byte-identical** to its python3 reference (the in-development verification
oracle, ADR-2606131300).

## Reusable technique (the analyzer/compute-port pattern)

- Own minimal EDN reader per actor (keywords kept as `":ns/name"` strings) + edge-primary read.
- Constitutional gates ported 1:1 and **test-enforced via `ex-info`** (not just documented):
  e.g. トレードはしない (shionome), 嗜好THC-excluded (nusa), fossil-virgin-crude-unrepresentable
  (kamado), no-targeting/sensing-not-surveillance (noroshi), 使者-not-代理人 (kadode),
  steward-not-sovereign (tanemaki), no-server-key + UPL-unrepresentable, etc.
- **Byte-parity discipline**: HALF_EVEN via exact `BigDecimal.(double)` (Java `String.format`
  is HALF_UP — mis-rounds); `fmt-g` for Python `{v:g}`; `Double/toString`+signed-zero
  `Math/copySign` for `repr(float)`; `::order` / vector-of-pairs to reproduce Python dict
  insertion order past the 8-entry array-map threshold; mutable control-loop state in atoms
  for bit-faithful multi-thousand-step accumulation; Math/* transcendentals are last-ULP on
  the JVM.
- **Hand-ported stdlib/crypto primitives** (pure portable .cljc, no host dep — for SCI/WASM):
  CPython **siphash13** + setobject (kabuto), **BLAKE2b** RFC 7693 (shomei), **MT19937**
  init_by_array + genrand_res53 + gauss (noroshi isac_sim), and a **complex** cmath helper
  (noroshi). CIDv1 raw sha2-256 reproduced byte-identical to `ipfs add` (kadode/hinagata).
- **kuni-umi/robotics `_substrate`** (PID/Droop/PlanarArm/SafetyEnvelope) ported once per
  actor as `<actor>.methods.substrate` (clean ns — leading-underscore munges in SCI), reused
  across hikari/mizuho/noroshi/kamado.

## Decisions of record

1. **Fleet does NOT do the port** (ADR-2606120500): gemma4 e4b ~20% quality, small-corpus
   CPT/SFT ±0; 12b +7.4pp measured. Correctness-porting is done by Claude agents; the fleet
   stays for bulk/harvest. The fleet was kept **idle** the entire arc (no duplicate GPU jobs).
   Recommendation on the table: raise the default fleet workhorse to **gemma4 12b-qat**; do
   NOT reinvest in small-corpus CPT; 27b only as a quality-tier subset.
2. **Verification basis** (ADR-2606131300): determinism + golden-file are first-class;
   python3 byte-parity is an in-development convenience oracle; the CID-chain-continuity
   obligation is dropped (pre-production → logs may be re-genesised).
3. **bb test-discovery** (#1723): bb.edn is now static — dropping a `test_*.cljc` is enough.
   This eliminated the recurring merge-conflict hot-region (every tier branch used to edit one
   shared hand-list). Verified across 3 consecutive zero-bb.edn-churn cycles (#1725/#1727/#1730).

## Bugs surfaced upstream (founder follow-ups)

- **fuchi** `analyze._report` KeyError — `live_gate.py` went R2 ({autonomous_r2_mode:true}) but
  `_report` still reads the old per-condition keys; `python3 analyze.py main()` crashes before
  writing. The Clojure port mirrors the lookups but degrades gracefully (nil→✗) rather than
  crash. Fix: update `_report` to the R2 conditions shape.
- **uchiwake** `analyze.py` non-determinism — material→products reachability iterates an
  unordered Python `set`, so tie-group order is `PYTHONHASHSEED`-dependent (a substrate-bound
  bug, since the output is content-addressed). The Clojure port pins a deterministic discovery
  order; a `parity_oracle.py` confirms the same line-multiset. Fix: sort the tie-groups.

## Boundaries (deliberately NOT ported)

- **tsumugi `analyze.py` / `analyze_influence.py`** — numpy spectral embedding
  (`np.linalg.eigh` of a graph Laplacian). Byte-parity is infeasible without a numerical
  symmetric eigensolver (eigenvector sign/order ambiguity + iterative-convergence drift vs
  LAPACK). A separate founder decision: (a) Jacobi eigensolver + tolerance test (relaxes
  byte-identity), (b) numpy-in-wasm, or (c) leave Python. `tsumugi/coverage_report` is blocked
  on the same numpy `analyze_influence`.
- **I/O-coupled layers** (autorun / ingest / social / kotoba_bridge / live_gate cells) — network
  / kotoba-engine bound; the constitutional gates they guard are already ported + test-enforced
  in the analyze/weave/compute layer.
- Static-site / mirror-actor generators (tate site_gen/case_actors_gen), cell `.solve()` /
  state-machine + commissioning suites — out of the pure-method scope.

## Registry note

`deps.toml` (the CLAUDE.md-referenced SSoT) is not git-tracked in the working tree at the time
of this close, so the usual `[[adrs]]`/`[[modules]]` registration could not be PR'd; this ADR
+ the ADR README index row are the durable record. If `deps.toml` is restored to tracking, add
the `[[adrs]]` row for this id and `[[modules]]` rows for the ported `<actor>.methods.*` cljc.

## Status at close

- Merged: #1706/#1714/#1716/#1718/#1719/#1720/#1721/#1723/#1725.
- Open (parallel-mergeable — discovery means different files + zero bb.edn → no conflict):
  #1727 (tier6), #1730 (tier7).
- Next session (zero bb.edn churn): mitooshi bridge/bridge_kakaku/ingest/persist/social,
  himotoki/request, maps/*, kawaraban/ingest — then report when pure-method targets are dry.
