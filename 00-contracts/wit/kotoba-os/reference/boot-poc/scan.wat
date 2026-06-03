;; Minimal core-wasm control program run BY wasmi INSIDE the unikernel.
;; Imports host functions (the kotoba-os device/datom surface, minimized);
;; exports `scan` = read input -> bang-bang (setpoint 10) -> commit command.
(module
  (import "kotoba" "read_input"     (func $read_input (result i32)))
  (import "kotoba" "commit_command" (func $commit_command (param i32)))
  (func (export "scan") (result i32)
    (local $on i32)
    (local.set $on (i32.lt_s (call $read_input) (i32.const 10)))
    (call $commit_command (local.get $on))
    (local.get $on)))
