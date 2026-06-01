// SPDX-License-Identifier: Apache-2.0
// Per /CHARTER-RIDER.md v2.0
//
// iwakura_top — die top-level.
//
// Phase 1 (this commit): the ternary compute tile is now a *live* integration
// of verified IP, not a stub:
//   - pe_array            (weight-stationary ternary matrix-vector engine)
//   - zero_skip_dispatcher (per-block clock-gate decision + activity estimate)
// exposed through a clean direct-compute interface (weights/activations/start/
// done/y) so cocotb can drive the integrated datapath end to end.
//
// Still Phase-2 (placeholders, tied to safe defaults below):
//   - PCIe Gen4 x4 host DMA  → compute-tile feed/drain
//   - LPDDR5X-7500 controller + radix3 weight unpacker → on-die SRAM
//   - frozen modality encoder hard-wired path
// The PHY↔tile DMA path (host_rx/dram_* ↔ weights_flat/activations_flat) lands
// in the Phase-2 wave (ADR-2605242515 §Phase-2).

`default_nettype none

module iwakura_top
  #(
    // Full-die spec parameters (target array geometry). The Phase-1 commit
    // instantiates only the TILE_ROWS×TILE_COLS compute tile below; these
    // describe the Phase-3 tape-out die and are consumed when the full PE
    // grid + SRAM/DRAM controllers land in Phase 2.
    /* verilator lint_off UNUSEDPARAM */
    parameter int PE_ROWS         = 256,
    parameter int PE_COLS         = 256,
    parameter int SRAM_KB         = 16 * 1024,   // 16 MB
    parameter int DRAM_GB         = 2,           // 2 GB LPDDR5X-7500
    /* verilator lint_on UNUSEDPARAM */
    parameter int ACT_WIDTH       = 8,
    parameter int ACC_WIDTH       = 24,
    // Phase-1 instantiated compute tile (a sub-grid of the full PE_ROWS×PE_COLS
    // array; kept small so Verilator elaboration + cocotb stay fast).
    parameter int TILE_ROWS       = 4,
    parameter int TILE_COLS       = 4
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

    // ── Phase-1 direct-compute interface (clean tile API) ──────────────────
    input  wire                              tile_start,
    input  wire [TILE_ROWS*TILE_COLS*2-1:0]  tile_weights_flat,
    input  wire [TILE_COLS*ACT_WIDTH-1:0]    tile_activations_flat,
    output wire                              tile_done,
    output wire                              tile_busy,
    output wire signed [TILE_ROWS*ACC_WIDTH-1:0] tile_y_flat,

    // Power telemetry: live per-op active-PE count from the compute tile.
    output wire [31:0]  pe_active_count
  );

  // ── Ternary compute tile (live) ──────────────────────────────────────────
  pe_array #(
    .ROWS      (TILE_ROWS),
    .COLS      (TILE_COLS),
    .ACT_WIDTH (ACT_WIDTH),
    .ACC_WIDTH (ACC_WIDTH)
  ) u_tile (
    .clk              (clk),
    .rst_n            (rst_n),
    .start            (tile_start),
    .weights_flat     (tile_weights_flat),
    .activations_flat (tile_activations_flat),
    .done             (tile_done),
    .busy             (tile_busy),
    .y_flat           (tile_y_flat),
    .pe_active_count  (pe_active_count),
    .acc_write_count  (tile_acc_writes)
  );
  wire [31:0] tile_acc_writes;  // Phase-1: telemetry not yet surfaced off-die

  // ── Zero-skip pre-decode for the first weight column (activity estimate) ──
  // Wires the dispatcher into the integration: it reports, combinationally, how
  // many PEs in column 0 will fire — the pre-fetch activity estimate the ADR's
  // dispatcher provides to the power manager. (Full per-column gate wiring is
  // Phase-2.) Exposed via host_tx_data so a smoke test can observe it.
  wire [TILE_ROWS-1:0]            col0_clk_en;
  wire [$clog2(TILE_ROWS+1)-1:0]  col0_active;
  wire                           col0_all_zero;
  zero_skip_dispatcher #(
    .BLOCK (TILE_ROWS)
  ) u_dispatch (
    .weights      (tile_weights_flat[TILE_ROWS*2-1:0]),  // column 0 weights of each row's slot
    .clk_en       (col0_clk_en),
    .active_count (col0_active),
    .all_zero     (col0_all_zero)
  );

  // ── Phase-2 placeholders (safe defaults; no X-prop during smoke) ──────────
  // host_tx low byte carries the column-0 activity estimate; bit 8 = all_zero.
  wire [7:0] tx_active8 = 8'(col0_active);
  assign host_tx_data  = {119'b0, col0_all_zero, tx_active8};  // 119 + 1 + 8 = 128
  assign host_tx_valid = tile_done;
  assign dram_cmd      = '0;
  assign dram_addr     = '0;
  assign dram_wdata    = '0;

  // Suppress unused warnings (Verilator-friendly).
  wire _unused_ok = &{1'b0, host_rx_data, host_rx_valid, dram_rdata, col0_clk_en,
                      tile_acc_writes, 1'b0};

endmodule

`default_nettype wire
