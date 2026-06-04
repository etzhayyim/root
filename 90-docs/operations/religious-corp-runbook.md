---
id: religious-corp-runbook
title: Religious-corp Stack — Operations Runbook
status: active
doc_type: how-to
topic: murakumo-operations
authoritative: true
last_verified: 2026-05-21
related:
V05191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - 50-infra/murakumo/fleet.toml
  - 50-infra/cluster/murakumo/cell-runner/cells.toml
---

# Religious-corp Stack — Operations Runbook

This runbook covers operations on the religious-corp Python stack deployed across the 10 Mac mini Murakumo fleet + EVO-X2 inference pod.

**Constitutional context**: ADR-2605191346 (no commercial K8s), ADR-2605215000 (no commercial GPU rental), CHARTER-RIDER.md §2(i).

## §1 Fleet topology

10 Mac minis (12-tribes naming per ADR-2605182312):

| Node | LAN IP | Role | Cells | Special services |
|---|---|---|---|---|
| naphtali | 192.168.1.18 | charter-compliance + kuni-umi-survey leader | CharterAttestationRequestCell, CharterAttestationFinalizationCell, CharterRehabilitationCell, SiteSurveyCell | — |
| simeon | 192.168.1.19 | ipfs-pinner + stewardship + kuni-umi-commission leader | LandStewardshipMonitoringCell, CommissioningCell, **EvolutionEmissionCell** | **mst-projector** (:8765) + ipfs-pinner |
| judah | 192.168.1.17 | land-trust leader | LandDonationProcessingCell, LandDisputeResolutionCell, StewardSuccessionCell | **LiteLLM gateway** (:4000) |
| zebulun | 192.168.1.11 | economic + kuni-umi-planning leader | EligibilityCell, TreasuryRebalanceCell, PublicFundGrantCell, TitheRoutingCell, DeploymentPlanningCell | — |
| levi | 192.168.1.16 | membership + council + kuni-umi-audit leader | AdherentAttestationCell, CouncilLevelAdvancementCell, CouncilDeliberationCell, AuditWitnessCell, **ShinkaHeartbeatCell**, **KarmaHegemonObservationCell**, **EvolutionValidationCell**, **JouchoAggregationCell** | — |
| joseph | 192.168.1.15 | phenotype shard 0 + kuni-umi-construction leader | PhenotypeAgent (shard 0, tokenId 0..N/3), ConstructionOrchestrationCell | — |
| issachar | 192.168.1.12 | phenotype shard 1 | PhenotypeAgent (shard 1, tokenId N/3..2N/3) | — |
| dan | 192.168.1.13 | phenotype shard 2 + kuni-umi-decommission leader | PhenotypeAgent (shard 2, tokenId 2N/3..N), DecommissionCell | — |
| benjamin | TBD (WoL pending) | force + ethics leader | ForceAuthorizationCell, ForceLogMonitoringCell, EthicsContentClassifierCell | — |
| asher | TBD (WoL pending) | replica + failover | (dynamic — picks up leader role on failover) | — |

> **Note**: benjamin and asher have `status = "pending_wol_2026_05_18"` — WoL recovery required before deploy. `deploy-fleet.sh` excludes them by default.

External: **evo-x2** (Windows LAN-only @ 192.168.1.70) — AMD Ryzen AI Max+ 395 + Radeon 8060S (gfx1151, RDNA 3.5), 32 GiB VRAM UMA, 96 GB RAM, Windows 11 Pro 24H2. Endpoints: Ollama :11434 (llama3.2:3b @ 83 tok/s, llama3.3:70b @ 1.18 tok/s), LiteLLM :4000, ComfyUI :8188.

## §2 Bring-up procedure (10 nodes)

### Step 1 — local precheck

From the operator workstation, verify SSH connectivity to each deployed node:

```bash
for node in naphtali simeon judah zebulun levi joseph issachar dan; do
    echo "=== $node ===" && ssh -o ConnectTimeout=5 "$node@${node}nomac-mini.local" 'uname -n && sw_vers -productVersion'
done
```

