#!/usr/bin/env bash
# deploy-religious-corp-stack.sh — orchestrate the religious-corp Python stack
# across the 10 Mac mini fleet + EVO-X2 inference pod.
#
# Per ADR-2605191346 (no commercial K8s) + ADR-2605215000 (no commercial GPU rental).
#
# Phase 0 prerequisites:
#   - SSH access to all 10 Mac minis (~/.ssh/config entries: naphtali, simeon, ...)
#     Each Host alias must resolve to <tribe>nomac-mini.local or the LAN IP.
#   - uv installed locally + on each Mac mini (auto-installed by bootstrap phase)
#   - git + ssh-agent set up with access to $REPO_GIT_URL
#   - Repo cloned at $REPO_ROOT_REMOTE (default: /opt/etzhayyim/root on each node)
#     On first run this is cloned; subsequent runs git-pull.
#
# Topology (fleet.toml):
#   naphtali  192.168.1.18  charter-compliance-leader + kuni-umi-survey-leader
#   simeon    192.168.1.19  ipfs-pinner + stewardship-leader + mst-projector host
#   judah     192.168.1.17  land-trust-leader + LiteLLM gateway :4000
#   zebulun   192.168.1.11  economic-leader
#   levi      192.168.1.16  membership + council orchestration
#   joseph    192.168.1.15  phenotype-agent shard 0
#   issachar  192.168.1.12  phenotype-agent shard 1
#   dan       192.168.1.13  phenotype-agent shard 2
#   benjamin  WoL-pending   force + ethics leader
#   asher     WoL-pending   replica + failover
#
# Usage:
#   ./deploy-religious-corp-stack.sh                           # deploy all 10 nodes
#   ./deploy-religious-corp-stack.sh --nodes dan,levi          # deploy subset
#   ./deploy-religious-corp-stack.sh --dry-run                 # show what would happen
#   ./deploy-religious-corp-stack.sh --component cell-runner   # cell-runner only (all nodes)
#   ./deploy-religious-corp-stack.sh --component mst-projector # simeon only
#   ./deploy-religious-corp-stack.sh --component litellm       # judah (LiteLLM gateway)
#   ./deploy-religious-corp-stack.sh --nodes simeon --component mst-projector

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
REPO_ROOT_REMOTE="${REPO_ROOT_REMOTE:-/opt/etzhayyim/root}"
REPO_GIT_URL="${REPO_GIT_URL:-git@github.com:etzhayyim/root.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
SSH_PARALLELISM="${SSH_PARALLELISM:-3}"
DEPLOY_LOG_DIR="${DEPLOY_LOG_DIR:-$(mktemp -d /tmp/etzhayyim-deploy-XXXXXX)}"

# ── Fleet topology (must match 50-infra/murakumo/fleet.toml) ─────────────────
declare -a ALL_NODES=(naphtali simeon judah zebulun levi joseph issachar dan benjamin asher)

# Components per node:
#   cell-runner:    all 10 nodes (launchd LaunchAgent per ADR-2605192415 §7.1)
#   mst-projector:  simeon only (ipfs-pinner co-location, ADR-2605215500)
#   litellm:        judah (LiteLLM gateway :4000; override via --litellm-gateway)
declare -a CELL_RUNNER_NODES=("${ALL_NODES[@]}")
declare -a MST_PROJECTOR_NODES=(simeon)
declare -a LITELLM_GATEWAY_NODES=(judah)  # fleet.toml: judah hosts LiteLLM :4000

# ── Parse args ────────────────────────────────────────────────────────────────
DRY_RUN=false
NODES=""
COMPONENTS="all"  # all | cell-runner | mst-projector | litellm

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --nodes)
            NODES="$2"
            shift 2
            ;;
        --component)
            COMPONENTS="$2"
            shift 2
            ;;
        --ssh-parallelism)
            SSH_PARALLELISM="$2"
            shift 2
            ;;
        --litellm-gateway)
            LITELLM_GATEWAY_NODES=("$2")
            shift 2
            ;;
        -h|--help)
            sed -n '/^# Usage:/,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        *)
            printf 'Unknown arg: %s\n' "$1" >&2
            exit 1
            ;;
    esac
