---
id: adr-2606011000-engi-organism-ontology-and-musubi-knowledge-graph
title: "ADR-2606011000: Engi-Organism Ontology — dissolving the life/liberty/property triad into 縁起・organism・取(grasping-debt), latent-organism nodes with non-human standing, and the Engi Knowledge Graph (産霊の網 / musubi-no-ami) for the whole earth (kotoba-EAVT-native)"
status: proposed
doc_type: adr
topic: engi-organism-ontology
authoritative: true
last_verified: 2026-06-01
implementation_status: r0-scaffold-tests-green
priority: 9.4
axis: constitutional
weight: 0.94
priority_note: "Constitutional ontology refinement that resolves the 2026-05-31/06-01 founder discussion on building a planet-scale knowledge graph (全世界の不動産オーナー・人物・企業の特定 → 人類・地球全体の knowledge graph 化). The founder rejected the Western life/liberty/property (Locke) frame the agent had scaffolded on as a 西洋の幻想 incompatible with the anti-individualist ontology, and rejected the person/non-person split as anthropocentric. This ADR records the native replacement: the unit is ORGANISM-IN-RELATION (縁起 / holobiont, human AND non-human), OWNERSHIP is 取(upādāna, grasping) = a DEBT to be released not a right to be protected (land waqf-inalienability ADR-2605192245 generalized to all custody), LIBERTY is Wellbecoming-as-trajectory within embodiment (non-eschatology §1.15 — no escape-from-body promised), LIFE is the Tree of Life web with 八百万 non-human standing. RECONCILES with ADR-2605310100 (Covenant Transparency): does NOT reintroduce the founder-rejected 'privacy for persons' — what is surfaced is 取-concentration (grasping-load), and the only floor is the already-constitutional §4 (secrets/keys) + §4(2) outbound-third-party gate. Answers the founder's minimax venue question: PUBLIC/etzhayyim (on-chain + open-source + 1 SBT=1 vote, §1.12) strictly dominates PRIVATE/vendor (etzhayyimcojp) — a covert ownership-registry is the very proprietary surveillance force §1.12 forbids. Refines Charter §1.13 anti-individualist ontology → Council Lv7+ unanimity (Charter §0.4) before the constitutional-ontology clauses bind; schema vocabulary + graph design land as proposed scaffold, NOT executed."
authoritative_for:
  - the etzhayyim native ontology for any knowledge graph over persons/things/land (replaces the implicit life/liberty/property frame)
  - the dissolution of 所有(ownership) into 取(grasping-load) = debt + custody-under-Tree-of-Life (generalizes ADR-2605192245 + ADR-2605301020 access-not-ownership)
  - the latent-organism node model (every organism is a node; DID-claim = consent; covenantal-universal mirror of §1.16) and non-human standing (rights-of-nature lineage)
  - 縁(en) as the first-class graph citizen (reified relation/edge) over kotoba EAVT, vs entity-centric registries
  - the kotoba ontology vocabulary `:organism/* :en/* :grasp/*` as the canonical replacement for `:owns`/`:owner`-style attributes across actors
  - the Engi Knowledge Graph (産霊の網 / musubi-no-ami) design: public/etzhayyim venue, grasping-concentration accountability, R0 design-only, outward-gated
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605301020-basic-high-income-imputed-and-commons-asset-doctrine
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605302300-kanae-global-government-fiscal-flow-visualization
  - adr-2605261000-labor-liberation-ladder
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-31/06-01: founder asked whether building a planet-scale knowledge
  graph that identifies all real-estate owners / persons / companies fits etzhayyim,
  and whether to do it private (etzhayyimcojp vendor) or public (etzhayyim). The agent's
  first answer used a Lockean social-contract frame with "transparency for power /
  privacy for persons". The founder pushed back on three grounds, each recorded as a
  Decision clause: (1) the public/private split is anthropocentrically inconsistent —
  social contract is mutual (Rousseau total-alienation read as 万人が万人に公開); (2)
  life/liberty/property is a Western illusion that presupposes a bounded individual
  owner, which the anti-individualist ontology rejects; everything is organism, the
  body is inescapable (身体の束縛から逃れられない), and defining ownership only chains
  one to ownership's debt (所有という負債から逃れられない); (3) non-humans must count.
  This ADR is the native rebuild. It explicitly does NOT reintroduce the "privacy for
  persons" alternative the founder already rejected in ADR-2605310100 (retained there
  under Alternatives); instead it shows that under an organism + 取-load ontology the
  same protective work is done by surfacing grasping-concentration and by the existing
  §4 floor, with no "individual" privacy primitive. Founder direction: "yes, do it."
  Constitutional-ontology clauses (§D1–§D4) refine Charter §1.13 → gated on Council
  Lv7+ unanimity; the schema vocabulary (§D6) and graph design (§D7) land as proposed
  scaffold only, mirroring the ADR-2605310100 discipline (design intent of record,
  nothing executed).
