#!/usr/bin/env bash
# install-langservers.sh — Per-host LSP binary installer.
#
# Consumes 50-infra/etzhayyim-langserver/langservers.toml and installs the
# pinned versions on the host this script runs on. Verifies post-install
# version matches the pin (no silent upgrades).
#
# Usage:
#   ./install-langservers.sh                # dry-run; print what would happen
#   ./install-langservers.sh --check         # verify-only: report pin-vs-installed
#   ./install-langservers.sh --apply         # actually install (requires explicit flag)
#   ./install-langservers.sh --apply rust    # install only `rust` langserver
#
# Per CLAUDE.md: this script is the only sanctioned path to install LSP
# binaries on the fleet. It does NOT load any launchd plist (that is
# install-plists.sh, to land in L6).

set -euo pipefail

cd "$(dirname "$0")/.."

MANIFEST="langservers.toml"
if [ ! -f "$MANIFEST" ]; then
  echo "FATAL: $MANIFEST not found (run from 50-infra/etzhayyim-langserver/scripts/)" >&2
  exit 1
fi

MODE="dry-run"
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --apply) MODE="apply" ;;
    --check) MODE="check" ;;
    --dry-run) MODE="dry-run" ;;
    --help|-h)
      sed -n '2,17p' "$0"
      exit 0
      ;;
    *) TARGETS+=("$arg") ;;
  esac
done

# Parse the TOML manifest with the most portable tool available.
# Order: yq (homebrew, supports toml), python3+tomllib (always on macOS 14+).
if command -v yq >/dev/null 2>&1; then
  PARSER="yq"
elif command -v python3 >/dev/null 2>&1; then
  PARSER="python3"
else
  echo "FATAL: neither yq nor python3 available for TOML parsing" >&2
  exit 2
fi

emit_langservers_json() {
  if [ "$PARSER" = "yq" ]; then
    yq -p=toml -o=json '.langserver' "$MANIFEST"
  else
    python3 - <<'PY'
import json, sys, tomllib, pathlib
data = tomllib.loads(pathlib.Path("langservers.toml").read_text())
print(json.dumps(data.get("langserver", []), indent=2))
PY
  fi
}

emit_prereqs_json() {
  if [ "$PARSER" = "yq" ]; then
    yq -p=toml -o=json '.prereq' "$MANIFEST"
  else
    python3 - <<'PY'
import json, tomllib, pathlib
data = tomllib.loads(pathlib.Path("langservers.toml").read_text())
print(json.dumps(data.get("prereq", []), indent=2))
PY
  fi
}

run_or_dry() {
  local desc="$1"; shift
  case "$MODE" in
    apply)
      echo "[apply] $desc"
      "$@"
      ;;
    dry-run)
      echo "[dry-run] would run: $*"
      ;;
    check)
      :  # check mode never executes mutations
      ;;
  esac
}

# ── prereqs ──
echo "═══ prereqs (transport tooling for L4) ═══"
emit_prereqs_json | python3 -c '
import json, sys
SEP = "\x1f"  # ASCII Unit Separator — not in default IFS whitespace, safe with empty fields
for p in json.load(sys.stdin):
    fields = ["PREREQ", p["name"], p["version"], p["install"], p["bin"], p["check_cmd"]]
    print(SEP.join(fields))
' | while IFS=$'\x1f' read -r tag name version install bin check_cmd; do
  echo "── $name @ $version"
  if [ -x "$bin" ]; then
    actual=$(eval "$check_cmd" 2>&1 | head -1 || echo "?")
    echo "   installed: $actual"
  else
    echo "   NOT installed (expected at $bin)"
    run_or_dry "install $name" bash -c "$install"
  fi
done

# ── langservers ──
echo ""
echo "═══ language servers ═══"

emit_langservers_json | python3 -c '
import json, sys
SEP = "\x1f"
items = json.load(sys.stdin)
for ls in items:
    fields = [
        ls.get("lang",""),
        ls.get("name",""),
        ls.get("version",""),
        ls.get("install",""),
        ls.get("bin",""),
        ls.get("args",""),
        str(ls.get("heuristic_ram_mb", 0)),
        ls.get("preferred_host_role",""),
    ]
    print(SEP.join(fields))
' | while IFS=$'\x1f' read -r lang name version install bin args ram role; do
  # Filter by target if specified
  if [ ${#TARGETS[@]} -gt 0 ]; then
    skip=true
    for t in "${TARGETS[@]}"; do [ "$t" = "$lang" ] && skip=false; done
    [ "$skip" = true ] && continue
  fi

  echo "── $lang : $name @ $version  (≈${ram} MB RAM, role=$role)"

  # Resolve $HOME / ~ in bin path
  bin_resolved="${bin/#\~/$HOME}"

  if [ -x "$bin_resolved" ]; then
    actual=$("$bin_resolved" --version 2>&1 | head -1 || echo "(no --version)")
    echo "   installed:  $actual"
    if [[ "$actual" == *"$version"* ]]; then
      echo "   ✓ pin match"
    else
      echo "   ✗ pin MISMATCH (want $version, got $actual)"
      if [ "$MODE" = "apply" ]; then
        echo "     refusing silent upgrade — bump langservers.toml in a separate PR"
      fi
    fi
  else
    echo "   ✗ NOT installed (expected at $bin_resolved)"
    run_or_dry "install $name" bash -c "$install"
  fi
done

echo ""
echo "═══ summary ═══"
case "$MODE" in
  dry-run) echo "MODE=dry-run · re-run with --apply to perform installs" ;;
  check)   echo "MODE=check · pin verification only, no changes" ;;
  apply)   echo "MODE=apply · installs attempted (review above for failures)" ;;
esac
