# 50-infra/deploy — Religious-corp stack deploy tooling

Scripts in this directory orchestrate the religious-corp Python stack across
the 10-node Murakumo Mac mini fleet and the EVO-X2 inference pod.

Per **ADR-2605191346** (no commercial Kubernetes) + **ADR-2605192415**
(Pregel daemon architecture — launchd on macOS).

---

## Topology

```
Host          IP             Role
──────────────────────────────────────────────────────────────────────────────
naphtali      192.168.1.18   charter-compliance-leader + kuni-umi-survey-leader
simeon        192.168.1.19   ipfs-pinner + stewardship-leader + mst-projector
judah         192.168.1.17   land-trust-leader + LiteLLM gateway :4000
zebulun       192.168.1.11   economic-leader + kuni-umi-planning-leader
levi          192.168.1.16   membership + council orchestration
joseph        192.168.1.15   phenotype-agent shard 0
issachar      192.168.1.12   phenotype-agent shard 1
dan           192.168.1.13   phenotype-agent shard 2
benjamin      WoL-pending    force + ethics leader
asher         WoL-pending    replica + failover
evo-x2        192.168.1.70   GPU inference pod (Ollama :11434, LiteLLM :4000, ComfyUI :8188)
```

Source of truth: `50-infra/murakumo/fleet.toml`

### Component placement

| Component        | Nodes      | launchd type    | Label |
|------------------|------------|-----------------|-------|
| cell-runner      | all 10     | LaunchAgent     | `com.etzhayyim.kotodama-cell-runner` |
| mst-projector    | simeon only| LaunchDaemon    | `com.etzhayyim.mst-projector` |
| LiteLLM gateway  | judah      | LaunchDaemon    | `com.etzhayyim.litellm-gateway` |

---

## Scripts

### `deploy-religious-corp-stack.sh`

Master orchestrator. SSHs into each node in parallel, bootstraps uv + the git
repo, installs components, and smoke-tests services.

**Prerequisites (run from your local machine or a jump host):**

1. `~/.ssh/config` entries for all 10 nodes by tribe name:
   ```
   Host naphtali
       HostName naphtalinomac-mini.local
       User naphtali
       IdentityFile ~/.ssh/id_ed25519_etzhayyim
   ```
2. `ssh-agent` running with the identity key loaded (`ssh-add ~/.ssh/id_ed25519_etzhayyim`).
3. `git` installed locally.
4. Network access to the Murakumo LAN (or via VPN/tailscale).

**Usage examples:**

```bash
# Deploy the full stack to all 10 nodes (parallelism = 3 by default)
./deploy-religious-corp-stack.sh

# Deploy only to a subset
./deploy-religious-corp-stack.sh --nodes dan,levi,issachar

# Dry-run: show SSH commands without executing them
./deploy-religious-corp-stack.sh --dry-run

# Install cell-runner only (skip mst-projector + LiteLLM)
./deploy-religious-corp-stack.sh --component cell-runner

# Re-deploy mst-projector on simeon only
./deploy-religious-corp-stack.sh --nodes simeon --component mst-projector

# Increase SSH parallelism for a faster roll-out
SSH_PARALLELISM=5 ./deploy-religious-corp-stack.sh

# Override remote repo path
REPO_ROOT_REMOTE=/Users/naphtali/etzhayyim-root ./deploy-religious-corp-stack.sh --nodes naphtali

# Override git branch
REPO_BRANCH=feat/kuni-umi-cells ./deploy-religious-corp-stack.sh --dry-run
```

**Environment variables:**

| Variable              | Default                              | Description |
|-----------------------|--------------------------------------|-------------|
| `REPO_ROOT_REMOTE`    | `/opt/etzhayyim/root`                | Repo path on each Mac mini |
| `REPO_GIT_URL`        | `git@github.com:etzhayyim/root.git`  | Repo to clone/pull |
| `REPO_BRANCH`         | `main`                               | Branch to deploy |
| `SSH_PARALLELISM`     | `3`                                  | Max concurrent SSH sessions |
| `DEPLOY_LOG_DIR`      | `/tmp/etzhayyim-deploy-<pid>`        | Per-node log files |

**Phases:**

| Phase | Action | Nodes |
|-------|--------|-------|
| 1 | Bootstrap: install uv + clone/pull repo | all targets |
| 2 | Install cell-runner LaunchAgent | all targets |
| 3 | Install mst-projector LaunchDaemon | simeon only |
| 4 | Install LiteLLM gateway LaunchDaemon | judah (default) |
| 5 | Smoke test: launchctl + HTTP probe | all targets |

**Exit codes:** `0` = all nodes succeeded. `1` = one or more nodes failed.
Per-node logs are written to `$DEPLOY_LOG_DIR/<node>.log`.

