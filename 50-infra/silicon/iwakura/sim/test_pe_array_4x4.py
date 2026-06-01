# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for pe_array (ADR-2605242515 §Phase-1 scope, "test_pe_array_4x4.py
# — 4×4 micro array (full systolic, INT8 act × ternary weight)").
#
# Verifies the weight-stationary ternary matrix-vector engine against a pure
# Python reference, plus the zero-skip activity counter (pe_active_count).
#
# Run: `make sim` (Makefile invokes Verilator + cocotb)

from __future__ import annotations

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

ROWS = 4
COLS = 4
ACT_WIDTH = 8
ACC_WIDTH = 24

# weight value → ternary_pe 2-bit encoding
PE_ENCODE = {0: 0b00, +1: 0b01, -1: 0b10}


def to_signed(value: int, width: int) -> int:
    return value & ((1 << width) - 1)


def from_signed(value: int, width: int) -> int:
    sign = 1 << (width - 1)
    return value - (1 << width) if (value & sign) else value


def pack_weights(W: list[list[int]]) -> int:
    """W[r][c] ∈ {-1,0,+1} → flat bus, W[r][c] at bit ((r*COLS)+c)*2."""
    bus = 0
    for r in range(ROWS):
        for c in range(COLS):
            bus |= PE_ENCODE[W[r][c]] << (((r * COLS) + c) * 2)
    return bus


def pack_acts(a: list[int]) -> int:
    """a[c] signed INT8 → flat bus, a[c] at bit c*ACT_WIDTH."""
    bus = 0
    for c in range(COLS):
        bus |= to_signed(a[c], ACT_WIDTH) << (c * ACT_WIDTH)
    return bus


def ref_matvec(W: list[list[int]], a: list[int]) -> list[int]:
    return [sum(W[r][c] * a[c] for c in range(COLS)) for r in range(ROWS)]


def unpack_y(raw: int) -> list[int]:
    return [
        from_signed((raw >> (r * ACC_WIDTH)) & ((1 << ACC_WIDTH) - 1), ACC_WIDTH)
        for r in range(ROWS)
    ]


async def reset(dut):
    dut.start.value = 0
    dut.weights_flat.value = 0
    dut.activations_flat.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_op(dut, W, a):
    """Drive one matrix-vector op, return (y_list, pe_active_count)."""
    dut.weights_flat.value = pack_weights(W)
    dut.activations_flat.value = pack_acts(a)
    # Pulse start for exactly one cycle.
    await FallingEdge(dut.clk)
    dut.start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.start.value = 0
    # Wait for done (bounded).
    for _ in range(COLS + 4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")  # let NBA settle before sampling
        if int(dut.done.value) == 1:
            y = unpack_y(int(dut.y_flat.value))
            cnt = int(dut.pe_active_count.value)
            return y, cnt
    raise AssertionError("done never asserted")


@cocotb.test()
async def known_vectors(dut):
    """A few hand-checked matrices."""
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    # Identity-ish: row r picks a[r].
    W = [[1 if r == c else 0 for c in range(COLS)] for r in range(ROWS)]
    a = [10, -20, 30, -40]
    y, cnt = await run_op(dut, W, a)
    assert y == a, f"identity: expected {a} got {y}"
    assert cnt == ROWS, f"identity activity: expected {ROWS} got {cnt}"

    # All -1 weights → y[r] = -sum(a).
    W = [[-1] * COLS for _ in range(ROWS)]
    y, cnt = await run_op(dut, W, a)
    want = ref_matvec(W, a)
    assert y == want, f"all -1: expected {want} got {y}"
    assert cnt == ROWS * COLS, f"all -1 activity: expected {ROWS*COLS} got {cnt}"

    # All zero weights → y = 0, zero activity (full zero-skip).
    W = [[0] * COLS for _ in range(ROWS)]
    y, cnt = await run_op(dut, W, a)
    assert y == [0] * ROWS, f"all-zero: expected zeros got {y}"
    assert cnt == 0, f"all-zero activity: expected 0 got {cnt}"

    dut._log.info("pe_array known_vectors ok")


@cocotb.test()
async def randomized_matvec(dut):
    """200 random ternary matrices vs reference; checks result + activity count."""
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    rng = random.Random(0xE7515)  # deterministic
    for n in range(200):
        W = [[rng.choice([-1, 0, +1]) for _ in range(COLS)] for _ in range(ROWS)]
        a = [rng.randint(-128, 127) for _ in range(COLS)]
        y, cnt = await run_op(dut, W, a)

        want = ref_matvec(W, a)
        assert y == want, f"case {n}: W={W} a={a} expected {want} got {y}"

        # pe_active_count must equal the number of nonzero weights (zero-skip).
        nonzero = sum(1 for r in range(ROWS) for c in range(COLS) if W[r][c] != 0)
        assert cnt == nonzero, f"case {n}: activity expected {nonzero} got {cnt}"

    dut._log.info("pe_array randomized_matvec: 200 cases ok")


@cocotb.test()
async def back_to_back_independence(dut):
    """Consecutive ops must not leak accumulator state."""
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    W1 = [[1] * COLS for _ in range(ROWS)]
    a1 = [1, 2, 3, 4]
    y1, _ = await run_op(dut, W1, a1)
    assert y1 == [10] * ROWS, f"op1 expected 10s got {y1}"

    # Immediately a different op — result must not include op1's sum.
    W2 = [[-1] * COLS for _ in range(ROWS)]
    a2 = [5, 5, 5, 5]
    y2, _ = await run_op(dut, W2, a2)
    assert y2 == [-20] * ROWS, f"op2 expected -20s (no leak) got {y2}"

    dut._log.info("pe_array back_to_back_independence ok")
