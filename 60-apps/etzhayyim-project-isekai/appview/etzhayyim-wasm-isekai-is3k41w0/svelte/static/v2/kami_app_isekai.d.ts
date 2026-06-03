/* tslint:disable */
/* eslint-disable */

/**
 * nv-compat banner; useful for HUD strings and audit trails.
 */
export function isekaiOmniverseBanner(): string;

/**
 * JS-callable: return the bundled default USDA so the JS side can
 * display / edit / re-submit it.
 */
export function isekaiOmniverseDefaultUsda(): string;

/**
 * JS-callable: return the built-in world catalog as a JSON string
 * `[{id, name, usda}]`. Each `usda` field is produced by
 * `kami_usd::to_usda` over a programmatically-built `Stage`.
 */
export function isekaiOmniverseWorldCatalog(): string;

/**
 * JS-callable: set the force (N) applied to every cartpole cart each
 * physics step. `omniverse.htm` / `worlds.htm` bind J/L (or ←/→) to
 * `isekaiSetCartForce(±F)` on keydown and `isekaiSetCartForce(0)` on
 * keyup.
 */
export function isekaiSetCartForce(force: number): void;

/**
 * Run the ISEKAI omniverse entry.
 *
 * `canvas_id`  — WebGPU canvas DOM id.
 * `usda_src`   — USDA stage text. Pass empty string to use
 *                `DEFAULT_ISEKAI_USDA`.
 */
export function runIsekaiOmniverse(canvas_id: string, usda_src: string): Promise<void>;

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
    readonly isekaiOmniverseBanner: () => [number, number];
    readonly isekaiOmniverseDefaultUsda: () => [number, number];
    readonly isekaiOmniverseWorldCatalog: () => [number, number];
    readonly runIsekaiOmniverse: (a: number, b: number, c: number, d: number) => any;
    readonly isekaiSetCartForce: (a: number) => void;
    readonly wasm_bindgen__closure__destroy__h4cc8d9ef82568b4c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h3435a2f46af78ad4: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h2272828a8287050c: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hf36f016bc8d48565: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h9ab28270d6b15822: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_1: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_2: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_3: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h352b1769adabbb37: (a: number, b: number) => void;
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
