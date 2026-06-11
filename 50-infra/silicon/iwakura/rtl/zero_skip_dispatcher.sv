// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// zero_skip_dispatcher — dynamic-power clock-gating decision for a weight block.
// Per ADR-2605242515 §"Zero-skip dispatcher (動的電力削減)".
//
// BitNet 1.58 post-training weight distribution is ~{0: 35%, +1: 32%, -1: 33%}.
// A weight of 0 (encoding 2'b00) or reserved (2'b11) contributes nothing to the
// dot product, so its PE's adder can be clock-gated for that cycle — saving the
// ~35% dynamic switching power those columns would otherwise burn.
//
// Given BLOCK ternary weights this module emits, combinationally:
//   - clk_en[i]    : 1 ⇒ weight i is ±1 → distribute the clock to PE i
//                    0 ⇒ weight i is zero-skip → gate PE i's adder this cycle
//   - active_count : popcount(clk_en)         (for the power-telemetry counter)
//   - all_zero     : 1 ⇒ the whole block is zero-skip (the entire row of adders
//                    can be gated and the accumulators simply pass through)
//
// The PE itself already passes acc_in through on a zero weight (ternary_pe), so
// clk_en is a *power* optimization, not a *functional* one: gating a PE whose
// weight is zero cannot change the numerical result. That invariant is what the
// cocotb test pins down.

`default_nettype none

module zero_skip_dispatcher
  #(
    parameter int BLOCK = 8     // weights dispatched per cycle (ADR: 8-wide pre-fetch)
  )
  (
    input  wire [BLOCK*2-1:0]          weights,       // BLOCK ternary weights, 2-bit each
    output wire [BLOCK-1:0]            clk_en,        // per-PE clock enable (1 = active)
    output wire [$clog2(BLOCK+1)-1:0]  active_count,  // popcount(clk_en)
    output wire                        all_zero       // 1 if no PE is active
  );

  // A weight is "active" iff it is +1 (2'b01) or -1 (2'b10).
  // Zero (2'b00) and reserved (2'b11) are zero-skip.
  genvar i;
  generate
    for (i = 0; i < BLOCK; i++) begin : g_mask
      wire [1:0] w = weights[i*2 +: 2];
      assign clk_en[i] = (w == 2'b01) || (w == 2'b10);
    end
  endgenerate

  // Population count of the enable mask.
  localparam int CNTW = $clog2(BLOCK + 1);
  reg [CNTW-1:0] cnt;
  integer k;
  always @(*) begin
    cnt = '0;
    for (k = 0; k < BLOCK; k++)
      cnt = cnt + (clk_en[k] ? (CNTW)'(1) : (CNTW)'(0));
  end
  assign active_count = cnt;

  assign all_zero = (clk_en == {BLOCK{1'b0}});

endmodule

`default_nettype wire