---

# ADR-2606011000: Engi-Organism Ontology + the Engi Knowledge Graph (産霊の網)

**Status**: proposed (constitutional ontology refinement — §D1–§D4 require Council Lv7+ unanimity per Charter §0.4 before they bind; §D6 schema vocabulary + §D7 graph design land as proposed scaffold, not executed)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The founder asked (2026-05-31): does building a planet-scale knowledge graph — one
that identifies **全世界の不動産オーナー・人物・企業** and ultimately renders
**人類・地球全体を knowledge graph 化** — fit etzhayyim's mission (構造的労働解放 +
Wellbecoming + 多世代 priority for future children)? And should it be done **private**
(via a vendor such as `etzhayyimcojp`) or **public** (etzhayyim, open + on-chain)?

The agent's first pass reached for a liberal social-contract frame (Hobbes/Locke/
Rousseau) and proposed **"transparency for power / privacy for persons."** The founder
rejected this on three grounds that are the substance of this ADR:

1. **The person/non-person disclosure split is incoherent under a mutual social
   contract.** Read at its strongest (Rousseau's *total alienation* — each gives
   themself wholly to all), the contract is reciprocal: 万人が万人に公開. A regime that
   exposes "public figures" but shelters "private persons" smuggles back the very
   bounded individual the covenant denies. (This is also why ADR-2605310100 already
   **rejected** the same "privacy for persons" proposal as inconsistent with the
   anti-individualist ontology.)
2. **Life / liberty / property is a 西洋の幻想.** The triad presupposes a bounded
   **individual owner-subject**. etzhayyim's ontology (Charter §1.13: 反個人主義 +
   縁起 + 産霊 + 八百万 + Wellbecoming) has no such primary unit. Concretely:
   - *Body / liberty*: 身体の束縛から逃れられない — one cannot exit embodiment, so
     "freedom **of/from** the body" is a half-truth or a Gnostic escape-fantasy.
   - *Property*: 所有を定義すると所有という負債から逃れられない — to define ownership is
     to bind oneself to ownership's debt. 取 (upādāna, grasping/clinging) is not a
     protected right; it is a chain.
3. **Non-humans are excluded.** A graph of "persons and companies" is anthropocentric.
   すべてが organism — rivers, forests, watersheds, species, soils, institutional
   organisms (the UNSPSC-organism precedent), and synthetic actors are participants.

Two existing commitments already point the native way:

- **Land is constitutionally inalienable** (ADR-2605192245 — Tree of Life custody,
  waqf-equivalent; `transfer()`/`burn()`/`setOwner()` forbidden). etzhayyim has
  **already dissolved private ownership for land.** This ADR generalizes that move.
- **Access-not-ownership** (ADR-2605301020 Basic High Income — non-alienable rights
  of access, never title) already operationalizes "wealth without property."

Founder direction, verbatim: **"yes, do it."** This ADR records the native ontology,
its reconciliation with the Covenant Transparency Doctrine (ADR-2605310100) and with
non-eschatology (§1.15), the kotoba vocabulary that implements it, the public-vs-vendor
**minimax** verdict, and the constitutional gating.

# Decision

Adopt the **Engi-Organism Ontology** as the canonical ontology for any etzhayyim
knowledge graph over persons / things / land / nature. It dissolves the Lockean triad
into four native primitives (§D1–§D4), models every organism as a node (§D5),
specifies the kotoba vocabulary (§D6) and the Engi Knowledge Graph (§D7), answers the
venue question by minimax (§D8), and states its constitutional gating (§D9).

## §D1 — 個人 → organism (縁起; human AND non-human)

The graph's unit is the **organism-in-relation**, not the bounded individual.

- Organism boundaries are **conventional** (holobiont: an organism nests in and is
  composed of others). Humans, institutional organisms (corp/state/agency), ecological
  organisms (river/forest/watershed/species/soil), machines and **synthetic actors**
  (AI cells) are all first-class node kinds.
