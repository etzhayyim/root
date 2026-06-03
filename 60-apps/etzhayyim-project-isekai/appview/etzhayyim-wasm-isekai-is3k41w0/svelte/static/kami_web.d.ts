/* tslint:disable */
/* eslint-disable */

/**
 * Cache a heightmap for per-frame `sample_terrain_height` calls.
 * Call once after terrain generation. Subsequent sample calls are ~5ns each.
 */
export function cache_heightmap(config_json: string): number;

/**
 * Cache the most recently generated vegetation instances for culling.
 * Call once after `generate_vegetation` — subsequent `cull_vegetation` calls
 * read from this cache (avoids re-uploading instances each frame).
 */
export function cache_vegetation(config_json: string): number;

/**
 * Check if WebGPU or WebGL2 is available for document rendering.
 */
export function check_document_gpu(): Promise<boolean>;

/**
 * Clamp a bone rotation (degrees) through humanoid joint constraints.
 *
 * Looks up `bone_name` in `default_humanoid_constraints()`, then clamps
 * `degrees` to the `[min, max]` range for the given `axis` ("x", "y", or "z").
 * Returns the clamped value, or the input unchanged if bone/axis is not found.
 */
export function clamp_bone(bone_name: string, axis: string, degrees: number): number;

/**
 * Compute sky uniform for the atmosphere shader.
 * `time_of_day`: [0, 1] where 0.5 = noon.
 * Returns JSON with sun_dir, sun_color, fog_color, fog_density.
 */
export function compute_sky_uniform(time_of_day: number): string;

/**
 * Compute full weather state (sky + wind + clouds) for one frame.
 * `time_of_day`: [0,1], `game_time`: seconds since start, `preset`: "default"|"overcast"|"clear".
 */
export function compute_weather(time_of_day: number, game_time: number): string;

/**
 * Compute weather with a named preset.
 */
export function compute_weather_preset(time_of_day: number, game_time: number, preset: string): string;

/**
 * Compute 4 Gerstner waves from wind direction + speed + gust.
 * Returns JSON: `{ "waves": [{dir, amp, wavelength, speed, steepness}, x4] }`
 *
 * Use this to update water uniform when wind changes — waves align with wind,
 * amplitude scales with Beaufort wind strength, wavelength follows deep-water
 * dispersion.
 */
export function compute_wind_waves(dir_x: number, dir_z: number, wind_speed: number, gust: number): string;

/**
 * Cull cached vegetation by camera position + budget.
 * Returns flat `[pos.xyz, scale, rotation, species, wind_phase, color_tint]` × N.
 * Call per frame. WASM does distance sort + LOD filter internally.
 */
export function cull_vegetation(cam_x: number, cam_z: number, budget: number): Float32Array;

/**
 * Detect platform: returns "ios", "android", or "web".
 */
export function detect_platform(): string;

/**
 * Get GPU adapter info for the document renderer.
 */
export function document_gpu_info(): Promise<string>;

/**
 * Evaluate a procedural motion animation at the given time.
 *
 * Computes bone rotations (in degrees) for one of 11 built-in motions
 * (idle, breathe, nod, shake, wave_hi, dance, bounce, sway, look_around,
 * excited, sad_sway). All rotations are clamped through
 * `default_humanoid_constraints()`. Returns a JSON object mapping bone names
 * to `{"x": deg, "y": deg, "z": deg}`.
 */
export function evaluate_motion(motion_key: string, time: number): string;

/**
 * Generate terrain chunk mesh data for a given config.
 * Returns JSON: `{ "vertices": [f32...], "indices": [u32...], "vertex_count": N }`
 *
 * `config_json`: `{ "width": 129, "depth": 129, "seed": 42, "max_height": 120,
 *   "frequency": 0.005, "octaves": 6, "origin_x": 0, "origin_z": 0, "lod": 0 }`
 */
export function generate_terrain_chunk(config_json: string): string;

