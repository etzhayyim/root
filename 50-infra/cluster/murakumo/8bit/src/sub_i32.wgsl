struct SubMeta {
  total: u32,
  _pad0: u32,
  _pad1: u32,
  _pad2: u32,
}

@group(0) @binding(0) var<storage, read> a_vals: array<i32>;
@group(0) @binding(1) var<storage, read> b_vals: array<i32>;
@group(0) @binding(2) var<storage, read_write> out_vals: array<i32>;
@group(0) @binding(3) var<uniform> params: SubMeta;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let idx = gid.x;
  if (idx >= params.total) {
    return;
  }
  out_vals[idx] = a_vals[idx] - b_vals[idx];
}
