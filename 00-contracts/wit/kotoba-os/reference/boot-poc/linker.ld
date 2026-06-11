ENTRY(_start)
SECTIONS {
  . = 0x40080000;            /* QEMU virt RAM base + offset */
  .text : { KEEP(*(.text._start)) *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
}
