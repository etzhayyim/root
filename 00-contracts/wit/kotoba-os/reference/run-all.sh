#!/usr/bin/env bash
# Consolidated coverage runner for the kotoba-os reference (ADR-2606031600).
# Runs every check in one place — WIT validation, the Rust crate suite, and the
# Python suite (which itself builds the real WASM component + runs the wasmtime
# e2e when the toolchain is present). Stages whose tooling is absent are SKIPPED,
# not failed, so this is safe in minimal environments. Exits non-zero iff a
# present-tooling stage fails.
#
# Usage:  bash run-all.sh
set -uo pipefail
cd "$(dirname "$0")"

PASS=0; FAIL=0; SKIP=0
ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[33mSKIP\033[0m  %s\n' "$1"; SKIP=$((SKIP+1)); }

echo "== kotoba-os reference coverage =="

# 1. WIT contract validates.
if command -v wasm-tools >/dev/null 2>&1; then
  if wasm-tools component wit ../kotoba-os.wit >/dev/null 2>&1; then
    ok "WIT: kotoba-os.wit validates (wasm-tools)"
  else bad "WIT: kotoba-os.wit failed validation"; fi
else skip "WIT validation (no wasm-tools)"; fi

# 2. Rust crate suite (native; plain cargo).
if command -v cargo >/dev/null 2>&1; then
  if out=$(cd kotoba-os-types && cargo test --quiet 2>&1); then
    n=$(printf '%s' "$out" | grep -oE '[0-9]+ passed' | head -1 | grep -oE '[0-9]+')
    ok "Rust: kotoba-os-types (${n:-?} tests passed)"
  else printf '%s\n' "$out" | tail -5; bad "Rust: kotoba-os-types tests"; fi
else skip "Rust crate tests (no cargo)"; fi

# 2b. Browser edge (L1c): the substrate crate must compile to wasm32
#     (the baien edge target, ADR-2605241900 / §D6). rustup wasm32 std required;
#     Homebrew rust shadows it, so pin the toolchain bin.
if command -v rustup >/dev/null 2>&1; then
  TC="$(rustup show active-toolchain 2>/dev/null | awk '{print $1}')"
  WBIN="$HOME/.rustup/toolchains/$TC/bin"
  if [ -n "$TC" ] && ls "$HOME/.rustup/toolchains/$TC/lib/rustlib/wasm32-unknown-unknown/lib/libcore-"*.rlib >/dev/null 2>&1; then
    if ( cd kotoba-os-types && env -u RUSTC -u RUSTFLAGS PATH="$WBIN:/usr/bin:/bin" \
         "$WBIN/cargo" build --quiet --target wasm32-unknown-unknown --release >/dev/null 2>&1 ); then
      ok "Wasm32: kotoba-os-types compiles to wasm32 (browser edge / baien target)"
    else bad "Wasm32: kotoba-os-types failed wasm32 build"; fi
  else skip "Wasm32 build (no rustup wasm32-unknown-unknown std)"; fi
else skip "Wasm32 build (no rustup)"; fi

# 3. Python suite (incl. toolchain-guarded component build + wasmtime e2e).
if command -v python3 >/dev/null 2>&1; then
  if out=$(python3 -m unittest 2>&1); then
    n=$(printf '%s' "$out" | grep -oE 'Ran [0-9]+ tests' | grep -oE '[0-9]+')
    ok "Python: reference suite (${n:-?} tests)"
  else printf '%s\n' "$out" | tail -8; bad "Python: reference suite"; fi
else skip "Python suite (no python3)"; fi

echo "== summary: ${PASS} passed, ${FAIL} failed, ${SKIP} skipped =="
[ "$FAIL" -eq 0 ]