Benjamin and asher require WoL first:

```bash
# WoL recovery: obtain MAC addresses from physical labels, then:
wakeonlan <MAC_ADDRESS>
```

All nodes must be reachable and on macOS 14+ before proceeding.

### Step 2 — deploy cell-runner to all nodes

```bash
# Dry-run to verify plan
./50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh --dry-run

# Deploy to 8 default tribes (benjamin + asher excluded until WoL recovery)
./50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh

# Once benjamin + asher are recovered:
./50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh --tribes benjamin,asher
```

`deploy-fleet.sh` SSHes into each node, runs `git pull`, then runs
`50-infra/cluster/murakumo/cell-runner/install.sh --node <tribe>`.
The installer materialises `~/Library/LaunchAgents/com.etzhayyim.magatama-cell-runner.plist`
and loads the LaunchAgent.

### Step 3 — deploy mst-projector (simeon only)

```bash
ssh simeon@simeonnomac-mini.local
# On simeon:
cd ~/etzhayyim-root
sudo ./50-infra/mst-projector/py/install.sh
```

Installs to `/opt/etzhayyim/mst-projector`, data at `/var/lib/etzhayyim/mst-projector`,
logs at `/var/log/etzhayyim/mst-projector.{out,err}.log`.

### Step 4 — deploy LiteLLM gateway (judah only)

```bash
ssh judah@judahnomac-mini.local
# On judah — register Keychain entry first:
KEY="sk-litellm-$(openssl rand -hex 32)"
security add-generic-password -s "etzhayyim.litellm" -a "MASTER_KEY" -w "$KEY" -U

# Then install:
cd ~/etzhayyim-root
./50-infra/cluster/murakumo/litellm/install.sh
```

### Step 5 — verify

```bash
# Each node has cell-runner LaunchAgent active?
for node in naphtali simeon judah zebulun levi joseph issachar dan; do
    echo -n "$node: "
    ssh "$node@${node}nomac-mini.local" 'launchctl list | grep com.etzhayyim.magatama-cell-runner'
done

# mst-projector /healthz on simeon?
curl -s http://simeonnomac-mini.local:8765/healthz | jq

# LiteLLM gateway on judah?
curl -s http://judahnomac-mini.local:4000/v1/models \
    -H "Authorization: Bearer $LITELLM_MASTER_KEY" | jq

# EVO-X2 reachable from fleet?
ssh dan@dannomac-mini.local 'curl -fs http://192.168.1.70:11434/api/tags | jq .models[].name'
```

### Step 6 — soak

Watch logs for 1 hour:

```bash
# levi runs the most cells — watch its runner log
ssh levi@levinomac-mini.local 'tail -F ~/.etzhayyim/log/magatama-cell-runner.stdout.log'
```

If no errors → bring-up complete.

## §3 Common debug commands

### Cell-runner status (any node)

```bash
ssh <node>@<node>nomac-mini.local 'launchctl list com.etzhayyim.magatama-cell-runner'
```

### Cell-runner logs (any node)

```bash
# LaunchAgent writes to ~/.etzhayyim/log/ on each node
ssh <node>@<node>nomac-mini.local 'tail -F ~/.etzhayyim/log/magatama-cell-runner.stdout.log'
ssh <node>@<node>nomac-mini.local 'tail -F ~/.etzhayyim/log/magatama-cell-runner.stderr.log'
```

### Cell healthz endpoints (per node)

Cell-runner exposes individual cell healthz ports in the 13000–14000 range (per `cells.toml`
`[runner] healthz_port_range`). Examples:

```bash
# ShinkaHeartbeatCell on levi (port 13026)
ssh levi@levinomac-mini.local 'curl -s http://127.0.0.1:13026/healthz | jq'

# KarmaHegemonObservationCell on levi (port 13023)
ssh levi@levinomac-mini.local 'curl -s http://127.0.0.1:13023/healthz | jq'

# EvolutionEmissionCell on simeon (port 13025)
ssh simeon@simeonnomac-mini.local 'curl -s http://127.0.0.1:13025/healthz | jq'
```

