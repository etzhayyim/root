/* tslint:disable */
/* eslint-disable */

/**
 * Detect platform: returns "ios", "android", or "web".
 */
export function detect_platform(): string;

/**
 * Check if current platform is mobile (iOS or Android).
 */
export function is_mobile(): boolean;

export function run('canvas_id': string): Promise<void>;

/**
 * Embed mode: auto-orbit camera, no keyboard input. For iframe/mascot embed.
 */
export function run_embed('canvas_id': string, 'scene_json': string): Promise<void>;

/**
 * NeRF: Density grid with noise + blur — simulates a learned 3D reconstruction.
 */
export function run_embed_nerf('canvas_id': string, resolution: number, 'volume_type': string): Promise<void>;

/**
 * Embed mode with OpenSCAD code: parse → SDF → voxelize → mesh → render.
 * Supports 'volume_type': "dense" | "sparse" | "octree".
 * SCAD: OpenSCAD text → parser → evaluator → per-entity SDF → mesh.
 * Each primitive is a separate entity (union = no fusion between parts).
 * This demonstrates what an LLM generates: human-readable CSG text.
 */
export function run_embed_scad('canvas_id': string, 'scad_code': string, resolution: number, 'volume_type': string): Promise<void>;

/**
 * SDF: Direct Rust SDF code — smooth union fuses parts organically.
 * This is what a programmer writes in Rust: mathematical distance functions.
 */
export function run_embed_sdf('canvas_id': string, resolution: number, 'volume_type': string): Promise<void>;

/**
 * SDF JSON-LD: Parse JSON-LD string into SDF tree → mesh → render.
 * Most LLM-efficient format (η=0.95).
 */
export function run_embed_sdf_jsonld('canvas_id': string, jsonld: string, resolution: number, 'volume_type': string): Promise<void>;

/**
 * Goriketsu Dash!! — chase game on KAMI Engine.
 * Loads scene JSON-LD + runs GoriketsuGame logic each frame.
 * Top-down camera follows player. WASD move, E slap, Space sprint.
 */
export function run_with_game('canvas_id': string, 'scene_json': string, 'game_id': string): Promise<void>;

/**
 * System graph visualizer — renders haisen/SoS JSON as PCB-style graph via WebGPU.
 * PCB layout (grid + bus). Orthographic top-down camera. WASD pan, Space/Shift zoom.
 */
export function run_with_graph('canvas_id': string, 'graph_json': string, mode: string): Promise<void>;

/**
 * Sabi-Otoshi!! — 3D rust restoration game on KAMI Engine.
 * Turntable camera orbit, SDF items, NeRF rust, step-by-step disassembly.
 * Drag to rotate, scroll to zoom, Space/right-click to apply tool, E to disassemble, 1-6 tool select.
 */
export function run_with_sabiotoshi('canvas_id': string, 'scene_json': string): Promise<void>;

export function run_with_scene('canvas_id': string, 'scene_json': string): Promise<void>;

export function start(): void;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly 'detect_platform': () => [number, number];
    readonly 'is_mobile': () => number;
    readonly run: (a: number, b: number) => any;
    readonly 'run_embed': (a: number, b: number, c: number, d: number) => any;
    readonly 'run_embed_nerf': (a: number, b: number, c: number, d: number, e: number) => any;
    readonly 'run_embed_scad': (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
    readonly 'run_embed_sdf': (a: number, b: number, c: number, d: number, e: number) => any;
    readonly 'run_embed_sdf_jsonld': (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
    readonly 'run_with_game': (a: number, b: number, c: number, d: number, e: number, f: number) => any;
    readonly 'run_with_graph': (a: number, b: number, c: number, d: number, e: number, f: number) => any;
    readonly 'run_with_sabiotoshi': (a: number, b: number, c: number, d: number) => any;
    readonly 'run_with_scene': (a: number, b: number, c: number, d: number) => any;
    readonly start: () => void;
    readonly 'wasm_bindgen__closure__destroy__h95a711ea1799e637': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__h58248470da3c1778': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__hdc06e97948d3d628': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__h65a83ee28c491949': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__h60a4caed9770f7f1': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__h14efb445bdf2c435': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__h50b91ea838929c49': (a: number, b: number) => void;
    readonly 'wasm_bindgen__closure__destroy__hf05eaf164083c114': (a: number, b: number) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__h4f3d1bb8ebec98d2': (a: number, b: number, c: any) => [number, number];
    readonly 'wasm_bindgen__convert__closures_____invoke__h07c5524e2faf0ff9': (a: number, b: number, c: any, d: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__h0d3c3e716750a55a': (a: number, b: number, c: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__hb6456330879e5c0c': (a: number, b: number, c: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__hb57275de00957bd7': (a: number, b: number, c: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__h6090315cfaf72934': (a: number, b: number, c: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__hc99e0d11a9e5ad83': (a: number, b: number, c: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__hab61f17cdeb776a7': (a: number, b: number, c: any) => void;
    readonly 'wasm_bindgen__convert__closures_____invoke__h3bbceb0bab7158be': (a: number, b: number) => number;
    readonly 'wasm_bindgen__convert__closures_____invoke__h067db1996cf8db1f': (a: number, b: number) => void;
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
 * @param {{ 'module_or_path': InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { 'module_or_path': InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
