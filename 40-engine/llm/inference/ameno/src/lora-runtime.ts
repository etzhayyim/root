/**
 * WebGPU LoRA runtime merge engine.
 *
 * Applies LoRA adapters to base model weights in-browser via WebGPU compute shaders.
 * Computes W' = W + α·B·A where B and A are low-rank matrices from the adapter.
 *
 * Supports per-actor adapters fetched from R2 CDN and multi-adapter weighted merge.
 */

/**
 * Parsed LoRA adapter metadata from R2 `meta.json`.
 *
 * Stored alongside `adapter.safetensors` at `lora/{actorDid}/{adapterId}/`.
 */
export interface LoraAdapterMeta {
  /** Unique adapter identifier (e.g. `"finance-m1a2b3"`). */
  adapterId: string;
  /** Owner actor DID that this adapter is personalized for. */
  actorDid: string;
  /** HuggingFace base model ID (e.g. `"Qwen/Qwen3.5-0.8B"`). */
  baseModel: string;
  /** LoRA rank (typically 4-64). Lower = smaller adapter, higher = more capacity. */
  rank: number;
  /** LoRA alpha scaling factor. Effective scale = alpha / rank. */
  alpha: number;
  /** Target module names for LoRA injection (e.g. `["q_proj", "v_proj"]`). */
  targetModules: string[];
  /** ISO 8601 timestamp of adapter creation. */
  createdAt: string;
  /** Training metrics from distillation pipeline. */
  metrics?: { loss: number; evalScore: number };
}

/**
 * LoRA adapter weights for a single transformer layer.
 *
 * Each layer stores two low-rank matrices (A, B) such that
 * the weight update is ΔW = B @ A where B is [out, rank] and A is [rank, in].
 */
export interface LoraLayerWeights {
  /** Fully qualified module name (e.g. `"model.layers.0.self_attn.q_proj"`). */
  module: string;
  /** Low-rank matrix A with shape `[rank, inFeatures]`, row-major Float32. */
  loraA: Float32Array;
  /** Low-rank matrix B with shape `[outFeatures, rank]`, row-major Float32. */
  loraB: Float32Array;
  /** LoRA rank — number of columns in B / rows in A. */
  rank: number;
  /** Input feature dimension (columns of the original weight matrix). */
  inFeatures: number;
  /** Output feature dimension (rows of the original weight matrix). */
  outFeatures: number;
}

/**
 * Fully loaded LoRA adapter with parsed metadata and weight tensors.
 *
 * Fetched from R2 CDN via {@link fetchLoraAdapter} and ready for
 * GPU merge via {@link applyLoraAdapters}.
 */
export interface LoadedLoraAdapter {
  /** Adapter metadata from R2 `meta.json`. */
  meta: LoraAdapterMeta;
  /** Per-layer weight pairs parsed from `adapter.safetensors`. */
  layers: LoraLayerWeights[];
}

/**
 * Specification for merging a single adapter into base model weights.
 *
 * Used in multi-adapter composition where each adapter contributes
 * a weighted fraction to the final merged weights.
 */
export interface AdapterMergeSpec {
  /** Loaded adapter with weights. */
  adapter: LoadedLoraAdapter;
  /**
   * Merge weight in range `[0.0, 1.0]`.
   *
   * Final scaling = `weight * (alpha / rank)`. When omitted, defaults to 1.0
   * (full adapter contribution at its native alpha/rank scale).
   */
  weight?: number;
}

