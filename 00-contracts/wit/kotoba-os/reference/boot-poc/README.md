# kotoba-os boot PoC — minimal unikernel boot + real MMIO device I/O

**ADR**: [ADR-2606031600](../../../../90-docs/adr/2606031600-kotoba-os-content-addressed-wasm-unikernel.md) §L1/L2

A `no_std`, single-address-space **aarch64** image that boots on QEMU's `virt`
hypervisor machine (the class Firecracker/KVM use) and writes to the **real PL011
UART via MMIO** (`0x09000000`) — a genuine, if minimal, demonstration of the two
things the reference otherwise only *claimed*: a unikernel boot and real
(memory-mapped) device I/O.

```
$ bash run.sh
=== kotoba-os boot (aarch64 no_std unikernel on QEMU virt) ===
L2 kernel: single address space, MMIO UART up (real device I/O)
boot: kernel image entered at _start, SP set, .text running
boot: PL011 UART @ 0x09000000 written via volatile MMIO
KOTOBA-OS BOOT OK

-- scan cycles (each commit = a Datom transaction) --
DATOM t=0 ctrl :ctrl/command=1     # pv=3  -> ON
DATOM t=1 ctrl :ctrl/command=0     # pv=20 -> OFF
DATOM t=2 ctrl :ctrl/command=1     # pv=8  -> ON
SCAN: committed_cycles=3 faulted=1 faulted_datoms=0 total_datoms=6
KOTOBA-OS SCAN OK
```

After boot it brings up a bump-allocator heap and **runs the kotoba-os scan-cycle
model inside the unikernel**: each committed cycle is a Datom transaction, and the
faulted cycle commits nothing (N3 atomicity) — printed over the real UART.

## What it proves / does NOT

- **Proves**: a `no_std` single-address-space image boots with no OS underneath on
  a hypervisor (`qemu-system-aarch64 -machine virt`), enters at `_start`, sets a
  stack, runs Rust, and does **real** volatile MMIO to a hardware UART (not a
  simulated/canned bus).
- **Does NOT (yet)**: run the WASM runtime, the Datom log, or the device-WIT host
  inside the unikernel. That = boot-PoC + `kotoba-runtime` + the substrate, which is
  the production-crate work handed off in [`../../PORTING.md`](../../PORTING.md)
  (target: Hermit-derived kernel in the `40-engine/kotoba` subrepo).

## Reproduce

Needs the `aarch64-unknown-none` rust target + `qemu-system-aarch64`:

```bash
rustup target add aarch64-unknown-none
bash run.sh
```

The image `wfi`-loops after printing, so `run.sh` caps QEMU with a timeout.
