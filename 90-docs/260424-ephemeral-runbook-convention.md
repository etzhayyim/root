---
id: doc-260424-ephemeral-runbook-convention
title: "Convention: ephemeral cutover runbooks (deleted after the flip)"
status: active
doc_type: reference
topic: doc-governance
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - cutover runbook naming + lifecycle
  - criteria for "delete me after flip" docs
  - pattern used by strict-mode + legacy-trust runbooks
related:
  - doc-260424-oauth-strict-mode-cutover
  - doc-260424-legacy-trust-headers-cutover
---

# Goal

A cutover runbook is a document whose sole purpose is to describe *one*
staged production flip — typically an env-var change that retires a
grace-window behavior after a fixed observation period. These
documents are valuable for exactly one window and then become stale
carrying instructions to execute a no-longer-relevant flip.

This note codifies the pattern: **ephemeral runbooks are born with a
deletion trigger and should be deleted when the trigger fires.**

# Pattern

## Structure

An ephemeral runbook has the following sections in this order:

1. **Context** — what grace behavior + flag it targets; which ADR it
   serves.
2. **Pre-flip validation** — the gates that must pass before flipping
   (usually: deployment age ≥ N days, logs show ≈ 0 legacy hits,
   staging rehearsal green). Each gate has a concrete query.
3. **Flip procedure** — per-Worker deploy order and the single line of
   config being changed. Order matters when downstream and upstream
   depend on each other's accept/emit behavior.
4. **Rollback** — reverse the flip, same order or reversed, with
   cache-invalidation notes.
5. **Observability hooks** — table of signal / source / threshold the
   operator watches during cutover and the T+N day after.
6. **Post-flip cleanup** — concrete list of code/config the operator
   deletes after the signal has stayed green for the post-flip window.
   **Includes "delete this runbook" as the final item.**

## Lifecycle

```
T-Ndays    runbook lands ──┐
                           │   (grace window — users cite it)
T0         cutover day ────┤
                           │   (post-flip observation, typically 2 weeks)
T+Ndays    cleanup day ────┘   ← delete the runbook, delete the env var,
                                  delete the grace branches in code
```

The runbook ships with the grace behavior, not ahead of it. Deleting
after cleanup is what distinguishes "ephemeral" from a normal how-to
doc: there is nothing left in the system the runbook could describe.

## Naming

- Path: `90-docs/YYMMDD-<slug>-cutover-runbook.md`
- `id:` field: `doc-YYMMDD-<slug>-cutover`
- Front-matter `status: active` until cleanup day; changing to
  `deprecated` is optional — the default cleanup is file deletion.

## When to use — ephemeral vs permanent

| Document type | Signal for ephemeral |
|---|---|
| Cutover (flag flip, grace close, MV rebuild) | **Yes** — delete after |
| Deploy checklist (recurring, per release) | No — permanent, updates in place |
| ADR (design decision) | No — permanent, supersede via new ADR |
| Operational dashboard | No — permanent, updates in place |
| Incident postmortem | No — permanent, history |
| Runbook for an always-on daily ops task | No — permanent |

# Examples on this repo

| Runbook | Flip | Post-flip cleanup day |
|---|---|---|
| `260424-oauth-strict-mode-cutover-runbook.md` | `DPOP_CNF_JKT_ENFORCEMENT: warn → strict` | ≈ 2026-05-22 (T0 + 14d) |
| `260424-legacy-trust-headers-cutover-runbook.md` | `LEGACY_TRUST_HEADERS: on → off` on 4 Workers | ≈ T0 + 14d (T0 TBD, ≥2 weeks after HMAC deploy) |

Both runbooks carry the deletion-as-cleanup-step explicitly in their
Post-flip cleanup section.

# Operational notes

- **Do not** fold an ephemeral runbook's steps into the ADR it serves —
  the ADR is permanent, the runbook isn't, and conflating them makes
  the ADR carry stale instructions.
- **Do** link the ADR `related:` list back to the runbook while it's
  alive, and remove that link entry in the same commit that deletes the
  runbook.
- **Do** track the cutover signal in `deps.toml` as a `[[migrations]]`
  entry if you want it to surface in `etzhayyim` tooling. The migration
  entry is permanent; it just flips from `status="staged"` to
  `status="done"` when the runbook is deleted.