### mst-projector status (simeon)

```bash
ssh simeon@simeonnomac-mini.local 'launchctl print system/com.etzhayyim.mst-projector' | head -30
ssh simeon@simeonnomac-mini.local 'sudo tail -F /var/log/etzhayyim/mst-projector.out.log'
curl -s http://simeonnomac-mini.local:8765/healthz | jq
```

### LiteLLM gateway status (judah)

```bash
ssh judah@judahnomac-mini.local 'launchctl list com.etzhayyim.litellm'
curl -s http://judahnomac-mini.local:4000/v1/models \
    -H "Authorization: Bearer $LITELLM_MASTER_KEY" | jq
```

### Tailmesh status

```bash
# Binary name depends on Step 8 cutover state:
# Pre-Step-8:  etzhayyim-murakumo
# Post-Step-8: etzhayyim-murakumo
ssh <node>@<node>nomac-mini.local '/usr/local/bin/etzhayyim-murakumo murakumo-mesh status'   # post-Step 8
ssh <node>@<node>nomac-mini.local '/usr/local/bin/etzhayyim-murakumo murakumo-mesh status'        # pre-Step 8
```

### EVO-X2 inference test

```bash
# From any node:
ssh dan@dannomac-mini.local 'curl -fs http://192.168.1.70:11434/api/tags | jq .models[].name'

# LiteLLM endpoint on EVO-X2 (note: separate from judah's LiteLLM gateway)
ssh dan@dannomac-mini.local 'curl -fs http://192.168.1.70:4000/v1/models \
    -H "Authorization: Bearer $EVO_X2_LITELLM_KEY" | jq'
```

### Reload a cell-runner (any node)

```bash
PLIST="$HOME/Library/LaunchAgents/com.etzhayyim.magatama-cell-runner.plist"
ssh <node>@<node>nomac-mini.local "launchctl unload $PLIST && launchctl load $PLIST"
```

## §4 Rollback playbook

### Scenario: cell-runner deploy fails on one or more nodes

```bash
# Identify which nodes failed from deploy-fleet.sh output, then retry subset:
./50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh --tribes <failed-node>

# Or SSH directly and run install manually:
ssh <node>@<node>nomac-mini.local
cd ~/etzhayyim-root && git pull --ff-only
./50-infra/cluster/murakumo/cell-runner/install.sh --node <node>
```

To pin a specific commit on a node:

```bash
ssh <node>@<node>nomac-mini.local
cd ~/etzhayyim-root
git checkout <previous-tag>
./50-infra/cluster/murakumo/cell-runner/install.sh --node <node>
```

### Scenario: cluster runtime rename (Step 8 cutover) breaks a node

The Step 8 atomic rename replaces `etzhayyim-*` binaries and paths with `etzhayyim-*`.
If a post-cutover deploy fails on a node:

```bash
# Stop cell-runner on the failed node
ssh <node>@<node>nomac-mini.local \
    "launchctl unload ~/Library/LaunchAgents/com.etzhayyim.magatama-cell-runner.plist"

# Revert repo to pre-Step-8 commit on that node
ssh <node>@<node>nomac-mini.local 'cd ~/etzhayyim-root && git checkout <pre-step8-tag>'

# Re-deploy with old binary names
ssh <node>@<node>nomac-mini.local \
    'cd ~/etzhayyim-root && ./50-infra/cluster/murakumo/cell-runner/install.sh --node <node>'
```

See `50-infra/cluster/murakumo/STEP8-INTEGRATED-RUNBOOK.md` for full cutover procedure.

### Scenario: mst-projector data corruption (simeon)

