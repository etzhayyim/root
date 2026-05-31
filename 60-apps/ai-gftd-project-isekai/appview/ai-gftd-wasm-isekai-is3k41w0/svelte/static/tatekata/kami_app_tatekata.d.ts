/* tslint:disable */
/* eslint-disable */

/**
 * JS hook: number of engineering clashes detected (red/orange markers).
 */
export function giemonFactoryClashCount(): number;

/**
 * JS hook: the htm HUD polls this for the current 建築手順 step label.
 */
export function giemonFactoryStep(): string;

/**
 * JS hook: current step + robot + material-process %.
 */
export function giemonTatekataStatus(): string;

export function run_giemon_factory_build_v1(canvas_id: string): Promise<void>;

export function run_giemon_factory_v1(canvas_id: string): Promise<void>;

export function run_tatekata_v1(canvas_id: string): Promise<void>;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly giemonTatekataStatus: () => [number, number];
    readonly run_tatekata_v1: (a: number, b: number) => any;
    readonly giemonFactoryClashCount: () => number;
    readonly giemonFactoryStep: () => [number, number];
    readonly run_giemon_factory_build_v1: (a: number, b: number) => any;
    readonly run_giemon_factory_v1: (a: number, b: number) => any;
    readonly wasm_bindgen__closure__destroy__h39db2ccfcdb5a7c0: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h4cc8d9ef82568b4c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h3435a2f46af78ad4: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hf36f016bc8d48565: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h9ab28270d6b15822: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_2: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_3: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2d97656a5ae4bcf4_4: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__he88c7ef83b23de30: (a: number, b: number) => void;
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
