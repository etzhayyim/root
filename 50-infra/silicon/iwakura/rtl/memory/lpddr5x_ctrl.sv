// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// lpddr5x_ctrl — behavioural LPDDR5X controller + on-die radix-3 weight unpacker.
// Per ADR-2605242515 §"Memory hierarchy" + §"radix-3 weight packing convention"
// ("iwakura の DRAM controller + on-die unpacker が wire-level で radix-3 →
// 2-bit { weight pairs } に展開する").
//
// SCOPE (50-infra/silicon/CLAUDE.md rule 5): this is the *controller behavioural
// model* only — NO LPDDR5X PHY RTL (that is foundry IP under NDA). It models:
//   - a byte-addressable packed-weight backing store (sim: preloadable)
//   - a fixed read latency pipeline (stand-in for DRAM CAS + bus latency)
//   - the on-die radix-3 unpacker: each fetched byte → 5 ternary weights in the
//     ternary_pe 2-bit encoding (reuses shared-ip/radix3-packer/radix3_decoder)
//
// A weight fetch therefore returns 5 PE-ready weights per byte — the 25%
// bandwidth saving the ADR's packing convention buys.

`default_nettype none

module lpddr5x_ctrl
  #(
    parameter int ADDR_W  = 10,          // byte address space (2^ADDR_W bytes)
    parameter int LATENCY = 4            // modelled read latency in cycles (>=1)
  )
  (
    input  wire               clk,
    input  wire               rst_n,

    // Backing-store preload port (simulation/bring-up: load packed bytes).
    input  wire               ld_we,
    input  wire [ADDR_W-1:0]  ld_addr,
    input  wire [7:0]         ld_byte,

    // Weight-fetch command: read the radix-3 byte at cmd_addr, unpack 5 weights.
    input  wire               cmd_valid,
    input  wire [ADDR_W-1:0]  cmd_addr,

    // Response (LATENCY cycles after an accepted command).
    output reg                rsp_valid,
    output reg  [1:0]         w0,
    output reg  [1:0]         w1,
    output reg  [1:0]         w2,
    output reg  [1:0]         w3,
    output reg  [1:0]         w4,
    output reg                rsp_code_valid    // 0 if the byte was a reserved code
  );

  localparam int DEPTH = (1 << ADDR_W);
  reg [7:0] store [DEPTH];

  // Latency pipeline: a shift register of (valid, addr). Stage 0 is the cycle a
  // command is accepted; the read+decode happens when it reaches stage LATENCY-1.
  reg              vpipe [LATENCY];
  reg [ADDR_W-1:0] apipe [LATENCY];

  // Combinational radix-3 decode of the byte arriving at the pipeline tail.
  wire [7:0] tail_byte = store[apipe[LATENCY-1]];
  wire [1:0] dw0, dw1, dw2, dw3, dw4;
  wire       dcv;
  radix3_decoder u_dec (
    .code       (tail_byte),
    .w0         (dw0), .w1 (dw1), .w2 (dw2), .w3 (dw3), .w4 (dw4),
    .code_valid (dcv)
  );

  integer s;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rsp_valid      <= 1'b0;
      rsp_code_valid <= 1'b0;
      {w0, w1, w2, w3, w4} <= '0;
      for (s = 0; s < LATENCY; s++) begin
        vpipe[s] <= 1'b0;
        apipe[s] <= '0;
      end
    end else begin
      if (ld_we) store[ld_addr] <= ld_byte;

      // Advance the latency pipeline.
      vpipe[0] <= cmd_valid;
      apipe[0] <= cmd_addr;
      for (s = 1; s < LATENCY; s++) begin
        vpipe[s] <= vpipe[s-1];
        apipe[s] <= apipe[s-1];
      end

      // Emit the decoded weights when a command reaches the tail.
      rsp_valid <= vpipe[LATENCY-1];
      if (vpipe[LATENCY-1]) begin
        w0 <= dw0; w1 <= dw1; w2 <= dw2; w3 <= dw3; w4 <= dw4;
        rsp_code_valid <= dcv;
      end
    end
  end

endmodule

`default_nettype wire
