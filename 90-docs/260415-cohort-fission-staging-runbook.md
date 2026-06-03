---
id: cohort-fission-staging-runbook-260415
title: "Cohort Fission Staging Runbook (ADR-0026 Phase A→C end-to-end)"
status: active
doc_type: how-to
topic: cohort-staging
authoritative: false
last_verified: 2026-04-15
related:
  - adr-0026-agent-only-reverse-identity-topology
  - cohort-coverage-evaluation-baseline-260414
supersedes: []
superseded_by: []
---

# Goal

ADR-0026 cohort lifecycle (Phase A→B→C) を staging 環境で end-to-end 動作確認する。

# Prerequisites

- Migrations 0052/0053/0054/0056 が staging RisingWave に apply 済
- PDS deploy 済 (handlers/etzhayyim/cohort.ts + agent/cohort-watchdog.ts)
- `etzhayyim authn signin` で session token 取得済
- staging PDS URL: 通常 `https://atproto.etzhayyim.com` (本番と分離する場合は `--pds` flag)

# Procedure

## 0. Baseline snapshot

```bash
etzhayyim cohort dashboard
# ┌─ ADR-0026 Cohort Fleet Dashboard ─────────────────────
# │  total           : 0  (cohort=0, fissioned=0)   ← clean staging
etzhayyim cohort snapshot --out-dir data/staging-cohort-baseline/
```

## 1. Phase A — seed 1 cohort

```bash
AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.cohort.seed --ttl 600)
etzhayyim_TOKEN=$AT_TOKEN etzhayyim cohort gen \
  --pcfL1 3-market-sell --role salesRep --locale jp --k 50

# Output: gen ok: did=did:plc:pending-X1Y2Z3W4 handle=cohort-X1Y2Z3W4.etzhayyim.com
```

verify:

```bash
etzhayyim cohort list --pcfL1 3-market-sell
# 1 row 表示
```

## 2. Phase B — emit 50 evidence

`50 件 emit` で k_anonymity floor を確保しつつ、最後の 1 件で fission gate を満たす。

```bash
COHORT="did:plc:pending-X1Y2Z3W4"

# 49 件 ambient evidence (low posterior, no judge)
AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.cohort.emitEvidence --ttl 600)
for i in $(seq 1 49); do
  etzhayyim_TOKEN=$AT_TOKEN etzhayyim cohort emit \
    --cohort "$COHORT" \
    --signal-kind "behavior.observation" \
    --payload "obs-$i" \
    --posterior 0.4 --judge=false
done

# 1 件 fission-ready evidence
etzhayyim_TOKEN=$AT_TOKEN etzhayyim cohort emit \
  --cohort "$COHORT" \
  --signal-kind "identity.confirm" \
  --payload "judge-confirmed" \
  --posterior 0.97 --judge=true
```

verify mv 反映 (RisingWave streaming, ~1s lag):

```bash
etzhayyim cohort evidence --cohort "$COHORT" --min-posterior 0.95 --judge true
# → 1 row (the fission-ready one)
```

## 3. Phase C — fission

```bash
AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.cohort.fission --ttl 60)
etzhayyim_TOKEN=$AT_TOKEN etzhayyim cohort fission \
  --cohort "$COHORT" \
  --posterior 0.97 --judge=true \
  --evidence "at://cohort-X1Y2Z3W4.etzhayyim.com/com.etzhayyim.cohort.evidence/<rkey>"

# Expected response:
# {
#   "individualDid": "did:plc:pending-AABBCCDD",
#   "individualHandle": "agent-AABBCCDD.etzhayyim.com",
#   "derivedFrom": "did:plc:pending-X1Y2Z3W4",
#   "lineageArchiveUri": "at://agent-AABBCCDD.etzhayyim.com/com.etzhayyim.cohort.fissionLineage/self",
#   "fissionAt": "2026-04-15T..."
# }
```

verify graph 状態:

```bash
etzhayyim cohort lineage --did did:plc:pending-AABBCCDD
# lineage (2 hop):
#   ├─ did:plc:pending-AABBCCDD  agent-...  kind=fissioned
#   └─ did:plc:pending-X1Y2Z3W4  cohort-...  kind=cohort

etzhayyim cohort lineage-stats --pcfL1 3-market-sell
# direct_children=1 で表示

etzhayyim cohort forest --pcfL1 3-market-sell
# tree 表示 (root → fissioned)
```

## 4. Audit / Drift check

```bash
# Should be 0 drift after a clean E2E run
curl -H "Authorization: Bearer $etzhayyim_TOKEN" \
  "https://atproto.etzhayyim.com/xrpc/com.etzhayyim.pds.getOcel?index=com.etzhayyim.cohort.lineageDrift" \
  | jq '.data[].doubles[0]'   # edgeMissing count
```

## 5. Cleanup (staging only)

```bash
# manual TRUNCATE — only acceptable on staging; production uses cascade purge
psql $STAGING_HYPERDRIVE_URL <<SQL
DELETE FROM edge_cohort_derived WHERE src_vid = '$COHORT';
DELETE FROM edge_cohort_evidence_about WHERE dst_vid = '$COHORT';
DELETE FROM edge_cohort_routes_to WHERE src_vid = '$COHORT';
DELETE FROM vertex_cohort_actor WHERE cohort_did = '$COHORT' OR derived_from = '$COHORT';
DELETE FROM vertex_repo_record WHERE cohort_did = '$COHORT';
SQL
```

# Success Criteria

| Check | Expected |
|---|---|
| `cohort dashboard` baseline | 0 cohort |
| Phase A | 1 cohort row, 1 routes_to edge |
| Phase B | 50 vertex_repo_record + 50 edge_cohort_evidence_about |
| Phase C | +1 fissioned actor + 1 derived edge + 1 lineageArchive record |
| MV freshness | mv_cohort_identity_posterior fission_ready_count = 1 within 5s |
| OCEL events | cohort.genesis + 50× evidence.accrued + 1× fissionReady + 1× cohort.fission |
| lineageDrift | 0 (no drift after clean run) |

# Failure Modes & Triage

| Symptom | Diagnosis |
|---|---|
| `posterior must be >= 0.95` error on fission | check `--posterior` value; gate enforced server-side |
| `cohort fission_enabled=false` error | watchdog disabled it — check `mv_cohort_k_drift` for k_proxy < 50 |
| MV not updating | check RisingWave compute pod logs, possibly OOM |
| edge_cohort_derived missing | `etzhayyim cohort repair-edge --did <fissioned> --dry-run=false` |

# References

- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
- `90-docs/260415-cohort-evidence-oncommit-spec.md`
- `90-docs/260415-cohort-lineage-dual-source-consistency.md`
- `70-tools/etzhayyim/CLAUDE.md` §etzhayyim cohort