/**
 * Generate vegetation instances (grass/fern/palm/conifer/bush) over terrain.
 * Returns JSON: `{ "instances": [f32... 8 per instance], "count": N, "by_species": {...} }`
 */
export function generate_vegetation(config_json: string): string;

/**
 * Generate water plane mesh + Gerstner wave parameters.
 * `config_json`: `{ "sea_level": 18, "extent": 512, "resolution": 128 }`
 * Returns JSON: `{ "vertices": [f32...], "indices": [u32...], "waves": [...], ... }`
 */
export function generate_water_mesh(config_json: string): string;

/**
 * Get the currently targeted block for JS HUD crosshair highlight.
 * Returns `{x, y, z, block}` or `null` if no block is targeted.
 * Reads from `window.__kami_target_block` closure set by `run_with_scene`.
 */
export function get_target_block(): any;

/**
 * Get VRM morph target names as JSON array.
 */
export function get_vrm_morph_names(): string;

export function invert_mat4(m: Float32Array): Float32Array;

/**
 * Check if current platform is mobile (iOS or Android).
 */
export function is_mobile(): boolean;

export function perspective(fov_y: number, aspect: number, near: number, far: number): Float32Array;

/**
 * Render a PPTX slide to a canvas using wgpu (WebGPU + WebGL2 fallback).
 *
 * # Arguments
 * * `canvas_id` — HTML canvas element ID.
 * * `slide_json` — JSON string matching `DocumentSlide` (shapes, dimensions, selection).
 *
 * # Returns
 * Resolves when the frame is rendered. Call again for each frame update.
 */
export function render_document_frame(canvas_id: string, slide_json: string): Promise<void>;

/**
 * Reset all VRM morph weights to 0.
 */
export function reset_vrm_morphs(): void;

/**
 * Create an SDP answer for a specific peer. Returns signal JSON.
 */
export function rtc_create_answer(to_peer_id: string, sdp: string): string;

/**
 * Create an ICE candidate message. Returns signal JSON.
 */
export function rtc_create_ice_candidate(to_peer_id: string, candidate_json: string): string;

/**
 * Create an SDP offer for a specific peer. Returns signal JSON.
 */
export function rtc_create_offer(to_peer_id: string, sdp: string): string;

/**
 * Create a WebRTC room and return the join signal as JSON.
 *
 * # Arguments
 * * `room_id` - Unique room identifier
 * * `local_peer_id` - Local user's peer ID (DID or session ID)
 * * `display_name` - Local user's display name
 * * `config_json` - Room configuration as JSON (optional, empty = defaults)
 */
export function rtc_create_room(room_id: string, local_peer_id: string, display_name: string, config_json: string): string;

/**
 * Leave the room and clean up. Returns leave signal JSON.
 */
export function rtc_leave_room(): string;

/**
 * Process an incoming signaling message. Returns events as JSON array.
 */
export function rtc_process_signal(signal_json: string): string;

/**
 * Get room summary as JSON.
 */
export function rtc_room_summary(): string;

/**
 * Send data channel message (cursor, annotation, reaction). Returns signal JSON.
 */
export function rtc_send_data(data_json: string): string;

/**
 * Run spatial audio spatialization. Returns JSON array of
 * `[peer_id, left_vol, right_vol, pan]` tuples.
 */
export function rtc_spatialize(): string;

/**
 * Update local position for spatial audio. Returns signal JSON to broadcast.
 */
export function rtc_update_position(x: number, y: number, z: number): string;

export function run(canvas_id: string): Promise<void>;

/**
 * Embed mode: auto-orbit camera, no keyboard input. For iframe/mascot embed.
 */
export function run_embed(canvas_id: string, scene_json: string): Promise<void>;

/**
 * NeRF: Density grid with noise + blur — simulates a learned 3D reconstruction.
 */
export function run_embed_nerf(canvas_id: string, resolution: number, volume_type: string): Promise<void>;

/**
 * Embed mode with OpenSCAD code: parse → SDF → voxelize → mesh → render.
 * Supports volume_type: "dense" | "sparse" | "octree".
 * SCAD: OpenSCAD text → parser → evaluator → per-entity SDF → mesh.
 * Each primitive is a separate entity (union = no fusion between parts).
 * This demonstrates what an LLM generates: human-readable CSG text.
 */
