---
id: adr-2606011800-tsumugi-spirit-intel-power-graph
title: "ADR-2606011800: tsumugi 紡ぎ — Spirit-in-Physics intel over the Engi Knowledge Graph (取-concentration of real public power-entities) + no-LFS/DataLad policy"
status: proposed
doc_type: adr
topic: tsumugi-spirit-intel-power-graph
authoritative: true
last_verified: 2026-06-01
priority: 7.0
axis: architecture
weight: 0.7
priority_note: "First concrete executor of §D7.1 (Engi Knowledge Graph) under the edge-primary spirit-ontology"
authoritative_for:
  - tsumugi actor (Engi Knowledge Graph intel weaver)
  - spirit-in-physics power-graph analyzer
  - no-git-lfs / DataLad-via-IPFS asset policy
depends_on:
  - adr-2606011500-spirit-in-physics-kotoba-datafication
  - adr-2606011000-engi-organism-ontology-and-musubi-knowledge-graph
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605170000-deai-spirit-physics-matching
  - adr-2605241500-dataset-cid-substrate
related:
  - adr-2605301600-danjo-public-accountability
  - adr-2605301400-tadori-onchain-tracing
  - adr-2605302300-kanae-fiscal-flow-visualization
  - adr-2605310100-covenant-transparency
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606011800: tsumugi 紡ぎ — Spirit-in-Physics intel over the Engi Knowledge Graph

**Status**: proposed (R0 design-only; outward/live ingest Council + operator gated)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The founder asked (2026-06-01): *「この spirit in physics に基づいて 実在の法人、人物の 依存関係,
follow 関係をすべて分析して intel, 繋げていって」* — analyze the dependency / follow relations of
real corporations and persons with Spirit-in-Physics, turn it into intel, and connect it up.

This is the first concrete executor of **§D7.1 of ADR-2606011000** (the Engi Knowledge Graph
/ 産霊の網), now realizable because the **edge-primary spirit-ontology** landed in
ADR-2606011500 (`:spirit.bond/*` over `:en/*` 縁). It must obey the venue/scope verdicts the
founder already set in §D8/§D9 and the edge-primary karma layer (ADR-2605081300).

The literal scope ("すべて … 人物") collides with two of this corp's own constitutional floors,
so the request is executed in the form those floors mandate — not weakened, not refused:

- **§D9 — the lens points at 取-concentration of the POWERFUL, not at private persons.** The
  powerless / child / private organism holds no 取 to surface and is absent **by
  construction**. This is an accountability map, **not a target-list of every person**.
- **§D8 — public/etzhayyim venue strictly dominates a private/covert registry** (which would
  itself be the proprietary surveillance force §1.12 forbids). Open-source + on-chain +
  1 SBT = 1 vote + symmetric access-log.

A second founder direction this session: **drop git-lfs; use DataLad.** The spirit-in-physics
submodule (ADR-2606011500) uses LFS upstream for paper PDFs; LFS is not the substrate-aligned
mechanism (the repo already runs DataLad + git-annex + IPFS per ADR-2605241500).

# Decision

## A. tsumugi 紡ぎ — the Engi Knowledge Graph intel weaver

New Tier-B actor `20-actors/tsumugi/`. It weaves real public power-entities + their 縁 into the
kotoba graph and runs the Spirit-in-Physics pipeline over it, surfacing 取-concentration.

- **Input** `data/seed-power-graph.kotoba.edn` — real, PUBLICLY-DOCUMENTED power entities
  (`:organism/*`) and relations (`:en/*` 縁: `:custodies` ownership/control, `:depends-on`
  supply/compute/IP, `:nests-in`, `:tends` stewardship, `:follows` attention), each with an
  `:en/grasping-load` (the しがらみ/呪い the tie binds). Flagged `:sourcing :representative`
  (bounded sample, no fabricated coverage).
- **Pipeline** `methods/analyze.py` (stdlib + numpy, the same math as spirit-in-physics):
  10-dim sector/role emotion vector → **RBF emotion-kernel** `W` → Laplacian `L = D − W` →
  **spectral 3D embedding** (eigvecs 2–4) → **tensegrity** unilateral-spring relax over the
  縁. Then **取-concentration per organism = Σ incident inbound 縁 grasping-load** (the
  integral of incident edges, N1 — never a stored per-soul scalar), plus spirit connectivity
  / separation (ADR-2605170000) and connected components.
- **Output** `out/intel-report.md` (aggregate-first 取-concentration ranking + spirit readout
  + 繋がった components) and `out/spirit-graph.kotoba.edn` (`:spirit.bond/*` edges with
  `mode`/`rest-length`/`stiffness`/`signed-weight`/`conductance` + `:spirit/*` per-node
  aggregates + `:grasp/concentration` + `:grasp/release-target`).
- **Position**: upper layer over **danjo** (power 取), **kanae** (fiscal render), **tadori**
  (attribution), **himotoki** (self-claim) — integrates, does not replace.

## A.1 The §D7.1 ingester (`methods/ingest.py`)

The mechanism that grows the web beyond the curated seed ("繋げていって"): it weaves the seed
with ingest sources (`data/ingest/*.edn`) into one `out/woven-graph.kotoba.edn`, deduping by
`:organism/id` / `:en/id`, **claimed-first + aggregate-first**:

- Latent organisms minted from public handles are forced `:organism/claimed? false` +
  `:organism/standing :latent` (become `:member` only on the §D5 covenant claim) and stay
  `:sourcing :representative`.
- **G1**: ingest fixtures contain institutions / public-role nodes only — no private persons.
- **G7 gate**: the live path (`--live`, real `app.bsky.graph.getFollows`) is **refused**
  unless `TSUMUGI_OPERATOR_GATE` is set; even then it is a documented scaffold (wire via
  `@etzhayyim/sdk` + MST membrane, ADR-2605231902, under Council ratification). Default =
  fixture mode, no network — the §D7.1 R0 posture.

