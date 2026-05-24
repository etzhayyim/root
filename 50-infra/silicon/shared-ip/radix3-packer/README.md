# shared-ip/radix3-packer — 5-ternary-per-byte weight packing

Per **ADR-2605242515** §"radix-3 weight packing convention".

Naive 2-bit packing yields 4 weights per byte. Radix-3 packing
(3⁵ = 243 < 256) yields **5 weights per byte = 25% memory bandwidth
saving**.

Both iwakura DRAM controller and fuigo HBM controller decode wire-level
radix-3 bytes into pairs of 2-bit ternary weights for the PE array.

## Encode

```
encode(w0, w1, w2, w3, w4):    # each w_i ∈ {-1, 0, +1}
    code = 0
    for w in [w4, w3, w2, w1, w0]:
        code = code * 3 + (w + 1)
    return code                  # 0..242, fits in 1 byte
```

## Decode (hardware)

A small ROM-based divider (5-stage unrolled) produces 5 ternary weights
per cycle. Stage-i computes `(code / 3^i) mod 3 - 1`. Implementation is
combinational; latency 0 (purely wire-level once `code` is registered).

## Phase 1 scope

`rtl/radix3_decoder.sv` (Phase 2) — combinational decoder.
This README placeholder for now.
