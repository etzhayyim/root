// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// pe_array — weight-stationary ternary matrix-vector engine.
// Per ADR-2605242515 §"ternary processing element (PE)" + §Phase-1 scope
// ("pe_array.sv — PE grid, generate-for で配線").
//
// Computes  y[r] = Σ_c  W[r][c] · a[c]      (r ∈ 0..ROWS-1, c ∈ 0..COLS-1)
//   W[r][c] : 2-bit ternary weight  ({-1,0,+1}, ternary_pe encoding)
//   a[c]    : signed INT8 activation
//   y[r]    : signed INT(ACC_WIDTH) dot product
//
// Dataflow (weight-stationary, column-streamed):
//   ROWS dot-product lanes run in parallel, one per output element.
//   Each cycle k presents the scalar activation a[k] on a shared bus; every
//   lane r selects its own weight W[r][k] and performs one ternary_pe step:
//       acc[r] <= acc[r] + W[r][k]·a[k]
//   After COLS cycles each lane holds the full dot product and `done` pulses.
//   This is the time-multiplexed form of a systolic column; it reuses the
//   canonical ternary_pe unchanged (one instance per lane — shared IP, no fork).
//
//   The accumulator for column 0 is forced to zero (acc_in = 0 when col == 0),
//   so each matrix-vector op is independent of the previous one with no
//   explicit clear cycle. `col` returns to 0 between ops (idle invariant).
//
// Zero-skip: ternary_pe.pe_active is 0 whenever W[r][k] ∈ {0, reserved}, so
// the summed pe_active across the op is the true MAC count — the dynamic-power
// telemetry the zero_skip_dispatcher and iwakura_top consume.
//
// Latency: COLS cycles from the `start` pulse to the `done` pulse
//          (1 cycle when COLS == 1).

