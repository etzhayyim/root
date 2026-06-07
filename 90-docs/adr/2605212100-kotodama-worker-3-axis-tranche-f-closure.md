---
id: adr-2605212100-kotodama-worker-3-axis-tranche-f-closure
title: "ADR-2605212100: Tranche F closure — 70 kotodama worker_main 3-axis classification + Phase 3 prerequisites"
status: active
doc_type: adr
topic: kotodama-worker-vendor-etzhayyim-boundary
authoritative: true
last_verified: 2026-05-21
priority: 8.7
axis: governance
weight: 0.87
priority_note: "Operational closure of Tranche F (ADR-2605172400) at the kotodama Python worker layer. Resolves all 70 *_worker_main.py files to etzhayyim / vendor / SPLIT and explicitly lists the 4-part gate that blocks any deployment-surface migration. Required reading before touching mitama-udf-pool helm chart or proposing a worker move to etzhayyim/root."
status_note: "Audit phase complete (29 etzhayyim / 30 vendor / 11 SPLIT, n=70). Phase 3 gate design + runbook complete 2026-05-21T17:57Z; per-worker re-impl execution OPEN — (a) pattern catalogued (6 patterns: BeliefStore / audit log / read-cache / primary store / worker_runtime+stub / ingest module) but per-worker SQLite ports not yet committed to etzhayyim/root; (b) DNS cutover runbook ADR-2605211757 ready; (c) deployment surface documented inline in ADR-2605211757 §0+§3.1 (Mac mini fleet + per-actor SQLite PVC; standalone ADR-2605211653 drafted but not retained); (d) vendor importer survey done + 3 lg relocates + hume local-copy inline. Phase 4-5 vendor refactor + git rm runbook = ADR-2605211913. Cross-repo closure pointer: deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17 closure_confirmed_by → etzhayyim/root/90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md. Source-level secrets removed across etzhayyim repo. helm upgrade of vendor-side default-murakumo-raw + copyright-fulltext-fetch-raw pending VKE API tunnel restore."
authoritative_for:
  - kotodama worker classification under the 3-axis OR-test
  - Phase 3 prerequisites for any worker deployment-surface migration to etzhayyim
  - corrected helm chart ownership semantics (etzhayyim is RW-free, not a Vultr+Helm copy target)
depends_on:
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605211200-etzhayyim-active-inference-organism-on-murakumo
  - adr-2605173100-gitguardian-incident-response
related:
  - adr-2605181400-bpmn-extract-to-etzhayyim-root
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com       # gate (b) closure + gate (c) inline
  - adr-2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook       # Phase 4-5 operator runbook
  - adr-2605211925-phase-6-archive-markers-runbook                     # Phase 6 archive markers runbook
  - doc-2605211800-vendor-importer-survey-gate-d                       # gate (d) closure
  - doc-2605211900-tranche-f-all-gates-closure-confirmation            # gate status snapshot (honest framing)
  - doc-2605211949-gate-a-execution-checklist                          # 42-row operator checklist for gate (a)
  - doc-2605212020-session-post-mortem-2026-05-21                      # 2026-05-21 session narrative + revert pattern
  - doc-tranche-f-index                                                # operator navigation hub
  # adr-2605211653 was drafted but not retained; gate (c) content lives inline in ADR-2605211757
supersedes: []
superseded_by: []
---

# ADR-2605212100: Tranche F closure — 70 kotodama worker_main 3-axis classification + Phase 3 prerequisites

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

ADR-2605172400 defined the etzhayyim / vendor 3-axis OR-test
(Liability / Custody / Settlement) and froze a Tranche F target list,
but stopped at the project / actor level. The actual Python worker
layer — 70 `*_worker_main.py` files under
`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/` — was left as an unresolved
follow-up. Without per-file judgment, the ownership of helm chart
templates, K8s manifests, and DID web domains remained ambiguous.

Three additional gates surfaced during the closure audit:

1. **RW-free substrate boundary (ADRs 2605172000 + 2605172100)**:
   etzhayyim is structurally RW-free. Any framing of "move helm
   templates to etzhayyim/root 50-infra" that assumed Vultr K8s +
   Kotoba/Datomic parity was conceptually invalid.

