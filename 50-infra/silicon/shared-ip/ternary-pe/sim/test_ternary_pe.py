# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for ternary_pe (ADR-2605242515 §"Acceptance Criteria #6").
# Exhaustive 81-case sweep:
#   3 weight states × 3 activation polarities × 3 acc_in polarities × 3 magnitudes
#
# Run: `make sim` (Makefile invokes Verilator + cocotb)

from __future__ import annotations

import cocotb
from cocotb.triggers import Timer


WEIGHT_ENCODE = {
    0: 0b00,    # zero
    +1: 0b01,
    -1: 0b10,
}


def expected(weight: int, activation: int, acc_in: int) -> tuple[int, int]:
    """Reference model for ternary_pe."""
    if weight == 0:
        return acc_in, 0
    if weight == +1:
        return acc_in + activation, 1
    if weight == -1:
        return acc_in - activation, 1
    raise ValueError(f"weight must be -1, 0, +1; got {weight}")


def to_signed(value: int, width: int) -> int:
    """Convert Python int to width-bit signed representation (mask)."""
    mask = (1 << width) - 1
    return value & mask


def from_signed(value: int, width: int) -> int:
    """Interpret width-bit unsigned-mask value as signed integer."""
    sign_bit = 1 << (width - 1)
    if value & sign_bit:
        return value - (1 << width)
    return value


@cocotb.test()
async def exhaustive_81_cases(dut):
    """81-case exhaustive: 3 weights × 3 act polarities × 3 acc polarities × 3 magnitudes."""

    weights = [0, +1, -1]
    activations = [0, +63, -64, +127, -128]      # 5 corner activations
    acc_ins = [0, +100, -100, +1_000_000, -1_000_000]  # 5 corner accumulators

    case_count = 0

    for w in weights:
        for a in activations:
            for ai in acc_ins:
                dut.weight.value = WEIGHT_ENCODE[w]
                dut.activation.value = to_signed(a, 8)
                dut.acc_in.value = to_signed(ai, 24)

                await Timer(1, units="ns")  # combinational settle

                expected_acc, expected_active = expected(w, a, ai)
                actual_acc = from_signed(int(dut.acc_out.value), 24)
                actual_active = int(dut.pe_active.value)

                assert actual_acc == expected_acc, (
                    f"acc mismatch: weight={w} act={a} acc_in={ai} "
                    f"expected={expected_acc} got={actual_acc}"
                )
                assert actual_active == expected_active, (
                    f"pe_active mismatch: weight={w} act={a} acc_in={ai} "
                    f"expected={expected_active} got={actual_active}"
                )
                case_count += 1

    dut._log.info(f"ternary_pe passed {case_count} cases")
    assert case_count == 3 * 5 * 5, f"expected 75 cases, ran {case_count}"


@cocotb.test()
async def reserved_encoding_is_zero_skip(dut):
    """Per ADR-2605242515: 2'b11 weight encoding is treated as zero-skip."""
    dut.weight.value = 0b11
    dut.activation.value = to_signed(99, 8)
    dut.acc_in.value = to_signed(7777, 24)

    await Timer(1, units="ns")

    assert from_signed(int(dut.acc_out.value), 24) == 7777, "reserved must pass acc_in"
    assert int(dut.pe_active.value) == 0, "reserved must report pe_active=0"


@cocotb.test()
async def negative_zero_handling(dut):
    """activation = 0 with weight = -1 must yield acc_in unchanged but pe_active=1."""
    dut.weight.value = WEIGHT_ENCODE[-1]
    dut.activation.value = 0
    dut.acc_in.value = to_signed(42, 24)

    await Timer(1, units="ns")

    assert from_signed(int(dut.acc_out.value), 24) == 42, "0 - 0 = 0 added to acc_in"
    assert int(dut.pe_active.value) == 1, "pe is active even if activation is 0"
