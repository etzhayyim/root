# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for radix3_decoder (ADR-2605242515 §"radix-3 weight packing").
# Exhaustive: all 256 possible byte codes.
#   - codes 0..242  : 5 valid trits, code_valid = 1
#   - codes 243..255: reserved, all weights 0, code_valid = 0
#
# Run: `make sim` (Makefile invokes Verilator + cocotb)

from __future__ import annotations

import cocotb
from cocotb.triggers import Timer


# ternary_pe 2-bit encoding (must match radix3_decoder.digit_to_pe + ternary_pe)
PE_ENCODE = {
    0: 0b00,   # weight 0
    +1: 0b01,  # weight +1
    -1: 0b10,  # weight -1
}


def encode(trits: list[int]) -> int:
    """Reference encoder: 5 trits (LSB-first, each in {-1,0,+1}) → byte 0..242."""
    code = 0
    for w in reversed(trits):          # w4, w3, w2, w1, w0
        code = code * 3 + (w + 1)
    return code


def decode_ref(code: int) -> list[int]:
    """Reference decoder: byte → [w0, w1, w2, w3, w4] (LSB-first)."""
    out = []
    for _ in range(5):
        out.append((code % 3) - 1)
        code //= 3
    return out


@cocotb.test()
async def exhaustive_all_256_codes(dut):
    """Drive every possible byte 0..255; check trits and code_valid."""
    valid_count = 0
    for code in range(256):
        dut.code.value = code
        await Timer(1, unit="ns")  # combinational settle

        actual = [
            int(dut.w0.value),
            int(dut.w1.value),
            int(dut.w2.value),
            int(dut.w3.value),
            int(dut.w4.value),
        ]
        actual_valid = int(dut.code_valid.value)

        if code <= 242:
            ref_trits = decode_ref(code)
            ref_enc = [PE_ENCODE[w] for w in ref_trits]
            assert actual_valid == 1, f"code={code} should be valid"
            assert actual == ref_enc, (
                f"code={code}: trits {ref_trits} expected enc {ref_enc} got {actual}"
            )
            valid_count += 1
        else:
            assert actual_valid == 0, f"code={code} (reserved) must be invalid"
            assert actual == [0, 0, 0, 0, 0], (
                f"code={code} (reserved) must emit all-zero weights, got {actual}"
            )

    dut._log.info(f"radix3_decoder: 256 codes checked, {valid_count} valid")
    assert valid_count == 243, f"expected 243 valid codes, got {valid_count}"


@cocotb.test()
async def roundtrip_corner_vectors(dut):
    """Encode known trit vectors, decode in HW, confirm exact roundtrip."""
    vectors = [
        [0, 0, 0, 0, 0],        # all zero  → code 121 (center)
        [+1, +1, +1, +1, +1],   # all +1    → code 242 (max)
        [-1, -1, -1, -1, -1],   # all -1    → code 0   (min)
        [+1, 0, -1, +1, 0],     # mixed
        [-1, +1, 0, 0, +1],     # mixed
    ]
    for trits in vectors:
        code = encode(trits)
        assert 0 <= code <= 242, f"encoder produced out-of-range {code}"
        dut.code.value = code
        await Timer(1, unit="ns")

        got = [
            int(dut.w0.value), int(dut.w1.value), int(dut.w2.value),
            int(dut.w3.value), int(dut.w4.value),
        ]
        want = [PE_ENCODE[w] for w in trits]
        assert got == want, f"trits {trits} (code {code}): want {want} got {got}"
        assert int(dut.code_valid.value) == 1

    dut._log.info(f"radix3_decoder: {len(vectors)} roundtrip vectors ok")