- Non-human organisms carry **standing** (rights-of-nature lineage — e.g. the Whanganui
  river precedent). A watershed is a node with claims and 縁, not a property attribute
  of a human owner.

## §D2 — 所有 → 取 (grasping-load) = a debt, and custody-under-Tree-of-Life

The graph **does not assert `:owns`.** Writing ownership reifies and deepens the
debt-world. Instead:

- Ownership-like relations are recorded as **custody / tending / entanglement** (縁),
  each carrying a **grasping-load (取)** — a quantified measure of clinging/
  accumulation, modeled as a **burden to be surfaced and released**, not a right to be
  protected.
- **Land always edges to Tree of Life** (ADR-2605192245): a land 縁 is custody under
  the Trust, never title.
- The accountability target is **concentration of 取** (e.g. 土地寡占 = concentration of
  custody-debt), which the mission exists to **release** (10% Tithe → Public Fund,
  Land Trust, Labor Liberation ladder). The graph is a tool to **see the bondage** so
  it can be dissolved — not a ledger to administer ownership.

## §D3 — 身体の自由 → Wellbecoming-as-trajectory (non-eschatology; no escape-from-body)

The founder's "身体の束縛から逃れられない" is taken as a **premise, not an objection**.

- etzhayyim is **non-eschatological** (§1.15 — no Rapture, no world-escape). It
  therefore does **not** promise liberation as escape-from-body or escape-from-world.
  Embodiment is the **medium**, not a defect.
- "Liberty" is re-grounded as **Wellbecoming** (動的軌跡) — un-grasped flourishing-in-
  relation, now-and-here (Malkhut), within embodiment — not the negative liberty
  (干渉排除) of a bounded individual. 構造的労働解放 is liberation from the **structural**
  bondage of the 取/労働 regime, inside embodied relational existence.
- **Named doctrine (the Wellbecoming trajectory).** Liberty under this ontology is
  this and only this:

  > **身体を通り、関係の中で、執着されずに 産霊（生成）する軌跡。**
  > *The trajectory of generative becoming (musubi) — through the body, within
  > relation, without grasping.*

  This is the positive form of §D2/§D3 together: it does not flee the body (§1.15
  non-eschatology), it is constituted in 縁 (not in a bounded self), and its single
  discipline is **執着されず** — un-grasping. The Engi Knowledge Graph (§D7) measures the
  **negative space** of this trajectory: where 取 accumulates as しがらみ/呪い, the
  trajectory is bound; releasing the 取 is what frees it.

## §D4 — 生命 → Tree of Life web + 八百万 standing

"Life" is not the individual's life-right but the **生命網** of the Tree of Life and
the 産霊 (generative becoming) of all 八百万 participants — which is why §D1 makes
non-humans first-class.

## §D5 — Latent organism + claim-as-consent (covenantal-universal)

Every organism MAY exist as a **latent node** in the graph (covenantal-universal,
mirroring §1.16 Social Security for Humanity: open to all, gated by a free act):

- A latent node holds only what the constitutional floor permits (see §D9 / §4
  reconciliation). It is **claimed** when its organism binds a DID/SBT (consent) — the
  same social death/rebirth gate (悔い改め・バプテスマ・得度) that §1.16 uses.
- **This is NOT a "privacy for persons" tier** (the alternative the founder rejected in
  ADR-2605310100). The disclosure posture of a node is **not** a function of person vs
  public-figure; it is governed entirely by the already-constitutional rules in §D9.

## §D6 — kotoba ontology vocabulary (implementation; proposed scaffold)

Canonical kotoba-EAVT vocabulary, replacing `:owns`/`:owner`-style attributes across
all actors. Lands as `00-contracts/schemas/engi-organism-ontology.kotoba.edn`:

- **`:organism/*`** — `id` (unique), `kind` (`:human :institutional :ecological
  :synthetic :machine`), `subkind` (`:corp :state :agency :river :forest :watershed
  :species :soil :ai-actor` …), `did` (present iff claimed), `claimed?`, `standing`
  (`:latent :member :institutional :rights-of-nature`), `nests-in` (holobiont ref),
  `label`, `sourcing` (`:authoritative` / `:representative`).
