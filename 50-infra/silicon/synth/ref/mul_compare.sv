// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// Multiplier-only density micro-comparison for ADR-2605242515 §"面積".
// These are synthesis reference cells, NOT shipped iwakura RTL. They isolate
// the *multiplier block* that BitNet 1.58 ternary weights eliminate, separately
// from the 24-bit accumulator both PE styles share.

`default_nettype none

// Conventional NPU multiply: full signed 8×8 → 16-bit product.
module mul8x8
  (
    input  wire signed [7:0]  a,
    input  wire signed [7:0]  b,
    output wire signed [15:0] p
  );
  assign p = a * b;
endmodule

// Ternary "multiply": select 0 / +a / −a by the 2-bit weight (no multiplier).
//   2'b00 / 2'b11 → 0,  2'b01 → +a,  2'b10 → −a   (ternary_pe encoding)
module ternary_mul
  (
    input  wire [1:0]         w,
    input  wire signed [7:0]  a,
    output wire signed [15:0] p
  );
  wire is_zero = (w == 2'b00) || (w == 2'b11);
  wire is_neg  = (w == 2'b10);
  wire signed [15:0] ax = {{8{a[7]}}, a};
  assign p = is_zero ? 16'sd0 : (is_neg ? -ax : ax);
endmodule

`default_nettype wire