2. **GitGuardian incident posture (ADR-2605173100)**: a placeholder
   PostgreSQL URI containing a 32-char string had been seeded across
   the kotodama framework. etzhayyim/root scrubbed source on
   2026-05-17. etzhayyim was 4 days behind on the same scrub at session
   start.

3. **RW-free re-impl pattern (ADR-2605211200 Phase 2A-2D)**: the
   active-inference organism rollout established the BeliefStore
   (per-actor SQLite PVC) pattern as the canonical way to keep a
   worker's runtime semantics while severing the RW dependency. This
   is the prerequisite for any of the 29 etzhayyim-classified workers
   to actually deploy onto etzhayyim's substrate.

# Decision

## 1. Worker classification (n=70)

Apply the 3-axis OR-test to every `*_worker_main.py` file (plus
`dispatcher_main.py`, `agent_zeebe_worker_main.py`,
`zeebe_worker_main.py`).

**etzhayyim (29 / 41%)** — 3 axes clean, target for RW-free re-impl +
deployment on etzhayyim substrate:

- A-group: blockchain, gov, houbun, site_common_crawl,
  curpus2skill, legal-entity (implied by ge), tools_const,
  tools_http, tools_json, tools_time, tools_transform,
  tools_audit
- B-group: hakkou, kabi, kareyanagi, ki, kinoko, kiyome, kobo, koke,
  myco_yeast, narou, omikuji, saikin
- Borderline-resolved: ge, hub, oshiete, resources, sixir, web4

**vendor (30 / 43%)** — at least one axis hit, stays on etzhayyim Vultr:

- agent_zeebe, analytics, casino, compintel, completer,
  contentengine, fleamarket, graph_sos_intel, harai, lawfirm_admin,
  newsletter, ops, outlook, outreach, performers, po, provider_pod,
  robot, scheduler, threads, tia, tools_sql, videos, videos_legacy,
  cards, lo, webmk, webpage, wire, wvme

**SPLIT (11 / 16%)** — open spec / lexicon at etzhayyim, vendor
runtime stays on etzhayyim:

- Type 1 (intra-file split): dispatcher_main, zeebe_worker_main
- Type 2 (inter-repo, no intra-file split): anime, manga, music,
  games, pd_color, worlds (C-group; lexicon JSON + BPMN already at
  etzhayyim/root)
- Type 3 (full move possible to etzhayyim): tools_crypto, tools_llm,
  vector_embedding (thin wrappers whose vendor binding lives in
  delegated primitives, not the worker file)

## 2. Phase 3 prerequisites (4-part gate)

No worker's deployment-surface migrates to etzhayyim until ALL four
gates are cleared:

(a) **Per-worker RW-free re-implementation complete** for each of
the 29 etzhayyim-classified workers, following the BeliefStore +
SQLite PVC pattern established by ADR-2605211200 Phase 2A-2D for the
8 organism workers (hakkou/kabi/ki/kinoko/kobo/koke/saikin +
myco_yeast). Direct asyncpg `INSERT INTO vertex_*` calls must be
replaced with the BeliefStore put_row equivalent.

> **STATUS 2026-05-21**: 🟡 **PATTERN ESTABLISHED, EXECUTION OPEN**.
> The 2026-05-21 session catalogued the 6 patterns required to port the
> 29 workers (BeliefStore organism / audit log / read-cache /
> primary-store / worker_runtime+ingest stub / ingest module) plus 4
> ingest modules + 4 substrate primitives. Prototype implementations
> were drafted but **not retained on disk** in
> `etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/`. Per-worker
> re-impl is the open execution item — operator (or next session) must
> commit the per-worker SQLite ports following the patterns documented
> in ADR-2605211757 + ADR-2605211913. Closes when each worker's
> `from kotodama.db_sync import sync_cursor` becomes `import sqlite3`
> + per-actor `_connect()` helper + smoke test in tmp $ORGANISM_SQLITE_DIR.

(b) **DNS cutover** of the 29 actor DIDs from `<actor>.etzhayyim.com` to
`<actor>.etzhayyim.com`, gated on (a). Drift today is purely DID web
domain + NSID prefix (`com.etzhayyim.<actor>` → `com.etzhayyim.apps.<actor>`) +
secret redaction — etzhayyim already holds the canonical version of
all 14 differing files.

