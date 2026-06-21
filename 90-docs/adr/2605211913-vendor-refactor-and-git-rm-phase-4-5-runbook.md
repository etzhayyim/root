---
id: adr-2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook
title: "ADR-2605211913: Phase 4-5 runbook — vendor business-app dependency switch + open-scope deletion (ADR-2605152100 finale)"
status: proposed
doc_type: adr
topic: vendor-refactor-and-git-rm-phase-4-5-runbook
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: operations
weight: 0.80
priority_note: "Operator runbook for the final two phases of ADR-2605152100 cutover (Phase 4 vendor business-app dep switch + Phase 5 vendor open-scope deletion). Pairs with ADR-2605211757 (DNS cutover) as the second operator-facing runbook of the Tranche F closure. Both runbooks are gated on the per-worker kotoba re-impl (Phase 3 gate (a)) actually landing in etzhayyim/root."
authoritative_for:
  - vendor-side refactor + deletion procedure for the 27 worker + 4 ingest + 4 primitive files
  - etzhayyim lg subtree deletion order (3 already-relocated subtrees + their kotodama imports)
  - rollback procedure for partial vendor refactor failures
  - verification protocol post-deletion (vendor build + downstream importer survey)
depends_on:
  - adr-2605212100-kotodama-worker-3-axis-tranche-f-closure
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
related:
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605211925-phase-6-archive-markers-runbook
  - doc-2605211800-vendor-importer-survey-gate-d
  - doc-2605211900-tranche-f-all-gates-closure-confirmation
supersedes: []
superseded_by: []
---

# ADR-2605211913: Phase 4-5 runbook — vendor business-app dep switch + open-scope deletion

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 (etzhayyim GitHub org boundary) defined a 6-phase cutover for
splitting the etzhayyim vendor monorepo from the etzhayyim open religious-corp
monorepo:

1. Catalog freeze ✅ (Tranche F + earlier Tranches)
2. etzhayyim/root scaffolding ✅
3. Content copy ✅
4. **Vendor business-app dependency switch** — point vendor business apps at
   etzhayyim packages / submodules instead of local kotodama paths
5. **Vendor open-scope deletion** — `git rm` the etzhayyim-classified worker
   / ingest / primitive files from the etzhayyim repo
6. Archive markers — `[MOVED → github.com/etzhayyim/root]` description prefix
   on archived etzhayyim repos

Phases 1-3 are complete. ADR-2605211757 covers gate (b) DNS cutover (which is
operationally distinct from Phase 4-5 but must precede the final `git rm` so
external callers see 410 Gone rather than missing-source build failures).
This ADR is the runbook for Phase 4-5.

The current kotodama vendor file count is:

| Path | Count |
|------|-------|
| `kotodama/*.py` (workers + ad-hoc) | 111 |
| `kotodama/primitives/*.py` | 796 |
| `kotodama/ingest/*.py` | 60 |

Of these, the etzhayyim-classified scope per Tranche F closure (ADR-2605212100
§1) is: **29 workers + 4 ingest modules + 4 substrate primitives** = ~37 files
plus their per-actor companion files (see deletion catalog below).

# Decision

Adopt the 4-step Phase 4-5 runbook below. The runbook is **per-target** —
operators MAY run multiple lg subtrees in parallel, but the kotodama deletion
step (Step 3) is a single atomic commit per safety.

## 0. Pre-flight

These conditions MUST hold before any Phase 4-5 step:

1. **Phase 3 gate (a) closed**: the 29 per-worker Python ports + 4 ingest
   modules + 4 substrate primitives MUST exist on disk at
   `etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/` and pass their
   smoke tests. As of 2026-05-21 evening this gate is OPEN — Phase 4-5
   execution is blocked until those files land.
2. **DNS cutover at least to Wave C completed** (ADR-2605211757) — vendor 410
   for the cut-over actor hosts already in place via routing-gateway so
   external callers don't hit dangling URLs during the vendor `git rm`.
3. **gate (d) executable steps done** (per doc 2605211800):
   - 3 lg subtree relocates: `lg_organism` (pre-existing), `lg_legal_entity`
     (relocated 2026-05-21), `lg_curpus2skill` (relocated 2026-05-21) ✅
   - 1 hume inline copy: `_local_ingest_core.py` (193 LoC) ✅
4. **Operator authority**: this runbook uses `git rm` which is a destructive
   operation under the project's git safety policy. Operator MUST acknowledge
   explicit authorization in the commit message body (`Authorized-By:` trailer).

## 1. Phase 4 — vendor business-app dependency switch

Vendor business apps that currently `from kotodama.{X}` etzhayyim-scoped
modules MUST switch to a non-fragile source. Three options, in order of
preference:

| Option | Mechanism | When |
|--------|-----------|------|
| **A. Git submodule** | `git submodule add https://github.com/etzhayyim/root etzhayyim` in etzhayyim repo, then `from etzhayyim.20-actors.kotodama.py.src.kotodama.X` (or symlink for shorter paths) | Single-source-of-truth preserved; etzhayyim repo build sees etzhayyim source as a transitive checkout. Best for ongoing development |
| **B. Python package** | Publish `kotodama-substrate` (or split into `@etzhayyim/kotodama-{substrate,workers,ingest}`) to a private index; vendor `pip install` it | Best for production stability. Requires CI for package builds. Defer to a separate ADR if/when this is chosen |
| **C. Local copy** | Operator copies the etzhayyim files into a etzhayyim-side `_vendored/kotodama/` directory and updates imports | Fastest. Highest drift risk. Use ONLY for files vendor needs to keep running through a transition window |

**Default for Phase 4**: Option A (git submodule). Operator commands:

```bash
cd /Users/junkawasaki/github/etzhayyim-root
git submodule add https://github.com/etzhayyim/root etzhayyim
# Or if the submodule already exists at .gitmodules level, just:
git submodule update --init etzhayyim
```

For vendor scripts that need a short import path:

```bash
ln -s etzhayyim/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama_etz
# Then vendor imports `from kotodama_etz.X` instead of `from kotodama.X`
```

The only **mandatory** Phase 4 import switches are the 4 gate-(d) target files
(per doc 2605211800):

| # | Vendor file | Current import | Phase 4 treatment | Status |
|---|-------------|----------------|-------------------|--------|
| 1 | `60-apps/etzhayyim-project-ki/lg/lg_organism/server.py` | `from kotodama.{hakkou,kabi,ki,kinoko,kobo,koke,saikin}_worker_main` | Delete (relocated to etzhayyim) | Step 2.A below |
| 2 | `60-apps/etzhayyim-project-legal-entity/lg/lg_legal_entity/server.py` | `from kotodama.primitives.legal_entity` | Delete (relocated to etzhayyim) | Step 2.A below |
| 3 | `60-apps/etzhayyim-project-curpus2skill/lg/lg_curpus2skill/server.py` | `from kotodama.ingest.curpus2skill` | Delete (relocated to etzhayyim) | Step 2.A below |
| 4 | `60-apps/etzhayyim-project-hume/scripts/persist_hume_artifacts.py` | `from kotodama.ingest.core` | Already switched to local copy (`_local_ingest_core.py`) | ✅ done 2026-05-21 |

Audit for additional importers (run before Step 2):

```bash
cd /Users/junkawasaki/github/etzhayyim-root
grep -rln "from kotodama" --include="*.py" \
  | grep -v _archive \
  | grep -v "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/" \
  | grep -v "/tests/" \
  > /tmp/phase4-vendor-importers.txt
# Compare with doc-2605211800 baseline (68 importers, 4 in-scope)
diff /tmp/phase4-vendor-importers.txt <(cat <<EOF
... (paste the 68-file list from doc 2605211800)
EOF
)
```

If new in-scope importers appeared since 2026-05-21, extend Step 2 to cover
them (relocate or local-copy per the same playbook).

## 2. Phase 5 — vendor open-scope deletion

### Step 2.A — Delete relocated lg subtrees

```bash
cd /Users/junkawasaki/github/etzhayyim-root
git rm -r 60-apps/etzhayyim-project-ki/lg
git rm -r 60-apps/etzhayyim-project-legal-entity/lg
git rm -r 60-apps/etzhayyim-project-curpus2skill/lg
git commit -m "phase5(tranche-f): remove relocated lg subtrees (ki/legal-entity/curpus2skill)

These lg directories now live in etzhayyim/root/60-apps/<project>/lg/
per gate (d) doc-2605211800 and the 2026-05-21 relocate.

Closes: gate (d) #1-3 of ADR-2605212100 (vendor importer survey clean)

Authorized-By: <operator>
"
```

The corresponding `60-apps/etzhayyim-project-<project>/wasm/` Worker apps are
NOT deleted by this step. They are separate decisions under the 3-axis split
rule (see ADR-2605172400 §1; legal-entity wasm has a custody axis hit if it
holds JP corporate-registry PII → vendor; otherwise etzhayyim).

### Step 2.B — Delete the 29 worker_main files