```bash
# Stop service
ssh simeon@simeonnomac-mini.local \
    'sudo launchctl unload /Library/LaunchDaemons/com.etzhayyim.mst-projector.plist'

# Backup broken data dir
ssh simeon@simeonnomac-mini.local \
    'sudo cp -a /var/lib/etzhayyim/mst-projector \
       /var/lib/etzhayyim/mst-projector.broken-$(date +%Y%m%d-%H%M)'

# Drop LanceDB tables (service replays from cursor.txt on restart)
ssh simeon@simeonnomac-mini.local \
    'sudo rm -f /var/lib/etzhayyim/mst-projector/*.lance'

# Restart — service replays the MST firehose from cursor.txt to rebuild tables
ssh simeon@simeonnomac-mini.local \
    'sudo launchctl load /Library/LaunchDaemons/com.etzhayyim.mst-projector.plist'
```

Replay progress is visible in the out log:

```bash
ssh simeon@simeonnomac-mini.local 'sudo tail -F /var/log/etzhayyim/mst-projector.out.log'
```

### Scenario: LiteLLM gateway (judah) fails to start

```bash
# Check Keychain entry is present
ssh judah@judahnomac-mini.local \
    'security find-generic-password -s etzhayyim.litellm -a MASTER_KEY -w'

# Re-run installer (idempotent)
ssh judah@judahnomac-mini.local \
    'cd ~/etzhayyim-root && ./50-infra/cluster/murakumo/litellm/install.sh'
```

## §5 Backup / restore procedures

### Daily backup (run on simeon)

```bash
#!/usr/bin/env bash
# Suggested location: /opt/etzhayyim/backup-daily.sh (cron on simeon)
BACKUP_DIR="/var/backups/etzhayyim/$(date +%Y%m%d)"
sudo mkdir -p "$BACKUP_DIR"

# LanceDB snapshot (mst-projector)
sudo tar -czf "$BACKUP_DIR/lancedb.tgz" -C /var/lib/etzhayyim mst-projector

# Cursor checkpoint (replay start-point)
sudo cp /var/lib/etzhayyim/mst-projector/cursor.txt "$BACKUP_DIR/cursor.txt"

# IPFS pinset
ipfs pin ls > "$BACKUP_DIR/ipfs-pins.txt"

# Encrypt + push to off-fleet storage (operator-specific; out of scope for this runbook)
```

### Restore from backup (simeon)

```bash
BACKUP_DATE="20260601"
ssh simeon@simeonnomac-mini.local bash <<EOF
sudo launchctl unload /Library/LaunchDaemons/com.etzhayyim.mst-projector.plist
sudo tar -xzf /var/backups/etzhayyim/${BACKUP_DATE}/lancedb.tgz -C /var/lib/etzhayyim/
sudo launchctl load /Library/LaunchDaemons/com.etzhayyim.mst-projector.plist
EOF
```

### Keychain backup (per operator Mac)

Critical Keychain items:

- `service=etzhayyim, account=DID_PRIVATE_KEY_ED25519` — per-repo DID signing key
- `service=etzhayyim.litellm, account=MASTER_KEY` — LiteLLM gateway master key (judah)
- `service=etzhayyim.l2, account=ANCHOR_KEY` — Base L2 anchor hot key

Export:

```bash
# Run on each operator's Mac:
security export \
    -k login.keychain \
    -t cert,priv,pub,symmetric \
    -P "<passphrase>" \
    -o ~/Documents/etzhayyim-keychain-backup.p12
```

Import (restore):

```bash
security import ~/Documents/etzhayyim-keychain-backup.p12 -P "<passphrase>"
```

## §6 Common failure modes + remediation