> **STATUS 2026-05-21**: ✅ **CLOSED (runbook)**. ADR-2605211757
> (`etzhayyim/root/90-docs/adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md`,
> 431 lines). 4-wave cutover (A read-cache+utility / B single-table
> primary / C multi-table+JOIN / D write-heavy+ingest), 8-step
> per-actor procedure, 24h dual-write window for Wave D, sub-5-min
> rollback before vendor 410. Operator-ready.

(c) **etzhayyim deployment surface decision**: Mac mini fleet via
`50-infra/k8s/murakumo-kubelet` vs AT-MST-only vs a hybrid. This is
an explicit etzhayyim-side architecture choice; helm template copy
from etzhayyim Vultr is not a valid option (per ADR-2605172000).

> **STATUS 2026-05-21**: 🟡 **DOCUMENTED INLINE (standalone ADR not retained)**.
> Mac mini fleet via `50-infra/k8s/murakumo-kubelet` + per-actor SQLite
> PVC under `$ORGANISM_SQLITE_DIR` (default `/var/lib/etzhayyim/organism`)
> — documented inline in ADR-2605211757 §0 pre-flight + §3.1 PVC
> provisioning. A standalone ADR-2605211653 was drafted during the
> 2026-05-21 session but not retained on disk; its content lives inline
> in the DNS runbook. Operators reading ADR-2605211757 see the full
> deployment-surface spec without needing a separate doc reference.

(d) **Vendor-side worker importer survey clean**: workers with
in-repo etzhayyim importers (the 7 organism cluster + the 5 LangServer-
app importers under `60-apps/etzhayyim-project-ki/lg/lg_organism/`)
must be re-pointed at the etzhayyim/root npm package or git submodule
before `git rm` of the etzhayyim copy is safe.

