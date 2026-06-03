---
id: adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
title: "ADR-2605211757: DNS cutover runbook for the 27 ported workers — *.etzhayyim.com → *.etzhayyim.com (Phase 3 gate (b))"
status: proposed
doc_type: adr
topic: dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: operations
weight: 0.80
priority_note: "Closes ADR-2605212100 Phase 3 gate (b) at the **runbook** level. Specifies the operator runbook + verify protocol for cutting actor DIDs from vendor (etzhayyim.com) to etzhayyim (etzhayyim.com). Gate (c) deployment surface choice (Mac mini fleet + per-actor SQLite PVC) is embedded inline (§0 + §3.1). Gate (a) per-worker RW-free re-impl is **pattern-established but execution OPEN** — Wave A-D cutover assumes per-worker ports land before each wave's target actors are switched."
authoritative_for:
  - DNS cutover ordering for the 27 ported workers
  - per-worker verify protocol (curl /.well-known/did.json + worker smoke ping + SQLite state seed)
  - rollback procedure (CNAME revert + worker restart pointed back at vendor)
  - coordination with PDS publish callback (AT MST sync wiring)
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605211200-etzhayyim-active-inference-organism-on-murakumo
  # adr-2605211653 (per-actor SQLite PVC deployment surface) was drafted but not retained on disk; its content lives inline in §0 + §3.1 of this runbook
  - adr-2605212100-magatama-worker-3-axis-tranche-f-closure
related:
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
supersedes: []
superseded_by: []
---

# ADR-2605211757: DNS cutover runbook — *.etzhayyim.com → *.etzhayyim.com for the 27 ported workers

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

ADR-2605212100 §Decision 2 specified a 4-part gate for Phase 3 deployment-surface
migration. As of 2026-05-21:

| Gate | State |
|------|-------|
| (a) per-worker RW-free re-impl for 29 etzhayyim-classified workers | 🟡 **pattern established, execution OPEN** — 6 patterns catalogued (BeliefStore / audit log / read-cache / primary store / worker_runtime / ingest module) with prototypes that were not retained in `etzhayyim/root/20-actors/magatama/py/src/pymagatama/`. Per-actor wave below is gated on landing the per-worker ports before each wave's target switches |
| (b) DNS cutover ``*.etzhayyim.com`` → ``*.etzhayyim.com`` | 🟢 **this ADR** |
| (c) etzhayyim deployment surface | 🟡 documented inline in §0 + §3.1 (Mac mini fleet via ``50-infra/k8s/murakumo-kubelet`` + per-actor SQLite PVC under ``$ORGANISM_SQLITE_DIR``); a standalone ADR was drafted but not retained on disk |
| (d) vendor-side worker importer survey clean | 🟢 unblocked — separate work item |

The DNS cutover changes which hostname the operator deploys each worker under.
Worker source code already targets ``did:web:{actor}.etzhayyim.com`` (the port
process locked the actor DID into module constants — e.g. ``narou_worker_main.py``
has ``ACTOR_DID = "did:web:narou.etzhayyim.com"``). What remains is operational:

- ``{actor}.etzhayyim.com`` DNS A/AAAA records must resolve to the Mac mini fleet
  ingress (or the per-app CF Worker if the actor has one).
- ``{actor}.etzhayyim.com/.well-known/did.json`` must serve the actor's DID
  document signed by the etzhayyim key registry (per `etzhayyim-did-web` worker
  in ``50-infra/etzhayyim-did-web/``).
- Per-actor SQLite PVCs must be provisioned and (where applicable) seeded with
  initial state imported from the vendor RW snapshot.
- The vendor-side ``{actor}.etzhayyim.com`` route must serve a 410 Gone (preferred) or
  301 to the new URL during the public-objection / soak window, after which it
  is removed.

Without this ADR, every cutover re-litigates the order of operations and the
verify protocol; an operator pulled into a partial cutover does not know
whether to advance or revert.

# Decision

Adopt the 5-phase cutover runbook below. Each phase has explicit gating
criteria and a single-line operator command. The runbook is **per-actor** —
operators MAY run multiple actors in parallel as long as the actors are
independent (no shared SQLite PVC, no cross-actor ingest dependency).

## 0. Pre-flight (one-time per fleet)

