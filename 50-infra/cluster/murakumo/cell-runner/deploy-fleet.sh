#!/usr/bin/env bash
# deploy-fleet.sh — fleet-wide installer for kotodama-cell-runner.
#
# Per ADR-2605202100 + ADR-2605202200. Iterates the 12-tribe list (default:
# all currently-deployed tribes per 50-infra/murakumo/fleet.toml status),
# SSHs into each Mac mini, pulls the repo, runs install.sh --node <tribe>,
# and verifies the LaunchAgent registered a PID.
#
# Usage:
#   ./deploy-fleet.sh                                 # all deployed tribes
#   ./deploy-fleet.sh --tribes naphtali,zebulun       # subset
#   ./deploy-fleet.sh --tribes naphtali --dry-run     # print plan, don't ssh
#   ./deploy-fleet.sh --repo-path /opt/etzhayyim/root # override remote path
#
# Idempotent: re-running re-pulls + reloads the LaunchAgent.
#
# Prereqs (per tribe):
#   - SSH access as the tribe user (e.g., naphtali@naphtalinomac-mini.local)
#   - The repo checked out at $REPO_PATH (default ~/etzhayyim-root)
#   - homebrew + uv installed (this script installs uv if missing)
#   - LaunchAgent allowed (System Settings → General → Login Items, on first run)

set -euo pipefail

# 8 currently-deployed tribes per fleet.toml cell_fleet config + deps.toml
# [platform.cell_fleet] cells_live. benjamin + asher are WoL-pending per
# fleet.toml status="pending_wol_2026_05_18".
DEFAULT_TRIBES="naphtali,simeon,judah,zebulun,levi,joseph,issachar,dan"

TRIBES_INPUT=""
REPO_PATH="~/etzhayyim-root"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tribes)
      TRIBES_INPUT="$2"
      shift 2
      ;;
    --repo-path)
      REPO_PATH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      sed -n '2,22p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $1" >&2
      exit 2
      ;;
  esac
done

TRIBES="${TRIBES_INPUT:-$DEFAULT_TRIBES}"
IFS=',' read -r -a TRIBE_LIST <<< "$TRIBES"

# Validate each tribe against the 12-tribe allowlist
VALID_TRIBES="naphtali simeon judah zebulun levi joseph issachar dan benjamin asher"
for tribe in "${TRIBE_LIST[@]}"; do
  case " $VALID_TRIBES " in
    *" $tribe "*) ;;
    *)
      echo "ERROR: '$tribe' is not a valid Murakumo tribe" >&2
      echo "       valid: $VALID_TRIBES" >&2
      exit 2
      ;;
  esac
done

# ---------------------------------------------------------------------------

step()  { printf "\033[34m==>\033[0m %s\n" "$*"; }
ok()    { printf "\033[32m✓\033[0m  %s\n" "$*"; }
warn()  { printf "\033[33m!\033[0m  %s\n" "$*"; }
fail()  { printf "\033[31m✗\033[0m  %s\n" "$*"; }

step "fleet roll-out plan"
echo "  tribes (${#TRIBE_LIST[@]}):  ${TRIBE_LIST[*]}"
echo "  repo path:                  $REPO_PATH"
echo "  dry-run:                    $DRY_RUN"
echo ""

if $DRY_RUN; then
  for tribe in "${TRIBE_LIST[@]}"; do
    echo "[dry-run] would: ssh ${tribe}@${tribe}nomac-mini.local"
    echo "[dry-run]   cd $REPO_PATH && git pull"
    echo "[dry-run]   ./50-infra/cluster/murakumo/cell-runner/install.sh --node $tribe"
    echo "[dry-run]   launchctl list | grep kotodama-cell-runner"
  done
  exit 0
fi

# ---------------------------------------------------------------------------
# Per-tribe remote-install sequence (idempotent).

# shellcheck disable=SC2087
REMOTE_INSTALL_SCRIPT=$(cat <<'REMOTE'
set -e

TRIBE=$1
REPO_PATH_RAW=$2
# Expand ~ in REPO_PATH on the remote (HOME-dependent)
REPO_PATH="${REPO_PATH_RAW/#\~/$HOME}"

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

echo "[$TRIBE] repo at: $REPO_PATH"

# Install uv if missing
if ! command -v uv >/dev/null 2>&1; then
  echo "[$TRIBE] installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ ! -d "$REPO_PATH" ]; then
  echo "[$TRIBE] ERROR: repo not found at $REPO_PATH" >&2
  echo "[$TRIBE]        bootstrap: git clone https://github.com/etzhayyim/root.git $REPO_PATH" >&2
  exit 3
fi

cd "$REPO_PATH"
echo "[$TRIBE] git pull"
git pull --ff-only 2>&1 | tail -3 || true

INSTALL="$REPO_PATH/50-infra/cluster/murakumo/cell-runner/install.sh"
if [ ! -x "$INSTALL" ]; then
  echo "[$TRIBE] ERROR: install.sh missing or not executable at $INSTALL" >&2
  exit 3
fi

echo "[$TRIBE] running install.sh --node $TRIBE"
"$INSTALL" --node "$TRIBE" --repo-path "$REPO_PATH"

echo "[$TRIBE] post-install verify"
launchctl list | grep kotodama-cell-runner || echo "[$TRIBE] WARN: service not in launchctl list"
REMOTE
)

FAILED_TRIBES=()
SUCCESS_TRIBES=()

for tribe in "${TRIBE_LIST[@]}"; do
  HOST="${tribe}nomac-mini.local"
  step "deploying $tribe ($HOST)"

  if ssh -o StrictHostKeyChecking=accept-new \
         -o ConnectTimeout=10 \
         "$tribe@$HOST" \
         bash -s -- "$tribe" "$REPO_PATH" <<< "$REMOTE_INSTALL_SCRIPT"; then
    ok "$tribe deployed"
    SUCCESS_TRIBES+=("$tribe")
  else
    fail "$tribe FAILED"
    FAILED_TRIBES+=("$tribe")
  fi
  echo ""
done

# ---------------------------------------------------------------------------
# Summary

step "fleet roll-out summary"
echo "  ✓ success (${#SUCCESS_TRIBES[@]}/${#TRIBE_LIST[@]}):  ${SUCCESS_TRIBES[*]:-(none)}"
if [ "${#FAILED_TRIBES[@]}" -gt 0 ]; then
  echo "  ✗ failed (${#FAILED_TRIBES[@]}/${#TRIBE_LIST[@]}):   ${FAILED_TRIBES[*]}"
  echo ""
  warn "Some tribes failed. To inspect a tribe manually:"
  echo "    ssh ${FAILED_TRIBES[0]}@${FAILED_TRIBES[0]}nomac-mini.local"
  echo "    tail -f ~/.etzhayyim/log/kotodama-cell-runner.stderr.log"
  exit 1
fi

echo ""
ok "All ${#SUCCESS_TRIBES[@]} tribes deployed successfully."
echo ""
echo "Aggregate status check:"
for tribe in "${SUCCESS_TRIBES[@]}"; do
  HOST="${tribe}nomac-mini.local"
  echo "  ssh $tribe@$HOST 'launchctl list | grep kotodama-cell-runner'"
done