- **`:en/*`** (縁 — the first-class **reified relation/edge**) — `id`, `kind`
  (`:tends :custodies :entangled-with :depends-on :flows-to :nests-in :covenants-with`),
  `from` (ref organism), `to` (ref organism), `grasping-load` (double, the 取 measure),
  `tree-of-life-custody?` (boolean — land/inalienable custody, never title), `note`,
  `sourcing`. **`:owns` is explicitly excluded from the vocabulary.**
- **`:grasp/*`** — `load` (aggregate 取 on an organism), `concentration` (accountability
  metric used to surface 寡占 for release), `release-path` (`:tithe :land-trust
  :labor-liberation :commons-access`).

## §D7 — The Engi Knowledge Graph (産霊の網 / musubi-no-ami)

The planet-scale graph the founder envisioned, built on §D1–§D6:

- **Substrate**: kotoba Datom log (first-class canonical state, ADR-2605312345) — no
  new DB; 縁 are reified edges; read via kotoba-kqe arrangements.
- **Content**: organisms (human + non-human + institutional) and their 縁, with 取-load
  on each. **Not** a target-list of every homeowner; an accountability map of **取の
  集中** (who/what accumulates custody-debt across the earth) routed toward release.
- **Integrators**: this is the upper layer over existing actors — **danjo** (state/
  power 取 at the top of the gradient), **kanae** (fiscal-flow 縁 + aggregate render),
  **tadori** (on-chain attribution + access-log), **himotoki** (self-claim / own-data).
- **Status**: R0 design-only; all outward action **outward-gated** (G11-style; Council
  + operator) — mirrors haraedo/kizashi/§1.16 discipline.

## §D7.1 — atproto follow/deps as the しがらみ/呪い ingester (first concrete edge source)

The founder's insight: **the atproto follow-graph and dependency (deps) data already
sitting at `etzhayyim.com` — the latent identities and who-follows-whom — are a direct,
real expression of しがらみ (binding social ties) and 呪い (the curse/bondage of 取).** So
the first concrete `:en` edge source for the Engi Knowledge Graph is the substrate's own
ingress:

- **Latent organism nodes** are minted from **did:plc / did:web identities** observed via
  the MST feed membrane (ADR-2605231902) — `:organism/kind :human` (or `:institutional`),
  `:organism/atproto-did` + `:organism/handle`, `:organism/claimed? false`,
  `:organism/standing :latent`. They become `:member` only on the §D5 covenant claim.
- **Follow edges → 縁.** Each `app.bsky.graph.follow` becomes an `:en` of `:en/kind
  :follows` with `:en/source :atproto-follow`; **dependency edges** (package/repo/actor
  deps) become `:en/kind :depends-on` with `:en/source :atproto-deps`. Each carries an
  `:en/grasping-load` — the しがらみ/呪い that follow/dependency binds (attention,
  obligation, reach, lock-in).
