// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 etzhayyim religious-corp
// Subject to /CHARTER-RIDER.md v2.0 (Apache 2.0 + etzhayyim Charter Compliance Rider).
//
// radix3_decoder — wire-level 5-ternary-per-byte unpacker.
// Per ADR-2605242515 §"radix-3 weight packing convention" and
//     shared-ip/radix3-packer/README.md.
//
// A byte holds 5 ternary weights because 3^5 = 243 < 256.
//   encode(w0..w4): code = Σ_i (w_i + 1) · 3^i        (w_i ∈ {-1,0,+1})
//   decode(code):   w_i  = ((code / 3^i) mod 3) − 1
//
// This decoder is purely combinational. It emits each unpacked weight in the
// 2-bit ternary encoding consumed by ternary_pe:
//   weight = 0  → 2'b00
//   weight = +1 → 2'b01
//   weight = −1 → 2'b10
// (ternary_pe treats 2'b11 as zero-skip; this decoder never emits it.)
//
// Inputs whose byte value is in the reserved range 243..255 are clamped to the
// all-zero weight vector and flagged via `code_valid = 0`, so a malformed
// weight stream degrades to a zero-skip (no spurious accumulate) rather than
// producing out-of-range trits.

`default_nettype none

module radix3_decoder
  (
    input  wire [7:0]  code,        // packed radix-3 byte (valid 0..242)
    output wire [1:0]  w0,          // least-significant trit (3^0)
    output wire [1:0]  w1,          // 3^1
    output wire [1:0]  w2,          // 3^2
    output wire [1:0]  w3,          // 3^3
    output wire [1:0]  w4,          // most-significant trit (3^4)
    output wire        code_valid   // 1 iff code <= 242
  );

  // A code in 243..255 is not a legal radix-3 packing of 5 trits.
  wire valid = (code <= 8'd242);

  // Successive division by 3. Each stage takes the running quotient and
  // produces (quotient mod 3) as the next trit's {0,1,2} digit, plus the
  // next quotient. Widths shrink because the maximum value shrinks by /3.
  //   q0 in 0..242, q1 in 0..80, q2 in 0..26, q3 in 0..8, q4 in 0..2
  // The 2-bit casts `2'(...)` are explicit: a mod-3 result is always 0..2, so
  // the truncation is lossless, but Verilator (correctly) demands we say so.
  wire [7:0] q0 = code;
  wire [1:0] d0 = 2'(q0 % 8'd3);  wire [7:0] q1 = q0 / 8'd3;
  wire [1:0] d1 = 2'(q1 % 8'd3);  wire [7:0] q2 = q1 / 8'd3;
  wire [1:0] d2 = 2'(q2 % 8'd3);  wire [7:0] q3 = q2 / 8'd3;
  wire [1:0] d3 = 2'(q3 % 8'd3);  wire [7:0] q4 = q3 / 8'd3;
  wire [1:0] d4 = 2'(q4 % 8'd3);

  // Map ternary digit {0,1,2} (= weight {-1,0,+1}) → ternary_pe 2-bit encoding.
  //   digit 0 → weight −1 → 2'b10
  //   digit 1 → weight  0 → 2'b00
  //   digit 2 → weight +1 → 2'b01
  function automatic [1:0] digit_to_pe(input [1:0] d);
    case (d)
      2'd0:    digit_to_pe = 2'b10;  // −1
      2'd1:    digit_to_pe = 2'b00;  //  0
      2'd2:    digit_to_pe = 2'b01;  // +1
      default: digit_to_pe = 2'b00;  // unreachable (d ∈ 0..2)
    endcase
  endfunction

  // On an invalid byte, force all weights to zero (zero-skip) so the PE array
  // does not accumulate garbage; surface the condition via code_valid.
  assign w0 = valid ? digit_to_pe(d0) : 2'b00;
  assign w1 = valid ? digit_to_pe(d1) : 2'b00;
  assign w2 = valid ? digit_to_pe(d2) : 2'b00;
  assign w3 = valid ? digit_to_pe(d3) : 2'b00;
  assign w4 = valid ? digit_to_pe(d4) : 2'b00;
  assign code_valid = valid;

endmodule

`default_nettype wire