export function run_embed_scad(canvas_id: string, scad_code: string, resolution: number, volume_type: string): Promise<void>;

/**
 * SDF: Direct Rust SDF code — smooth union fuses parts organically.
 * This is what a programmer writes in Rust: mathematical distance functions.
 */
export function run_embed_sdf(canvas_id: string, resolution: number, volume_type: string): Promise<void>;

/**
 * SDF JSON-LD: Parse JSON-LD string into SDF tree → mesh → render.
 * Most LLM-efficient format (η=0.95).
 */
export function run_embed_sdf_jsonld(canvas_id: string, jsonld: string, resolution: number, volume_type: string): Promise<void>;

/**
 * Load VRM/GLB from URL and render with PBR pipeline.
 * Fetches GLB binary via JS fetch(), parses with gltf_loader, renders all primitives.
 */
export function run_embed_vrm(canvas_id: string, vrm_url: string): Promise<void>;

/**
 * Character Maker: CharacterDef JSON → parametric mesh → direct GPU upload → PBR render.
 *
 * Unlike run_embed (which uses IslandScene), this directly uploads kami-character mesh parts
 * as wgpu vertex/index buffers with per-material MaterialUniform bind groups.
 * Renders with the existing PBR shader (SSS skin, clearcoat eyes, anisotropic hair).
 */
export function run_with_character(canvas_id: string, character_json: string): Promise<void>;

/**
 * Goriketsu Dash!! — chase game on KAMI Engine.
 * Loads scene JSON-LD + runs GoriketsuGame logic each frame.
 * Top-down camera follows player. WASD move, E slap, Space sprint.
 */
export function run_with_game(canvas_id: string, scene_json: string, game_id: string): Promise<void>;

/**
 * System graph visualizer — renders haisen/SoS JSON as PCB-style graph via WebGPU.
 * PCB layout (grid + bus). Orthographic top-down camera. WASD pan, Space/Shift zoom.
 */
export function run_with_graph(canvas_id: string, graph_json: string, mode: string): Promise<void>;

/**
 * Run the quarry-walk demo inside a canvas.
 */
export function run_with_quarry_walk(canvas_id: string): Promise<void>;

/**
 * Sabi-Otoshi!! — 3D rust restoration game on KAMI Engine.
 * Turntable camera orbit, SDF items, NeRF rust, step-by-step disassembly.
 * Drag to rotate, scroll to zoom, Space/right-click to apply tool, E to disassemble, 1-6 tool select.
 */
export function run_with_sabiotoshi(canvas_id: string, scene_json: string): Promise<void>;

export function run_with_scene(canvas_id: string, scene_json: string): Promise<void>;

/**
 * Sample terrain height at world (x, z) with bilinear interpolation.
 * Returns 0 if outside the cached heightmap.
 */
export function sample_terrain_height(x: number, z: number): number;

/**
 * Set VRM camera orbit (yaw radians, pitch radians, distance).
 */
export function set_vrm_camera(yaw: number, pitch: number, distance: number): void;

/**
 * Set VRM morph target weight by index (0.0-1.0).
 * Call this from JS to animate face expressions.
 */
export function set_vrm_morph(index: number, weight: number): void;

/**
 * Set VRM morph target weight by name.
 */
export function set_vrm_morph_by_name(name: string, weight: number): void;

export function start(): void;

/**
 * Build `viewProj = perspective * lookAt` in one call (saves one WASM boundary crossing).
 */