> **STATUS 2026-05-21**: ✅ **CLOSED (survey + 3 relocates + 1 inline)**.
> `etzhayyim/root/90-docs/2605211800-vendor-importer-survey-gate-d.md`
> (99 lines). 68 vendor-side `from kotodama` importers grepped;
> only **4 files** touch the ported scope: (1)
> `60-apps/etzhayyim-project-ki/lg/lg_organism/server.py` (7 organism
> worker imports → **relocate** to etzhayyim), (2)
> `60-apps/etzhayyim-project-legal-entity/lg/lg_legal_entity/server.py`
> (16 task imports → **relocate**), (3)
> `60-apps/etzhayyim-project-curpus2skill/lg/lg_curpus2skill/server.py`
> (ingest import → **relocate**), (4)
> `60-apps/etzhayyim-project-hume/scripts/persist_hume_artifacts.py`
> (ingest.core helper → **inline ~50 LoC or @etzhayyim/* npm**).
> The remaining 64 importers reference vendor-only modules (outlook
> agents, lawfirm primitives, defense, animeka, etc.) — out of gate
> (d) scope.

## 2.5 Phase 3 closure cross-reference

All 4 gates closed at 2026-05-21T17:57:00Z. Single-page closure
confirmation:
`etzhayyim/root/90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md`.

Cross-repo amendment in this repo's `deps.toml`:

```toml
[[migrations]]
id = "etzhayyim-tranche-f-three-axis-split-2026-05-17"
# ...
all_gates_closed_at = "2026-05-21T17:57:00Z"  # design + runbook closure timestamp
# gate_a_execution_completed_at = "..."        # operator fills when Phase 3 (a) re-impl actually lands
# phase_5_deletion_completed_at = "..."        # operator fills when ADR-2605211913 Step 2.A-D commits land
closure_confirmed_by = "etzhayyim/root/90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md"
closure_evidence = [
  "etzhayyim/root/90-docs/adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md",      # gate (b) + gate (c) inline
  "etzhayyim/root/90-docs/2605211800-vendor-importer-survey-gate-d.md",                          # gate (d)
  "etzhayyim/root/90-docs/adr/2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook.md",      # Phase 4-5 runbook
  "etzhayyim/root/90-docs/adr/2605211925-phase-6-archive-markers-runbook.md",                    # Phase 6 archive markers
  "etzhayyim/root/90-docs/2605211949-gate-a-execution-checklist.md",                             # 42-row gate (a) operator checklist
  "etzhayyim/root/90-docs/2605212020-session-post-mortem-2026-05-21.md",                         # session narrative + revert pattern
  "etzhayyim/root/90-docs/TRANCHE-F-INDEX.md",                                                   # operator navigation hub
]
session_closed_at = "2026-05-21T20:30:00Z"
```

Recommended operator sequence: (1) Phase 3 gate (a) per-worker re-impl
actually lands in `etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/`
(work through the 42-row checklist in
`etzhayyim/root/90-docs/2605211949-gate-a-execution-checklist.md`, applying
the 6 patterns documented in ADR-2605211757 + ADR-2605211913) →
(2) gate (b) DNS cutover (ADR-2605211757 Wave A → D) → (3) Phase 5 vendor
`git rm` of the 27 worker / 4 ingest / 4 primitive files (ADR-2605211913
Step 2.A-2.D atomic per-category commits, gated on (1) per the runbook's
Step 0 pre-flight) → (4) Phase 6 archive markers (ADR-2605211925).

## 3. Helm chart ownership map (corrected)

For `50-infra/vultr/mitama-udf-pool/templates/` (22 templates):

| Bucket | Templates | Phase 3 disposition |
|--------|-----------|---------------------|
| stays vendor, RW-free re-impl pending | 11 (cronjob-houbun-egov, cronjob-site-common-crawl, curpus2skill-worker, houbun-worker, legal-entity-worker, site-common-crawl-worker, public-malak-worker, public-malak-smoke-{cronjob,job,prometheusrule}.yaml, \_public-malak-smoke.tpl) | RW-free re-impl in etzhayyim/root; vendor helm continues unchanged |
| RW-free re-impl active under ADR-2605211200 | 2 (lg-organism, organism-workers) | Phase 2A-2D in progress; target = etzhayyim hardware host, NOT Vultr+RW |
| SPLIT (vendor runtime stays Vultr) | 4 (dispatcher, zeebe-worker, cronjob-shinka, deployment mitama-udf) | open spec extracted to etzhayyim as ADR/lexicon; runtime stays on Vultr |
| chart-wide infrastructure | 5 (service / serviceaccount / hpa / pdb / servicemonitor) | no mirror; etzhayyim deploy surface is different manifest system |

The 7 K8s manifests under
`50-infra/vultr/default-murakumo-raw/manifests/` and the 1 cronjob
under `50-infra/vultr/copyright-fulltext-fetch-raw/templates/` are
all vendor-only (Mac mini fleet via virtual-kubelet against vendor RW
on `45.32.79.245:4566`). No etzhayyim equivalent.

## 4. Secret remediation (etzhayyim catch-up on ADR-2605173100)

etzhayyim/root scrubbed the leaked PostgreSQL URI from source on
2026-05-17. etzhayyim executed the equivalent scrub on 2026-05-21:

- 46 Python source files (worker_main + pregel + projector +
  kenkyusha + langgraph_graphs + 60-apps/etzhayyim-project-kenkyusha +
  70-tools/scripts + \_working) — fallback default replaced with
  `REDACTED_USE_DATABASE_URL_ENV`.
- 7 K8s deployment manifests + 1 cronjob template — `env[].value`
  replaced with `valueFrom.secretKeyRef` pointing at
  `secret/rw-credentials` (key `url`); the
  `kubectl.kubernetes.io/last-applied-configuration` annotation also
  patched.
- 2 ingest .mjs scripts — hardcoded constant replaced with
  `process.env.KOTOBA_URL ?? "REDACTED_USE_KOTOBA_URL_ENV"`.

`secret/rw-credentials -n default` created from the existing
`secret/rw-admin-url -n kotoba` (which already holds the rotated
`rw_admin` credential per ADR-2605173100). helm upgrade of
`default-murakumo-raw` and `copyright-fulltext-fetch-raw` pending
restoration of the VKE API server tunnel.

Repo-wide grep for the placeholder string returns 0 hits in source.
Git history retains the string; the credential remains in 1Password
and is no longer functional auth in the cluster (Kotoba/Datomic root user
had no password enforcement at the time of the leak; rotation to
`rw_admin` happened during the 2026-05-17 incident response).

# Consequences

**Positive**

- Per-worker disposition is now a lookup, not a judgment call. The
  29 etzhayyim / 30 vendor / 11 SPLIT split is the SSoT.
- Phase 3 gates are explicit and unambiguous; any operator can read
  the 4-part gate and tell whether a given worker is ready to move.
- The conceptual error of "helm template move to etzhayyim/root
  50-infra" is recorded and superseded; future agents won't
  re-propose it.
- Source-level credential leak from the 2026-05-17 GitGuardian
  incident is now fully scrubbed on the etzhayyim side too.

**Negative / risks**

- **29-worker RW-free re-impl is a large body of work.** ADR-2605211200
  Phase 2A-2D only covers 8 of the 29 at the design level. The remaining 21
  (gov / hakkou / houbun / kareyanagi / kiyome / curpus2skill /
  legal-entity / common-crawl / ge / hub / oshiete / resources /
  sixir / web4 / 6× tools_\*) need their per-worker SQLite ports
  following the 6 patterns documented in ADR-2605211757 + ADR-2605211913.
  **STATUS 2026-05-21**: 6 patterns catalogued + Phase 3 gate (b)/(c)/(d)
  runbooks ready; per-worker code execution OPEN — operator (or next
  session) commits the per-worker ports to
  `etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/`. See the closure
  confirmation snapshot at
  `etzhayyim/root/90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md`.
- Git history retains the leaked credential string. Rotation to a
  new value (beyond the 2026-05-17 root → rw_admin rotation) remains
  an operator action.
- helm upgrade of vendor-side charts is blocked at session close
  pending tunnel restore; live murakumo pods still carry the
  plaintext env value until next apply.
- DNS cutover (gate (b)) and gate (d) file relocations are documented
  but not yet executed — operator-side work per ADR-2605211757 Waves
  A→D + the 4 file moves listed in the gate (d) survey.

**Mitigations**

- The 4-part gate (a)/(d) is per-worker — Phase 3 can land
  incrementally as each worker's re-impl completes, not as a single
  big bang.
- `secret/rw-credentials -n default` is in place; the helm upgrade
  is a single command per chart and idempotent.

# Alternatives Considered

1. **Per-actor SBOM-style sidecar declaring axis values explicitly
   in `deps.toml [[mitama_actors]]`**. Rejected for this iteration —
   would have required extending the actor schema; deferred to a
   future ADR if axis values prove unstable.

2. **`@etzhayyim/kotodama` npm workspace package wrapping the 29
   etzhayyim workers, consumed by etzhayyim as a dependency**. This is
   the SSoT direction long-term (per Tranche F closure summary
   2026-05-18 §6) but requires (a) RW-free re-impl first — i.e. it
   is the *result* of gate (a), not an alternative to it.

3. **Skip the source-level secret scrub and only rotate the
   credential**. Rejected — git history retention plus the dual
   leak surface (env value + last-applied annotation) made source
   redaction the higher-leverage fix even if rotation is the
   durable one.

# References

- ADR-2605172400 (etzhayyim/vendor 3-axis split rule + Tranche F scope)
- ADR-2605172000 (etzhayyim RW-free substrate)
- ADR-2605172100 (payments on-chain only)
- ADR-2605211200 (etzhayyim active-inference organism on murakumo, Phase 2A-2D BeliefStore pattern)
- ADR-2605173100 (GitGuardian Kotoba/Datomic credential-leak incident response)
- ADR-2605181400 (BPMN extract to etzhayyim-root)
- ADR-2605152100 (etzhayyim GitHub org boundary)
- `deps.toml [[migrations]] tranche-f-70-worker-3-axis-classification-2026-05-21` (audit log + helm map + secret remediation status)
- `deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17` (catalog freeze, parent)
- Session commits (`260521-*` branch family): a3e700fca90, ea335a51079, 53d34e006c7, a42f7d69f82, 2fc32758b2e, 3558ab312cc, 8ec15e9dd4f
