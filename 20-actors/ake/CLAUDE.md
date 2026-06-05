# ake (朱) — community-edit membrane (Wikipedia-stance KG/profile correction)

**DID**: `did:web:etzhayyim.com:actor:ake` · **Tier**: B · **Status**: R0 · **ADR**: 2606052100

**Read the root `/CLAUDE.md` Charter + substrate rules first.** ake-specific invariants below
OVERRIDE nothing in the Charter; they make it concrete for this actor.

## The one-sentence identity

ake is **Wikipedia's collaborative-correction stance, fitted to the charter**. 朱 (vermillion
editorial ink; 朱を入れる = to correct a manuscript) is how a **信者 (SBT holder)** proposes a
correction to a **KG fact** or an **actor profile**. Every edit is a **member-signed proposal
appended to the kotoba Datom log** (never an overwrite — 非終末論, full revision history). It is
**NOT anonymous open-edit** — it is 信者-gated + member-signed by construction.

## The pipeline

```
propose ─▶ edit_triage ─▶ ┌ auto-accept (optimistic: low risk + high quality)
(信者署名) (LLM score+route) ├ vote        (1 SBT = 1 vote + 48h timelock)
                            ├ council-lv7 (invariant-adjacent — Council Lv7+)
                            └ refused     (Charter-Rider §2 hit — no vote can promote)
                                   │
                                   ▼
                          promote ─▶ revision_log  (append-only; latest = current)
```

The Wikipedia analogue: triage is **ORES** (the ML edit-quality scorer), the optimistic path is
auto-accepting a good edit, the vote is discussion/RfC — but every contribution is a **signed,
on-chain** act, and the history is **immutable** (you cannot delete a revision).

## The 9 gates — do NOT weaken

- **G1 信者-gated + no-server-key** — `:edit/author-kind` is `:db/allowed [:member]` (schema),
  `const "member"` (lexicon), `ValueError` (`triage.score_edit` + `propose`). `:server`/`:anon`
  and `serverHeldKey:true` are **unrepresentable**. The platform never signs an edit
  (ADR-2605231525). **This is the permissioned-wiki invariant — not Wikipedia's anonymous model.**
- **G2 LLM non-adjudicating** — `:triage/decision` **does not exist**. Triage emits `:triage/risk`
  + `:triage/quality` + `:triage/route` only, and **`route_for(risk, quality, rider)` is a PURE
  FUNCTION** — the model scores, it never accepts/rejects (非裁定). Never add a decision field or
  let the LLM pick the route.
- **G3 mirror-preserving** — `:edit/target-kind ∈ {:kg-fact :actor-profile}`. `:entity-speech`/
  `:impersonate`/`:speak-as-entity` are **not enum members**. An entity-actor is corrected as an
  **observation**, never spoken-as (ADR-2606042330 + no-server-key).
- **G4 sourcing-mandatory** — `:edit/provenance` is required; an unsourced proposal **raises**
  (not merely scores low). `:representative→:authoritative` promotion needs **verifiable**
  provenance (`revision.promote_sourcing` raises otherwise; ooyake G20 precedent).
- **G5 append-only / non-destructive** — every mutating helper in `revision.py` **returns a new
  list**; `:delete`/`:overwrite` are unrepresentable; a retract is itself an appended datom
  (kotoba-canonical ADR-2605312345 + 非終末論). The log only ever grows.
- **G6 Murakumo-only** — any LLM refinement of risk/quality runs on the Murakumo fleet
  (LiteLLM `127.0.0.1:4000`), never a commercial GPU (ADR-2605215000).
