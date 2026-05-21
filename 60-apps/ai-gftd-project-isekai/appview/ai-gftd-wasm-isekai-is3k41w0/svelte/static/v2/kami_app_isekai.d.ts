/* tslint:disable */
/* eslint-disable */

/**
 * Entry point exported to JS.
 *
 * ```js
 * import init, { run_isekai_v2 } from './kami_app_isekai.js';
 * await init();
 * await run_isekai_v2('gc');
 * ```
 */
export function run_isekai_v2(canvas_id: string): Promise<void>;

/**
 * v3 demo variant with a scene selector.
 *
 * Gates DEC subsystems so each phase can be demoed in isolation:
 *
 *   0 — heat diffusion only (M1 rule + Λ⁰ Laplacian)
 *   1 — + moisture field (compositional Λ⁰ composition, wet-paper rule)
 *   2 — + EdgeField wind + buoyancy + semi-Lagrangian advection
 *   3 — + Helmholtz projection (Jacobi Poisson → divergence-free)
 *   4 — + wall boundary (EdgeField::mask_solid) — full v3 stack
 */
export function run_isekai_v2_scene(canvas_id: string, scene: number): Promise<void>;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly run_isekai_v2: (a: number, b: number) => any;
    readonly run_isekai_v2_scene: (a: number, b: number, c: number) => any;
    readonly wasm_bindgen__closure__destroy__h2999ab7c8b76f609: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h4100316d4464f38b: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h2d51862d9d8acb10: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h7fab2cc70c6a6a11: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h5db5e8dc2faf8fdd: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h67d2d77a4c3b48e0: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h67d2d77a4c3b48e0_3: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h67d2d77a4c3b48e0_4: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h74397136654de27e: (a: number, b: number) => void;
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
