struct UpdateMeta {
  total: u32,
  sign_step: i32,
  _pad0: u32,
  _pad1: u32,
}

@group(0) @binding(0) var<storage, read_write> weights: array<i32>;
@group(0) @binding(1) var<storage, read> grads: array<i32>;
@group(0) @binding(2) var<storage, read_write> error_buf: array<i32>;
@group(0) @binding(3) var<uniform> params: UpdateMeta;

fn sign_i32(x: i32) -> i32 {
  if (x > 0) {
    return 1;
  }
  if (x < 0) {
    return -1;
  }
  return 0;
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let idx = gid.x;
  if (idx >= params.total) {
    return;
  }
  let corrected = grads[idx] + error_buf[idx];
  let delta = sign_i32(corrected) * params.sign_step;
  error_buf[idx] = corrected - delta;
  weights[idx] = clamp(weights[idx] - delta, -128, 127);
}
