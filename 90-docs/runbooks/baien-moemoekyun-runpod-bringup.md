---
id: runbook-baien-moemoekyun-runpod-bringup
title: "Operator runbook — first RunPod B200 train session for baien-moemoekyun R2"
status: active
doc_type: how-to
topic: baien-moemoekyun-runpod-bringup
authoritative: true
last_verified: 2026-05-26
related:
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
  - 70-tools/baien-moemoekyun-train/scripts/rental-orchestrator.py
  - 70-tools/baien-moemoekyun-train/configs/r2-iter01.yaml
---

# Runbook — baien-moemoekyun R2 first RunPod B200 train session

## Constitutional precondition

This runbook is **executable only after ADR-2605262200 amendment is effective**:

- P0 (2026-05-26): proposed ✅
- P1 (→2026-06-19): Bootstrap Council Seats 2-5 RFP — see [COUNCIL-BOOTSTRAP-RFP.md](../../COUNCIL-BOOTSTRAP-RFP.md)
- P2 (2026-06-19+): Council Lv6+ vote ≥4/7 seats
- P3 (P2+30 days): public objection period
- **P4 (earliest 2026-07-19): amendment effective ← executing this runbook before P4 is constitutional violation**

Until P4: use [`baien-moemoekyun-r1-bringup.md`](baien-moemoekyun-r1-bringup.md) (R1.4 on EVO-X2 single, charter unaffected).

## Pre-flight checklist (T-1 day)

- [ ] ADR-2605262200 status confirmed `accepted` (Council ratification + 30-day objection passed)
- [ ] CHARTER-RIDER.md §2(i)(2) text rewritten per amendment ADR (verify by `grep "§2(i)(2)" CHARTER-RIDER.md`)
- [ ] RunPod account active with payment method, ≥$50 prepaid balance
- [ ] RunPod B200 SXM availability checked (community or secure pool). Fallback = H100 SXM (always available).
- [ ] `e7m-dataset` CLI working on mac-260317 + Kubo daemon running on 127.0.0.1:5001 (`e7m-dataset where`)
- [ ] Train corpus IPFS CIDs all present in `90-docs/baien/datasets.jsonl` and verified via `e7m-dataset verify`
- [ ] Eval corpus CIDs (langgraph-coding + HumanEval+) registered (R2.0 deliverable)
- [ ] `~/.etzhayyim/runpod-api-key` exists with vendor API token (chmod 600)
- [ ] Mac mini fleet split-role bench cells running (per ADR-2605262100 §3.4):
  - naphtali (.18) `moemoekyun-bench-langgraph` launchd cell active
  - simeon (.19) `moemoekyun-bench-humanevalplus` launchd cell active
  - asher (.21) `moemoekyun-ledger` launchd cell active

## Step 1: dry-run rehearsal (T-1h, mac-260317)

```sh
cd /Users/junkawasaki/github/etzhayyim-root
export ETZ_DATASET_ROOT=/Volumes/260317/etzhayyim
export IPFS_PATH=/Volumes/260317/etzhayyim/ipfs-data

# Verify Kubo daemon
curl -sX POST http://127.0.0.1:5001/api/v0/version

# Dry-run orchestrator — emits dry-run AT URIs, validates config + pre-flight checks
python 70-tools/baien-moemoekyun-train/scripts/rental-orchestrator.py \
    --config 70-tools/baien-moemoekyun-train/configs/r2-iter01.yaml \
    --dry-run

# Expected output: pre-flight PASS, dry-run rentalAttestation + rentalCostLog (with commitDecision=aborted-engineering-failure
# since vendor stub raises NotImplementedError), printed cost log JSON
```

If dry-run errors out at pre-flight (e.g., budget cap exceeded, Charter Rider scan failure, tier validation), **fix config before live run**.

## Step 2: live execution (T+0, mac-260317)

```sh
# Live mode — requires R2.1 vendor SDK integration (RunPod adapter)
python 70-tools/baien-moemoekyun-train/scripts/rental-orchestrator.py \
    --config 70-tools/baien-moemoekyun-train/configs/r2-iter01.yaml \
    --live
```

Internally the orchestrator (per ADR-2605262300 §7):

