;; Core-wasm control program that returns its command as a STRING in linear
;; memory (the primitive real Component-Model components use to pass Fact
;; strings). `scan` reads the input, bang-bangs, and returns a packed (offset<<8)|len
;; pointing at "ON"/"OFF" in `mem`; the host reads that slice from the guest's memory.
(module
  (import "kotoba" "read_input" (func $read_input (result i32)))
  (memory (export "mem") 1)
  (data (i32.const 0) "OFFON")          ;; OFF @ 0..3 , ON @ 3..5
  (func (export "scan") (result i32)
    (if (result i32) (i32.lt_s (call $read_input) (i32.const 10))
      (then (i32.const 770))            ;; ON : (3<<8)|2
      (else (i32.const 3)))))           ;; OFF: (0<<8)|3
