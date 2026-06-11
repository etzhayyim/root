#!/usr/bin/env bash
# precheck-node.sh — verify a Mac mini node is ready for religious-corp deploy.
#
# Run locally on the Mac mini itself (or via `ssh <node> bash < precheck-node.sh`)
# to confirm all prerequisites are satisfied before running
# deploy-religious-corp-stack.sh.
#
# Usage (local):
#   ETZHAYYIM_NODE_NAME=naphtali ./precheck-node.sh
#
# Usage (remote, from orchestrator host):
#   ssh naphtali bash -s < /path/to/precheck-node.sh
#
# Exit codes:
#   0 — all checks pass (or only warnings)
#   1 — one or more checks FAIL; deploy will not succeed

set -euo pipefail

NODE_NAME="${ETZHAYYIM_NODE_NAME:-$(hostname -s)}"
checks_pass=0
checks_fail=0
checks_warn=0

_pass() { printf '  PASS  %s\n' "$1"; checks_pass=$((checks_pass + 1)); }
_fail() { printf '  FAIL  %s\n' "$1"; checks_fail=$((checks_fail + 1)); }
_warn() { printf '  WARN  %s\n' "$1"; checks_warn=$((checks_warn + 1)); }

printf '=== precheck for %s ===\n' "$NODE_NAME"

# ── 1. uv installed? ──────────────────────────────────────────────────────────
_uv_path=""
for _candidate in "$HOME/.local/bin/uv" /opt/homebrew/bin/uv /usr/local/bin/uv; do
    if [ -x "$_candidate" ]; then
        _uv_path="$_candidate"
        break
    fi
done
# Also check PATH
if [ -z "$_uv_path" ] && command -v uv >/dev/null 2>&1; then
    _uv_path="$(command -v uv)"
fi

if [ -n "$_uv_path" ]; then
    _pass "uv: $("$_uv_path" --version 2>&1) at $_uv_path"
else
    _fail "uv not installed (fix: curl -LsSf https://astral.sh/uv/install.sh | sh)"
fi

# ── 2. launchctl available? ───────────────────────────────────────────────────
if command -v launchctl >/dev/null 2>&1; then
    _pass "launchctl: available (macOS $(sw_vers -productVersion 2>/dev/null || echo '?'))"
else
    _fail "launchctl: missing — is this macOS?"
fi

# ── 3. macOS version (14+ required for launchd per install.sh) ───────────────
_macos_major="$(sw_vers -productVersion 2>/dev/null | cut -d. -f1 || echo 0)"
if [ "$_macos_major" -ge 14 ] 2>/dev/null; then
    _pass "macOS version: $( sw_vers -productVersion 2>/dev/null ) (>= 14)"
else
    _warn "macOS version: $( sw_vers -productVersion 2>/dev/null ) — recommend 14+ (Sonoma)"
fi

# ── 4. Disk space: >5 GB free in $HOME ───────────────────────────────────────
_free_gb=$(df -g "$HOME" 2>/dev/null | tail -1 | awk '{print $4}' || echo 0)
if [ "$_free_gb" -gt 5 ] 2>/dev/null; then
    _pass "disk free: ${_free_gb} GB available in $HOME"
elif [ "$_free_gb" -gt 2 ] 2>/dev/null; then
    _warn "disk free: ${_free_gb} GB — recommended >= 5 GB"
else
    _fail "disk free: ${_free_gb} GB — insufficient (need at least 2 GB)"
fi

# ── 5. sudo available without interactive passphrase ────────────────────────
if sudo -n true 2>/dev/null; then
    _pass "sudo: passwordless sudo available"
elif sudo -v 2>/dev/null; then
    _warn "sudo: requires password entry — deploy will prompt interactively"
else
    _fail "sudo: not available (required for mst-projector LaunchDaemon + /opt dir)"
fi

# ── 6. /opt writable or creatable via sudo ───────────────────────────────────
if [ -w /opt ]; then
    _pass "/opt: writable directly"
elif sudo -n test -d /opt 2>/dev/null; then
    _pass "/opt: exists, sudo available to write"
else
    _warn "/opt: may need sudo mkdir /opt/etzhayyim/root"
fi

# ── 7. /var/log/etzhayyim writable (for cell + mst-projector logs) ────────────
if sudo -n test -d /var/log/etzhayyim 2>/dev/null && sudo -n test -w /var/log/etzhayyim 2>/dev/null; then
    _pass "/var/log/etzhayyim: exists and writable"