```bash
cd /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama
# 8 organism BeliefStore
git rm hakkou_worker_main.py kabi_worker_main.py ki_worker_main.py \
       kinoko_worker_main.py kobo_worker_main.py koke_worker_main.py \
       saikin_worker_main.py myco_yeast_worker_main.py
# Wave 1-4 + utility (rwfree by gate (a) port)
git rm tools_audit_worker_main.py sixir_worker_main.py \
       hub_worker_main.py web4_worker_main.py oshiete_worker_main.py \
       resources_worker_main.py omikuji_worker_main.py \
       kareyanagi_worker_main.py kiyome_worker_main.py \
       gov_worker_main.py narou_worker_main.py ge_worker_main.py \
       blockchain_worker_main.py houbun_worker_main.py \
       curpus2skill_worker_main.py site_common_crawl_worker_main.py
# 5 truly-clean utility
git rm tools_const_worker_main.py tools_http_worker_main.py \
       tools_json_worker_main.py tools_time_worker_main.py \
       tools_transform_worker_main.py
git commit -m "phase5(tranche-f): remove 29 etzhayyim-classified worker_main files

Classified per ADR-2605212100 §1; kotoba ports landed in
etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ (gate (a)).

Closes: gate (a) execution + final vendor-side trace of these workers

Authorized-By: <operator>
"
```

### Step 2.C — Delete the 4 ingest modules

```bash
cd /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama
git rm ingest/blockchain.py ingest/houbun.py ingest/curpus2skill.py \
       ingest/site_common_crawl.py ingest/core.py
git commit -m "phase5(tranche-f): remove 4 etzhayyim ingest modules + ingest.core

ingest.core was retained at etzhayyim repo through gate (d) so hume could
continue to import it. After Phase 4 hume switch (2026-05-21 done) +
ingest.core port to etzhayyim/root, the etzhayyim copy is now removable.

Closes: gate (a) execution for ingest modules

Authorized-By: <operator>
"
```

### Step 2.D — Delete the 4 substrate primitives

```bash
cd /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives
git rm active_inference_substrate.py at_ipfs_belief_store.py \
       rw_belief_store.py legal_entity.py
# worker_runtime.py was at kotodama/ root, not primitives/, but is also etzhayyim:
git rm ../worker_runtime.py
git commit -m "phase5(tranche-f): remove 4 etzhayyim substrate primitives

Substrate boundary per ADR-2605172000 (kotoba) finalized:
- active_inference_substrate.py — BeliefStore Protocol
- at_ipfs_belief_store.py — kotoba BeliefStore impl
- rw_belief_store.py — RW-bound BeliefStore impl (vendor-only? double-check)
- legal_entity.py — gate (d) primitive
- worker_runtime.py — vendor-neutral runtime helpers

Authorized-By: <operator>
"
```

### Step 2.E — Post-deletion verification

```bash
cd /Users/junkawasaki/github/etzhayyim-root
# 1. No vendor file should still import any deleted symbol:
deleted_symbols=("hakkou_worker_main" "kabi_worker_main" "ki_worker_main"
                 "kinoko_worker_main" "kobo_worker_main" "koke_worker_main"
                 "saikin_worker_main" "myco_yeast_worker_main"
                 "tools_audit_worker_main" "sixir_worker_main"
                 "hub_worker_main" "web4_worker_main" "oshiete_worker_main"
                 "resources_worker_main" "omikuji_worker_main"
                 "kareyanagi_worker_main" "kiyome_worker_main"
                 "gov_worker_main" "narou_worker_main" "ge_worker_main"
                 "blockchain_worker_main" "houbun_worker_main"
                 "curpus2skill_worker_main" "site_common_crawl_worker_main"
                 "ingest.blockchain" "ingest.houbun" "ingest.curpus2skill"
                 "ingest.site_common_crawl" "ingest.core"
                 "primitives.active_inference_substrate"
                 "primitives.at_ipfs_belief_store"
                 "primitives.legal_entity"
                 "worker_runtime")
for s in "${deleted_symbols[@]}"; do
  hits=$(grep -rln "from kotodama.${s}\|import kotodama.${s}" \
         --include="*.py" 2>/dev/null \
         | grep -v _archive \
         | grep -v "/tests/" \
         | wc -l | tr -d ' ')
  if [ "$hits" -gt 0 ]; then
    echo "FAIL: ${s} still has $hits importers"
    grep -rln "from kotodama.${s}\|import kotodama.${s}" \
      --include="*.py" 2>/dev/null \
      | grep -v _archive | grep -v "/tests/"
  fi
done

# 2. Vendor Python build/lint passes:
cd 40-engine/kotoba/crates/kotoba-kotodama/py && uv sync --dev && uv run pyright . | tail -5

# 3. CI green on a representative branch:
gh pr create --base main --title "phase5(tranche-f): finalize vendor open-scope deletion" \
  --body "..."
```

### Step 2.F — `deps.toml` post-deletion amendment

