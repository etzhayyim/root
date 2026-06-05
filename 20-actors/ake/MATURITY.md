# ake (朱) — maturity ledger

**Actor**: 朱 (ake) — community-edit membrane (Wikipedia-stance) · **ADR**: 2606052100 · **DID**:
`did:web:etzhayyim.com:actor:ake`

| Axis | R0 (this) | R1 (gated) | R2 (gated) |
|---|---|---|---|
| **propose intake** | offline screen+record over seed | live `:edit/*` intake over real KG seed | standing service across all KG actors |
| **triage** | deterministic risk+quality + pure-function route | Murakumo-only LLM refines scores (route stays pure) | calibrated scoring vs accepted-edit history |
| **review** | optimistic / vote-sim / council-pending + challenge→revert rollback primitive | real 1 SBT = 1 vote + 48h timelock | edit-war resolution wired to danjo-observed + Council |
| **promote** | member-signed dry-run, `published=false` | member-signed live promotion | `:representative→:authoritative` coverage pipeline |
| **history** | append-only revision engine (as-of/current) | "view history" tab on /actor + /search | contributor-trajectory dashboards |

## R0 evidence

- **99 tests green** (`./run_tests.sh`): 17 triage + 7 revision + 6 edit-war + 8 contributor + 5
  ingest + 16 charter-invariants + 6 analyze + 5 lexicons + 9 consistency/SSoT-drift-lock (methods)
  + 20 cell state-machine.
- **Edit-war resolution landed** (`revision.revert` + `test_editwar.py`): a `:challenge` routes
  high→vote; an upheld challenge rolls back to the predecessor by appending (Wikipedia revert) — the
  bad edit is undone for the current reader yet preserved in the auditable history (danjo-observable).
- **Membrane proven over REAL repo data** (`methods/ingest.py`): bootstraps the append-only revision
  history from the actual committed `actor-profile-seed.kotoba.edn`; surfaced + closed an
  `INFRA_ACTORS`↔profile-seed drift (added mitooshi + noroshi profile records, 19→21).
- **End-to-end membrane** (`methods/analyze.py`): 5 seed edits route to all 5 outcomes
  (auto-accept / vote-accepted×2 / council-pending / rider-refused); accepted edits land in the
  append-only revision history, refused/pending do not.
- **Structural invariants** enforced in 3 places each and tested structurally (not by prose-grep):
  G1 member-only + no-server-key, G2 no `:triage/decision` + pure-function route, G3 mirror
  target-kinds, G4 provenance-required, G5 append-only ops, G7 Council-Lv7 invariant-lock, G8
  `published=false`.
- **Registered** in `INFRA_ACTORS` → `did:web:etzhayyim.com:actor:ake` (resolvable + searchable);
  actor-profile seed added.

## Honest gaps (R0)

- No live ingest / binding vote / promotion / publish — all G8 (Council Lv6+ + operator).
- Triage scoring is deterministic; the Murakumo-only LLM refinement is R1.
- The `:representative` seed is 5 illustrative edits, not the live KG.
- The contributor-trajectory (G9) is now real, tested code (`methods/contributor.py` — rate limit +
  recoverable trajectory); it is not yet wired into a live request-path rate-limiter (R1).
- No UI — the "view history" tab on /actor + /search is R1.

## Zero invariant amendments

ake **strengthens** four existing invariants and amends none: no-server-key (ADR-2605231525),
kotoba-canonical-state (ADR-2605312345), 1 SBT = 1 vote, and the mirror invariant (ADR-2606042330).
