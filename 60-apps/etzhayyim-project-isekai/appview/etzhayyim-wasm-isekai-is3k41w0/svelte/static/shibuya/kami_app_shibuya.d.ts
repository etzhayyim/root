/* tslint:disable */
/* eslint-disable */

export function run_shibuya_v1(canvas_id: string): Promise<void>;

/**
 * #3 — Splat backdrop + live physics: the real Mapillary-SfM cloud as the
 * visual world, with kami-genesis floating-base agents doing full physics on a
 * ground plane inside it. (Pairs the GsplatAdapter overlay with the
 * ContactWorld sim — a coarse "physics on a captured city" integration.)
 */
export function run_splat_physics_v1(canvas_id: string): Promise<void>;

/**
 * Standalone 3-D Gaussian-Splat viewer: sky + GsplatAdapter, orbit camera
 * framed on a cloud centred at the origin (radius ≈ 60, normalised by
 * `opensfm_to_splat.py`). The JS shell loads a `.splat` via `shibuyaLoadSplat`.
 * Used to view REAL Mapillary-SfM point clouds (Tsuru / Boston / …).
 */
export function run_splat_viewer_v1(canvas_id: string): Promise<void>;

/**
 * JS hook: remove the 3DGS overlay (back to the box city).
 */
export function shibuyaClearSplat(): void;

/**
 * JS hook: load a `.splat` (antimatter15 32-byte) cloud into the 3DGS overlay.
 */
export function shibuyaLoadSplat(bytes: Uint8Array): boolean;

/**
 * JS hook: load a `.ply` (gsplat training output) cloud into the 3DGS overlay.
 */
export function shibuyaLoadSplatPly(bytes: Uint8Array): boolean;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly run_shibuya_v1: (a: number, b: number) => any;
    readonly run_splat_physics_v1: (a: number, b: number) => any;
    readonly run_splat_viewer_v1: (a: number, b: number) => any;
    readonly shibuyaLoadSplat: (a: number, b: number) => number;
    readonly shibuyaLoadSplatPly: (a: number, b: number) => number;
    readonly shibuyaClearSplat: () => void;
    readonly wasm_bindgen__closure__destroy__h4cc8d9ef82568b4c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h3435a2f46af78ad4: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h5cc718e39248ba03: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hf36f016bc8d48565: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h9ab28270d6b15822: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_1: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_2: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_3: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hea8de30ba9aec218: (a: number, b: number) => void;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_exn_store: (a: number) => void;
    readonly __externref_table_alloc: () => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __externref_table_dealloc: (a: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