1. **Mac mini fleet ingress healthy**:
   ```bash
   kubectl -n murakumo-runtime get pods -l role=ingress
   kubectl -n murakumo-runtime top pods
   ```
2. **Per-actor PVC template applied**:
   ```bash
   # 50-infra/k8s/murakumo-kubelet/templates/organism-pvc.yaml
   kubectl -n etzhayyim-organism apply -f organism-pvc.yaml
   ```
3. **did:web base resolver live**:
   ```bash
   curl -sI https://etzhayyim.com/.well-known/did.json | head -1
   # expect: HTTP/2 200
   ```
   (this is the canonical did:web resolver for the org, deployed 2026-05-17
   per ADR-2605172600.)

## 1. Worker classification snapshot

Worker → actor DID mapping (the 27 etzhayyim-classified workers targeted by gate (a); fully-ported state is the **wave precondition**, not the current disk state):

| Worker file | Primary actor DID | Pattern |
|-------------|-------------------|---------|
| ``hakkou_worker_main.py`` | ``did:web:hakkou.etzhayyim.com`` | BeliefStore |
| ``kabi_worker_main.py`` | ``did:web:kabi.etzhayyim.com`` | BeliefStore |
| ``ki_worker_main.py`` | ``did:web:ki.etzhayyim.com`` | BeliefStore |
| ``kinoko_worker_main.py`` | ``did:web:kinoko.etzhayyim.com`` | BeliefStore |
| ``kobo_worker_main.py`` | ``did:web:kobo.etzhayyim.com`` | BeliefStore |
| ``koke_worker_main.py`` | ``did:web:koke.etzhayyim.com`` | BeliefStore |
| ``saikin_worker_main.py`` | ``did:web:saikin.etzhayyim.com`` | BeliefStore |
| ``myco_yeast_worker_main.py`` | ``did:web:myco-yeast.etzhayyim.com`` | BeliefStore |
| ``tools_audit_worker_main.py`` | (per-repo, no fixed actor) | Audit log |
| ``sixir_worker_main.py`` | ``did:web:6ir.etzhayyim.com`` | Read-cache |
| ``hub_worker_main.py`` | ``did:web:hub.etzhayyim.com`` | Primary store |
| ``web4_worker_main.py`` | ``did:web:web4.etzhayyim.com`` | Primary store |
| ``oshiete_worker_main.py`` | ``did:web:oshiete.etzhayyim.com`` | Primary store |
| ``resources_worker_main.py`` | ``did:web:resources.etzhayyim.com`` | Primary store |
| ``omikuji_worker_main.py`` | ``did:web:omikuji.etzhayyim.com`` | Primary store |
| ``kareyanagi_worker_main.py`` | ``did:web:kareyanagi.etzhayyim.com`` | Primary store |
| ``kiyome_worker_main.py`` | ``did:web:kiyome.etzhayyim.com`` | Primary store |
| ``gov_worker_main.py`` | ``did:web:gov.etzhayyim.com`` | Primary store (4 table) |
| ``narou_worker_main.py`` | ``did:web:narou.etzhayyim.com`` | Primary store (write-heavy) |
| ``ge_worker_main.py`` | ``did:web:ge.etzhayyim.com`` | Primary store (legal-entity) |
| ``blockchain_worker_main.py`` | ``did:web:blockchain.etzhayyim.com`` | worker_runtime + ingest |
| ``houbun_worker_main.py`` | ``did:web:houbun.etzhayyim.com`` | worker_runtime + ingest |
| ``curpus2skill_worker_main.py`` | ``did:web:curpus2skill.etzhayyim.com`` | worker_runtime + ingest |
| ``site_common_crawl_worker_main.py`` | ``did:web:site.etzhayyim.com`` | worker_runtime + ingest |
| 5 truly-clean utility | (no DNS — internal MCP only) | tools_const/http/json/time/transform |

(2 of the 29 — ``blockchain``/``site`` parents — share their domain with
sibling deploys; the per-actor SQLite path key still uses the actor short name.)

## 2. Wave order

The cutover proceeds in 4 waves matched to the worker-port-pattern risk profile:

### Wave A — read-cache + utility (lowest risk, 6 actors)

``6ir``, ``tools-audit`` (per-repo), 5 utility (no DNS).