/** WGSL compute shader for LoRA merge: W' = W + α·(B × A). */
const LORA_MERGE_WGSL = /* wgsl */ `
struct Params {
  M: u32,       // out_features (rows of W and B)
  N: u32,       // in_features (cols of W and A)
  R: u32,       // rank (cols of B, rows of A)
  alpha: f32,   // scaling factor α/rank
}

@group(0) @binding(0) var<uniform> params: Params;
@group(0) @binding(1) var<storage, read_write> W: array<f32>;
@group(0) @binding(2) var<storage, read> B: array<f32>;
@group(0) @binding(3) var<storage, read> A: array<f32>;

@compute @workgroup_size(16, 16)
fn main(@builtin(global_invocation_id) gid: vec3u) {
  let row = gid.x;
  let col = gid.y;
  if (row >= params.M || col >= params.N) { return; }

  // Compute dot(B[row, :], A[:, col]) = sum_r B[row*R+r] * A[r*N+col]
  var dot: f32 = 0.0;
  for (var r: u32 = 0u; r < params.R; r = r + 1u) {
    dot = dot + B[row * params.R + r] * A[r * params.N + col];
  }

  // W'[row, col] = W[row, col] + alpha * dot(B_row, A_col)
  let idx = row * params.N + col;
  W[idx] = W[idx] + params.alpha * dot;
}
`;

/** Cached WebGPU device — reused across all merge operations. */
let cachedDevice: GPUDevice | null = null;
/** Cached compiled LoRA merge compute pipeline. */
let cachedPipeline: GPUComputePipeline | null = null;

/**
 * Lazily initialize WebGPU device and compile the LoRA merge compute pipeline.
 *
 * The pipeline is compiled once and cached for the lifetime of the page.
 * Returns `null` if WebGPU is unavailable (triggers CPU fallback).
 *
 * @returns Device + pipeline pair, or `null` if WebGPU is not supported.
 */
async function ensureGpuPipeline(): Promise<{ device: GPUDevice; pipeline: GPUComputePipeline } | null> {
  if (cachedDevice && cachedPipeline) {
    return { device: cachedDevice, pipeline: cachedPipeline };
  }

  if (!navigator.gpu) return null;

  const adapter = await navigator.gpu.requestAdapter();
  if (!adapter) return null;

  const device = await adapter.requestDevice();
  const shaderModule = device.createShaderModule({ code: LORA_MERGE_WGSL });

  const pipeline = device.createComputePipeline({
    layout: "auto",
    compute: { module: shaderModule, entryPoint: "main" },
  });

  cachedDevice = device;
  cachedPipeline = pipeline;
  return { device, pipeline };
}

/**
 * Merge a single LoRA layer into base weights on GPU.
 *
 * Dispatches a WebGPU compute pass that computes `W'[i,j] = W[i,j] + α · Σ_r B[i,r]·A[r,j]`
 * in parallel across a 16x16 workgroup grid. GPU buffers are created, used, and destroyed
 * within this call — no persistent GPU memory is leaked.
 *
 * @param device - WebGPU device from {@link ensureGpuPipeline}.
 * @param pipeline - Compiled LoRA merge compute pipeline.
 * @param baseWeights - Base weight matrix as flat `Float32Array` with shape `[M, N]`.
 * @param layer - LoRA low-rank pair (B: `[M, R]`, A: `[R, N]`).
 * @param scalingFactor - Pre-computed scaling `α/rank * mergeWeight`.
 * @returns New `Float32Array` with merged weights (original is not mutated).
 */
