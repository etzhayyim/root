# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for sram_scratch (ADR-2605242515 §"Memory hierarchy").
# Behavioural single-port SRAM: write, 1-cycle registered read, read-first on
# write/read address collision.
#
# Run: `make sim DUT=sram_scratch`

from __future__ import annotations

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

ADDR_W = 8
DATA_W = 64
DEPTH = 1 << ADDR_W
MASK = (1 << DATA_W) - 1


async def reset(dut):
    dut.we.value = 0
    dut.re.value = 0
    dut.waddr.value = 0
    dut.raddr.value = 0
    dut.wdata.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def write(dut, addr, data):
    await FallingEdge(dut.clk)
    dut.we.value = 1
    dut.waddr.value = addr
    dut.wdata.value = data & MASK
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.we.value = 0


async def read(dut, addr):
    await FallingEdge(dut.clk)
    dut.re.value = 1
    dut.raddr.value = addr
    await RisingEdge(dut.clk)   # read is registered: data appears next edge
    await FallingEdge(dut.clk)
    dut.re.value = 0
    await Timer(1, unit="ps")
    return int(dut.rdata.value), int(dut.rvalid.value)


@cocotb.test()
async def write_then_read(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)

    rng = random.Random(0x5A4D)
    model = {}
    # Write a spread of addresses.
    for _ in range(64):
        a = rng.randrange(DEPTH)
        d = rng.getrandbits(DATA_W)
        model[a] = d
        await write(dut, a, d)

    # Read them all back.
    for a, d in model.items():
        rdata, rvalid = await read(dut, a)
        assert rvalid == 1, f"rvalid low for addr {a}"
        assert rdata == d, f"addr {a}: expected {d:#x} got {rdata:#x}"

    dut._log.info(f"sram_scratch: {len(model)} addresses write/read verified")


@cocotb.test()
async def rvalid_tracks_re(dut):
    cocotb.start_soon(Clock(dut.clk, 1, unit="ns").start())
    await reset(dut)
    await write(dut, 7, 0xDEADBEEF)
    # With re=0, rvalid must be 0 the following cycle.
    await FallingEdge(dut.clk)
    dut.re.value = 0
    dut.raddr.value = 7
    await RisingEdge(dut.clk)
    await Timer(1, unit="ps")
    assert int(dut.rvalid.value) == 0, "rvalid should be 0 when re=0"
    dut._log.info("sram_scratch: rvalid tracks re")