done

# Validate --component value
case "$COMPONENTS" in
    all|cell-runner|mst-projector|litellm) ;;
    *)
        printf 'ERROR: --component must be one of: all cell-runner mst-projector litellm\n' >&2
        exit 1
        ;;
esac

# ── Setup ─────────────────────────────────────────────────────────────────────
mkdir -p "$DEPLOY_LOG_DIR"
printf 'deploy log dir: %s\n' "$DEPLOY_LOG_DIR"

# Filter target nodes
if [ -n "$NODES" ]; then
    IFS=',' read -ra TARGET_NODES <<< "$NODES"
else
    TARGET_NODES=("${ALL_NODES[@]}")
fi

# Validate each target node against the 10-node allowlist
_VALID="naphtali simeon judah zebulun levi joseph issachar dan benjamin asher"
for _n in "${TARGET_NODES[@]}"; do
    case " $_VALID " in
        *" $_n "*) ;;
        *)
            printf 'ERROR: "%s" is not a valid Murakumo node.\n' "$_n" >&2
            printf '       valid: %s\n' "$_VALID" >&2
            exit 1
            ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
_log() {
    local node="$1"
    shift
    printf '[%s] %s\n' "$node" "$*" | tee -a "$DEPLOY_LOG_DIR/$node.log"
}

# Wrapper: runs SSH command or prints DRY-RUN trace.
# All remote commands use BatchMode=yes so they never hang on passphrase prompts.
_run_ssh() {
    local node="$1"
    shift
    if [ "$DRY_RUN" = true ]; then
        _log "$node" "DRY-RUN: ssh $node -- $*"
        return 0
    fi
    ssh \
        -o ConnectTimeout=15 \
        -o BatchMode=yes \
        -o StrictHostKeyChecking=accept-new \
        "$node" "$@" 2>&1 | tee -a "$DEPLOY_LOG_DIR/$node.log"
}

# Check whether a node is in a given bash array.
# Usage: _in_array "$node" "${SOME_NODES[@]}"
_in_array() {
    local needle="$1"
    shift
    local elem
    for elem in "$@"; do
        [ "$elem" = "$needle" ] && return 0
    done
    return 1
}

# ── Phase 1: per-node bootstrap (uv + repo) ───────────────────────────────────
# Idempotent: clones on first run, git-pulls on subsequent runs.
bootstrap_node() {
    local node="$1"
    _log "$node" "--- Phase 1: bootstrap (uv + repo) ---"

    # Install uv if missing (uses the official installer; places binary in ~/.local/bin)
    _run_ssh "$node" "
        export PATH=\"\$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH\"
        command -v uv >/dev/null 2>&1 || {
            echo '[bootstrap] installing uv...'
            curl -LsSf https://astral.sh/uv/install.sh | sh
        }
        uv --version
    "

    # Ensure repo root directory exists and is owned by the current user
    _run_ssh "$node" "
        sudo mkdir -p '${REPO_ROOT_REMOTE}'
        sudo chown \"\$(id -u):\$(id -g)\" '${REPO_ROOT_REMOTE}'
    "

    # Clone or pull
    _run_ssh "$node" "
        export PATH=\"\$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH\"
        if [ -d '${REPO_ROOT_REMOTE}/.git' ]; then
            echo '[bootstrap] repo exists — pulling'
            cd '${REPO_ROOT_REMOTE}'
            git fetch --quiet
            git checkout '${REPO_BRANCH}' --quiet
            git pull --ff-only 2>&1 | tail -3
        else
            echo '[bootstrap] cloning repo'
            git clone -b '${REPO_BRANCH}' '${REPO_GIT_URL}' '${REPO_ROOT_REMOTE}'
        fi
    "

    _log "$node" "bootstrap complete"
}

# ── Phase 2: install cell-runner (all nodes) ──────────────────────────────────
# Runs the per-node install.sh which materialises the launchd plist and loads it.
install_cell_runner() {
    local node="$1"
    _log "$node" "--- Phase 2: cell-runner install ---"

    _run_ssh "$node" "
        export PATH=\"\$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH\"
        cd '${REPO_ROOT_REMOTE}/50-infra/cluster/murakumo/cell-runner'
        ETZHAYYIM_NODE_NAME='${node}' bash install.sh --node '${node}' --repo-path '${REPO_ROOT_REMOTE}'
    "

    _log "$node" "cell-runner installed"
}