Update the closure cross-reference:

```toml
# etzhayyim-root/deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17
all_gates_closed_at = "2026-05-21T17:57:00Z"          # design + runbook
gate_a_execution_completed_at = "2026-MM-DDTHH:MMZ"   # operator fills when Phase 3 (a) re-impl lands
phase_5_deletion_completed_at = "2026-MM-DDTHH:MMZ"   # operator fills when Step 2.A-2.D commits land
```

# Rollback

Rollback differs by step:

- **Step 2.A failure** (lg subtrees deletion): `git revert <commit>`. Vendor build
  resumes; etzhayyim copies remain unaffected. <5 min.
- **Step 2.B-D failure** (kotodama deletion): `git revert <commit>`. Vendor build
  resumes. Etzhayyim copies are independent (they live in the other repo).
  However, after revert the operator MUST also revert any subsequent step's
  commit, otherwise the deletion-state drift between commits causes diff noise.
- **Post-2.E discovers broken downstream importer**: forward-fix only. Either
  (i) restore the deleted file as a `_vendored/` local copy in etzhayyim, OR
  (ii) fix the downstream importer to use the etzhayyim submodule path.
  Choose (ii) for sustainability.

# Consequences

**Positive**

- Operator has a single, ordered checklist for Phase 4-5; no per-file
  judgment calls.
- Per-step atomic commits give git-bisect-friendly granularity for
  post-deletion regressions.
- Cross-reference with ADR-2605211757 + doc-2605211800 keeps the closure
  evidence chain intact.
- Closes the long-tail of the org-split started in ADR-2605152100 (2026-05-15).

**Negative / risks**

- The runbook is gated on Phase 3 gate (a) per-worker re-impl actually
  landing in `etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/`. Without
  that, Step 2.B-D `git rm` deletes the only copies of the workers —
  unrecoverable except via git history. Pre-flight gate (a) check MUST be
  enforced.
- The "remove 5 truly-clean utility worker" step is straightforward but
  there's no downstream importer survey yet — operator should add a
  pre-deletion grep for `from kotodama.tools_(const|http|json|time|transform|audit)_worker_main`.
- The substrate primitive deletion (Step 2.D) names `rw_belief_store.py`. This
  is RW-bound and conceptually vendor-only; **double-check before deleting**
  — it may need to stay on the vendor side for any remaining vendor agent
  that uses the dual-write pattern (ADR-2605211200 Phase 2A-2D §dual-write).
- The relocated lg subtrees in etzhayyim/root currently lack their own
  CLAUDE.md / project README; operator should add these before Step 2.A so
  etzhayyim discoverability isn't reduced.

**Mitigations**

- Pre-flight Step 0 §1 is a hard gate. The runbook explicitly tells the
  operator to verify gate (a) before proceeding.
- Each Step 2.X is its own commit; rollback granularity is 1 commit per ~10
  files.
- The Authorized-By trailer in commit messages creates an audit trail.

# Alternatives Considered

1. **Single big-bang `git rm` of all 37+ files**.
   Rejected: deletion granularity matters for post-deletion troubleshooting.
   Per-category atomic commits are the floor.

2. **Skip Phase 4 git submodule, jump straight to Phase 5 deletion**.
   Rejected: vendor scripts that import the soon-to-be-deleted files would
   break with no alternative source. The 4 gate-(d) target files already have
   their alternatives in place (3 relocates + 1 inline) but the runbook
   assumes future vendor-side scripts may also need access; the submodule
   gives them a path without re-copying.

3. **Publish Python package and have vendor `pip install` it** (Phase 4 Option
   B in the table above).
   Considered. Higher operational quality but introduces CI complexity
   (publish pipeline, version locking, security scanning). Deferred — git
   submodule is the lower-friction default; package-publish is a follow-up
   ADR if/when the vendor CI matures to need it.

4. **Keep the etzhayyim copies as a permanent fallback** (no Phase 5 at all).
   Rejected: violates ADR-2605152100 §"Step 8 vendor open-scope cleanup".
   The whole point of the org-split is to NOT have two copies of the same
   open-scope code drifting independently.

# References

- ADR-2605152100 (etzhayyim GitHub org boundary — Phase 4-5 definition source)
- ADR-2605172400 (3-axis split rule)
- ADR-2605212100 (Tranche F closure — gate definitions)
- ADR-2605211757 (DNS cutover runbook — Wave A-D operator runbook)
- ADR-2605172000 (kotoba substrate — primitive boundary)
- `90-docs/2605211800-vendor-importer-survey-gate-d.md` — gate (d) target list
- `90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md` — gate status snapshot
- `etzhayyim-root/deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17` — cross-repo log
