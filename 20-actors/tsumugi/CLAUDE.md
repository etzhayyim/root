# tsumugi 紡ぎ — Engi Knowledge Graph intel weaver (spirit-in-physics over real power-entities)

**ADR**: 2606011800 · **depends**: 2606011000 (§D7 産霊の網) + 2606011500 (spirit-ontology)
· 2605081300 (edge-primary karma) · 2605170000 (spirit=thermodynamic info) · 2605301600
(danjo) · 2605301400 (tadori) · 2605302300 (kanae). **Status**: 🟡 R0 design-only.

tsumugi ("紡ぎ" = spinning threads together) executes §D7.1 of ADR-2606011000: it weaves
the **Engi Knowledge Graph (産霊の網 / musubi-no-ami)** — real-world 法人 / institution /
ecological / public-role entities and their 縁 (follow / depends-on / custodies) — and runs
the **Spirit-in-Physics** pipeline (RBF emotion-kernel → spectral 3D embed → tensegrity
relax) over it to surface **取-concentration** (custody-debt that accumulates over others),
routed toward release.

It is the upper layer over **danjo** (power 取), **kanae** (fiscal-flow render), **tadori**
(on-chain attribution), **himotoki** (self-claim). It does NOT replace them.

## Hard gates (constitutional — read before any change)

- **G1 — power-only scope (§D8/§D9).** Only power-holding entities: 法人, institutions, and
  persons STRICTLY in a public-power role (chair/exec/official). The powerless / private
  individuals are absent **by construction**. This is an accountability map of 取の集中,
  **never a target-list**.
- **G2 — edge-primary (N1).** karma/取 lives ONLY on edges (`:spirit.bond/signed-weight`).
  An organism's 取-concentration = the **integral of its incident 縁**, computed on read —
  never a stored per-soul score. There is no `:spirit/score-of-soul`.
- **G3 — aggregate-first + claimed-first.** Members' own declared 縁 are covenant-visible
  (ADR-2605310100 §1–2); the latent remainder is aggregate-first only. Never a per-person
  exposure dump.
- **G4 — public venue (§D8).** Open-source + on-chain + 1 SBT = 1 vote + symmetric
  access-log (sousveillance of the watchers). Never a private/covert registry at a vendor.
- **G5 — sourcing honesty.** Every record carries `:sourcing :authoritative | :representative`.
  No fabricated coverage. The committed seed is `:representative` (public docs, bounded).
- **G6 — Murakumo-only narration.** Any LLM narration routes through Murakumo (ADR-2605215000).
- **G7 — outward-gated (G11).** Live planet-scale ingest (atproto follow/deps over real
  persons) requires Council + operator. R0 = analyzer + schema + seed only.
- **G8 — no git-lfs.** Large/binary assets via DataLad → IPFS (80-data/spirit-in-physics).
- **G9 — PII envelope.** Any 要配慮 datum (human assay) → XChaCha20-Poly1305 (ADR-2605181100).

## Layout

```
20-actors/tsumugi/
├── CLAUDE.md                       # this file
├── manifest.jsonld                 # actor manifest
├── data/seed-power-graph.kotoba.edn  # real PUBLIC power entities + 縁 (:representative)
├── methods/analyze.py              # spirit-in-physics intel analyzer (stdlib + numpy)
└── out/                            # GENERATED — do not hand-edit
    ├── intel-report.md             # aggregate-first 取-concentration report
    └── spirit-graph.kotoba.edn     # :spirit.bond/* + :spirit/* + :grasp/* datoms
```

## Run

```bash
python3 20-actors/tsumugi/methods/analyze.py            # uses data/seed-power-graph.kotoba.edn
python3 20-actors/tsumugi/methods/analyze.py <seed.edn> --out <dir>
```

Emits the connected spirit-graph (edge-primary) + the 取-concentration intel report. To
advance over more of the earth: extend the seed with `:representative`-flagged public
relationships, or (Council-gated) wire the atproto follow/deps ingester (§D7.1).
