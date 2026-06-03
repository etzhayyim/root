//! Minimal kotoba-os boot stub (ADR-2606031600 L1/L2 PoC).
//! A no_std, single-address-space image that boots on the QEMU `virt`
//! hypervisor and writes to the real PL011 UART via MMIO — the most basic but
//! genuine "unikernel boot + real memory-mapped device I/O".
#![no_std]
#![no_main]
use core::panic::PanicInfo;

// QEMU virt PL011 UART0
const UART_DR: *mut u8 = 0x0900_0000 as *mut u8;

unsafe fn putc(b: u8) { core::ptr::write_volatile(UART_DR, b); }
fn puts(s: &str) { for b in s.bytes() { unsafe { putc(b) } } }

core::arch::global_asm!(
    ".section .text._start",
    ".global _start",
    "_start:",
    "  ldr x30, =0x40200000",   // set a stack pointer in RAM
    "  mov sp, x30",
    "  bl rust_main",
    "1: wfi",
    "  b 1b",
);

#[no_mangle]
pub extern "C" fn rust_main() -> ! {
    puts("\n");
    puts("=== kotoba-os boot (aarch64 no_std unikernel on QEMU virt) ===\n");
    puts("L2 kernel: single address space, MMIO UART up (real device I/O)\n");
    // a tiny stand-in for the boot sequence: "verify -> ready"
    puts("boot: kernel image entered at _start, SP set, .text running\n");
    puts("boot: PL011 UART @ 0x09000000 written via volatile MMIO\n");
    puts("KOTOBA-OS BOOT OK\n");
    loop { unsafe { core::arch::asm!("wfi") } }
}

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { loop {} }
