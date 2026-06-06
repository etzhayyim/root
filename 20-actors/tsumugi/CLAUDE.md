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
├── data/
│   ├── seed-power-graph.kotoba.edn      # real PUBLIC power entities + 縁 (:representative)
│   └── ingest/*.edn                     # §D7.1 ingest sources (atproto follow fixtures, deps…)
├── methods/
│   ├── ingest.py                        # §D7.1 ingester — weave seed + sources (gated)
│   └── analyze.py                       # spirit-in-physics intel analyzer (stdlib + numpy)
└── out/                                 # GENERATED — do not hand-edit
    ├── woven-graph.kotoba.edn           # seed + ingest merged (claimed-first, latent-flagged)
    ├── intel-report.md                  # aggregate-first 取-concentration report
    └── spirit-graph.kotoba.edn          # :spirit.bond/* + :spirit/* + :grasp/* datoms
```

## Run

```bash
# 1. weave the graph (fixture mode — NO network; latent organisms flagged claimed?=false)
python3 20-actors/tsumugi/methods/ingest.py
# 2. analyze the woven graph (or a specific seed)
python3 20-actors/tsumugi/methods/analyze.py 20-actors/tsumugi/out/woven-graph.kotoba.edn --out 20-actors/tsumugi/out
python3 20-actors/tsumugi/methods/analyze.py <seed.edn> --out <dir>
```

Emits the connected spirit-graph (edge-primary) + the 取-concentration intel report. To
advance over more of the earth (§D7.1, "繋げていって"): drop more `:representative` public
relations into `data/ingest/`, or (Council-gated, `--live` + `TSUMUGI_OPERATOR_GATE`) wire
the real `app.bsky.graph.getFollows` fetch via `@etzhayyim/sdk` + MST membrane (ADR-2605231902).

---

# Diachronic influence-history extension (ADR-2606061500)

tsumugi's present-tense power-graph, run **BACKWARD IN TIME**. Models past humanity as a
diachronic graph of **influence-bearing PUBLIC historical figures, documents, events and
traditions** (incl. YHWH/Torah, Jesus/Gospels, Buddha/suttas — as **influence nodes in
human history**, never as theological claims) and the directed 縁 by which information (an
idea, a text, a practice) flowed from an earlier node and **deformed the metric** of a later
one. Frame: junkawasaki.com "spirit is information" (spirit = metric deformation of a
self-boundary as external info is integrated; covariant gradient of free energy). That frame
is *individual* — this extension supplies the missing **inter-personal, diachronic
propagation**: an influence 縁 is the **channel** across which that deformation travels
between selves and across centuries.

> Same 縁-physics, new axis. Reuses the spirit-ontology pipeline (RBF kernel → spectral
> embed → tensegrity); adds a temporal DAG, influence flows, and Katz reach.

## Five structural invariants (read influence-history-ontology.kotoba.edn before any change)

- **N1 — edge-primary.** Influence/karma lives ONLY on `:flow/signed-weight`. A node's
  influence is the **integral of its incident flows**, computed on read. There is NO
  `:influence/score-of-figure`. Modeling the dead must not become **ranking souls**.
- **N2 — mirror, never impersonation.** Every node `:mirror/is-mirror` true; a post is an
  **observation ABOUT** a figure's documented influence, never the figure speaking.
  `:post/voice` is locked to `:observer`; there is no first-person field, so impersonation
  is unrepresentable (`project_influence_posts.py` refuses any non-mirror node).
- **N3 — non-eschatological + non-adjudicating truth (Charter §1.15).** We datafy the
  **INFLUENCE OF** a tradition (a historical-information claim), NEVER its theological truth.
  No `:truth/verdict`, no `:salvation/status`, no `:afterlife/*`, no final-state datom.
- **N4 — public + long-settled + no PII.** Only documented public influence-bearing figures.
  Living-private persons remain the **Council-Lv7+-gated `:human` scale** of spirit-ontology;
  this is an influence map, never a target-list, hagiography, or ranking of worth.
- **N5 — temporal DAG.** Every `:flow` points forward in time (`source.year-from ≤
  receiver.year-to`). Information cannot precede its source; violations are reported.

`:hist/dating-confidence` carries dating honesty per node (`:attested` / `:scholarly-consensus`
/ `:traditional` / `:legendary`) — legendary attributions (Moses, Bodhidharma) are **flagged,
never asserted**. The `self.etzhayyim` node maps the entity's **own doctrinal genealogy**
(Protestant Sola Scriptura/万人祭司/Tree of Life + 八百万/縁起/産霊/和) as **inbound-only**
influence (the 産霊 receiving side) — never authored as a source over others.

## Run (influence mode)

```bash
# diachronic influence analysis (temporal-DAG check + Katz reach + spirit embed)
python3 20-actors/tsumugi/methods/analyze_influence.py            # default seed
python3 20-actors/tsumugi/methods/analyze_influence.py <seed.edn> --out <dir>
# dry-run mirror posts (observer voice, published=false; impersonation refused)
python3 20-actors/tsumugi/methods/project_influence_posts.py
# tests (12 — one per invariant + seed/projector checks)
python3 20-actors/tsumugi/tests/test_influence.py
```

Outputs (GENERATED — do not hand-edit): `out/influence-report.md` (aggregate-first: top
influence SOURCES = outbound Katz reach · top SYNTHESIZERS = inbound · top BROKERS · era
layering · etzhayyim genealogy), `out/influence-graph.kotoba.edn` (`:spirit.bond/*` +
`:influence/*` edge-integral readouts), `out/influence-posts.dryrun.kotoba.edn`.

**R0 design-only.** Live ingest (archives, citation graphs, genealogy corpora) and any
**published** post are **G7 + Council-gated** (`:post/published` false at R0). Live narration
routes through Murakumo (G6). New lexicons: `com.etzhayyim.influence.{influencePost,influenceFlow}`.
