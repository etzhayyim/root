#!/usr/bin/env bash
# Build the kotoba-os boot image and boot it on QEMU's `virt` machine.
# Pins the rustup toolchain bin (Homebrew rust shadows rustup's aarch64 std).
set -euo pipefail
cd "$(dirname "$0")"
TC="$(rustup show active-toolchain | awk '{print $1}')"
BIN="$HOME/.rustup/toolchains/$TC/bin"
( env -u RUSTC -u RUSTFLAGS PATH="$BIN:/usr/bin:/bin" "$BIN/cargo" build --release )
IMG="target/aarch64-unknown-none/release/kotoba-os-boot"
echo "=== booting $IMG on qemu-system-aarch64 (virt) ==="
# the image wfi-loops after printing, so cap it with a timeout
timeout 12 qemu-system-aarch64 -machine virt -cpu cortex-a72 -m 128 -nographic -kernel "$IMG" || true