First fixture = `data/ingest/atproto-institutional.kotoba.edn` (7 public institutional atproto
accounts — NYTimes, Reuters, Guardian, AP, NASA, Bluesky, The Verge — + 11 follow 縁 with low
attention-取, some cross-weaving into the corp component).

## B. First run (empirical, this ADR)

Seed = 19 real public organisms (Toyota keiretsu · SoftBank→Arm · TSMC · NVIDIA · Apple ·
Microsoft↔OpenAI · Alphabet→Google · Sony · MUFG · METI · a watershed for non-human standing ·
one public-role node), 28 縁. Result: **one connected component** (everything weaves together),
σ_eff ≈ 0.30. Top 取-concentration holders (power held over others):

| rank | entity | 取 held | release-target |
|---|---|---|---|
| 1 | TSMC (foundry) | 3.28 | 2.28 |
| 2 | Toyota Motor | 2.88 | 1.88 |
| 3 | Arm Holdings | 2.03 | 1.03 |
| 4 | NVIDIA | 1.92 | 0.92 |

The bottleneck/lock-in nodes (foundry, semiconductor IP, keiretsu hub) surface as the highest
取-concentration — exactly the accountability signal §D2 intends, with the powerless absent.

**After ingest** (`ingest.py` weaves the atproto-institutional fixture): **26 organisms (7
latent/unclaimed) / 39 縁, still one connected component** — the press/agency cluster weaves
into the power cluster. NVIDIA rises to #3 (2.22) and OpenAI to #5 (1.27) as press attention-縁
accrue; Reuters surfaces as an attention-hub (0.51). This is "繋げていって" working: the web
grows by ingest, stays connected, and the 取-concentration signal re-ranks accordingly.

## C. No git-lfs — DataLad → IPFS

Per founder direction + ADR-2605241500: **git-lfs is not used anywhere in this monorepo.**

- `60-apps/spirit-in-physics` is cloned **pointer-only** (`GIT_LFS_SKIP_SMUDGE=1`); upstream
  LFS blobs are never fetched here.
- Large/binary spirit assets (paper PDFs, assay corpora, kernel/embedding snapshots) live in a
  new DataLad dataset **`80-data/spirit-in-physics/`** (git-annex `text2git` → IPFS pinner),
  registered as a root submodule (local-only, `ignore = dirty`, mirroring
  `90-docs/baien/datasets`). Text artifacts (EDN/JSON/MD) stay in plain git.
- 要配慮 PII (raw assay responses) is XChaCha20-Poly1305 enveloped (ADR-2605181100), never
  plaintext annex content.

## D. Status & gating

R0. The committed analyzer + `:representative` seed + generated graph are design/scaffold. **The
live planet-scale ingester** (§D7.1: atproto follow/deps over real persons via the MST feed
membrane) is **G11 outward-gated** (Council + operator) and unbuilt. Members' own declared 縁
are covenant-visible (ADR-2605310100 §1–2) and need no gate; the latent remainder is
aggregate-first only.

# Consequences

**Positive.** (1) §D7.1 has a working, runnable executor — real entities, real public
relations, connected into one spirit-graph, with a reproducible 取-concentration intel readout.
(2) Edge-primary + power-only-by-construction makes §D8/§D9 structurally enforced, not just
documented. (3) The spirit-graph output is kotoba-EAVT-ready and kami-genesis-renderable
(tensegrity). (4) Removes git-lfs as a dependency; aligns large assets to the DataLad/IPFS
substrate.

**Negative / honest limits.** (a) Seed is `:representative` (bounded public sample), not
authoritative or exhaustive. (b) Emotion vectors are sector-derived representatives, not
measured assays — fidelity is illustrative. (c) The tensegrity relax is a lightweight
gradient pass, not the full unilateral-spring solver in `60-apps/spirit-in-physics`. (d) No
live ingest — coverage of "every entity on earth" (§D7.1) is aspirational and Council-gated.
(e) The DataLad dataset is local-only until a public annex/IPFS sibling is published.

# Alternatives Considered

- **Ingest all real persons' follow graphs now (literal reading).** Rejected — §D9 (lens at
  取-concentration, not persons) + §D8 (public, not covert) + G11 (outward-gated). The
  powerless are excluded by construction; live person-ingest is Council-gated.
- **Build it privately at a vendor for "intel".** Rejected — §D8 minimax: a covert registry IS
  the surveillance force §1.12 forbids (worst case −9) and violates the Ownership rule.
- **Store karma/取 as a per-organism score.** Rejected — edge-primary N1 (ADR-2605081300);
  概念上 it must be the integral of incident 縁.
- **Keep git-lfs for spirit assets.** Rejected — founder direction + ADR-2605241500
  (DataLad/git-annex/IPFS is the substrate mechanism).

# References

- `20-actors/tsumugi/` — actor (CLAUDE.md + manifest + methods/analyze.py + data + out)
- `00-contracts/schemas/spirit-ontology.kotoba.edn` — `:spirit.bond/*` edge-primary vocabulary
- `80-data/spirit-in-physics/` — DataLad dataset (no git-lfs)
- ADR-2606011000 §D7/§D7.1/§D8/§D9 — Engi Knowledge Graph + venue/scope verdicts
- ADR-2606011500 — spirit-in-physics → kotoba datafication
- ADR-2605081300 — edge-primary karma (`signed_weight : Edge → ℝ`)
- ADR-2605170000 — spirit as thermodynamic information quantity
- ADR-2605241500 — Dataset CID substrate (DataLad + git-annex + IPFS)