async function mergeLayerGpu(
  device: GPUDevice,
  pipeline: GPUComputePipeline,
  baseWeights: Float32Array,
  layer: LoraLayerWeights,
  scalingFactor: number,
): Promise<Float32Array> {
  const M = layer.outFeatures;
  const N = layer.inFeatures;
  const R = layer.rank;

  // Uniform params buffer
  const paramsData = new ArrayBuffer(16);
  const paramsView = new DataView(paramsData);
  paramsView.setUint32(0, M, true);
  paramsView.setUint32(4, N, true);
  paramsView.setUint32(8, R, true);
  paramsView.setFloat32(12, scalingFactor, true);

  const paramsBuffer = device.createBuffer({
    size: 16,
    usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
  });
  device.queue.writeBuffer(paramsBuffer, 0, paramsData);

  // W buffer (read-write storage)
  const wBuffer = device.createBuffer({
    size: baseWeights.byteLength,
    usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST | GPUBufferUsage.COPY_SRC,
  });
  device.queue.writeBuffer(wBuffer, 0, baseWeights);

  // B buffer (read-only storage)
  const bBuffer = device.createBuffer({
    size: layer.loraB.byteLength,
    usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST,
  });
  device.queue.writeBuffer(bBuffer, 0, layer.loraB);

  // A buffer (read-only storage)
  const aBuffer = device.createBuffer({
    size: layer.loraA.byteLength,
    usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST,
  });
  device.queue.writeBuffer(aBuffer, 0, layer.loraA);

  // Bind group
  const bindGroup = device.createBindGroup({
    layout: pipeline.getBindGroupLayout(0),
    entries: [
      { binding: 0, resource: { buffer: paramsBuffer } },
      { binding: 1, resource: { buffer: wBuffer } },
      { binding: 2, resource: { buffer: bBuffer } },
      { binding: 3, resource: { buffer: aBuffer } },
    ],
  });

  // Dispatch compute
  const encoder = device.createCommandEncoder();
  const pass = encoder.beginComputePass();
  pass.setPipeline(pipeline);
  pass.setBindGroup(0, bindGroup);
  pass.dispatchWorkgroups(Math.ceil(M / 16), Math.ceil(N / 16));
  pass.end();

  // Read back merged weights
  const readBuffer = device.createBuffer({
    size: baseWeights.byteLength,
    usage: GPUBufferUsage.MAP_READ | GPUBufferUsage.COPY_DST,
  });
  encoder.copyBufferToBuffer(wBuffer, 0, readBuffer, 0, baseWeights.byteLength);

  device.queue.submit([encoder.finish()]);
  await readBuffer.mapAsync(GPUMapMode.READ);
  const result = new Float32Array(readBuffer.getMappedRange().slice(0));
  readBuffer.unmap();

  // Cleanup GPU buffers
  paramsBuffer.destroy();
  wBuffer.destroy();
  bBuffer.destroy();
  aBuffer.destroy();
  readBuffer.destroy();

  return result;
}

/**
 * CPU fallback for LoRA layer merge when WebGPU is unavailable.
 *
 * Triple-nested loop computing `W'[i,j] = W[i,j] + α · Σ_r B[i,r]·A[r,j]`.
 * For a Qwen3.5 0.8B model with rank 8, each layer merge takes ~10-50ms on CPU.
 *
 * @param baseWeights - Base weight matrix as flat `Float32Array` with shape `[M, N]`.
 * @param layer - LoRA low-rank pair (B: `[M, R]`, A: `[R, N]`).
 * @param scalingFactor - Pre-computed scaling `α/rank * mergeWeight`.
 * @returns New `Float32Array` with merged weights (original is not mutated).
 */
function mergeLayerCpu(
  baseWeights: Float32Array,
  layer: LoraLayerWeights,
  scalingFactor: number,
): Float32Array {
  const result = new Float32Array(baseWeights);
  const M = layer.outFeatures;
  const N = layer.inFeatures;
  const R = layer.rank;

  for (let row = 0; row < M; row++) {
    for (let col = 0; col < N; col++) {
      let dot = 0;
      for (let r = 0; r < R; r++) {
        dot += layer.loraB[row * R + r] * layer.loraA[r * N + col];
      }
      result[row * N + col] += scalingFactor * dot;
    }
  }
  return result;
}

/**
 * Parse a safetensors binary file into LoRA layer weights.
 *
 * Safetensors format: `[8-byte LE header_size][JSON header][tensor data]`.
 * LoRA adapters use the naming convention `{module}.lora_A.weight` and
 * `{module}.lora_B.weight`. This parser groups A/B pairs by module name
 * and converts F16/BF16 tensors to F32 for GPU consumption.
 *
 * @param buffer - Raw `ArrayBuffer` from fetching `adapter.safetensors`.
 * @returns Array of parsed layer weights, one per LoRA-injected module.
 *   Modules with only A or only B (incomplete pairs) are skipped with a warning.
 *
 * @example
 * ```ts
 * const resp = await fetch(adapterUrl);
 * const layers = parseSafetensors(await resp.arrayBuffer());
 * // layers[0].module === "model.layers.0.self_attn.q_proj"
 * // layers[0].rank === 8
 * ```
 */
