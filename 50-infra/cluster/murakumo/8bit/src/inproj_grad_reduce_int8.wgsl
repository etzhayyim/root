struct InprojGradMeta {
  tokens: u32,
  dim: u32,
  inner: u32,
  _pad0: u32,
}

@group(0) @binding(0) var<storage, read> input_vals: array<i32>;
@group(0) @binding(1) var<storage, read> residual_vals: array<i32>;
@group(0) @binding(2) var<storage, read> w_out: array<i32>;
@group(0) @binding(3) var<storage, read_write> grad_vals: array<i32>;
@group(0) @binding(4) var<uniform> params: InprojGradMeta;

fn isqrt_i32(value: i32) -> i32 {
  if (value <= 0) {
    return 0;
  }
  var x: u32 = u32(value);
  var y: u32 = (x + 1u) / 2u;
  loop {
    if (y >= x) {
      break;
    }
    x = y;
    y = (x + u32(value) / x) / 2u;
  }
  return i32(x);
}

fn normed_input(token_base: u32, d: u32) -> i32 {
  var mean: i32 = 0;
  for (var i: u32 = 0u; i < params.dim; i = i + 1u) {
    mean = mean + input_vals[token_base + i];
  }
  mean = mean / i32(params.dim);
  var var_acc: i32 = 0;
  for (var i: u32 = 0u; i < params.dim; i = i + 1u) {
    let delta = input_vals[token_base + i] - mean;
    var_acc = var_acc + delta * delta;
  }
  var_acc = var_acc / i32(params.dim);
  let denom = 1 + isqrt_i32(var_acc);
  let centered = input_vals[token_base + d] - mean;
  return clamp((centered * 32) / denom, -128, 127);
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let idx = gid.x;
  let total = params.inner * 2u * params.dim;
  if (idx >= total) {
    return;
  }
  let row = idx / params.dim;
  let d = idx % params.dim;
  let j = row % params.inner;
  let gate_scale = select(1, 2, row < params.inner);

  var acc: i32 = 0;
  for (var t: u32 = 0u; t < params.tokens; t = t + 1u) {
    let token_base = t * params.dim;
    let normed = normed_input(token_base, d);
    var hidden_res: i32 = 0;
    for (var o: u32 = 0u; o < params.dim; o = o + 1u) {
      hidden_res = hidden_res + ((residual_vals[token_base + o] * w_out[o * params.inner + j]) >> 6);
    }
    acc = acc + (((hidden_res / gate_scale) * normed) >> 12);
  }
  grad_vals[idx] = acc;
}