`default_nettype none

module pe_array
  #(
    parameter int ROWS      = 4,
    parameter int COLS      = 4,
    parameter int ACT_WIDTH = 8,
    parameter int ACC_WIDTH = 24,
    // Phase-2 zero-skip clock gating. When 1, a zero_skip_dispatcher over the
    // current column's weights produces a per-lane accumulator write-enable, so
    // a zero-weight lane's register is not clocked (dynamic-power saving). The
    // numerical result is bit-identical to CLOCK_GATE=0 — gating a zero-weight
    // PE cannot change the sum. Default 0 keeps the Phase-1 behaviour exactly.
    parameter bit CLOCK_GATE = 0
  )
  (
    input  wire                              clk,
    input  wire                              rst_n,

    // Begin a new matrix-vector op. weights_flat/activations_flat must stay
    // stable from this pulse until `done`.
    input  wire                              start,

    // W[r][c] at bit offset ((r*COLS)+c)*2, 2 bits each, ternary_pe encoding.
    input  wire [ROWS*COLS*2-1:0]            weights_flat,
    // a[c] at bit offset c*ACT_WIDTH, signed INT8.
    input  wire [COLS*ACT_WIDTH-1:0]         activations_flat,

    output reg                               done,           // 1-cycle pulse when y valid
    output wire                              busy,            // high while streaming columns
    output reg  signed [ROWS*ACC_WIDTH-1:0]  y_flat,          // y[r] at r*ACC_WIDTH
    output reg  [31:0]                       pe_active_count, // Σ pe_active this op (telemetry)
    output reg  [31:0]                       acc_write_count  // Σ accumulator register writes
  );

  // Column counter: which column is being streamed (combinationally) this cycle.
  // One extra bit so the value COLS (== COLS-1 + 1) never overflows the field.
  localparam int CW = (COLS <= 1) ? 1 : $clog2(COLS);
  reg  [CW:0] col;          // idle invariant: col == 0 whenever !running
  reg         running;
  assign busy = running;

  wire        col_is_zero = (col == '0);
  wire        col_is_last = (col == (CW+1)'(COLS-1));

  // Per-lane accumulator registers.
  reg signed [ACC_WIDTH-1:0] acc [ROWS];

  // Shared activation bus for the current column (variable part-select).
  wire signed [ACT_WIDTH-1:0] act_k =
      $signed(activations_flat[(32'(col))*ACT_WIDTH +: ACT_WIDTH]);

  // Per-lane combinational PE outputs for the current column.
  wire signed [ACC_WIDTH-1:0] acc_out_lane [ROWS];
  wire                        pe_active_lane [ROWS];
  // Current column's weights assembled into one bus (for the dispatcher).
  // Consumed only in the CLOCK_GATE=1 generate branch below.
  /* verilator lint_off UNUSEDSIGNAL */
  wire [ROWS*2-1:0]           col_weights;
  /* verilator lint_on UNUSEDSIGNAL */

  genvar r;
  generate
    for (r = 0; r < ROWS; r++) begin : g_lane
      // W[r][col] — variable part-select, base = ((r*COLS)+col)*2.
      wire [1:0] w_rk = weights_flat[((r*COLS) + 32'(col))*2 +: 2];
      assign col_weights[r*2 +: 2] = w_rk;
      // acc_in is 0 on column 0 (op-independent start), else the running sum.
      wire signed [ACC_WIDTH-1:0] acc_in_lane = col_is_zero ? '0 : acc[r];

      ternary_pe #(
        .ACT_WIDTH (ACT_WIDTH),
        .ACC_WIDTH (ACC_WIDTH)
      ) u_pe (
        .weight     (w_rk),
        .activation (act_k),
        .acc_in     (acc_in_lane),
        .acc_out    (acc_out_lane[r]),
        .pe_active  (pe_active_lane[r])
      );
    end
  endgenerate

  // Per-lane accumulator write-enable. With CLOCK_GATE, a zero_skip_dispatcher
  // over the current column gates writes for zero-weight lanes — except on
  // column 0, where every lane must write to establish the (zeroed) base.
  wire [ROWS-1:0] lane_we;
  generate
    if (CLOCK_GATE) begin : g_cg
      wire [ROWS-1:0]            zsd_en;
      wire [$clog2(ROWS+1)-1:0]  zsd_cnt;
      wire                       zsd_allzero;
      zero_skip_dispatcher #(.BLOCK(ROWS)) u_zsd (
        .weights      (col_weights),
        .clk_en       (zsd_en),
        .active_count (zsd_cnt),
        .all_zero     (zsd_allzero)
      );
      assign lane_we = col_is_zero ? {ROWS{1'b1}} : zsd_en;
    end else begin : g_nocg
      assign lane_we = {ROWS{1'b1}};   // Phase-1: every lane writes every cycle
    end
  endgenerate

  // Population count of lanes that will write this cycle.
  integer m;
  reg [31:0] writes_this_cycle;
  always @(*) begin
    writes_this_cycle = 32'd0;
    for (m = 0; m < ROWS; m++)
      writes_this_cycle = writes_this_cycle + (lane_we[m] ? 32'd1 : 32'd0);
  end

  // Population count of lanes that fired this cycle.
  integer i;
  reg [31:0] active_this_cycle;
  always @(*) begin
    active_this_cycle = 32'd0;
    for (i = 0; i < ROWS; i++)
      active_this_cycle = active_this_cycle + (pe_active_lane[i] ? 32'd1 : 32'd0);
  end

  integer j;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      running         <= 1'b0;
      done            <= 1'b0;
      col             <= '0;
      pe_active_count <= '0;
      acc_write_count <= '0;
      y_flat          <= '0;
      for (j = 0; j < ROWS; j++) acc[j] <= '0;
    end else begin
      done <= 1'b0;  // done is a 1-cycle pulse by default

      if (!running) begin
        // Idle (col == 0 invariant). Latch column 0 when start fires.
        if (start) begin
          pe_active_count <= active_this_cycle;
          acc_write_count <= writes_this_cycle;
          // Per-lane gated write (lane_we is all-1 on col 0, so every lane
          // writes its zeroed base here regardless of CLOCK_GATE).
          for (j = 0; j < ROWS; j++)
            if (lane_we[j]) acc[j] <= acc_out_lane[j];
          if (COLS == 1) begin
            done <= 1'b1;                       // single-column op finishes now
            col  <= '0;
            for (j = 0; j < ROWS; j++)
              y_flat[j*ACC_WIDTH +: ACC_WIDTH] <= acc_out_lane[j];
          end else begin
            running <= 1'b1;
            col     <= (CW+1)'(1);
          end
        end
      end else begin
        // Streaming. This cycle accumulated column `col`.
        pe_active_count <= pe_active_count + active_this_cycle;
        acc_write_count <= acc_write_count + writes_this_cycle;
        for (j = 0; j < ROWS; j++)
          if (lane_we[j]) acc[j] <= acc_out_lane[j];
        if (col_is_last) begin
          running <= 1'b0;
          col     <= '0;                        // restore idle invariant
          done    <= 1'b1;
          // y must reflect the final value for EVERY lane, including gated
          // ones: a gated lane held acc[j], so publish acc_out_lane[j] when it
          // wrote, else the held acc[j].
          for (j = 0; j < ROWS; j++)
            y_flat[j*ACC_WIDTH +: ACC_WIDTH] <= lane_we[j] ? acc_out_lane[j] : acc[j];
        end else begin
          col <= col + (CW+1)'(1);
        end
      end
    end
  end

endmodule

`default_nettype wire