export function parseSafetensors(buffer: ArrayBuffer): LoraLayerWeights[] {
  const view = new DataView(buffer);
  const headerSize = Number(view.getBigUint64(0, true));
  const headerBytes = new Uint8Array(buffer, 8, headerSize);
  const header = JSON.parse(new TextDecoder().decode(headerBytes)) as Record<
    string,
    { dtype: string; shape: number[]; data_offsets: [number, number] }
  >;

  const dataOffset = 8 + headerSize;
  const tensorMap = new Map<string, { data: Float32Array; shape: number[] }>();

  for (const [name, info] of Object.entries(header)) {
    if (name === "__metadata__") continue;
    const [start, end] = info.data_offsets;
    const raw = new Uint8Array(buffer, dataOffset + start, end - start);

    let floats: Float32Array;
    if (info.dtype === "F32") {
      floats = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
    } else if (info.dtype === "F16" || info.dtype === "BF16") {
      floats = convertToF32(raw, info.dtype);
    } else {
      console.warn(`Unsupported dtype ${info.dtype} for tensor ${name}, skipping`);
      continue;
    }
    tensorMap.set(name, { data: floats, shape: info.shape });
  }

  // Group lora_A and lora_B by module name
  const modules = new Map<string, { a?: { data: Float32Array; shape: number[] }; b?: { data: Float32Array; shape: number[] } }>();

  for (const [name, tensor] of tensorMap) {
    const loraAMatch = name.match(/^(.+)\.lora_A\.weight$/);
    const loraBMatch = name.match(/^(.+)\.lora_B\.weight$/);

    if (loraAMatch) {
      const mod = loraAMatch[1];
      if (!modules.has(mod)) modules.set(mod, {});
      modules.get(mod)!.a = tensor;
    } else if (loraBMatch) {
      const mod = loraBMatch[1];
      if (!modules.has(mod)) modules.set(mod, {});
      modules.get(mod)!.b = tensor;
    }
  }

  const layers: LoraLayerWeights[] = [];
  for (const [module, { a, b }] of modules) {
    if (!a || !b) {
      console.warn(`Incomplete LoRA pair for module ${module}, skipping`);
      continue;
    }
    // A: [rank, in_features], B: [out_features, rank]
    layers.push({
      module,
      loraA: a.data,
      loraB: b.data,
      rank: a.shape[0],
      inFeatures: a.shape[1],
      outFeatures: b.shape[0],
    });
  }

  return layers;
}

/**
 * Convert F16 (IEEE 754 half-precision) or BF16 (Brain Float 16) raw bytes to F32.
 *
 * BF16 conversion is a simple bit-shift (same exponent range as F32).
 * F16 requires full exponent/mantissa remapping.
 *
 * @param raw - Raw 16-bit tensor data bytes.
 * @param dtype - Source dtype: `"F16"` or `"BF16"`.
 * @returns Converted `Float32Array` with the same number of elements.
 */
function convertToF32(raw: Uint8Array, dtype: string): Float32Array {
  const count = raw.byteLength / 2;
  const result = new Float32Array(count);
  const view = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);

  for (let i = 0; i < count; i++) {
    const bits = view.getUint16(i * 2, true);
    if (dtype === "BF16") {
      // BF16 → F32: shift left 16 bits
      const f32Bits = bits << 16;
      const tmp = new DataView(new ArrayBuffer(4));
      tmp.setUint32(0, f32Bits, true);
      result[i] = tmp.getFloat32(0, true);
    } else {
      // F16 → F32 (IEEE 754 half-precision)
      const sign = (bits >> 15) & 1;
      const exp = (bits >> 10) & 0x1f;
      const frac = bits & 0x3ff;

      if (exp === 0) {
        result[i] = (sign ? -1 : 1) * Math.pow(2, -14) * (frac / 1024);
      } else if (exp === 0x1f) {
        result[i] = frac === 0 ? (sign ? -Infinity : Infinity) : NaN;
      } else {
        result[i] = (sign ? -1 : 1) * Math.pow(2, exp - 15) * (1 + frac / 1024);
      }
    }
  }
  return result;
}

