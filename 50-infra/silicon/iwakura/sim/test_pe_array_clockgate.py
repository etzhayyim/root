# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for pe_array with CLOCK_GATE=1 (Phase-2 zero-skip clock gating,
# ADR-2605242515 §"Zero-skip dispatcher"). Confirms:
#   - results are bit-identical to the ungated array (gating cannot change math)
#   - acc_write_count drops vs the ungated worst case (ROWS*COLS), i.e. the
#     accumulator registers are genuinely not clocked on zero-weight lanes
#
# Elaborated with -GCLOCK_GATE=1 (see Makefile DUT=pe_array_cg).
# Run: `make sim DUT=pe_array_cg`

from __future__ import annotations

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

ROWS = 4
COLS = 4
ACT_WIDTH = 8
ACC_WIDTH = 24
PE_ENCODE = {0: 0b00, +1: 0b01, -1: 0b10}


def to_signed(v, w):
    return v & ((1 << w) - 1)


def from_signed(v, w):
    s = 1 << (w - 1)
    return v - (1 << w) if (v & s) else v


def pack_weights(W):
    bus = 0
    for r in range(ROWS):
        for c in range(COLS):
            bus |= PE_ENCODE[W[r][c]] << (((r * COLS) + c) * 2)
    return bus


def pack_acts(a):
    bus = 0
    for c in range(COLS):
        bus |= to_signed(a[c], ACT_WIDTH) << (c * ACT_WIDTH)
    return bus


def ref(W, a):
    return [sum(W[r][c] * a[c] for c in range(COLS)) for r in range(ROWS)]


def unpack_y(raw):
    return [from_signed((raw >> (r * ACC_WIDTH)) & ((1 << ACC_WIDTH) - 1), ACC_WIDTH)
            for r in range(ROWS)]


def expected_writes(W):
    """With clock gating: col 0 writes all ROWS lanes (zeroed base); col>0 writes
    only nonzero-weight lanes."""
    writes = ROWS  # column 0: every lane writes its base
    for c in range(1, COLS):
        writes += sum(1 for r in range(ROWS) if W[r][c] != 0)
    return writes


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
    dut.weights_flat.value = pack_weights(W)
    dut.activations_flat.value = pack_acts(a)
    await FallingEdge(dut.clk)
    dut.start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.start.value = 0
    for _ in range(COLS + 4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")
        if int(dut.done.value) == 1:
            return (unpack_y(int(dut.y_flat.value)),
                    int(dut.pe_active_count.value),
                    int(dut.acc_write_count.value))
    raise AssertionError("done never asserted")


@cocotb.test()
async def gated_results_identical_and_save_writes(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    rng = random.Random(0xC10C6A7E)
    total_ungated = 0
    total_gated = 0
    for n in range(200):
        W = [[rng.choice([-1, 0, +1]) for _ in range(COLS)] for _ in range(ROWS)]
        a = [rng.randint(-128, 127) for _ in range(COLS)]
        y, active, writes = await run_op(dut, W, a)

        # 1) math is unchanged by gating
        assert y == ref(W, a), f"case {n}: gated result wrong: {y} vs {ref(W,a)}"

        # 2) write count matches the gating model and never exceeds the ungated
        #    worst case ROWS*COLS
        exp_w = expected_writes(W)
        assert writes == exp_w, f"case {n}: acc_write_count {writes} != model {exp_w}"
        assert writes <= ROWS * COLS

        total_ungated += ROWS * COLS
        total_gated += writes

    saved = 1.0 - total_gated / total_ungated
    dut._log.info(
        f"pe_array CLOCK_GATE=1: 200 cases bit-identical; "
        f"accumulator writes {total_gated}/{total_ungated} "
        f"({saved*100:.1f}% gated off)"
    )
    # On random ternary weights ~ (1 - p0) active for cols>0; with col0 always
    # writing, savings sit below the raw 35%. Just assert a real, positive save.
    assert saved > 0.10, f"expected meaningful write savings, got {saved:.3f}"
