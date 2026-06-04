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
use wasmi::{Caller, Engine, Linker, Module, Store};

/// The real core-wasm control program, assembled from `scan.wat`. wasmi runs
/// THIS inside the unikernel (the production crate runs the full Component Model
/// via kotoba-runtime; this PoC uses the no_std wasmi interpreter on bare metal).
const SCAN_WASM: &[u8] = include_bytes!("../scan.wasm");
/// A control module that returns its command as a STRING in linear memory — the
/// primitive real Component-Model components use to pass Fact strings.
const SCANMEM_WASM: &[u8] = include_bytes!("../scanmem.wasm");

// ---- real device I/O: QEMU virt PL011 UART0 (MMIO) -------------------------
const UART_DR: *mut u8 = 0x0900_0000 as *mut u8;
unsafe fn putc(b: u8) { core::ptr::write_volatile(UART_DR, b); }
fn puts(s: &str) { for b in s.bytes() { unsafe { putc(b) } } }

// ---- a minimal bump allocator over a static heap (.bss, zeroed by QEMU) ----
// 16 MiB: the wasmi interpreter + module/store/instance need real heap. The heap
// lives in .bss (NOBITS, so the image stays small); the stack is moved above it.
const HEAP_SIZE: usize = 16 * 1024 * 1024;
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

/// Host state the wasm module calls into (the kotoba-os device/datom surface).
struct WState {
    pv: i32,
    cycle: u64,
    log: Vec<(u64, i32)>, // (cycle, command) — Datoms produced via host calls
}

/// Run the real `scan.wasm` core module under the wasmi interpreter, IN-KERNEL.
/// The wasm imports `kotoba.read_input` / `kotoba.commit_command` (host funcs
/// implemented here); `scan` reads the input, bang-bangs, and commits a command.
fn run_wasm() {
    puts("\n-- wasmi: running scan.wasm (a real core-wasm module) in-kernel --\n");
    let engine = Engine::default();
    let module = match Module::new(&engine, SCAN_WASM) {
        Ok(m) => m,
        Err(_) => { puts("WASM: module load FAIL\n"); return; }
    };
    let mut store = Store::new(&engine, WState { pv: 0, cycle: 0, log: Vec::new() });
    let mut linker = <Linker<WState>>::new(&engine);
    let _ = linker.func_wrap("kotoba", "read_input", |caller: Caller<'_, WState>| -> i32 {
        caller.data().pv
    });
    let _ = linker.func_wrap("kotoba", "commit_command", |mut caller: Caller<'_, WState>, on: i32| {
        let c = caller.data().cycle;
        caller.data_mut().log.push((c, on));
    });
    let instance = match linker
        .instantiate(&mut store, &module)
        .and_then(|pre| pre.start(&mut store))
    {
        Ok(i) => i,
        Err(_) => { puts("WASM: instantiate FAIL\n"); return; }
    };
    let scan = match instance.get_typed_func::<(), i32>(&store, "scan") {
        Ok(f) => f,
        Err(_) => { puts("WASM: no scan export\n"); return; }
    };

    for (k, pv) in [(0u64, 3i32), (1, 20), (2, 8)] {
        store.data_mut().pv = pv;
        store.data_mut().cycle = k;
        let _cmd = scan.call(&mut store, ()).unwrap_or(-1); // returns the command
    }
    for (c, on) in &store.data().log {
        puts(&format!("WASM DATOM t={c} ctrl :ctrl/command={on}\n"));
    }
    let n = store.data().log.len();
    puts(&format!("WASM: cycles=3 datoms={n} (interpreter=wasmi, in-unikernel)\n"));
    if n == 3 {
        puts("KOTOBA-OS WASM OK\n");
    } else {
        puts("KOTOBA-OS WASM FAIL\n");
    }
}

/// Read a command STRING out of the wasm guest's linear memory — the primitive
/// real Component-Model components rely on (Fact strings / lists live in guest
/// memory, not in i32 returns). `scan` returns a packed (offset<<8)|len; the host
/// reads that slice from the instance's exported `mem`.
fn run_wasm_mem() {
    puts("\n-- wasmi: reading a command STRING from wasm linear memory --\n");
    let engine = Engine::default();
    let module = match Module::new(&engine, SCANMEM_WASM) {
        Ok(m) => m,
        Err(_) => { puts("WASMEM: module load FAIL\n"); return; }
    };
    let mut store = Store::new(&engine, WState { pv: 0, cycle: 0, log: Vec::new() });
    let mut linker = <Linker<WState>>::new(&engine);
    let _ = linker.func_wrap("kotoba", "read_input", |caller: Caller<'_, WState>| -> i32 {
        caller.data().pv
    });
    let instance = match linker
        .instantiate(&mut store, &module)
        .and_then(|pre| pre.start(&mut store))
    {
        Ok(i) => i,
        Err(_) => { puts("WASMEM: instantiate FAIL\n"); return; }
    };
    let scan = match instance.get_typed_func::<(), i32>(&store, "scan") {
        Ok(f) => f,
        Err(_) => { puts("WASMEM: no scan export\n"); return; }
    };
    let mem = match instance.get_memory(&store, "mem") {
        Some(m) => m,
        None => { puts("WASMEM: no mem export\n"); return; }
    };

    let mut ok = 0;
    for (k, pv) in [(0u64, 3i32), (1, 20), (2, 8)] {
        store.data_mut().pv = pv;
        let r = scan.call(&mut store, ()).unwrap_or(0);
        let off = (r >> 8) as usize;
        let len = (r & 0xff) as usize;
        let mut buf = [0u8; 8];
        if len <= buf.len() && mem.read(&store, off, &mut buf[..len]).is_ok() {
            let cmd = core::str::from_utf8(&buf[..len]).unwrap_or("?");
            puts(&format!("WASMEM t={k} ctrl :ctrl/command=\"{cmd}\" (read from guest memory)\n"));
            ok += 1;
        }
    }
    if ok == 3 {
        puts("KOTOBA-OS WASMEM OK\n");
    } else {
        puts("KOTOBA-OS WASMEM FAIL\n");
    }
}

core::arch::global_asm!(
    ".section .text._start",
    ".global _start",
    "_start:",
    "  ldr x30, =0x44000000", // stack pointer in RAM, above the 16 MiB .bss heap
    "  mov sp, x30",
    "  mrs x0, cpacr_el1",     // enable FP/SIMD at EL1 (FPEN=0b11) — wasmi needs it;
    "  orr x0, x0, #(3 << 20)",// without this, an FP/NEON insn traps and the CPU
    "  msr cpacr_el1, x0",     // hangs (no exception vectors). The integer-only
    "  isb",                   // native scan worked without it.
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
    puts("boot: bump heap (16 MiB) online\n");
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

    // --- run a REAL wasm module via the wasmi interpreter, in-kernel ---
    run_wasm();
    run_wasm_mem();

    loop {
        unsafe { core::arch::asm!("wfi") }
    }
}

#[panic_handler]
fn panic(_: &PanicInfo) -> ! {
    puts("PANIC\n");
    loop {}
}
