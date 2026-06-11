/* tslint:disable */
/* eslint-disable */

/**
 * JS hook: select which joint (1-based, matching the URDF j1..j6) the torque
 * drives. Out-of-range values are clamped.
 */
export function giemonSelectJoint(one_based: number): void;

/**
 * JS hook: torque (N·m) applied to the currently-selected joint. J → −T,
 * L → +T, key-up → 0.
 */
export function giemonSetJointTorque(torque: number): void;

export function run_giemon_caterpillar_v1(canvas_id: string): Promise<void>;

export function run_giemon_hitogata_v1(canvas_id: string): Promise<void>;

/**
 * Physics-driven kabitori (mold-removal) probe demo. The probe feeds into a
 * gap, droops its brush onto the mold surface (contact ground plane), and
 * scrubs autonomously (continuous brush spin + yaw sweep) — all advanced by
 * the kami-genesis 3-D solver + contact solver. Clean-room (ADR-2605261800).
 */
export function run_giemon_kabitori_sim_v1(canvas_id: string): Promise<void>;

export function run_giemon_otete_sim_v1(canvas_id: string): Promise<void>;

export function run_giemon_sim_v1(canvas_id: string): Promise<void>;

export function run_giemon_v1(canvas_id: string): Promise<void>;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly run_giemon_caterpillar_v1: (a: number, b: number) => any;
    readonly run_giemon_hitogata_v1: (a: number, b: number) => any;
    readonly run_giemon_kabitori_sim_v1: (a: number, b: number) => any;
    readonly run_giemon_otete_sim_v1: (a: number, b: number) => any;
    readonly run_giemon_sim_v1: (a: number, b: number) => any;
    readonly run_giemon_v1: (a: number, b: number) => any;
    readonly giemonSetJointTorque: (a: number) => void;
    readonly giemonSelectJoint: (a: number) => void;
    readonly wasm_bindgen__closure__destroy__h4cc8d9ef82568b4c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h3435a2f46af78ad4: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__hcea6cdf56f623c7c: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hf36f016bc8d48565: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h9ab28270d6b15822: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_1: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_2: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_3: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h107ec9ab60342548: (a: number, b: number) => void;
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