Read-cache and utility workers have no externally-visible state and no
cross-actor write dependency. Safe to cut over first; failure mode is "404 /
empty result" rather than "data loss".

### Wave B — primary store, single-table (4 actors)

``hub``, ``web4``, ``ge``, ``oshiete``.

Workers with 1-2 SQLite tables that the worker itself populates. The
``$ORGANISM_SQLITE_DIR/{module}-{actor}.db`` starts empty and accretes; no
seed import needed. Lower verify surface than Wave C.

### Wave C — primary store, multi-table + JOIN (5 actors)

``resources``, ``omikuji``, ``kareyanagi``, ``kiyome``, ``gov``.

Workers with 2-4 tables and at least one JOIN query (``ge`` metrics,
``kiyome`` compliance, ``gov`` getAgency+officials). Verify must exercise
the JOIN path post-cutover to catch missing FK / index regressions.

### Wave D — write-heavy + ingest (12 actors)

``hakkou``, ``kabi``, ``ki``, ``kinoko``, ``kobo``, ``koke``, ``saikin``,
``myco-yeast`` (BeliefStore organism cluster), ``narou`` (LLM-driven novel
write), ``blockchain``, ``houbun``, ``curpus2skill``, ``site`` (ingest).

Highest risk: BeliefStore organism cluster is the active-inference loop —
disruption to belief state can stall the agent's mood / cadence. Narou
holds LLM-generated content that's expensive to regenerate. Ingest modules
pull data via outbound HTTP — cutover failure can wedge a long-running
import.

For Wave D, the runbook adds a **dual-write window** of 24h (etzhayyim
deploy writes the new SQLite; vendor RW is also still written via the
legacy worker) before cutting the vendor-side worker. Detail below.

## 3. Per-actor cutover steps

For each actor ``{a}`` in the wave order above, the operator runs:

### Step 3.1 — Provision PVC

```bash
helm -n etzhayyim-organism upgrade --install ${a} \
  50-infra/k8s/murakumo-kubelet/charts/organism \
  --set actor=${a} \
  --set replicas=0           # not running yet
```

This creates ``pvc/${a}-organism-data`` mounted at ``/var/lib/etzhayyim/organism``.

### Step 3.2 — Initial data import (Wave C + D only)

Skip for Wave A/B (workers start with empty state).

For Wave D BeliefStore actors and write-heavy workers, copy the latest RW
snapshot for the actor's tables into the PVC:

```bash
# operator-side script (separate, not in repo)
etzhayyim-tools/export-actor-state.py --actor ${a} \
  --tables vertex_${module}_* \
  --out /tmp/${a}-init.sql

kubectl -n etzhayyim-organism cp /tmp/${a}-init.sql \
  ${a}-organism-0:/var/lib/etzhayyim/organism/init.sql

kubectl -n etzhayyim-organism exec ${a}-organism-0 -- \
  sqlite3 /var/lib/etzhayyim/organism/${module}-did-web-${a}.etzhayyim.com.db \
  < init.sql
```

After import, the SQLite file contains the same rows the vendor RW had
(modulo any rows written during the export-to-import window — acceptable
for Wave C, mitigated by dual-write for Wave D).

### Step 3.3 — Scale worker to 1 replica

```bash
helm -n etzhayyim-organism upgrade --install ${a} \
  50-infra/k8s/murakumo-kubelet/charts/organism \
  --set actor=${a} \
  --set replicas=1
```

Verify pod healthy:

```bash
kubectl -n etzhayyim-organism rollout status deployment/${a}-organism
kubectl -n etzhayyim-organism logs -l app=${a}-organism --tail=50 | grep -i "starting\|registered"
# expect: "${a}_worker starting" + "registered tasks ..."
```

### Step 3.4 — DNS records

Update the etzhayyim.com zone (Cloudflare Registrar):

```
${a}.etzhayyim.com  A     <mac-mini-fleet-ingress-ip>
${a}.etzhayyim.com  AAAA  <mac-mini-fleet-ingress-ip6>
${a}.etzhayyim.com  TXT   v=etzhayyim-actor-1; pattern=<pattern>
```

The TXT record matches the worker classification in §1 (one of:
``belief-store``, ``audit-log``, ``read-cache``, ``primary-store``,
``worker-runtime``, ``ingest``) — used by ``50-infra/cdn`` for routing
hints + by the integration test harness.

