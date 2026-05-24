// SPDX-License-Identifier: Apache-2.0
// Per /CHARTER-RIDER.md v2.0
//
// iwakura_top — die top-level (port list + clock/reset only; internal
// instantiation is Phase 2 work per ADR-2605242515).
//
// This stub establishes the I/O contract so cocotb sims for individual
// submodules can reference consistent signal names.

`default_nettype none

module iwakura_top
  #(
    parameter int PE_ROWS         = 256,
    parameter int PE_COLS         = 256,
    parameter int SRAM_KB         = 16 * 1024,   // 16 MB
    parameter int DRAM_GB         = 2,           // 2 GB LPDDR5X-7500
    parameter int ACT_WIDTH       = 8,
    parameter int ACC_WIDTH       = 24
  )
  (
    // Clock + reset
    input  wire        clk,            // 1 GHz target
    input  wire        rst_n,

    // Host PCIe Gen4 x4 (simplified placeholder)
    input  wire [127:0] host_rx_data,
    input  wire         host_rx_valid,
    output wire [127:0] host_tx_data,
    output wire         host_tx_valid,

    // LPDDR5X PHY (simplified placeholder)
    output wire [31:0]  dram_cmd,
    output wire [31:0]  dram_addr,
    input  wire [255:0] dram_rdata,
    output wire [255:0] dram_wdata,

    // Power telemetry (per-cycle pe_active counter, Phase 2)
    output wire [31:0]  pe_active_count
  );

  // ───────────────────────────────────────────────────────────────────
  // Phase 1: stub only.  Internal modules (pe_array, zero_skip_dispatcher,
  // sram_scratch, lpddr5x_ctrl, frozen_modality_path) are instantiated
  // in Phase 2 wave.
  //
  // For now, tie outputs to safe defaults so a Verilator elaboration of
  // this stub does not produce X-prop warnings during higher-level smoke.
  // ───────────────────────────────────────────────────────────────────

  assign host_tx_data    = '0;
  assign host_tx_valid   = 1'b0;
  assign dram_cmd        = '0;
  assign dram_addr       = '0;
  assign dram_wdata      = '0;
  assign pe_active_count = '0;

  // Suppress unused warnings (Verilator-friendly).
  wire _unused_ok = &{1'b0, rst_n, host_rx_data, host_rx_valid, dram_rdata, 1'b0};

endmodule

`default_nettype wire