elif sudo -n test -w /var/log 2>/dev/null; then
    _pass "/var/log: writable via sudo (deploy will create /var/log/etzhayyim)"
else
    _warn "/var/log: sudo needed for log directory creation"
fi

# ── 8. git installed ─────────────────────────────────────────────────────────
if command -v git >/dev/null 2>&1; then
    _pass "git: $(git --version)"
else
    _fail "git: not installed (install via Xcode CLI tools: xcode-select --install)"
fi

# ── 9. ssh-agent running with keys loaded ─────────────────────────────────────
if ssh-add -l >/dev/null 2>&1; then
    _key_count=$(ssh-add -l 2>/dev/null | grep -c 'SHA256' || echo 0)
    _pass "ssh-agent: running with ${_key_count} key(s) loaded"
elif [ -n "${SSH_AUTH_SOCK:-}" ]; then
    _warn "ssh-agent: socket exists but no keys loaded — git clone may fail"
else
    _warn "ssh-agent: not running — git clone over SSH will prompt for key passphrase"
fi

# ── 10. Python 3.10+ (for tomllib used in cell-runner) ───────────────────────
if command -v python3 >/dev/null 2>&1; then
    _py_ver=$(python3 --version 2>&1 | awk '{print $2}')
    _py_major=$(printf '%s' "$_py_ver" | cut -d. -f1)
    _py_minor=$(printf '%s' "$_py_ver" | cut -d. -f2)
    if [ "$_py_major" -ge 3 ] && [ "$_py_minor" -ge 10 ] 2>/dev/null; then
        _pass "python3: $_py_ver (>= 3.10)"
    else
        _fail "python3: $_py_ver — need >= 3.10 (tomllib built-in; install via uv python install 3.12)"
    fi
else
    _fail "python3: not found (uv can manage this: uv python install 3.12)"
fi

# ── 11. Murakumo mDNS mesh: simeon reachable? ────────────────────────────────
if ping -c 1 -W 2 simeonnomac-mini.local >/dev/null 2>&1; then
    _pass "mDNS: simeonnomac-mini.local reachable (LAN mesh up)"
else
    _warn "mDNS: simeonnomac-mini.local unreachable (mesh may be down, or this IS simeon)"
fi

# ── 12. EVO-X2 inference pod reachable? (192.168.1.70) ───────────────────────
if ping -c 1 -W 2 192.168.1.70 >/dev/null 2>&1; then
    _pass "EVO-X2 (192.168.1.70): reachable"
else
    _warn "EVO-X2 (192.168.1.70): unreachable — LiteLLM dispatch + LLM fallback will fail"
fi

# ── 13. EVO-X2 Ollama endpoint responds? ─────────────────────────────────────
if curl -fs --max-time 3 http://192.168.1.70:11434/v1/models >/dev/null 2>&1; then
    _pass "EVO-X2 Ollama :11434: responds"
else
    _warn "EVO-X2 Ollama :11434: not responding (may be booting; cells use own-node fallback)"
fi

# ── 14. macOS Keychain accessible? (for secrets: DID key + LiteLLM master key) ─
if security list-keychains >/dev/null 2>&1; then
    _pass "macOS Keychain: accessible"
else
    _warn "macOS Keychain: not accessible (DID private key + EVO_X2_LITELLM_KEY may fail)"
fi

# ── 15. rsync installed? (mst-projector install.sh uses rsync) ───────────────
if command -v rsync >/dev/null 2>&1; then
    _pass "rsync: $(rsync --version 2>&1 | head -1)"
else
    _warn "rsync: not found — mst-projector install.sh requires rsync (brew install rsync)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
printf '\n'
printf '=======================================\n'
printf '  PASS=%-4s WARN=%-4s FAIL=%s\n' "$checks_pass" "$checks_warn" "$checks_fail"
printf '\n'

if [ "$checks_fail" -gt 0 ]; then
    printf 'CANNOT deploy until FAIL checks are resolved.\n'
    exit 1
elif [ "$checks_warn" -gt 0 ]; then
    printf 'Deploy possible but degraded — review WARNings above.\n'
    exit 0
else
    printf 'Node ready for deploy.\n'
    exit 0
fi