---

### `precheck-node.sh`

Runs 15 prerequisite checks on a single node before deploy. Use it to debug
why a node is failing, or as a pre-flight gate in your CI.

**Run remotely (from orchestrator host):**

```bash
ssh naphtali bash -s < precheck-node.sh
```

**Run locally on the node:**

```bash
ETZHAYYIM_NODE_NAME=naphtali ./precheck-node.sh
```

**Checks:**

| # | Check | Severity |
|---|-------|----------|
| 1 | `uv` installed | FAIL if missing |
| 2 | `launchctl` available (macOS) | FAIL if missing |
| 3 | macOS version >= 14 | WARN if < 14 |
| 4 | Disk free >= 5 GB in $HOME | FAIL if < 2 GB, WARN if < 5 GB |
| 5 | sudo available | FAIL/WARN |
| 6 | /opt writable | WARN |
| 7 | /var/log/etzhayyim writable | WARN |
| 8 | `git` installed | FAIL if missing |
| 9 | ssh-agent + keys loaded | WARN if missing |
| 10 | Python 3.10+ | FAIL if < 3.10 |
| 11 | `simeonnomac-mini.local` mDNS reachable | WARN |
| 12 | EVO-X2 (192.168.1.70) ping reachable | WARN |
| 13 | EVO-X2 Ollama :11434 HTTP responds | WARN |
| 14 | macOS Keychain accessible | WARN |
| 15 | `rsync` installed | WARN |

Exit code `0` on PASS-only or WARN-only. Exit code `1` on any FAIL.

---

## Idempotency

Both scripts are idempotent:

- Bootstrap phase does `git pull --ff-only` if the repo already exists.
- `cell-runner/install.sh` unloads the LaunchAgent before re-loading it.
- `mst-projector/install.sh` unloads the LaunchDaemon before re-installing.

Re-running the deploy on already-deployed nodes is safe.

---

## Logs

After a deploy run, per-node logs live in `$DEPLOY_LOG_DIR/`:

```
/tmp/etzhayyim-deploy-<id>/
  naphtali.log
  simeon.log
  judah.log
  ...
```

On each Mac mini, ongoing service logs:

```bash
# cell-runner
tail -f ~/.etzhayyim/log/kotodama-cell-runner.stderr.log

# mst-projector (simeon)
sudo tail -f /var/log/etzhayyim/mst-projector.err.log

# cell healthz probes
curl http://localhost:13001/healthz   # CharterAttestationRequestCell (naphtali)
curl http://localhost:13005/healthz   # LandStewardshipMonitoringCell (simeon)
```

Healthz port map is defined in `50-infra/murakumo/fleet.toml` under `[cells.*]`.

---

## Rollback

To roll back cell-runner on a single node:

```bash
ssh naphtali
cd /opt/etzhayyim/root
git log --oneline -5       # identify target commit
git checkout <prev-commit>
cd 50-infra/cluster/murakumo/cell-runner
./install.sh --node naphtali --repo-path /opt/etzhayyim/root
```

To roll back mst-projector (simeon):

```bash
ssh simeon
sudo launchctl unload /Library/LaunchDaemons/com.etzhayyim.mst-projector.plist
# restore previous install dir from backup, then:
sudo launchctl load /Library/LaunchDaemons/com.etzhayyim.mst-projector.plist
```

---

## Open items

- [ ] benjamin + asher: WoL-pending as of 2026-05-21. Once recovered, run
      `./deploy-religious-corp-stack.sh --nodes benjamin,asher`.
- [ ] `50-infra/cluster/murakumo/litellm/install.sh` not yet authored (Phase 4
      silently skips if missing). LiteLLM on judah currently managed manually.
- [ ] EVO-X2 (Windows): deploy managed separately via Windows Scheduled Tasks
      (OllamaServer + LiteLLMProxy + ComfyUI); not in scope for this script.
- [ ] CI gate: wire `precheck-node.sh` as a GitHub Actions step once
      self-hosted runners are registered on the fleet.
- [ ] Prometheus scrape config for per-cell healthz ports (13001-14000 range)
      referenced in `fleet.toml [monitoring]` but not yet wired.

---

## References

- `50-infra/murakumo/fleet.toml` — node topology + cell placement SSoT
- `50-infra/cluster/murakumo/cell-runner/install.sh` — per-node cell-runner installer
- `50-infra/cluster/murakumo/cell-runner/deploy-fleet.sh` — cell-runner-only fleet deploy
- `50-infra/cluster/murakumo/cell-runner/cells.toml` — per-node cell registry
- `50-infra/mst-projector/py/install.sh` — mst-projector installer (simeon)
- `90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md` — ADR
- `90-docs/adr/2605191346-*.md` — no commercial K8s ADR
