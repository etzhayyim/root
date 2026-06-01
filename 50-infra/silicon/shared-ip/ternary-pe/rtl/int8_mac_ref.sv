// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// int8_mac_ref — reference INT8-multiplier MAC cell (the conventional NPU PE).
//
// This is NOT a shipped iwakura cell. It exists solely as the apples-to-apples
// synthesis baseline for the ternary_pe density comparison in
// ADR-2605242515 §"面積 (gate-level estimate)":
//   conventional INT8-multiplier PE  ~5,200 gates
//   iwakura ternary PE (multiplier-less)  ~620 gates  → 8.4× density
//
// Same I/O contract as ternary_pe except the weight is a full signed INT8:
//   acc_out = acc_in + weight * activation
// so a yosys `stat` on both, under the same synth flow, measures exactly the
// silicon cost of the multiplier that BitNet 1.58 lets us delete.

`default_nettype none

module int8_mac_ref
  #(
    parameter int ACT_WIDTH = 8,    // INT8 activation (matches ternary_pe)
    parameter int W_WIDTH   = 8,    // INT8 weight (the multiplier this costs)
    parameter int ACC_WIDTH = 24    // INT24 accumulator (matches ternary_pe)
  )
  (
    input  wire signed [W_WIDTH-1:0]   weight,      // full INT8 weight
    input  wire signed [ACT_WIDTH-1:0] activation,
    input  wire signed [ACC_WIDTH-1:0] acc_in,
    output wire signed [ACC_WIDTH-1:0] acc_out,
    output wire                        pe_active
  );

  // The multiplier — this is the logic ternary weights make unnecessary.
  wire signed [W_WIDTH+ACT_WIDTH-1:0] product = weight * activation;

  wire signed [ACC_WIDTH-1:0] product_ext =
      {{(ACC_WIDTH-(W_WIDTH+ACT_WIDTH)){product[W_WIDTH+ACT_WIDTH-1]}}, product};

  assign acc_out   = acc_in + product_ext;
  assign pe_active = (weight != '0);

endmodule

`default_nettype wire