| Failure | Symptom | Remediation |
|---|---|---|
| Cell-runner OOM | Cells slowly terminate; stderr: "Killed (out of memory)" | Lower per-node cell density; move one cell to asher; check cell count in cells.toml for that node |
| mst-projector ingest lag | `mst_projector_last_indexed_seq_at` >10 min ago in healthz | Restart: `ssh simeon@simeonnomac-mini.local 'sudo launchctl kickstart -k system/com.etzhayyim.mst-projector'` |
| EVO-X2 unreachable | LLM cells emit warn logs; EthicsContentClassifierCell falls back to own-node Ollama gemma3:4b | Ping 192.168.1.70; restart Windows Scheduled Tasks (OllamaServer, LiteLLMProxy); physical access if persistent |
| LanceDB write failures | mst-projector logs "write failed: out of disk"; query 503 | Free disk on simeon; prune old LanceDB tables via `Indexer.drop_collection()` |
| Tailmesh peer disconnects | One node cannot reach others via `.mesh.etzhayyim.com` (pre-Step 8) or `.mesh.etzhayyim.com` (post-Step 8) | Restart mesh daemon: `pkill -f murakumo-mesh; ~/.etzhayyim/mesh/run-mesh.sh &` (or `~/.etzhayyim/mesh/run-mesh.sh` post-Step 8) |
| IPFS pin failures (simeon) | EvolutionEmissionCell logs "ipfs.pin_many failed" | Check `ipfs daemon` running; verify Kubo HTTP API at :5001 |
| L2 anchor failures | EvolutionEmissionCell logs "anchor RPC error" | Check Base L2 RPC reachable; verify ETZHAYYIM_L2_ANCHOR_KEY balance (gas) |
| Council attestation 0 | Lv6+ advancements blocked | Verify COUNCIL_LV6_DIDS populated (post-RFP-close 2026-06-19); `mst.get_council_lv6_dids()` returns non-empty list |
| naphtali Ollama DOWN | Inference fallback on naphtali only | Per fleet.toml note: naphtali Ollama :11434 was DOWN as of 2026-05-21; use EVO-X2 or own-node fallback |
| benjamin / asher offline | Force/ethics cells unavailable; no failover replica | Perform WoL recovery (status: pending_wol_2026_05_18), then deploy via `deploy-fleet.sh --tribes benjamin,asher` |

## §7 Healthcheck dashboard summary

Quick liveness check across the fleet:

```bash
#!/usr/bin/env bash
# fleet-health.sh — at-a-glance fleet status
# Run from operator workstation. Requires SSH access as tribe user to each node.

NODES=(naphtali simeon judah zebulun levi joseph issachar dan benjamin asher)
EVO_X2="192.168.1.70"

echo "=== Cell-runner (LaunchAgent) ==="
for node in "${NODES[@]}"; do
    status=$(ssh -o ConnectTimeout=3 -o BatchMode=yes \
        "$node@${node}nomac-mini.local" \
        'launchctl list com.etzhayyim.magatama-cell-runner 2>/dev/null | head -1' 2>/dev/null \
        || echo "UNREACHABLE")
    printf "  %-10s %s\n" "$node" "$status"
done

echo ""
echo "=== mst-projector (simeon :8765) ==="
mst_health=$(curl -fsS --max-time 3 http://simeonnomac-mini.local:8765/healthz 2>/dev/null \
    | jq -r '"collections=\(.indexed_collections // "?") seq=\(.last_indexed_seq // "?")"' 2>/dev/null \
    || echo "DOWN")
printf "  %-10s %s\n" "mst-proj" "$mst_health"

echo ""
echo "=== LiteLLM gateway (judah :4000) ==="
litellm_health=$(curl -fsS --max-time 3 http://judahnomac-mini.local:4000/v1/models \
    -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-unset}" 2>/dev/null \
    | jq -r '"models=\(.data | length)"' 2>/dev/null \
    || echo "DOWN")
printf "  %-10s %s\n" "litellm" "$litellm_health"

echo ""
echo "=== EVO-X2 ($EVO_X2) ==="
evo_models=$(curl -fsS --max-time 5 "http://$EVO_X2:11434/api/tags" 2>/dev/null \
    | jq -r '.models | length' 2>/dev/null || echo "DOWN")
comfyui=$(curl -fsS --max-time 3 "http://$EVO_X2:8188/system_stats" 2>/dev/null \
    | jq -r '"cuda=\(.system.cuda_device_name // "?")"' 2>/dev/null || echo "DOWN")
printf "  %-10s ollama_models=%s\n" "evo-x2" "$evo_models"
printf "  %-10s comfyui=%s\n" "evo-x2" "$comfyui"
```