# ── Phase 3: install mst-projector (simeon only) ──────────────────────────────
# mst-projector is a LaunchDaemon (root-owned) on simeon co-located with ipfs-pinner.
install_mst_projector() {
    local node="$1"

    if ! _in_array "$node" "${MST_PROJECTOR_NODES[@]}"; then
        return 0
    fi

    _log "$node" "--- Phase 3: mst-projector install (simeon co-location) ---"

    _run_ssh "$node" "
        export PATH=\"\$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH\"
        cd '${REPO_ROOT_REMOTE}/50-infra/mst-projector/py'
        sudo UV_PATH=\"\$(command -v uv)\" bash install.sh
    "

    _log "$node" "mst-projector installed"
}

# ── Phase 4: install LiteLLM gateway (judah by default) ──────────────────────
# LiteLLM proxies calls from cells to EVO-X2 Ollama + Claude API.
# The install script lives at 50-infra/cluster/murakumo/litellm/install.sh.
install_litellm_gateway() {
    local node="$1"

    if ! _in_array "$node" "${LITELLM_GATEWAY_NODES[@]}"; then
        return 0
    fi

    local litellm_install="${REPO_ROOT_REMOTE}/50-infra/cluster/murakumo/litellm/install.sh"

    _log "$node" "--- Phase 4: LiteLLM gateway install ---"

    _run_ssh "$node" "
        export PATH=\"\$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH\"
        if [ -f '${litellm_install}' ]; then
            cd '${REPO_ROOT_REMOTE}/50-infra/cluster/murakumo/litellm'
            sudo bash install.sh
        else
            echo '[litellm] install.sh not yet present at ${litellm_install} — skipping'
        fi
    "

    _log "$node" "LiteLLM gateway install done"
}

# ── Phase 5: smoke verification ───────────────────────────────────────────────
smoke_test_node() {
    local node="$1"
    _log "$node" "--- Phase 5: smoke test ---"
    local ok=true

    # cell-runner active? (LaunchAgent label per install.sh)
    if _run_ssh "$node" "launchctl list | grep -q 'com.etzhayyim.kotodama-cell-runner'" 2>/dev/null; then
        _log "$node" "PASS cell-runner: active"
    else
        _log "$node" "FAIL cell-runner: NOT loaded (check ~/.etzhayyim/log/kotodama-cell-runner.stderr.log)"
        ok=false
    fi

    # mst-projector active? (LaunchDaemon label — system domain)
    if _in_array "$node" "${MST_PROJECTOR_NODES[@]}"; then
        if _run_ssh "$node" "sudo launchctl list | grep -q 'com.etzhayyim.mst-projector'" 2>/dev/null; then
            _log "$node" "PASS mst-projector: active"
        else
            _log "$node" "FAIL mst-projector: NOT loaded (check /var/log/etzhayyim/mst-projector.err.log)"
            ok=false
        fi
        # HTTP reachability — warm-start tolerance (warn, don't fail)
        if _run_ssh "$node" "
            curl -fs -X POST http://localhost:8765/xrpc/com.etzhayyim.mstProjector.countByCollection \
              -H 'Content-Type: application/json' \
              -d '{\"collection\":\"app.bsky.feed.post\"}' >/dev/null 2>&1
        " 2>/dev/null; then
            _log "$node" "PASS mst-projector: countByCollection responds"
        else
            _log "$node" "WARN mst-projector: countByCollection unreachable (may be cold-starting)"
        fi
    fi

    # LiteLLM gateway health? (warn-only — EVO-X2 may be warming up)
    if _in_array "$node" "${LITELLM_GATEWAY_NODES[@]}"; then
        if _run_ssh "$node" "curl -fs http://localhost:4000/health >/dev/null 2>&1" 2>/dev/null; then
            _log "$node" "PASS LiteLLM gateway :4000 /health OK"
        else
            _log "$node" "WARN LiteLLM gateway :4000 unreachable (may not be installed yet)"
        fi
    fi

    "$ok" && return 0 || return 1
}

