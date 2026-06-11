struct GradMeta {
  tokens: u32,
  dim: u32,
  inner: u32,
  _pad0: u32,
}

@group(0) @binding(0) var<storage, read> yz_vals: array<i32>;
@group(0) @binding(1) var<storage, read> residual_vals: array<i32>;
@group(0) @binding(2) var<storage, read_write> grad_vals: array<i32>;
@group(0) @binding(3) var<uniform> params: GradMeta;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let idx = gid.x;
  let total = params.dim * params.inner;
  if (idx >= total) {
    return;
  }
  let o = idx / params.inner;
  let i = idx % params.inner;
  var acc: i32 = 0;
  for (var t: u32 = 0u; t < params.tokens; t = t + 1u) {
    acc = acc + ((residual_vals[t * params.dim + o] * yz_vals[t * params.inner + i]) >> 12);
  }
  grad_vals[idx] = acc;
}
