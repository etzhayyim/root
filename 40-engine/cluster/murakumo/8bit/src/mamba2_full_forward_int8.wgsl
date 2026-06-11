struct Meta {
  total_tokens: u32,
  batch_size: u32,
  seq_len: u32,
  dim: u32,
  inner: u32,
  state_dim: u32,
  _pad0: u32,
  _pad1: u32,
}

@group(0) @binding(0) var<storage, read> input_vals: array<i32>;
@group(0) @binding(1) var<storage, read> w_in_proj: array<i32>;
@group(0) @binding(2) var<storage, read> w_dt: array<i32>;
@group(0) @binding(3) var<storage, read> w_b: array<i32>;
@group(0) @binding(4) var<storage, read> w_c: array<i32>;
@group(0) @binding(5) var<storage, read> w_out: array<i32>;
@group(0) @binding(6) var<uniform> params: Meta;
@group(0) @binding(7) var<storage, read_write> output_vals: array<i32>;
@group(0) @binding(8) var<storage, read_write> yz_vals: array<i32>;

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

fn silu_i32(x: i32) -> i32 {
  let gate = clamp(x + 64, 0, 128);
  return (x * gate) >> 7;
}

fn softplus_i32(x: i32) -> i32 {
  return max(x, 0) + 1;
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
  let token_idx = gid.x;
  if (token_idx >= params.total_tokens || params.inner > 64u || params.state_dim > 16u || params.dim > 64u) {
    return;
  }
  let token_base = token_idx * params.dim;

  var x_in: array<i32, 64>;
  var z: array<i32, 64>;
  var normed: array<i32, 64>;

  for (var d: u32 = 0u; d < params.dim; d = d + 1u) {
    normed[d] = normed_input(token_base, d);
  }

  for (var j: u32 = 0u; j < params.inner; j = j + 1u) {
    var acc_x: i32 = 0;
    var acc_z: i32 = 0;
    for (var d: u32 = 0u; d < params.dim; d = d + 1u) {
      acc_x = acc_x + normed[d] * w_in_proj[j * params.dim + d];
      acc_z = acc_z + normed[d] * w_in_proj[(j + params.inner) * params.dim + d];
    }
    x_in[j] = acc_x >> 6;
    z[j] = silu_i32(acc_z >> 6);
  }

  var yz: array<i32, 64>;
  for (var j: u32 = 0u; j < params.inner; j = j + 1u) {
    var dt_j: i32 = 0;
    for (var k: u32 = 0u; k < params.inner; k = k + 1u) {
      dt_j = dt_j + x_in[k] * w_dt[j * params.inner + k];
    }
    dt_j = softplus_i32(dt_j >> 6);

    var y_j: i32 = 0;
    for (var s: u32 = 0u; s < params.state_dim; s = s + 1u) {
      var b_js: i32 = 0;
      var c_js: i32 = 0;
      let row = j * params.state_dim + s;
      for (var k: u32 = 0u; k < params.inner; k = k + 1u) {
        b_js = b_js + x_in[k] * w_b[row * params.inner + k];
        c_js = c_js + x_in[k] * w_c[row * params.inner + k];
      }
      let bv = (dt_j * (b_js >> 6)) >> 6;
      y_j = y_j + (((c_js >> 6) * bv) >> 6);
    }
    y_j = y_j + ((x_in[j] * 6) >> 6);
    yz[j] = (y_j * z[j]) >> 6;
    yz_vals[token_idx * params.inner + j] = yz[j];
  }

  for (var o: u32 = 0u; o < params.dim; o = o + 1u) {
    var out_acc: i32 = input_vals[token_base + o];
    for (var j: u32 = 0u; j < params.inner; j = j + 1u) {
      out_acc = out_acc + ((yz[j] * w_out[o * params.inner + j]) >> 6);
    }
    output_vals[token_base + o] = out_acc;
  }
}