Wait for propagation:

```bash
until dig +short ${a}.etzhayyim.com | grep -q .; do sleep 5; done
```

### Step 3.5 — did:web publish

Deploy the actor's DID document via ``50-infra/etzhayyim-did-web``:

```bash
cd 50-infra/etzhayyim-did-web
DID_ACTOR=${a} pnpm exec wrangler deploy
curl -s https://${a}.etzhayyim.com/.well-known/did.json | jq .id
# expect: "did:web:${a}.etzhayyim.com"
```

### Step 3.6 — Smoke verify

Per-pattern verify command (operator copies from the appropriate row):

| Pattern | Verify command |
|---------|----------------|
| BeliefStore | ``e7m worker invoke ${a} task_health_probe --json '{}'`` → ``status: healthy`` |
| Audit log | (per-repo, no DNS — covered by tools_audit integration test) |
| Read-cache | ``e7m worker invoke ${a} task_list_companies --json '{"limit":1}'`` → 200 OK, `companies` array |
| Primary store | ``e7m worker invoke ${a} task_list_{primary} --json '{"limit":1}'`` → 200 OK, paginated shape |
| worker_runtime + ingest | ``e7m worker invoke ${a} rw.health.probe --json '{}'`` → ``status: healthy``, then ``task_${ingest}_create_run --json '{...dry_run...}'`` → ``ok: true`` |

Smoke MUST exercise both a read and a write call (where applicable) to
confirm the SQLite path is wired correctly.

### Step 3.7 — Vendor-side 410 Gone (or 301)

After 24h soak (Wave D) / 1h soak (Wave A-C) of green smoke + no error
in worker logs, edit ``50-infra/cloudflare/workers/routing-gateway/src/worker.ts``
on the etzhayyim side (separate repo) to return 410 or 301 for ``${a}.etzhayyim.com``:

- **410 Gone** (preferred): clients update their address.
- **301 Moved Permanently** to ``https://${a}.etzhayyim.com$path$query``:
  legacy clients keep working. Use when there are unaudited downstream
  callers.

Deploy:

```bash
cd 50-infra/cloudflare/workers/routing-gateway
pnpm exec wrangler deploy
curl -I https://${a}.etzhayyim.com/
# expect 410 or 301
```

### Step 3.8 — Tranche F migration entry advance

Update ``deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17``
to record the cutover:

```toml
# under cutover_log = [...]
{ actor = "${a}", cutover_at = "2026-MM-DDTHH:MM:SSZ", wave = "B", verify = "green" },
```

## 4. Rollback

A rollback IS possible up to step 3.7 (vendor 410). After 410, rollback
becomes a forward-only fix.

### Before 3.7 — fast rollback (< 5 min)

1. Set ``${a}.etzhayyim.com`` DNS records back to vendor ingress.
2. Scale etzhayyim ``${a}`` worker to 0:
   ```bash
   helm -n etzhayyim-organism upgrade --install ${a} ... --set replicas=0
   ```
3. Scale vendor ``${a}`` worker back to its previous replica count (operator
   maintains the vendor manifest in the etzhayyim repo).
4. Document in ``deps.toml [[migrations]]`` why the rollback was triggered.

### After 3.7 — forward fix

Vendor-side 410 has already told external callers the route is gone. Reverting
that confuses clients (re-resurrection of a "permanently gone" URL). Instead:

1. Fix forward at etzhayyim ``${a}`` worker. The vendor 410 stays in place.
2. If etzhayyim cannot recover quickly, escalate to operator + post-mortem
   ADR (separate document, not this runbook).

## 5. Dual-write window (Wave D only)

For Wave D actors that have ongoing write traffic (BeliefStore organism
cluster, narou, ingest modules), the cutover adds a 24h dual-write window
between Step 3.3 and Step 3.7:

- etzhayyim ``${a}`` worker writes to its per-actor SQLite (the new path).
- Vendor ``${a}`` worker continues to write to RW (the old path).
- A bridge consumer reads etzhayyim SQLite WAL and replays the same writes
  into vendor RW, OR vice-versa.

The bridge is a one-shot operator process (not committed to this repo) that
the operator runs from ``50-infra/k8s/murakumo-kubelet/jobs/dual-write-bridge/``.
The bridge is parameterized on actor name and tables; it terminates when
Step 3.7 lands.