# ── Per-node orchestration ─────────────────────────────────────────────────────
deploy_node() {
    local node="$1"
    local start
    start=$(date +%s)
    _log "$node" "deploy start: $(date)"

    case "$COMPONENTS" in
        all)
            bootstrap_node "$node"        || return 1
            install_cell_runner "$node"   || return 1
            install_mst_projector "$node" || return 1
            install_litellm_gateway "$node" || return 1
            smoke_test_node "$node"       || return 1
            ;;
        cell-runner)
            bootstrap_node "$node"        || return 1
            install_cell_runner "$node"   || return 1
            ;;
        mst-projector)
            install_mst_projector "$node" || return 1
            ;;
        litellm)
            install_litellm_gateway "$node" || return 1
            ;;
    esac

    local end
    end=$(date +%s)
    _log "$node" "deploy complete in $((end - start))s"
    return 0
}

# ── Banner ────────────────────────────────────────────────────────────────────
printf '\n'
printf '================================================================\n'
printf '  Religious-corp stack deploy\n'
printf '  Per ADR-2605191346 (no commercial K8s) + ADR-2605192415\n'
printf '================================================================\n'
printf '  Target nodes  : %s\n' "${TARGET_NODES[*]}"
printf '  Components    : %s\n' "$COMPONENTS"
printf '  Repo          : %s @ %s\n' "$REPO_GIT_URL" "$REPO_BRANCH"
printf '  Remote path   : %s\n' "$REPO_ROOT_REMOTE"
printf '  Parallelism   : %s\n' "$SSH_PARALLELISM"
printf '  Dry run       : %s\n' "$DRY_RUN"
printf '  Log dir       : %s\n' "$DEPLOY_LOG_DIR"
printf '================================================================\n\n'

# ── Parallel orchestration ─────────────────────────────────────────────────────
# Each node runs in a background subshell. A sliding window limits concurrency
# to $SSH_PARALLELISM to avoid overwhelming the LAN switch.

declare -a pids=()
declare -a pid_to_node=()
running=0
declare -a failed_nodes=()

for node in "${TARGET_NODES[@]}"; do
    # Wait until a slot opens in the parallelism window
    while [ "$running" -ge "$SSH_PARALLELISM" ]; do
        new_pids=()
        new_pid_to_node=()
        for i in "${!pids[@]}"; do
            pid="${pids[$i]}"
            nname="${pid_to_node[$i]}"
            if kill -0 "$pid" 2>/dev/null; then
                new_pids+=("$pid")
                new_pid_to_node+=("$nname")
            else
                if ! wait "$pid" 2>/dev/null; then
                    failed_nodes+=("$nname")
                fi
                running=$((running - 1))
            fi
        done
        pids=("${new_pids[@]+"${new_pids[@]}"}")
        pid_to_node=("${new_pid_to_node[@]+"${new_pid_to_node[@]}"}")
        # Only sleep if we're still at capacity
        [ "$running" -ge "$SSH_PARALLELISM" ] && sleep 1
    done

    deploy_node "$node" &
    pids+=("$!")
    pid_to_node+=("$node")
    running=$((running + 1))
done

# Drain remaining background jobs
for i in "${!pids[@]}"; do
    pid="${pids[$i]}"
    nname="${pid_to_node[$i]}"
    if ! wait "$pid" 2>/dev/null; then
        failed_nodes+=("$nname")
    fi
done

# ── Final report ──────────────────────────────────────────────────────────────
printf '\n================================================================\n'
if [ "${#failed_nodes[@]}" -eq 0 ]; then
    printf 'All %d node(s) deployed successfully.\n' "${#TARGET_NODES[@]}"
    printf 'Logs: %s/\n' "$DEPLOY_LOG_DIR"
    exit 0
else
    printf 'FAILED nodes (%d): %s\n' "${#failed_nodes[@]}" "${failed_nodes[*]}"
    printf 'Check per-node logs: %s/<node>.log\n' "$DEPLOY_LOG_DIR"
    exit 1
fi
