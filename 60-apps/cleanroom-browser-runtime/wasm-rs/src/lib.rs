//! Compact clean-room actor for the RAW single-block WASM tier (browser-local,
//! ADR-2606014500/2606014600). No host imports (no WASI) → runs browser-local
//! via the ameno wasm-actor loader. An in-memory kotoba Datom store over linear
//! memory with a C-ABI surface; the loader marshals JSON on the host side.
//!
//! Exports: alloc/dealloc (buffer passing), actor_create, actor_count,
//! actor_get_len, actor_delete, actor_healthz.
#![no_std]
extern crate alloc;
use alloc::vec::Vec;
use core::alloc::{GlobalAlloc, Layout};

// --- tiny bump-ish allocator (single-threaded wasm) backed by a wee_alloc-free
// hand-rolled freelist would be heavier; use the dlmalloc-free `talc`-style
// minimal allocator: here a simple leaking bump allocator is enough for a PoC
// actor and keeps the module tiny. ---
struct Bump;
const HEAP: usize = 1 << 20;
static mut ARENA: [u8; HEAP] = [0; HEAP];
static mut OFF: usize = 0;
unsafe impl GlobalAlloc for Bump {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        let a = l.align();
        let p = (OFF + (a - 1)) & !(a - 1);
        if p + l.size() > HEAP { return core::ptr::null_mut(); }
        OFF = p + l.size();
        ARENA.as_mut_ptr().add(p)
    }
    unsafe fn dealloc(&self, _: *mut u8, _: Layout) {}
}
#[global_allocator]
static A: Bump = Bump;

#[panic_handler]
fn ph(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }

// in-memory Datom store: each record = owned bytes
static mut STORE: Option<Vec<Vec<u8>>> = None;
unsafe fn store() -> &'static mut Vec<Vec<u8>> {
    if STORE.is_none() { STORE = Some(Vec::new()); }
    STORE.as_mut().unwrap()
}

#[no_mangle]
pub extern "C" fn alloc(len: usize) -> *mut u8 {
    let mut v = Vec::<u8>::with_capacity(len);
    let p = v.as_mut_ptr();
    core::mem::forget(v);
    p
}

/// create a record from a host buffer; returns the new 1-based id (0 = error)
#[no_mangle]
pub extern "C" fn actor_create(ptr: *const u8, len: usize) -> u64 {
    if ptr.is_null() { return 0; }
    let mut rec = Vec::with_capacity(len);
    unsafe {
        for i in 0..len { rec.push(*ptr.add(i)); }
        store().push(rec);
        store().len() as u64
    }
}

/// number of records
#[no_mangle]
pub extern "C" fn actor_count() -> u64 { unsafe { store().len() as u64 } }

/// byte length of record `id` (1-based); 0 if absent
#[no_mangle]
pub extern "C" fn actor_get_len(id: u64) -> u64 {
    unsafe {
        let s = store();
        if id == 0 || id as usize > s.len() { 0 } else { s[(id - 1) as usize].len() as u64 }
    }
}

/// delete record `id` (1-based); returns new count
#[no_mangle]
pub extern "C" fn actor_delete(id: u64) -> u64 {
    unsafe {
        let s = store();
        if id != 0 && (id as usize) <= s.len() { s.remove((id - 1) as usize); }
        s.len() as u64
    }
}

/// health probe: returns a stable magic (0x0K) + record count in low bits
#[no_mangle]
pub extern "C" fn actor_healthz() -> u64 { unsafe { 0x6f6b_0000_0000_0000 | store().len() as u64 } }
