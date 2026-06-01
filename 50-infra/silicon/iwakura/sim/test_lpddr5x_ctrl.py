# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for lpddr5x_ctrl (ADR-2605242515 §"Memory hierarchy" +
# §"radix-3 weight packing"). Behavioural DRAM controller + on-die radix-3
# unpacker: a weight fetch returns 5 ternary weights per byte, LATENCY cycles
# after the command, in the ternary_pe 2-bit encoding.
#
# Run: `make sim DUT=lpddr5x_ctrl`

from __future__ import annotations

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

LATENCY = 4   # must match the RTL default parameter
PE_ENCODE = {0: 0b00, +1: 0b01, -1: 0b10}


def encode(trits):
    """5 trits LSB-first (each -1/0/+1) → radix-3 byte 0..242."""
    code = 0
    for w in reversed(trits):
        code = code * 3 + (w + 1)
    return code


async def reset(dut):
    dut.ld_we.value = 0
    dut.ld_addr.value = 0
    dut.ld_byte.value = 0
    dut.cmd_valid.value = 0
    dut.cmd_addr.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def preload(dut, addr, byte):
    await FallingEdge(dut.clk)
    dut.ld_we.value = 1
    dut.ld_addr.value = addr
    dut.ld_byte.value = byte
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.ld_we.value = 0


async def fetch(dut, addr):
    """Issue a weight fetch; wait LATENCY cycles; return (weights, code_valid)."""
    await FallingEdge(dut.clk)
    dut.cmd_valid.value = 1
    dut.cmd_addr.value = addr
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.cmd_valid.value = 0
    # Wait for rsp_valid (bounded by LATENCY + slack).
    for _ in range(LATENCY + 4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")
        if int(dut.rsp_valid.value) == 1:
            w = [int(dut.w0.value), int(dut.w1.value), int(dut.w2.value),
                 int(dut.w3.value), int(dut.w4.value)]
            return w, int(dut.rsp_code_valid.value)
    raise AssertionError("rsp_valid never asserted")


@cocotb.test()
async def fetch_unpacks_five_weights(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    rng = random.Random(0x1DD5)
    # Preload random trit vectors at distinct addresses.
    cases = []
    for addr in range(32):
        trits = [rng.choice([-1, 0, +1]) for _ in range(5)]
        await preload(dut, addr, encode(trits))
        cases.append((addr, trits))

    for addr, trits in cases:
        w, cv = await fetch(dut, addr)
        want = [PE_ENCODE[t] for t in trits]
        assert cv == 1, f"addr {addr}: code should be valid"
        assert w == want, f"addr {addr}: trits {trits} expected {want} got {w}"

    dut._log.info(f"lpddr5x_ctrl: {len(cases)} radix-3 fetches unpacked correctly")


@cocotb.test()
async def reserved_byte_flags_invalid(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)
    await preload(dut, 5, 250)            # 243..255 reserved
    w, cv = await fetch(dut, 5)
    assert cv == 0, "reserved byte must report code_valid=0"
    assert w == [0, 0, 0, 0, 0], f"reserved byte must emit zeros, got {w}"
    dut._log.info("lpddr5x_ctrl: reserved byte flagged invalid + zero-clamped")
