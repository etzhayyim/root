---
id: adr-2605211335-tranche-f-session-closure-category-a-split
title: "ADR-2605211335: Tranche F session 2026-05-21 closure + Category A SPLIT pattern generalization"
status: active
doc_type: adr
topic: tranche-f-closure
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - Tranche F session 2026-05-21 final closure state
  - Category A "BPMN-only SPLIT" pattern generalization (33 actors)
  - Cross-repo overlap classification 7-category taxonomy
related:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605211000
depends_on:
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
supersedes: []
superseded_by: []
---

# ADR-2605211335: Tranche F session 2026-05-21 closure + Category A SPLIT pattern generalization

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki + Claude Opus 4.7

# Context

The 2026-05-21 working session executed a Tranche F status sweep across both `etzhayyim/root` and `etzhayyim/etzhayyim-root` to close out the mechanical migration phase started 2026-05-17 (catalog freeze) and document the remaining structural patterns.

Inputs to the sweep:

- Tranche F catalog (ADR-2605172400) judged ~520 items A/B/C-group + vendor-confirmed
- Phase E/F milestone (2026-05-21) reported 25 rw-free actors at 100% + 25 worker XRPC adapters
- 16 `[[migrations]] category = "etzhayyim-split"` entries existed in vendor `deps.toml` before the sweep
- Cross-repo file presence revealed 45 actors present in both repos
- 7 new vendor projects landed post-freeze (2026-05-17 → 2026-05-20)
- Pre-existing TOML-malformed region in vendor `deps.toml` (lines ≈ 35797–36400) blocked safe in-place amend

# Decision

## 1. Closure record format

All status closures land as **new `[[migrations]]` entries appended at the clean trailing region** of vendor `deps.toml`, each referencing its predecessor via `supersedes_status_for`. This sidesteps the pre-existing malformed region and keeps closures parseable by strict TOML readers.

Required fields on closure entries:

- `id = "...-2026-05-21"` (date-suffixed)
- `status = "code-side-complete"` or `"superseded"` or `"audit-recorded"`
- `code_side_complete = true` (when applicable)
- `code_side_completed_at = "YYYY-MM-DD"`
- `next_action_owner = "..."` (or `"none"`)
- `supersedes_status_for = "<predecessor id>"` (string for 1, array for many)

## 2. Cross-repo overlap taxonomy (7 categories)

The 45 actors with identical `60-apps/etzhayyim-project-<name>` directories in both repos resolve to 7 distinct patterns:

| Cat | Pattern | Count | Steady state? |
|---|---|---|---|
| **A** | BPMN-only SPLIT (etz: `bpmn/` only; vendor: full runtime) | ~33 | yes — permanent |
| **B** | Phase E/F pre-sunset (etz: bpmn + rw-free + xrpc-adapter; vendor live) | 4 | no — operator sunset pending |
| **C** | `lg/` pod in both (potential duplicate) | 1 (ki) | no — per-project audit |
| **D** | Partial cut over (rw-free in etz, wasm legacy in both) | 1 (kiyo) | no — operator sunset pending |
| **E** | Fullmove pre-sunset (both repos full structure) | 1 (tsukuru) | no — Phase 3-6 multi-quarter |
| **F** | Closure already recorded (Phase 1 scaffold mirror landed) | 2 (public-malak / open-jpn-mynumber) | yes — Phase 1 done, Phase 2-4 deferred |
| **G** | Intentional dual stub (cross-actor doc on both sides) | 1 (yobel) | yes — by design |

`+H` (Category A variants — performers / hub) merged into A.

## 3. Category A SPLIT pattern — generalization

**The Category A SPLIT pattern is now the default disposition for "BPMN moved to etz, runtime stays vendor."** No per-actor 3-axis re-test is required for actors that match this pattern at audit time. They inherit:

- **Source** of generalization: dougaka SPLIT confirmation (vendor `tranche-f-s6-dougaka-split-confirmation-2026-05-20`)
- **Trigger to leave the pattern** (= re-judgment trigger per ADR-2605172400):
  - Actor starts billing fiat
  - Actor takes on regulatory liability shift
  - Actor's BPMN moves to a runtime that depends on etzhayyim substrate primitives (PDS XRPC / mst-projector / etc.)
  - Actor's BPMN gains user-facing PII surface
