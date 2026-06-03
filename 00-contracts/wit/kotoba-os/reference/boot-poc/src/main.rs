//! kotoba-os boot PoC (ADR-2606031600 L1/L2).
//!
//! A no_std, single-address-space aarch64 image that boots on the QEMU `virt`
//! hypervisor, brings up a heap (bump allocator) + the real PL011 UART (MMIO),
//! and then RUNS the kotoba-os control model **inside the unikernel**: a few
//! bang-bang scan cycles where each committed cycle is a Datom transaction, plus
//! a faulted cycle that commits nothing (N3 atomicity). The resulting Datom log
//! is printed over the real UART. This is genuine unikernel boot + real MMIO I/O
//! + the kotoba-os scan-cycle=Datom-transaction model executing on bare QEMU.
#![no_std]
#![no_main]

extern crate alloc;

use alloc::format;
use alloc::string::{String, ToString};
use alloc::vec::Vec;
use core::alloc::{GlobalAlloc, Layout};
use core::panic::PanicInfo;
use core::ptr::addr_of_mut;
use core::sync::atomic::{AtomicUsize, Ordering};

// ---- real device I/O: QEMU virt PL011 UART0 (MMIO) -------------------------
const UART_DR: *mut u8 = 0x0900_0000 as *mut u8;
unsafe fn putc(b: u8) { core::ptr::write_volatile(UART_DR, b); }
fn puts(s: &str) { for b in s.bytes() { unsafe { putc(b) } } }

// ---- a minimal bump allocator over a static heap (.bss, zeroed by QEMU) ----
const HEAP_SIZE: usize = 256 * 1024;
static mut HEAP: [u8; HEAP_SIZE] = [0; HEAP_SIZE];
static OFFSET: AtomicUsize = AtomicUsize::new(0);

struct Bump;
unsafe impl GlobalAlloc for Bump {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let (size, align) = (layout.size(), layout.align());
        loop {
            let cur = OFFSET.load(Ordering::Relaxed);
            let aligned = (cur + align - 1) & !(align - 1);
            let new = aligned + size;
            if new > HEAP_SIZE {
                return core::ptr::null_mut();
            }
            if OFFSET
                .compare_exchange(cur, new, Ordering::Relaxed, Ordering::Relaxed)
                .is_ok()
            {
                return (addr_of_mut!(HEAP) as *mut u8).add(aligned);
            }
        }
    }
    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {} // bump: no free
}
#[global_allocator]
static ALLOC: Bump = Bump;

// ---- the kotoba-os control model (no_std), running in the unikernel --------
struct Host {
    pv: i32,
    fail: bool,
    staged_out: Vec<(u32, bool)>,
    staged_facts: Vec<(String, String, i32)>, // entity, attribute, value
    log: Vec<(u64, String, String, i32)>,      // T, entity, attribute, value
}
impl Host {
    fn new() -> Self {
        Host { pv: 0, fail: false, staged_out: Vec::new(), staged_facts: Vec::new(), log: Vec::new() }
    }
    fn read_input(&self) -> Result<i32, ()> {
        if self.fail { Err(()) } else { Ok(self.pv) }
    }
    /// one scan cycle: read -> compute -> stage (no commit yet)
    fn scan(&mut self) -> Result<(), ()> {
        let pv = self.read_input()?;
        let on = pv < 10; // bang-bang setpoint = 10
        self.staged_out.push((10, on));
        self.staged_facts
            .push(("ctrl".to_string(), ":ctrl/command".to_string(), i32::from(on)));
        Ok(())
    }
    /// atomic commit: staged outputs + facts become one Datom transaction (T=t)
    fn commit(&mut self, t: u64) {
        for (ch, v) in core::mem::take(&mut self.staged_out) {
            self.log.push((t, format!("out:{ch}"), ":io/output".to_string(), i32::from(v)));
        }
        for (e, a, v) in core::mem::take(&mut self.staged_facts) {
            self.log.push((t, e, a, v));
        }
    }
    fn rollback(&mut self) {
        self.staged_out.clear();
        self.staged_facts.clear();
    }
}

core::arch::global_asm!(
    ".section .text._start",
    ".global _start",
    "_start:",
    "  ldr x30, =0x40200000", // stack pointer in RAM
    "  mov sp, x30",
    "  bl rust_main",
    "1: wfi",
    "  b 1b",
);

#[no_mangle]
pub extern "C" fn rust_main() -> ! {
    puts("\n=== kotoba-os boot (aarch64 no_std unikernel on QEMU virt) ===\n");
    puts("L2 kernel: single address space, MMIO UART up (real device I/O)\n");
    puts("boot: kernel image entered at _start, SP set, .text running\n");
    puts("boot: PL011 UART @ 0x09000000 written via volatile MMIO\n");
    puts("boot: bump heap (256 KiB) online\n");
    puts("KOTOBA-OS BOOT OK\n");

    // --- run the kotoba-os scan-cycle model inside the unikernel ---
    puts("\n-- scan cycles (each commit = a Datom transaction) --\n");
    let mut h = Host::new();
    let mut t: u64 = 0;
    for pv in [3, 20, 8] {
        h.pv = pv;
        if h.scan().is_ok() {
            h.commit(t); // committed
        }
        t += 1;
    }
    // faulted cycle (N3): sensor read errors -> stage discarded, nothing commits
    h.fail = true;
    h.pv = 5;
    let before = h.log.len();
    if h.scan().is_err() {
        h.rollback();
    } else {
        h.commit(t);
    }
    let faulted_committed = h.log.len() - before; // must be 0

    for (tt, e, a, v) in &h.log {
        puts(&format!("DATOM t={tt} {e} {a}={v}\n"));
    }
    puts(&format!(
        "SCAN: committed_cycles=3 faulted=1 faulted_datoms={faulted_committed} total_datoms={}\n",
        h.log.len()
    ));
    if h.log.len() == 6 && faulted_committed == 0 {
        puts("KOTOBA-OS SCAN OK\n");
    } else {
        puts("KOTOBA-OS SCAN FAIL\n");
    }

    loop {
        unsafe { core::arch::asm!("wfi") }
    }
}

#[panic_handler]
fn panic(_: &PanicInfo) -> ! {
    puts("PANIC\n");
    loop {}
}
