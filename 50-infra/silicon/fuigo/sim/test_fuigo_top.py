# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Forward-path integration smoke test for fuigo_top (ADR-2605242530 §Phase-1:
# "forward path は ternary-pe IP 再利用"). Confirms fuigo's forward systolic
# array — the shared pe_array / ternary-pe IP — computes correctly at the
# training accumulator width (ACC_WIDTH=32) and reports forward_pe_active.
#
# Run: `make sim`

from __future__ import annotations

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

ROWS = 4
COLS = 4
ACT_WIDTH = 8
ACC_WIDTH = 32   # fuigo training accumulator (wider than iwakura's 24)

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
    return [
        from_signed((raw >> (r * ACC_WIDTH)) & ((1 << ACC_WIDTH) - 1), ACC_WIDTH)
        for r in range(ROWS)
    ]


async def reset(dut):
    dut.fwd_start.value = 0
    dut.fwd_weights_flat.value = 0
    dut.fwd_activations_flat.value = 0
    dut.libp2p_peer_id.value = 0
    dut.libp2p_rx_valid.value = 0
    dut.libp2p_rx_data.value = 0
    dut.cxl_rx_flit.value = 0
    dut.cxl_rx_valid.value = 0
    dut.hbm_rdata.value = 0
    dut.training_start.value = 0
    dut.global_step.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run_fwd(dut, W, a):
    dut.fwd_weights_flat.value = pack_weights(W)
    dut.fwd_activations_flat.value = pack_acts(a)
    await FallingEdge(dut.clk)
    dut.fwd_start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.fwd_start.value = 0
    for _ in range(COLS + 4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")
        if int(dut.fwd_done.value) == 1:
            return unpack_y(int(dut.fwd_y_flat.value)), int(dut.forward_pe_active.value)
    raise AssertionError("fwd_done never asserted")


@cocotb.test()
async def forward_path_matvec(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    # Hand-checked. Activations are INT8 (ACT_WIDTH=8); fuigo's wider ACC_WIDTH=32
    # buys accumulation depth, not larger single activations.
    W = [[1, -1, 0, 1], [0, 1, 1, 0], [-1, -1, -1, -1], [1, 0, 0, 0]]
    a = [100, 120, -90, 70]
    y, cnt = await run_fwd(dut, W, a)
    assert y == ref(W, a), f"forward matvec: expected {ref(W,a)} got {y}"
    nz = sum(1 for r in range(ROWS) for c in range(COLS) if W[r][c] != 0)
    assert cnt == nz, f"forward_pe_active expected {nz} got {cnt}"
    assert int(dut.backward_mac_active.value) == 0, "backward is Phase-2 placeholder"

    # Randomized sweep at wide activations to push the 32-bit accumulator.
    rng = random.Random(0xF16160)
    for n in range(100):
        W = [[rng.choice([-1, 0, 1]) for _ in range(COLS)] for _ in range(ROWS)]
        a = [rng.randint(-128, 127) for _ in range(COLS)]
        y, cnt = await run_fwd(dut, W, a)
        assert y == ref(W, a), f"case {n}: W={W} a={a} expected {ref(W,a)} got {y}"

    dut._log.info("fuigo forward path: shared ternary-pe IP verified (ACC_WIDTH=32)")