export function view_projection(eye_x: number, eye_y: number, eye_z: number, target_x: number, target_y: number, target_z: number, fov_y: number, aspect: number, near: number, far: number): Float32Array;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly cache_vegetation: (a: number, b: number) => number;
    readonly clamp_bone: (a: number, b: number, c: number, d: number, e: number) => number;
    readonly compute_sky_uniform: (a: number) => [number, number];
    readonly compute_weather: (a: number, b: number) => [number, number];
    readonly compute_weather_preset: (a: number, b: number, c: number, d: number) => [number, number];
    readonly compute_wind_waves: (a: number, b: number, c: number, d: number) => [number, number];
    readonly cull_vegetation: (a: number, b: number, c: number) => [number, number];
    readonly detect_platform: () => [number, number];
    readonly evaluate_motion: (a: number, b: number, c: number) => [number, number];
    readonly generate_terrain_chunk: (a: number, b: number) => [number, number];
    readonly generate_vegetation: (a: number, b: number) => [number, number];
    readonly generate_water_mesh: (a: number, b: number) => [number, number];
    readonly get_target_block: () => any;
    readonly get_vrm_morph_names: () => [number, number];
    readonly is_mobile: () => number;
    readonly reset_vrm_morphs: () => void;
    readonly rtc_create_answer: (a: number, b: number, c: number, d: number) => [number, number];
    readonly rtc_create_ice_candidate: (a: number, b: number, c: number, d: number) => [number, number];
    readonly rtc_create_offer: (a: number, b: number, c: number, d: number) => [number, number];
    readonly rtc_create_room: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number) => [number, number];
    readonly rtc_leave_room: () => [number, number];
    readonly rtc_process_signal: (a: number, b: number) => [number, number];
    readonly rtc_room_summary: () => [number, number];
    readonly rtc_send_data: (a: number, b: number) => [number, number];
    readonly rtc_spatialize: () => [number, number];
    readonly rtc_update_position: (a: number, b: number, c: number) => [number, number];
    readonly run: (a: number, b: number) => any;
    readonly run_embed: (a: number, b: number, c: number, d: number) => any;
    readonly run_embed_nerf: (a: number, b: number, c: number, d: number, e: number) => any;
    readonly run_embed_scad: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
    readonly run_embed_sdf: (a: number, b: number, c: number, d: number, e: number) => any;
    readonly run_embed_sdf_jsonld: (a: number, b: number, c: number, d: number, e: number, f: number, g: number) => any;
    readonly run_embed_vrm: (a: number, b: number, c: number, d: number) => any;
    readonly run_with_character: (a: number, b: number, c: number, d: number) => any;
    readonly run_with_game: (a: number, b: number, c: number, d: number, e: number, f: number) => any;
    readonly run_with_graph: (a: number, b: number, c: number, d: number, e: number, f: number) => any;
    readonly run_with_sabiotoshi: (a: number, b: number, c: number, d: number) => any;
    readonly run_with_scene: (a: number, b: number, c: number, d: number) => any;
    readonly set_vrm_camera: (a: number, b: number, c: number) => void;
    readonly set_vrm_morph: (a: number, b: number) => void;
    readonly set_vrm_morph_by_name: (a: number, b: number, c: number) => void;
    readonly start: () => void;
    readonly cache_heightmap: (a: number, b: number) => number;
    readonly invert_mat4: (a: number, b: number) => [number, number];
    readonly perspective: (a: number, b: number, c: number, d: number) => [number, number];
    readonly sample_terrain_height: (a: number, b: number) => number;
    readonly view_projection: (a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number, j: number) => [number, number];
    readonly run_with_quarry_walk: (a: number, b: number) => any;
    readonly check_document_gpu: () => any;
    readonly document_gpu_info: () => any;
    readonly render_document_frame: (a: number, b: number, c: number, d: number) => any;
    readonly wasm_bindgen__closure__destroy__h099431940fb2f25c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h741d62785c1a078b: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h57bd9ab8f43c942e: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen__convert__closures_____invoke__h5db5e8dc2faf8fdd: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h013c750de6c22f52: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h013c750de6c22f52_1: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h013c750de6c22f52_2: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h013c750de6c22f52_3: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h8cad09eaeb7c0a22: (a: number, b: number) => any;
    readonly wasm_bindgen__convert__closures_____invoke__hed396ad1e81d846a: (a: number, b: number) => void;
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
