# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Integration smoke test for iwakura_top (ADR-2605242515 §Phase-1 scope).
# Drives the live compute tile (pe_array + zero_skip_dispatcher) through the
# top-level direct-compute interface and confirms:
#   - the integrated datapath produces a correct matrix-vector result
#   - pe_active_count reflects the real (zero-skipped) PE activity
#   - host_tx low byte carries the column-0 activity estimate from the dispatcher
#
# Run: `make sim DUT=iwakura_top`

from __future__ import annotations

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

TILE_ROWS = 4
TILE_COLS = 4
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
    for r in range(TILE_ROWS):
        for c in range(TILE_COLS):
            bus |= PE_ENCODE[W[r][c]] << (((r * TILE_COLS) + c) * 2)
    return bus


def pack_acts(a):
    bus = 0
    for c in range(TILE_COLS):
        bus |= to_signed(a[c], ACT_WIDTH) << (c * ACT_WIDTH)
    return bus


def ref(W, a):
    return [sum(W[r][c] * a[c] for c in range(TILE_COLS)) for r in range(TILE_ROWS)]


def unpack_y(raw):
    return [
        from_signed((raw >> (r * ACC_WIDTH)) & ((1 << ACC_WIDTH) - 1), ACC_WIDTH)
        for r in range(TILE_ROWS)
    ]


async def reset(dut):
    dut.tile_start.value = 0
    dut.tile_weights_flat.value = 0
    dut.tile_activations_flat.value = 0
    dut.host_rx_data.value = 0
    dut.host_rx_valid.value = 0
    dut.dram_rdata.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def integrated_matvec(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    W = [
        [1, 0, -1, 0],
        [0, 1, 0, -1],
        [-1, -1, 1, 1],
        [0, 0, 0, 0],   # fully zero-skipped row
    ]
    a = [50, -30, 20, 10]

    dut.tile_weights_flat.value = pack_weights(W)
    dut.tile_activations_flat.value = pack_acts(a)
    await FallingEdge(dut.clk)
    dut.tile_start.value = 1
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.tile_start.value = 0

    for _ in range(TILE_COLS + 4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")
        if int(dut.tile_done.value) == 1:
            break
    else:
        raise AssertionError("tile_done never asserted")

    y = unpack_y(int(dut.tile_y_flat.value))
    want = ref(W, a)
    assert y == want, f"integrated matvec: expected {want} got {y}"

    nonzero = sum(1 for r in range(TILE_ROWS) for c in range(TILE_COLS) if W[r][c] != 0)
    assert int(dut.pe_active_count.value) == nonzero, (
        f"pe_active_count expected {nonzero} got {int(dut.pe_active_count.value)}"
    )

    # host_tx valid pulses with done; low byte = column-0 activity estimate.
    assert int(dut.host_tx_valid.value) == 1, "host_tx_valid should pulse with done"
    col0_active = int(dut.host_tx_data.value) & 0xFF
    col0_nonzero = sum(1 for r in range(TILE_ROWS) if W[r][0] != 0)
    assert col0_active == col0_nonzero, (
        f"dispatcher col0 estimate expected {col0_nonzero} got {col0_active}"
    )

    dut._log.info(
        f"iwakura_top integrated: y={y}, pe_active_count={nonzero}, "
        f"col0_active={col0_active} — datapath live"
    )
