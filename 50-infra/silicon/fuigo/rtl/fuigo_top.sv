// SPDX-License-Identifier: Apache-2.0
// Per /CHARTER-RIDER.md v2.0
//
// fuigo_top — die top-level (port list stub).
// Per ADR-2605242530. Internal instantiation is Phase 2 work.

`default_nettype none

module fuigo_top
  #(
    parameter int FORWARD_PE_ROWS  = 1024,
    parameter int FORWARD_PE_COLS  = 1024,
    parameter int BACKWARD_MAC     = 8192,
    parameter int HBM_GB           = 96,
    parameter int ACT_WIDTH        = 8,
    parameter int ACC_WIDTH        = 32     // wider than iwakura — training accumulates more
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
    output wire [31:0]  forward_pe_active,
    output wire [31:0]  backward_mac_active
  );

  // Phase 1: stub. Internal modules instantiated in Phase 2.
  assign libp2p_tx_valid     = 1'b0;
  assign libp2p_tx_data      = '0;
  assign cxl_tx_flit         = '0;
  assign cxl_tx_valid        = 1'b0;
  assign hbm_cmd             = '0;
  assign hbm_addr            = '0;
  assign hbm_wdata           = '0;
  assign forward_pe_active   = '0;
  assign backward_mac_active = '0;

  wire _unused_ok = &{1'b0, rst_n, libp2p_peer_id, libp2p_rx_valid, libp2p_rx_data,
                       cxl_rx_flit, cxl_rx_valid, hbm_rdata, training_start, global_step, 1'b0};

endmodule

`default_nettype wire