Expected healthy output (example):

```
=== Cell-runner (LaunchAgent) ===
  naphtali   0 = 0 com.etzhayyim.magatama-cell-runner
  simeon     0 = 0 com.etzhayyim.magatama-cell-runner
  ...
=== mst-projector (simeon :8765) ===
  mst-proj   collections=12 seq=1823456
=== LiteLLM gateway (judah :4000) ===
  litellm    models=4
=== EVO-X2 (192.168.1.70) ===
  evo-x2     ollama_models=2
  evo-x2     comfyui=cuda=Radeon RX 8060S
```

## §8 Step 8 cutover procedure summary

See `50-infra/cluster/murakumo/STEP8-INTEGRATED-RUNBOOK.md` for full procedure.

Short version:

1. Legal registration complete (master gate — ADR-2605191346)
2. Council Lv6+ supermajority signed off on atomic PR
3. Branch from main: `git checkout -b step8-religious-corp-cutover-YYYY-MM-DD`
4. Apply 4 commits in order: cluster runtime → pymagatama → shinka → yoro
5. `cargo check` + `pytest` each commit
6. Deploy to `dan` canary, 24h soak
7. Roll out to remaining 9 nodes via `deploy-fleet.sh --tribes <remaining>`
8. Post-cutover cleanup: decommission `etzhayyim-*` binary + `~/.etzhayyim/` dirs

**Binary name change at cutover**: `etzhayyim-murakumo` → `etzhayyim-murakumo`, `~/.etzhayyim/` → `~/.etzhayyim/`, `.mesh.etzhayyim.com` → `.mesh.etzhayyim.com`.

## §9 References

- ADR-2605191346 — Vultr-free + no commercial K8s (`90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md`)
- ADR-2605182312 — 12-tribes naming convention
- ADR-2605192415 — Religious-corp daemon architecture + Pregel cell catalog (`90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md`)
- ADR-2605202100 — launchd-only cell hosting policy
- ADR-2605202345 — EVO-X2 inference pod (`50-infra/murakumo/fleet.toml` `[inference_backends.evo-x2]`)
- ADR-2605211910 — Fleet LAN IPs verified (`50-infra/murakumo/fleet.toml` header)
- ADR-2605215200 — shinka Pregel/MST rewrite (`50-infra/cluster/murakumo/cell-runner/cells.toml`)
- ADR-2605215400 — EVOLUTION_WITNESS_MIN (`cells.toml` EvolutionValidationCell)
- ADR-2605215500 — mst-projector server-side filter (`50-infra/mst-projector/README.md`)
- CHARTER-RIDER.md §2(i) — no commercial GPU rental
- `50-infra/murakumo/fleet.toml` — authoritative 10-node cell placement
- `50-infra/cluster/murakumo/cell-runner/cells.toml` — Pregel cell registry (shinka + joucho cells)
- `50-infra/cluster/murakumo/cell-runner/install.sh` — per-node cell-runner installer
- `50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh` — fleet-wide cell-runner deploy
- `50-infra/mst-projector/py/install.sh` — mst-projector installer
- `50-infra/cluster/murakumo/litellm/install.sh` — LiteLLM gateway installer (judah)
- `50-infra/cluster/murakumo/STEP8-INTEGRATED-RUNBOOK.md` — Step 8 full cutover procedure
- `20-actors/AUDIT-RUNPOD-RW-2026-05-21.md` — RunPod/commercial-GPU audit record
- `20-actors/magatama/py/{SHINKA,YORO-PYTHON,PYMAGATAMA}-MIGRATION-NOTES.md` — migration notes