/**
 * Fetch and parse a LoRA adapter from the R2 CDN.
 *
 * Downloads `meta.json` and `adapter.safetensors` from the R2 key prefix
 * `lora/{actorDid}/{adapterId}/`. Both requests use `cache: "force-cache"`
 * since adapter weights are immutable once trained.
 *
 * @param actorDid - Actor DID that owns the adapter (used as R2 path segment).
 * @param adapterId - Adapter identifier (e.g. `"finance-m1a2b3"`).
 * @param pdsBaseUrl - PDS base URL that proxies R2 content (e.g. `"https://atproto.etzhayyim.com"`).
 * @returns Loaded adapter with metadata and parsed weight tensors.
 * @throws If either fetch fails (non-2xx status).
 */
export async function fetchLoraAdapter(
  actorDid: string,
  adapterId: string,
  pdsBaseUrl: string,
): Promise<LoadedLoraAdapter> {
  const prefix = `lora/${encodeURIComponent(actorDid)}/${encodeURIComponent(adapterId)}`;

  // Fetch metadata
  const metaResp = await fetch(`${pdsBaseUrl}/${prefix}/meta.json`, {
    cache: "force-cache",
  });
  if (!metaResp.ok) throw new Error(`LoRA meta fetch failed: ${metaResp.status}`);
  const meta: LoraAdapterMeta = await metaResp.json();

  // Fetch safetensors (immutable, CDN cacheable)
  const weightsResp = await fetch(`${pdsBaseUrl}/${prefix}/adapter.safetensors`, {
    cache: "force-cache",
  });
  if (!weightsResp.ok) throw new Error(`LoRA weights fetch failed: ${weightsResp.status}`);
  const buffer = await weightsResp.arrayBuffer();

  const layers = parseSafetensors(buffer);

  return { meta, layers };
}

/**
 * Apply one or more LoRA adapters to base model weights.
 *
 * Iterates over all adapter layers and applies the merge formula:
 * `W'[module] = W[module] + Σ_i (weight_i · α_i/rank_i · B_i @ A_i)`.
 *
 * Uses WebGPU compute shader when available (sub-ms per layer on modern GPUs),
 * falls back to CPU triple-loop (~10-50ms per layer for 0.8B models).
 *
 * @param baseWeightsMap - Map of module name to base weight `Float32Array`.
 *   Keys must match the `.module` field in adapter layers.
 * @param adapters - One or more adapter merge specs from {@link ragLoraSelect}.
 *   For single-adapter use, pass `[{ adapter, weight: 1.0 }]`.
 * @param onProgress - Optional progress callback receiving percentage (0-100).
 *   Called once per layer merge. Total layers = sum of all adapters' layer counts.
 * @returns New map with merged weights. Modules not targeted by any adapter
 *   retain their original `Float32Array` reference (zero-copy).
 */
export async function applyLoraAdapters(
  baseWeightsMap: Map<string, Float32Array>,
  adapters: AdapterMergeSpec[],
  onProgress?: (pct: number) => void,
): Promise<Map<string, Float32Array>> {
  const gpu = await ensureGpuPipeline();
  const result = new Map(baseWeightsMap);

  let totalLayers = 0;
  for (const spec of adapters) totalLayers += spec.adapter.layers.length;
  let processed = 0;

  for (const spec of adapters) {
    const { adapter } = spec;
    const defaultScale = adapter.meta.alpha / adapter.meta.rank;
    const mergeWeight = spec.weight ?? 1.0;
    const scalingFactor = defaultScale * mergeWeight;

    for (const layer of adapter.layers) {
      const baseWeights = result.get(layer.module);
      if (!baseWeights) {
        console.warn(`Base weights not found for module ${layer.module}, skipping`);
        processed++;
        continue;
      }

      const merged = gpu
        ? await mergeLayerGpu(gpu.device, gpu.pipeline, baseWeights, layer, scalingFactor)
        : mergeLayerCpu(baseWeights, layer, scalingFactor);

      result.set(layer.module, merged);
      processed++;

      if (onProgress) {
        onProgress(Math.round((processed / totalLayers) * 100));
      }
    }
  }

  return result;
}
