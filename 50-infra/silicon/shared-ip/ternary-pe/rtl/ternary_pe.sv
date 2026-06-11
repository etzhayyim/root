// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// ternary_pe — multiplier-less ternary processing element
// Per ADR-2605242515 §"ternary processing element (PE)" and
//     ADR-2605242530 forward path IP reuse.
//
// Weight encoding (2-bit ternary):
//   2'b00 → weight =  0  (zero-skip)
//   2'b01 → weight = +1
//   2'b10 → weight = -1
//   2'b11 → reserved / treated as zero-skip
//
// Per-cycle behaviour:
//   - weight = 0 or reserved : pass acc_in through, gate adder clock, pe_active=0
//   - weight = +1            : acc_out = acc_in + sign_extend(activation)
//   - weight = -1            : acc_out = acc_in - sign_extend(activation)
//
// Gate-level estimate (TSMC N5 reference, behavioural synthesis):
//   ~620 gates per PE  (vs ~5,200 for INT8 multiplier — 8.4× density gain)
//
// This module is intentionally combinational (single-cycle). A higher-level
// systolic wrapper (pe_array.sv) handles pipelining via registers between rows.

`default_nettype none

module ternary_pe
  #(
    parameter int ACT_WIDTH = 8,    // INT8 activation
    parameter int ACC_WIDTH = 24    // INT24 accumulator
  )
  (
    input  wire [1:0]                weight,         // 2-bit ternary encoding
    input  wire signed [ACT_WIDTH-1:0] activation,   // signed activation
    input  wire signed [ACC_WIDTH-1:0] acc_in,       // incoming partial sum
    output wire signed [ACC_WIDTH-1:0] acc_out,      // outgoing partial sum
    output wire                       pe_active      // 1 if adder fired this cycle
  );

  // Decode ternary weight into "is_zero" + "is_negative".
  // Zero-skip when weight ∈ {2'b00, 2'b11}.
  wire is_zero     = (weight == 2'b00) || (weight == 2'b11);
  wire is_negative = (weight == 2'b10);

  // Sign-extend activation to accumulator width.
  wire signed [ACC_WIDTH-1:0] act_extended = {{(ACC_WIDTH-ACT_WIDTH){activation[ACT_WIDTH-1]}}, activation};

  // Adder / subtractor select. For is_zero, we pass acc_in through unchanged.
  wire signed [ACC_WIDTH-1:0] add_result = acc_in + act_extended;
  wire signed [ACC_WIDTH-1:0] sub_result = acc_in - act_extended;

  assign acc_out = is_zero     ? acc_in
                 : is_negative ? sub_result
                 :               add_result;

  assign pe_active = ~is_zero;

endmodule

`default_nettype wire