For Wave A-C (no ongoing-write actors): no dual-write window. Cutover is
atomic from the worker's perspective; clients see at most one minute of
"empty list" while DNS propagates.

# Consequences

**Positive**

- Operators have a single-document checklist; no per-actor judgment calls.
- The 4-wave grouping isolates risk by pattern: a Wave A failure does not
  block Wave B planning.
- Rollback is bounded (< 5 min) until Step 3.7, giving operators latitude
  to abort early waves on inconclusive smoke.
- Tranche F migration entry becomes the canonical cutover log — a single
  ``grep cutover_log deps.toml`` shows the field state.

**Negative / risks**

- Wave D dual-write requires a separate bridge process that does not exist
  in this repo. Operator must script + maintain it; without the bridge,
  the 24h window is "single-write at etzhayyim, vendor RW silently stale"
  which is unsafe for BeliefStore (mood drift).
- 4 ingest modules (blockchain / houbun / curpus2skill / site) currently
  start with empty SQLite. For ``houbun`` specifically (statute corpus,
  100s of MB), a full re-ingest from e-Gov / eCFR takes hours — operator
  should run an offline import before Step 3.3 instead of waiting on live
  ingest to repopulate.
- The DID document at ``{a}.etzhayyim.com/.well-known/did.json`` must
  match the actor's signing key in 1Password vault entry
  ``etzhayyim/did-web/key-0``. A mismatch breaks AT MST signature verify
  by external relays — silent failure mode, only visible via downstream
  Firehose subscriber complaints.

**Mitigations**

- For Wave D: schedule the cutover during a low-traffic window (BeliefStore
  is heartbeat-driven; pausing the agent for 5-10 min is acceptable). The
  dual-write bridge then handles the heartbeat backlog after cutover.
- For ``houbun``: explicit "import before deploy" sequence in Step 3.2
  (the eCFR / e-Gov full-title XML can be fetched offline and replayed
  into SQLite in ~30 min per title).
- DID key audit: ``etzhayyim-did-web`` deploy script (``50-infra/etzhayyim-did-web/scripts/verify.sh``)
  cross-checks the published document against the Keychain entry before
  promoting it. Operator runs this once per wave.

# Alternatives Considered

1. **Single big-bang cutover** (all 27 actors at once).
   Rejected: cross-actor failure correlation hides root cause. Wave-based
   cutover localizes failures to one pattern class at a time.

2. **Reverse order — Wave D first** (highest risk first, smallest blast
   radius if something goes wrong at the end).
   Rejected: Wave D depends on the bridge process that operators have not
   yet built. Starting with Wave A buys time to design + test the bridge
   while making concrete progress.

3. **No vendor 410** (keep vendor.etzhayyim.com alive indefinitely as fallback).
   Rejected: violates ADR-2605152100 §"Step 8 vendor open-scope cleanup"
   ("vendor open scope cleanup [...] after business app dependency
   切替"). Leaving the vendor route up forever defeats the org-split
   purpose.

4. **Skip DNS, route by HTTP host header** (single ingress sees both
   ``*.etzhayyim.com`` and ``*.etzhayyim.com``).
   Rejected: requires the etzhayyim ingress to claim ownership of the
   ``etzhayyim.com`` zone, which is owned by etzhayyim Japan株式会社 (vendor). The
   org-split is precisely about not crossing this boundary.

# References

- ADR-2605172000 (etzhayyim RW-free substrate)
- ADR-2605211200 (active-inference organism on murakumo — BeliefStore origin)
- (gate (c) deployment surface documented inline §0 + §3.1; standalone ADR-2605211653 was drafted but not retained)
- ADR-2605212100 (Tranche F closure — defines the 4-part gate this ADR
  closes (b) of)
- ADR-2605172400 (3-axis split rule)
- ADR-2605152100 (etzhayyim GitHub org boundary — vendor 410 / 301 policy)
- ``50-infra/etzhayyim-did-web/`` (did:web publisher worker)
- ``50-infra/k8s/murakumo-kubelet/`` (Mac mini fleet, PVC carrier)
- ``50-infra/cloudflare/workers/routing-gateway/`` (vendor 410/301 host)
- ``deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17``
  (cutover log target)
