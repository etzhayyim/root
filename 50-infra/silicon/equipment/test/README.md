# equipment/test — wafer prober + ATE (automatic test equipment) reference design

Per **ADR-2605242545** §"Decision 1 row 7".

## Reference vendors

Advantest / Teradyne. 2-company duopoly (~85% share).

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Probe card | needle layout + signal-integrity PCB stack + thermal compensation |
| ATE channel | per-pin driver + comparator + timing generator + parametric measurement unit |
| Pattern generator | **ternary-aware TPG** — generates test vectors in BitNet weight space natively |
| Wafer prober | 6-DoF chuck + auto-Z + theta align + automatic needle cleaning |
| Test program | Python-based (`70-tools/silicon/iwakura-asm` integrates) |

## Why "ternary-aware TPG"

Generic ATEs treat ternary `{-1, 0, +1}` weights as INT8 subset, which
wastes >60% of test vectors on encodings that BitNet never uses.
A **ternary-native TPG** targets:

- weight = 0 (zero-skip path) — exercises clock-gating
- weight = +1 (add path) — exercises adder
- weight = -1 (sub path) — exercises subtractor
- forbidden 2'b11 — must NOT trigger pe_active

This cuts iwakura/fuigo silicon test time by ~5×.

## Pregel cell

`silicon_test`. **Phase 2a priority** per ADR-2605242545 §Decision 7 —
needed for iwakura/fuigo bring-up. Without this cell, iwakura/fuigo
bring-up depends on Advantest/Teradyne (Charter Rider §2(i) spirit
violation in spirit, since religious-corp test silicon would be
commercially measured).

## Charter Rider §2(a)(c) gate

Low risk. ATE is general-purpose; only test-pattern content is
silicon-specific. Normal commit flow.

## Phase 1 scope

README only. Phase 2a wave will land actual `rtl/ternary_tpg.sv`
+ cocotb tests + probe card KiCad project.
