// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// sram_scratch — behavioural on-die SRAM scratch wrapper.
// Per ADR-2605242515 §"Memory hierarchy" (16 MB on-die SRAM: activation +
// KV-cache scratch).
//
// This is a *behavioural* single-port synchronous RAM model: synthesizable
// (infers block RAM on FPGA, maps to a compiled SRAM macro at tape-out), with a
// 1-cycle registered read. It is NOT a foundry SRAM macro or PHY (those are NDA
// IP, out of this tree per 50-infra/silicon/CLAUDE.md rule 5) — it models the
// timing/interface so the compute tile + controller can be simulated together.
//
// Depth/width are parameterized small for simulation; the iwakura-1 die targets
// 16 MB total (banked).

`default_nettype none

module sram_scratch
  #(
    parameter int ADDR_W = 8,            // 2^ADDR_W words
    parameter int DATA_W = 64            // word width (bits)
  )
  (
    input  wire               clk,
    input  wire               rst_n,

    // Write port
    input  wire               we,
    input  wire [ADDR_W-1:0]  waddr,
    input  wire [DATA_W-1:0]  wdata,

    // Read port (1-cycle registered latency)
    input  wire               re,
    input  wire [ADDR_W-1:0]  raddr,
    output reg  [DATA_W-1:0]  rdata,
    output reg                rvalid       // asserted the cycle rdata is valid
  );

  localparam int DEPTH = (1 << ADDR_W);
  reg [DATA_W-1:0] mem [DEPTH];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      rdata  <= '0;
      rvalid <= 1'b0;
    end else begin
      if (we) mem[waddr] <= wdata;
      // Read is registered; on a write-read address collision this returns the
      // OLD contents (read-first), the conservative behaviour for scratch use.
      rdata  <= mem[raddr];
      rvalid <= re;
    end
  end

endmodule

`default_nettype wire
