---
id: runpod-5090-access-status-260526
title: "RunPod RTX 5090 access status (2026-05-26) — credentials in 1Password vault but key path not on mac-260317"
status: active
doc_type: reference
topic: runpod-5090-access
authoritative: true
last_verified: 2026-05-26
related:
  - adr-2605263000-founder-lv7-emergency-authorization-runpod-5090-bench-interim
  - 90-docs/baien/runpod-5090-runlog-260526.jsonl
---

# RunPod RTX 5090 access status

## Pod metadata

| Field | Value |
|---|---|
| 1Password item | `runpod/oka-lm-train RTX5090` (etzhayyimcojp vault, ID `scclefhmwawwpf6pljf4gf3ibq`) |
| pod_id | `eoc5cmxtr6n3c4` |
| Connect | `ssh -p 51691 root@157.157.221.30` |
| key_path (per 1Password) | `~/.ssh/id_rsa` |
| Auth methods accepted | `publickey,password` |

## Access state from mac-260317 (2026-05-26)

| Attempt | Result |
|---|---|
| ssh -i ~/.ssh/id_ed25519 | publickey denied |
| ssh -i ~/.ssh/id_ed25519_performer | publickey denied |
| ssh -i ~/.ssh/id_ed25519_github_etzhayyim | publickey denied |
| ssh -i ~/.ssh/id_rsa | file does NOT exist on mac-260317 |
| sshpass -p $(op ... password) | password denied (1Password 17-char password not SSH password) |

→ mac-260317 currently cannot reach the pod. Pod responds (`port OPEN`)
but rejects all credentials available to mac.

## Three unblock paths

### Path A — recommended: authorize mac ed25519 key on pod

In the user's existing pod SSH terminal, run:

```sh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOvzaMbhK0JiiSNj5gkaY6Hi7Hz7P587IJaohN6YqQlK' \
  >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

After execution, mac-260317 can SSH directly via `id_ed25519`. No password,
no key copy needed.

### Path B — user drives bringup.sh themselves from pod-control machine

The user's machine that already has `~/.ssh/id_rsa` (the original key) runs:

```sh
# From user's pod-control machine
scp -P 51691 -i ~/.ssh/id_rsa <local-path>/runpod-5090-bench-bringup.sh \
  root@157.157.221.30:/workspace/bringup.sh

ssh -p 51691 -i ~/.ssh/id_rsa root@157.157.221.30 \
  'HF_TOKEN=$(op item get etzhayyim.hf/HF_TOKEN --reveal) bash /workspace/bringup.sh' \
  2>&1 | tee /tmp/runpod-bench.log
```

Then transfer results back to mac-260317:
```sh
scp -P 51691 -i ~/.ssh/id_rsa root@157.157.221.30:/workspace/bench-results-*.tar.gz \
  /Users/junkawasaki/github/etzhayyim-root/90-docs/baien/
```

### Path C — copy id_rsa to mac-260317

```sh
# From user's pod-control machine
scp ~/.ssh/id_rsa jun@mac-260317:~/.ssh/runpod-oka-lm-train

# On mac-260317
chmod 600 ~/.ssh/runpod-oka-lm-train
# Add SSH config entry:
cat >> ~/.ssh/config <<'EOF'

Host runpod-oka-lm-train
  Hostname 157.157.221.30
  Port 51691
  User root
  IdentityFile ~/.ssh/runpod-oka-lm-train
EOF
```

## Pre-flight runlog (still authorization pending, no actual run yet)

`90-docs/baien/runpod-5090-runlog-260526.jsonl` has 1 entry (pre-flight ADR
commit timestamp 2026-05-26T06:50:00Z); no post-flight entry yet (no bench
actually executed on 5090).

## Bench scripts ready

- `/tmp/runpod-5090-bench-bringup.sh` (NOT in repo; pod-only)
  - lm-eval-harness Phase 1 5-shot canonical
  - evalplus HumanEval+ with chat template
  - Result tarball pack + sync instructions

## Founder Lv7+ Emergency Authorization scope reminder

Per ADR-2605263000 §1:
- bench-eval inference ONLY (not train)
- baien-server-moemoekyun ONLY (not other actors)
- Cumulative cost cap $200 USD pre-P4
- Time-bound to P4 ~2026-07-19
- Council post-ratification recording required at 2026-06-19+ vote
