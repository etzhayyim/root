enable f16;

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

@group(0) @binding(0) var<storage, read> input_vals: array<f16>;
@group(0) @binding(1) var<storage, read> w_in_proj: array<f16>;
@group(0) @binding(2) var<storage, read> w_dt: array<f16>;
@group(0) @binding(3) var<storage, read> w_b: array<f16>;
@group(0) @binding(4) var<storage, read> w_c: array<f16>;
@group(0) @binding(5) var<storage, read> w_out: array<f16>;
@group(0) @binding(6) var<uniform> params: Meta;
@group(0) @binding(7) var<storage, read_write> output_vals: array<f16>;

fn sqrt_approx(x: f16) -> f16 {
  return max(f16(0.0001), sqrt(max(x, f16(0.0001))));
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let token_idx = gid.x;
  if (token_idx >= params.total_tokens || params.inner > 64u || params.state_dim > 16u || params.dim > 64u) {
    return;
  }
  let token_base = token_idx * params.dim;

  var normed: array<f16, 64>;
  var mean: f16 = f16(0.0);
  for (var d: u32 = 0u; d < params.dim; d = d + 1u) {
    mean = mean + input_vals[token_base + d];
  }
  mean = mean / f16(params.dim);
  var var_acc: f16 = f16(0.0);
  for (var d: u32 = 0u; d < params.dim; d = d + 1u) {
    let centered = input_vals[token_base + d] - mean;
    var_acc = var_acc + centered * centered;
  }
  var_acc = var_acc / f16(params.dim);
  let denom = sqrt_approx(var_acc) + f16(1.0);
  for (var d: u32 = 0u; d < params.dim; d = d + 1u) {
    normed[d] = (input_vals[token_base + d] - mean) / denom;
  }

  var x_in: array<f16, 64>;
  var z: array<f16, 64>;
  var yz: array<f16, 64>;

  for (var j: u32 = 0u; j < params.inner; j = j + 1u) {
    var acc_x: f16 = f16(0.0);
    var acc_z: f16 = f16(0.0);
    for (var d: u32 = 0u; d < params.dim; d = d + 1u) {
      acc_x = acc_x + normed[d] * w_in_proj[j * params.dim + d];
      acc_z = acc_z + normed[d] * w_in_proj[(j + params.inner) * params.dim + d];
    }
    x_in[j] = acc_x / f16(64.0);
    let sig = f16(1.0) / (f16(1.0) + exp(-acc_z / f16(64.0)));
    z[j] = (acc_z / f16(64.0)) * sig;
  }

  for (var j: u32 = 0u; j < params.inner; j = j + 1u) {
    var dt_j: f16 = f16(0.0);
    for (var k: u32 = 0u; k < params.inner; k = k + 1u) {
      dt_j = dt_j + x_in[k] * w_dt[j * params.inner + k];
    }
    dt_j = log(f16(1.0) + exp(dt_j / f16(64.0))) * f16(16.0);

    var y_j: f16 = f16(0.0);
    for (var s: u32 = 0u; s < params.state_dim; s = s + 1u) {
      var b_js: f16 = f16(0.0);
      var c_js: f16 = f16(0.0);
      let row = j * params.state_dim + s;
      for (var k: u32 = 0u; k < params.inner; k = k + 1u) {
        b_js = b_js + x_in[k] * w_b[row * params.inner + k];
        c_js = c_js + x_in[k] * w_c[row * params.inner + k];
      }
      y_j = y_j + (c_js / f16(64.0)) * (dt_j * (b_js / f16(64.0)));
    }
    y_j = y_j + f16(0.1) * x_in[j];
    yz[j] = y_j * z[j];
  }

  for (var o: u32 = 0u; o < params.dim; o = o + 1u) {
    var out_acc = input_vals[token_base + o];
    for (var j: u32 = 0u; j < params.inner; j = j + 1u) {
      out_acc = out_acc + yz[j] * w_out[o * params.inner + j];
    }
    output_vals[token_base + o] = out_acc;
  }
}