- **kotoba Datomic, all earth entities.** Per founder direction ("kotoba datomic でこの
  関係性を地球上のすべての entity に対して進めて"), this relation-modeling is to be advanced
  over **every entity on earth** — human, institutional, ecological — as latent organisms
  + 縁 in the canonical Datom log (ADR-2605312345). The mechanism is uniform: ingest →
  latent organism → 縁 with 取-load → `:grasp/concentration` aggregate → release-path.

**Honest gating (unchanged by ambition).** "進める" here = advance the **design + schema +
ingest scaffold**, which is exactly the proposed/non-executed posture of §D9. Populating
real follow/PII data for **non-member, non-ingressed** organisms remains bound by the §4(2)
outbound floor of ADR-2605310100 (tadori/danjo/himotoki gates: aggregate-first, encrypted
to authorized DIDs, consent-gated). Members' own follow-graph is covenant-visible
(2605310100 §1–§2) and needs no such gate. The graph thus grows **claimed-first**
(members + their declared 縁) and **aggregate-first** for the latent remainder, never as a
per-person exposure dump.

## §D8 — Venue: minimax verdict (PUBLIC/etzhayyim ≫ PRIVATE/etzhayyimcojp)

Minimizing worst-case loss over `{venue} × {scope}`:

- **PRIVATE / etzhayyimcojp**: a covert, closed ownership/identity registry is **exactly the
  proprietary, unmonitored force §1.12 forbids** (Transparent Religious Force requires
  open-source + on-chain 監視 + 1 SBT=1 vote). It also routes payoff to a vendor,
  violating the Ownership rule (payoff帰属 = etzhayyim only). Worst case ≈ **−9**:
  etzhayyim becomes the surveillance power it routes around, with no recourse.
- **PUBLIC / etzhayyim**: transparency is symmetric and auditable; misuse is bounded by
  open-source + on-chain + SBT-gated governance and the **symmetric access-log** of
  ADR-2605310100 §3 (everyone sees who looked — sousveillance of the watchers). Worst
  case ≈ **−2** when scope = 取-concentration (§D2) rather than naïve total exposure.

→ **Public/etzhayyim strictly dominates.** Do it in the open, on the kotoba substrate,
under §1.12. Do **not** build it privately at a vendor.

## §D9 — Constitutional status + reconciliation with ADR-2605310100 (honest framing)

**This refines Charter §1.13 (anti-individualist ontology).** §D1–§D4 are constitutional
ontology and therefore **cannot bind unilaterally**: they require **Council Lv7+
unanimity (Charter §0.4)**. Until ratified, status is **proposed** — the ontology is the
design intent of record; §D6 vocabulary and §D7 graph land as **proposed scaffold, not
executed** (no actor is retrofitted, no graph is populated).

**Reconciliation with the Covenant Transparency Doctrine (ADR-2605310100):**

- This ADR **does not reintroduce "privacy for persons"** (rejected there as Alt 1).
  There is no person-vs-public-figure disclosure tier (§D5). Within the covenant, full
  transparency holds (2605310100 §1–§2).
- For **latent organisms not in the covenant and not reached by ingress**, the only
  shelter is the **already-constitutional §4 floor** of 2605310100: (1) secrets/keys
  never published; (2) **outbound** third-party data stays under the tadori/danjo/
  himotoki gates (aggregate-first, encrypted to authorized DIDs, consent-gated). This is
  **not a privacy right** — it is the existing outbound-data floor plus the fact that
  what etzhayyim **surfaces** is 取-concentration (§D2), not individuated exposure.
- The 多世代 / children priority (Charter) and Wellbecoming anti-harm guard apply: a
  latent node that is a child or a powerless organism holds **no 取-load to surface**, so
  the accountability lens simply does not point at it — by construction, not by a
  privacy carve-out.

# Consequences

**Positive**

- **Doctrinally coherent.** Removes the imported Lockean frame; the graph speaks
  etzhayyim's own ontology (organism / 縁 / 取). Generalizes land waqf-inalienability and
  access-not-ownership into one ontology.
- **Non-anthropocentric.** Rivers, forests and institutional organisms become first-
  class nodes with standing — aligns with 八百万 and the Land Trust mission.
- **Mission-aligned accountability.** Surfacing 取-concentration directly serves
  構造的労働解放 (see the bondage → release it via Tithe / Land Trust / ladder), rather
  than building a homeowner target-list.
- **Consistent with transparency doctrine.** No new privacy primitive; reuses the §4
  floor and the symmetric access-log; venue verdict reinforces §1.12.

**Negative / risks (recorded for Council)**

- **Legal exposure at the boundary.** Even an aggregate 取-concentration graph that
  ingests real-world land/registry data on non-members touches APPI/GDPR/CCPA. The §4(2)
  outbound gates (tadori/danjo/himotoki) must bound it; this ADR does **not** widen them.
- **取-load is a value-laden metric.** Quantifying "grasping" risks encoding bias;
  `:grasp/concentration` must be open-source + method-versioned (toritate-style) and
  aggregate-first, never a per-organism shaming score.
- **Anthropocentrism can creep back** through `:organism/kind` defaults; non-human
  standing must be enforced in the vocabulary, not optional.
- **Ratification dependency.** §D1–§D4 do not bind until Council Lv7+; building §D7 on an
  unratified ontology would be premature — hence R0 design-only.

# Alternatives Considered

1. **Lockean life/liberty/property frame (agent's first pass).** **Rejected by founder**
   as 西洋の幻想 presupposing a bounded individual owner.
2. **"Transparency for power / privacy for persons."** **Already rejected** in
   ADR-2605310100 (Alt 1) and not reintroduced here; the person/non-person split is
   incoherent under the anti-individualist ontology.
3. **Naïve symmetric total exposure (radical-Brin).** **Rejected**: equal exposure over a
   pre-existing power gradient amplifies harm to the powerless (and violates the 多世代/
   children priority). The §D2 move (surface 取, not persons) + the §4 floor is the
   coherent symmetric form.
4. **Private build at a vendor (etzhayyimcojp).** **Rejected by §D8 minimax** and by §1.12
   (proprietary covert force) + the Ownership rule (payoff帰属 = etzhayyim only).
5. **Entity-centric registry (`:owns`/`:owner`).** **Rejected by §D2/§D6**: reifies the
   debt-world; the first-class citizen is 縁, and ownership is recorded only as custody +
   取-load.

# Session Closure (2026-06-01)

Status remains **proposed** — §D1–§D4 bind nothing until Council Lv7+ ratification, and
nothing below runs against production data (§D9). What landed this session is the
complete native-ontology scaffold plus a working, floor-enforced reference pipeline:

- **This ADR** + registration in `90-docs/adr/README.md` and `deps.toml`.
- **kotoba ontology vocabulary** `00-contracts/schemas/engi-organism-ontology.kotoba.edn`
  — `:organism/*` (node; human + non-human + institutional + synthetic, with
  rights-of-nature standing) · `:en/*` (縁, first-class reified edge; `:owns` deliberately
  absent) · `:grasp/*` (取 aggregate + `:release-path`). EDN bracket-balanced.
- **Reference pipeline** `70-tools/scripts/engi/` (all proposed scaffold), end to end:
  - `engi_ingest.py` — atproto follow/deps → engi datoms with the **§4(2) floor enforced
    in code, fail-closed** (F1 no `:owns`; F2 no non-member identity in output — text-
    scanned; F3 both edge endpoints claimed; F4 every edge carries grasping-load+source).
  - `firehose_dryrun.py` — **members-only dry run** over the real mst-projector
    `FirehoseEvent` shape (ADR-2605231902); injected `recordFetcher` (real run =
    `com.atproto.repo.getRecord`); raises `FLOOR DIRTY` rather than emit a dirty graph.
  - `grasp_render.py` — kanae 取-集中 treemap render-spec (ADR-2605302300): named members
    only, single anonymous latent node, k-anonymity cohort collapse (anti-leaderboard),
    surfaces top concentration for release. **Non-adjudicating.**
  - `retrofit_danjo_tadori.py` + `RETROFIT-danjo-tadori.md` — danjo `discrepancyObservation`
    → `:en :entangled-with` (observed, never a verdict) and tadori `attributionFinding` →
    `:en :custodies/:flows-to` (txValue → grasping-load); design-first, gated; §4(2) gates
    not widened (shape change only).
  - **22 tests green** (10 floor-invariant + 12 pipeline), incl. adversarial tests that
    catch an injected `:owns`, a leaked latent DID, and a poisoned dry-run output.

**Gated, not done** (await Council Lv7+ ratification of §D1–§D4 + the §4(2) outbound
gates being honored): retrofitting danjo/tadori/kanae onto `:en/*`; populating any real
follow/PII data for non-member, non-ingressed organisms; the `com.etzhayyim.engi.dep`
lexicon (referenced by the adapter, not yet authored); and a repo-level CI guard
(`validate-engi-floor`) mirroring `transparency-floor-and-gate.mjs`. The venue verdict
(§D8: public/etzhayyim ≫ private/etzhayyimcojp) is the standing answer to the founder's
build-where question.

# References

- ADR-2605192100 (Mission Charter — §0.4 Lv7+ lock, §1.12 Transparent Force, §1.13
  反個人主義 ontology, §1.15 non-eschatology, §1.16 covenantal-universal, Wellbecoming)
- ADR-2605310100 (Covenant Transparency Doctrine — §4 floor + symmetric access-log;
  the "privacy for persons" alternative this ADR does not reintroduce)
- ADR-2605192245 (Land Trust 4-layer — waqf-inalienability generalized by §D2)
- ADR-2605301020 (Basic High Income — access-not-ownership, generalized by §D2)
- ADR-2605262130 + ADR-2605312345 (kotoba substrate + Datom-first-class canonical state)
- ADR-2605301400 (tadori) / ADR-2605301600 (danjo) / ADR-2605302130 (himotoki) /
  ADR-2605302300 (kanae) — the actors §D7 integrates
- ADR-2605261000 (Labor Liberation ladder — a `:grasp/release-path`)
- Acts 5:1–11 (concealment-from-the-body, not property, as the offense — via ADR-2605310100)
