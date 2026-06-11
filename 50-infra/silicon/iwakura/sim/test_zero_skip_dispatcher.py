# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# cocotb test for zero_skip_dispatcher (ADR-2605242515 §"Zero-skip dispatcher").
#
# Checks, for an 8-wide weight block:
#   - clk_en mask is exactly the set of ±1 weights (0 and reserved are gated)
#   - active_count == popcount(clk_en)
#   - all_zero flag
#   - statistical: on the BitNet 1.58 distribution {0:35%, +1:32%, -1:33%},
#     the gated fraction is ~35% (the ADR's dynamic-power-saving claim).
#
# Run: `make sim DUT=zero_skip_dispatcher`

from __future__ import annotations

import random

import cocotb
from cocotb.triggers import Timer

BLOCK = 8

# weight value → 2-bit encoding
ENC = {0: 0b00, +1: 0b01, -1: 0b10}
RESERVED = 0b11


def pack(codes: list[int]) -> int:
    """codes: list of BLOCK 2-bit encodings → flat bus."""
    bus = 0
    for i, c in enumerate(codes):
        bus |= (c & 0b11) << (i * 2)
    return bus


def active_ref(codes: list[int]) -> list[int]:
    """1 if encoding is +1 (01) or -1 (10), else 0."""
    return [1 if c in (0b01, 0b10) else 0 for c in codes]


async def drive(dut, codes: list[int]):
    dut.weights.value = pack(codes)
    await Timer(1, unit="ns")
    mask = int(dut.clk_en.value)
    got = [(mask >> i) & 1 for i in range(BLOCK)]
    cnt = int(dut.active_count.value)
    az = int(dut.all_zero.value)
    return got, cnt, az


@cocotb.test()
async def corner_blocks(dut):
    """All-zero, all-reserved, all+1, all-1, mixed."""
    # all zero
    got, cnt, az = await drive(dut, [0b00] * BLOCK)
    assert got == [0] * BLOCK and cnt == 0 and az == 1, (got, cnt, az)
    # all reserved (also zero-skip)
    got, cnt, az = await drive(dut, [RESERVED] * BLOCK)
    assert got == [0] * BLOCK and cnt == 0 and az == 1, (got, cnt, az)
    # all +1
    got, cnt, az = await drive(dut, [0b01] * BLOCK)
    assert got == [1] * BLOCK and cnt == BLOCK and az == 0, (got, cnt, az)
    # all -1
    got, cnt, az = await drive(dut, [0b10] * BLOCK)
    assert got == [1] * BLOCK and cnt == BLOCK and az == 0, (got, cnt, az)
    # mixed: alternating +1 / 0
    codes = [0b01 if i % 2 == 0 else 0b00 for i in range(BLOCK)]
    got, cnt, az = await drive(dut, codes)
    assert got == active_ref(codes) and cnt == BLOCK // 2 and az == 0, (got, cnt, az)
    dut._log.info("zero_skip_dispatcher corner_blocks ok")


@cocotb.test()
async def exhaustive_all_blocks(dut):
    """Exhaustive over all 4^8 = 65536 weight blocks."""
    n = 0
    for code in range(4 ** BLOCK):
        codes = [(code >> (i * 2)) & 0b11 for i in range(BLOCK)]
        got, cnt, az = await drive(dut, codes)
        ref = active_ref(codes)
        assert got == ref, f"block {codes}: mask {ref} got {got}"
        assert cnt == sum(ref), f"block {codes}: count {sum(ref)} got {cnt}"
        assert az == (1 if sum(ref) == 0 else 0), f"block {codes}: all_zero wrong"
        n += 1
    dut._log.info(f"zero_skip_dispatcher exhaustive: {n} blocks ok")
    assert n == 4 ** BLOCK


@cocotb.test()
async def bitnet_distribution_power_saving(dut):
    """On the BitNet 1.58 distribution the gated fraction should be ~35%."""
    rng = random.Random(0x2605242515 & 0xFFFFFFFF)
    total = 0
    active = 0
    n_blocks = 20_000
    for _ in range(n_blocks):
        # sample weights: 0 w.p. 0.35, +1 w.p. 0.32, -1 w.p. 0.33
        codes = []
        for _ in range(BLOCK):
            r = rng.random()
            if r < 0.35:
                codes.append(ENC[0])
            elif r < 0.67:
                codes.append(ENC[+1])
            else:
                codes.append(ENC[-1])
        _, cnt, _ = await drive(dut, codes)
        active += cnt
        total += BLOCK

    gated_fraction = 1.0 - active / total
    dut._log.info(
        f"zero_skip_dispatcher: gated {gated_fraction*100:.1f}% "
        f"({total - active}/{total} PE-cycles clock-gated)"
    )
    # Expect ~0.35; allow generous tolerance for sampling noise.
    assert 0.32 < gated_fraction < 0.38, f"gated fraction {gated_fraction} off target 0.35"