- **G7 invariant-lock escalation** — an edit touching a constitutional invariant (charter §,
  force-class, license, no-server-key, an actor's own gates) routes to **Council Lv7+**, never
  optimistic-accept; a Charter-Rider §2(a)-(h) hit is `:refused` upstream (a vote cannot promote a
  Rider violation).
- **G8 outward-gated** — live ingest / binding vote / promotion / publish = Council Lv6+ +
  operator; `published` is `const false` at R0. `.solve()` raises on every cell.
- **G9 anti-vandalism / contributor-trajectory** — per-DID rate + a **Wellbecoming** acceptance
  history (`as-of`), NOT a punitive score-of-soul (kizashi G8). Repeated charter-violating
  proposals throttle; they never mint a permanent reputation number.

## When editing

- Structural invariants live in **three places each** (schema `:db/allowed`/enum + lexicon
  `const`/`enum` + Python `ValueError`/refusal). Touch one, touch all three or you've created a
  representable charter violation. `methods/test_charter_invariants.py` guards this.
- The cell directory is `edit_triage` (NOT `triage`) — that name is reserved for the methods
  module `methods/triage.py` (the heart). Renaming the cell back to `triage` re-introduces an
  import shadow; don't.
- Tests are standalone-runnable (`python3 test_*.py`) AND pytest-compatible
  (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`). Keep them so. Run everything with `./run_tests.sh`.
- `.solve()` raises `RuntimeError` on every cell at R0 — live execution is G8-gated. Do not wire a
  cell to a live vote, a live promotion, or the served registry; that needs Council Lv6+ + operator
  (Lv7+ for invariant-adjacent).
- `route_for` is the single routing authority. New risk/quality signals extend `assess_risk` /
  `assess_quality`; they must NEVER make the LLM emit a route or a decision.

## Siblings / boundaries

- **entity-as-actor (ADR-2606042330)** — supplies the mirror entity-actors ake corrects; ake never
  breaks the `isMirror` / keyless / person-excluded invariant.
- **ooyake / kabuto / kanjo / tsumugi / watatsuna / watari** — the KG actors whose seed facts ake
  promotes `:representative→:authoritative`; ake is the write membrane, they are the SSoT owners.
- **danjo / chigiri** — the boundary: ake corrects *records*; it does **not** adjudicate disputes
  of law or fact-of-wrongdoing (danjo observes, chigiri routes legal characterization). An
  edit-war's resolution is danjo-observed + Council, never an ake verdict.
- **tsukuroi / KaizenObserverCell** — the propose-only prior art ake generalizes from a single
  patch-proposer to a society-scale correction membrane.
- **no-server-key (ADR-2605231525) · kotoba-canonical (ADR-2605312345) · 1 SBT = 1 vote · Charter
  Rider (ADR-2605192200)** — the four invariants ake *strengthens*; it amends none.

## Build / test

```
./run_tests.sh                                  # all 11 suites, 106 tests
cd methods && python3 triage.py                 # triage the :representative seed
cd methods && python3 analyze.py                # end-to-end membrane dry-run → methods/out/membrane-dryrun.md
cd methods && python3 ingest.py                 # genesis history from the REAL actor-profile SSoT → methods/out/genesis-revisions.md
```

`methods/contributor.py` is the G9 engine (rate limit + recoverable Wellbecoming trajectory);
`methods/ingest.py` bootstraps the revision history from the REAL committed
`00-contracts/schemas/actor-profile-seed.kotoba.edn` (the SSoT the DID-web Worker publishes from) —
member edits append on top; `methods/test_consistency.py` is the SSoT drift-lock (manifest ↔ cell
tree ↔ lex ↔ ontology ↔ seed ↔ registry). Touch a cell/lexicon/route and the drift-lock fails
loudly before it ships.

Edit-wars: a `:challenge` of the current value routes high → vote (never auto); an upheld challenge
calls `revision.revert()` — the Wikipedia rollback — which **appends** a revision restoring the
predecessor's value. The bad edit is undone for the current reader but stays in the history
(time-travel `as_of` still surfaces it), so the war is fully auditable (danjo-observable). Live
binding votes + danjo/Council arbitration are R1/G8. See `methods/test_editwar.py`.

Test layering: `methods/*` unit-tests the engines; `cells/test_state_machines.py` unit-tests each
cell; `cells/test_membrane_flow.py` is the **cell-chain integration** — it threads one edit through
all five cells in sequence (propose→edit_triage→review_vote→promote→revision_log), the runtime path,
proving they compose. `.solve()` is never called (R0 scaffolds raise).

## Do not

- Do not add a `:triage/decision` field, or let the LLM choose the route — G2 (the model scores,
  `route_for` routes).
- Do not add `:server`/`:anon` to author-kinds, or a `serverHeldKey:true` path — G1 / no-server-key.
- Do not add `:entity-speech`/`:impersonate`/`:speak-as-entity` to target-kinds — G3 (mirror).
- Do not add a `:delete`/`:overwrite` op, or mutate a history list in place — G5 (append-only).
- Do not accept an unsourced edit, or promote to `:authoritative` without verifiable provenance — G4.
- Do not call any cell's `.solve()` — R0 scaffolds raise by design (G8).
- Do not route design/inference through a commercial GPU — G6 (Murakumo-only).