1. **Phase 0** pre-flight: budget cap validation + tier validation + Charter Rider scan over dataset CIDs
2. **Phase 1** publish `com.etzhayyim.train.rentalAttestation` to PDS (record AT URI captured)
3. **Phase 2** RunPod API: provision B200 SXM instance, returns instance IP + SSH key
4. upload `70-tools/baien-moemoekyun-train/` + `configs/r2-iter01.yaml` to instance `/workspace/`
5. SSH-execute `python /workspace/baien-moemoekyun-train/src/baien_moemoekyun/train.py --config /workspace/config.yaml`
6. poll until exit (max 1.5x expected_wall_minutes = ~37 min for R2 iter-01)
7. rsync fetch `/workspace/output/` → `/Volumes/260317/etzhayyim/checkpoints/baien-server-moemoekyun-r2-iter01/`
8. `e7m-dataset add local:///Volumes/260317/etzhayyim/checkpoints/... --name baien-server-moemoekyun-r2-iter01 --kind model-checkpoint --license apache-2.0-plus-charter-rider`
9. `e7m-dataset verify baien-server-moemoekyun-r2-iter01` → bytes round-trip CID
10. **Phase 4** fleet eval: NDJSON emit to Mac mini bench cells (naphtali + simeon), poll asher ledger cell for aggregated results
11. **Phase 5** commit_gate: Δ_langgraph ≥ +3pp AND Δ_humaneval+ ≥ 0 → commit; else abort
12. **Phase 6** publish `com.etzhayyim.train.rentalCostLog` (actual wall + actual cost + commit decision)
13. **Phase 7** RunPod API: terminate instance (final billing collected)

## Step 3: post-run verification (T+30 min)

```sh
# Verify both records emitted to PDS
# (R2.1 deliverable: e7m-pds list-records --collection com.etzhayyim.train.rentalAttestation)

# Verify checkpoint pinned + retrievable
ipfs cat <outputCheckpointCid> | head -c 100  # raw bytes preview

# Verify registry entry (if commitDecision=committed-to-registry)
cat 90-docs/baien/moemoekyun-models.jsonl | tail -1 | jq

# Confirm fleet inference can serve the new variant
curl -X POST http://192.168.1.17:4000/v1/chat/completions \
    -H "Authorization: Bearer $LITELLM_KEY" \
    -d '{"model": "baien-server-moemoekyun-r2-iter01", "messages": [{"role": "user", "content": "test"}]}'
```

## Step 4: cost log monthly aggregate update (T+24h)

Per CHARTER-RIDER §2(i)(2)(3), cost log MUST be emitted within 24h. Verify:

- `com.etzhayyim.train.rentalCostLog` record present in PDS for the rental attestation
- Monthly aggregate counter updated (per ADR-2605262300 §6 caps: ≤100h aggregate / ≤$1000)
- If aggregate approaches caps, surface warning to Council Lv4+ via asher cell

## Failure recovery

| Failure | Phase | Recovery |
|---|---|---|
| Charter Rider scan FAIL | Phase 0 | Inspect scan report CID; if dataset has §2(a)-(h) hit, REJECT dataset, swap with clean alternative |
| RunPod instance provisioning timeout | Phase 2 | Retry once; if persistent, switch `gpu_model` to `nvidia-h100-sxm` in config (B200 unavailable) |
| Train script exit != 0 | Phase 2 step 6 | SSH into instance before termination, inspect logs at `/workspace/output/train.log`. Common: OOM (reduce batch_size or move from 8 GPU to 1 GPU), ROCm/CUDA mismatch (verify image), dataset mount failure (HF cache miss) |
| `e7m-dataset add` FAIL | Phase 3 | Check Kubo daemon + disk space on `/Volumes/260317/` + `ETZ_DATASET_ROOT` env. Retry add. |
| `e7m-dataset verify` FAIL (round-trip mismatch) | Phase 3 | Bytes corruption on rented instance → vendor disk issue. Re-fetch + retry add. |
| Fleet eval timeout | Phase 4 | Bench cell crash (check `journalctl` on each Mac mini via Ansible jacob). Re-trigger eval on healthy nodes. |
| `commitDecision != committed-to-registry` | Phase 5 | Inspect deltas. If `aborted-regression`: ADR-2605262100 G10 honest scoring — DO NOT publish. Escalate to R3 hyperparameter sweep. If `aborted-delta-insufficient`: same. |
| Vendor termination FAIL | Phase 7 | Manually terminate via RunPod web UI. Verify billing closed. |

## Budget cap enforcement

Hard-kill conditions (orchestrator self-terminates rental):

- Wall time exceeds `expected_wall_minutes × 1.5` (50% headroom)
- Real-time billing exceeds `expected_usd_cost × 1.3` (30% headroom)
- Continuous rental runtime exceeds 24h (per §2(i)(2)(5))

Monthly aggregate caps (warning only, manual review):

- Wall ≥ 90h (90% of 100h cap)
- Cost ≥ $900 (90% of $1000 cap)

Beyond cap: Council Lv6+ ≥4/7 per-incident approval required to continue.

## Operator handoff

After successful R2 iter-01:

1. Push commit with new `com.etzhayyim.train.rentalAttestation/rentalCostLog` AT URIs referenced in `90-docs/baien/moemoekyun-r2-iter01-summary.md`
2. Update `90-docs/baien/moemoekyun-models.jsonl` entry (auto by orchestrator)
3. Surface decision to ledger cell (asher) for Council Lv4+ visibility
4. Plan R2 iter-02 hyperparameter sweep OR escalate to R3 (Phase 1 partial unfreeze) ADR