- **What "SPLIT" means concretely**:
  - `00-contracts/bpmn/com/etzhayyim/<actor>/*.bpmn` lives in etzhayyim/root (spec, open)
  - Worker / appview / LangServer task handlers / kotodama primitives stay in vendor (runtime)
  - Per-actor `kotodama.jsonld` typically declares `operator: etzhayyim.com` (or unspecified)
  - No 3-axis re-test required at quarterly cycle if no trigger fires

The 33 Category A actors at 2026-05-21 audit:

```
6ir / analytics / auto-sales-erp / business-manager / cards / casino /
completer / fleamarket / games / ge / gov / harai / hub / kaisya /
lawfirm-admin / lo / music / ops / oshiete / outlook / performers / po /
provider-pod / resources / robot / scheduler / threads / tia / videos /
videos-legacy / web4 / webpage / wire / worlds / wvme
```

## 4. Post-freeze 7-actor verdicts (catalog drift correction)

For projects added after 2026-05-17 catalog freeze, the 3-axis test was applied per actor (vendor PR #1339):

| Actor | First commit | Verdict |
|---|---|---|
| itonami | 2026-05-17T12:20 | VENDOR (aerospace certification liability) |
| deai | 2026-05-17T20:24 | **DEFERRED — Council Lv6+ ruling required** (PII + research, kotodama declares operator=etzhayyim) |
| mamoru-m4m0ru01 | 2026-05-18T12:27 | VENDOR (git secret guardian, customer repos) |
| ransomwatch | 2026-05-18T20:24 | MOVE TARGET (TLP:WHITE clean, scaffold landed etz PR #233) |
| dogaka | 2026-05-19T17:56 | VENDOR (3D video production; no lexicons exist to SPLIT) |
| yobel | 2026-05-20T10:38 | MOVE TARGET (in flight on etz PR #73) |
| cyber-drill | 2026-05-20T18:57 | VENDOR (self-declared VENDOR-PRIVATE per CLAUDE.md §Boundary) |

## 5. Final session totals

- etz `60-apps/etzhayyim-project-*`: 122 (open religious-corp scope)
- vendor `60-apps/etzhayyim-project-*`: 408 (vendor proprietary scope)
- intersection: 45
- unique total: 485 (122 + 408 − 45)

PRs merged this session (15 total):

| Repo | PR | Lane | Contribution |
|---|---|---|---|
| etz | #226 | B | public-malak Phase 1 scaffold + 14 lexicons |
| etz | #227 | E1 | open-jpn-mynumber carve-out + lexicon mirror |
| etz | #228 | I | ADR-2605211000 open-isco BPMN-only reconciliation |
| etz | #229 | J | dougaka SPLIT confirmation (etzhayyim mirror) |
| etz | #230 | K | CI pnpm-workspace fix (25-actor matrix unblock) |
| etz | #233 | P | ransomwatch Phase 1 scaffold + 4 lexicons |
| etz | #209 | (古) | kafun-bokumetsu ADR (carried over) |
| etz | #225 | (古) | mst-projector ProjectorConfig (carried over) |
| vendor | #1334 | D | maps cutover code-side complete + Stage 0-5 table |
| vendor | #1335 | E2 | open-jpn-mynumber Option A activated |
| vendor | #1336 | F | 5 vendor-confirmed actors closure |
| vendor | #1337 | L | Tranche F status sweep (ipaddress + tsukuru) |
| vendor | #1338 | N | 45-overlap cross-repo audit (7 categorization patterns) |
| vendor | #1339 | O | post-freeze 7-actor 3-axis audit |
| vendor | #1331 | M | (closed without merge) Vitest templates redundant |

## 6. Operator-gated remaining work

These cannot be moved by code-side work:

- maps Stage 0-5 (reader image build / backfill / shadow read / dual write / DNS cutover / vendor sunset)
- etz worker XRPC × 25 deploy (Tier 1 → wait 7d → Tier 2 → wait 2d → Tier 3/4)
- 220-file `etzhayyim` → `etzhayyim` sed cutover (after 法人登記変更)
- Base Sepolia testnet → Mainnet deploy (after Council Seat 2-5 RFP closes 2026-06-19)
- LanceDB+DuckDB+@huggingface optional peer install on projector pod (per ADR-2605212000)
- WebSocket `com.atproto.sync.subscribeRepos` client (replace PollingFirehose)

## 7. Council-gated remaining work

- **deai** disposition — PII + research data charter compatibility ruling (Lv6+)
- yobel etz PR #73 — Council Lv6+ ratification of ADR-2605201800

## 8. Non-mechanical follow-ups deferred

- rw-free quality fixes — 19 isbn vitest assertion failures + tsconfig drift (anime / narou / 70-tools/integration-tests) + lib.webworker.d.ts TypeScript lib conflict on xrpc-adapters
- vendor `deps.toml` malformed region (lines ≈ 35797–36400) — needs git-archaeology per-entry reconstruction
- C-category audit (ki — `lg/` pod in both) — per-project disposition

# Consequences

## 正の効果

- **Single closure pattern** for Tranche F entries: append-at-end with `supersedes_status_for`. Future agents do not re-investigate predecessor entries.
- **Category A SPLIT** is now the explicit default disposition (33 actors). No per-actor 3-axis re-test required unless a trigger fires.
- **Cross-repo overlap is bounded**: 45 actors, all classified, all with disposition (action / no-action / operator-gated).
- **Post-freeze drift caught**: 7 new vendor actors classified within the same session as catalog freeze.
- **CI unblocked**: 25-actor vitest/tsc/wrangler-validate matrices now run actual logic instead of failing on workspace resolution. Test failures become meaningful signal.

## 負の効果 / コスト

- **deai stuck**: PII + research project cannot proceed without Council ruling. Kotodama-declared operator (etzhayyim) and 3-axis verdict (HIT on L+C) are inconsistent.
- **vendor `deps.toml` malformed region persists**: the audit + closure entries route around it, but the canonical historical record is still partially unparseable.
- **rw-free quality regressions visible**: 19 isbn test failures + tsconfig drift were hidden by the workspace bug. They now show as CI red, which may pressure premature fixes if not gated under "post-migration quality" budget.
- **Concurrent agent contention observed**: at least one other agent made commits on the same branches mid-session (e.g., user's surplus-router ADR on a CI-fix branch). Force-push reconciliation needed twice.

# Alternatives Considered

## Alternative A: per-actor closure entries instead of bulk closure

Each of the 5 vendor-confirmed actors (sense / joucho / kagami / ohanashi / dougaka) gets its own `code-side-complete` entry instead of the single `tranche-f-vendor-confirmed-actors-closure-2026-05-21` bulk entry. Rejected because each per-actor entry would duplicate the same "no migration code follows" signal 5× without new information.

## Alternative B: in-place amend the predecessor entries

For each closure, edit the predecessor entry's `status` / `code_side_complete` fields directly. Rejected because most predecessors live in the pre-existing TOML-malformed region and in-place edits risk further corruption. Append-at-end is the safer pattern; the `supersedes_status_for` link preserves the lineage.

## Alternative C: per-actor 3-axis re-test for Category A 33 actors

Apply the ADR-2605172400 3-axis OR-test to each of the 33 Category A actors individually instead of inheriting SPLIT from the dougaka precedent. Rejected for cost reasons (33 per-actor entries) and consistency (the BPMN-only-in-etz state already implies the test was effectively applied during the original Tranche F mechanical Phase 3 lexicon copy wave). Quarterly re-judgment cycle handles drift.

## Alternative D: defer Category A documentation to a separate session

Don't document the Category A SPLIT pattern in this ADR; let future agents re-derive from the dougaka precedent + cross-repo audit. Rejected because the 33-actor scope is too large to leave as folklore. Explicit documentation reduces re-investigation cost.

# References

- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605172400 — vendor 3-axis split rule (+ Re-judgment triggers)
- ADR-2605211000 — worker XRPC deploy runbook (open-isco reconciliation in this session)
- ADR-2605212000 — mst-projector Phase 3 (optional peer deps reference)
- ADR-2605215000 — Murakumo-fleet-only inference (Phase 3 target for ransomwatch)
- vendor deps.toml entries: `tranche-f-*-2026-05-21` family + `tranche-f-vendor-confirmed-actors-closure-2026-05-21` + `tranche-f-45-overlap-cross-repo-audit-2026-05-21` + `tranche-f-post-freeze-7-actors-audit-2026-05-21`
- etz deps.toml session_summaries: `public-malak-scaffold-2026-05-21` / `open-jpn-mynumber-carve-out-2026-05-21` / `dougaka-split-confirmed-2026-05-21` / `ransomwatch-scaffold-2026-05-21`
