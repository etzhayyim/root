// SPDX-License-Identifier: Apache-2.0
// Per /CHARTER-RIDER.md v2.0
//
// fuigo_top — die top-level (hybrid forward-ternary / backward-BF16 training ASIC).
// Per ADR-2605242530.
//
// Phase 1 (this commit): the **forward systolic array reuses the shared
// ternary-pe IP** via pe_array — exactly the ADR-2605242530 §"Phase 1
// deliverable = ... forward path は ternary-pe IP 再利用" item. The forward
// path is now a live, verified datapath (identical engine to iwakura, no fork),
// exposed through a clean direct-compute interface.
//
// Still Phase-2 (placeholders, safe defaults below):
//   - backward BF16 systolic array (the FP unit fuigo adds over iwakura)
//   - HBM3e PHY + controller, CXL.mem endpoint, libp2p NIC control plane
// Backward BF16 is deliberately out of Phase-1 scope (it is the part fuigo does
// NOT share with iwakura); forward-path IP reuse is the verifiable deliverable.

`default_nettype none

module fuigo_top
  #(
    // Full-die spec parameters (consumed when the full forward/backward arrays
    // + HBM land in Phase 2). Phase 1 instantiates only the FWD_TILE below.
    /* verilator lint_off UNUSEDPARAM */
    parameter int FORWARD_PE_ROWS  = 1024,
    parameter int FORWARD_PE_COLS  = 1024,
    parameter int BACKWARD_MAC     = 8192,
    parameter int HBM_GB           = 96,
    /* verilator lint_on UNUSEDPARAM */
    parameter int ACT_WIDTH        = 8,
    parameter int ACC_WIDTH        = 32,    // wider than iwakura — training accumulates more
    // Phase-1 instantiated forward tile (sub-grid of the full forward array).
    parameter int FWD_TILE_ROWS    = 4,
    parameter int FWD_TILE_COLS    = 4
  )
  (
    input  wire        clk,                 // 1 GHz target
    input  wire        rst_n,

    // libp2p NIC (peer-id register accessible via control plane)
    input  wire [255:0] libp2p_peer_id,     // burned at tape-out per lot
    input  wire         libp2p_rx_valid,
    input  wire [255:0] libp2p_rx_data,
    output wire         libp2p_tx_valid,
    output wire [255:0] libp2p_tx_data,

    // CXL.mem 3.0 endpoint (simplified placeholder)
    input  wire [63:0]  cxl_rx_flit,
    input  wire         cxl_rx_valid,
    output wire [63:0]  cxl_tx_flit,
    output wire         cxl_tx_valid,

    // HBM3e PHY (simplified placeholder)
    output wire [63:0]  hbm_cmd,
    output wire [63:0]  hbm_addr,
    input  wire [1023:0] hbm_rdata,
    output wire [1023:0] hbm_wdata,

    // Training control plane
    input  wire         training_start,
    input  wire [31:0]  global_step,

    // ── Phase-1 forward-path direct-compute interface (shared ternary-pe IP) ──
    input  wire                                      fwd_start,
    input  wire [FWD_TILE_ROWS*FWD_TILE_COLS*2-1:0]  fwd_weights_flat,
    input  wire [FWD_TILE_COLS*ACT_WIDTH-1:0]        fwd_activations_flat,
    output wire                                      fwd_done,
    output wire                                      fwd_busy,
    output wire signed [FWD_TILE_ROWS*ACC_WIDTH-1:0] fwd_y_flat,

    output wire [31:0]  forward_pe_active,           // live forward MAC telemetry
    output wire [31:0]  backward_mac_active          // Phase-2 (placeholder)
  );

  // ── Forward systolic array: shared ternary-pe IP (no fork) ────────────────
  pe_array #(
    .ROWS      (FWD_TILE_ROWS),
    .COLS      (FWD_TILE_COLS),
    .ACT_WIDTH (ACT_WIDTH),
    .ACC_WIDTH (ACC_WIDTH)
  ) u_forward (
    .clk              (clk),
    .rst_n            (rst_n),
    .start            (fwd_start),
    .weights_flat     (fwd_weights_flat),
    .activations_flat (fwd_activations_flat),
    .done             (fwd_done),
    .busy             (fwd_busy),
    .y_flat           (fwd_y_flat),
    .pe_active_count  (forward_pe_active),
    .acc_write_count  (fwd_acc_writes)
  );
  wire [31:0] fwd_acc_writes;  // Phase-1: telemetry not yet surfaced off-die

  // ── Phase-2 placeholders (safe defaults) ──────────────────────────────────
  assign backward_mac_active = '0;            // backward BF16 array — Phase 2
  assign libp2p_tx_valid     = 1'b0;
  assign libp2p_tx_data      = '0;
  assign cxl_tx_flit         = '0;
  assign cxl_tx_valid        = 1'b0;
  assign hbm_cmd             = '0;
  assign hbm_addr            = '0;
  assign hbm_wdata           = '0;

  // Suppress unused warnings (Verilator-friendly). FORWARD_PE_*/BACKWARD_MAC/
  // HBM_GB are full-die spec params consumed when the full array lands (Phase 2).
  /* verilator lint_off UNUSEDSIGNAL */
  wire _unused_ok = &{1'b0, libp2p_peer_id, libp2p_rx_valid, libp2p_rx_data,
                       cxl_rx_flit, cxl_rx_valid, hbm_rdata, training_start, global_step,
                       fwd_acc_writes, 1'b0};
  /* verilator lint_on UNUSEDSIGNAL */

endmodule

`default_nettype wire
