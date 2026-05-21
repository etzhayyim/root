/**
 * KAMI Engine WebGPU/WebGL2 Bridge — GPU-accelerated slide rendering with Canvas 2D fallback.
 *
 * Uses kami-web WASM (`render_document_frame`) for instanced SDF rect rendering
 * via wgpu (WebGPU primary, WebGL2 fallback ~97% browser coverage).
 *
 * Falls back to Canvas 2D (slide-renderer.ts) when WASM is not loaded.
 */

import type { PptxPresentation, PptxSlide, PptxShape } from "./ooxml-parser";

/** KAMI WASM module interface (wasm-bindgen exports). */
interface KamiDocModule {
  default: (input?: any) => Promise<any>;
  render_document_frame: (canvasId: string, slideJson: string) => Promise<void>;
  check_document_gpu: () => Promise<boolean>;
  document_gpu_info: () => Promise<string>;
}

let kamiMod: KamiDocModule | null = null;
let loadAttempted = false;

/** Check if GPU rendering is available (WebGPU or WebGL2). */
export async function checkWebGPU(): Promise<boolean> {
  if (kamiMod) {
    try { return await kamiMod.check_document_gpu(); } catch { /* fall through */ }
  }
  const nav = navigator as unknown as Record<string, unknown>;
  if (!nav.gpu) return false;
  try {
    const gpu = nav.gpu as { requestAdapter: () => Promise<unknown | null> };
    return (await gpu.requestAdapter()) !== null;
  } catch { return false; }
}

/** Get GPU adapter info string. */
export async function getGPUInfo(): Promise<string | null> {
  if (kamiMod) {
    try { return await kamiMod.document_gpu_info(); } catch { /* fall through */ }
  }
  return null;
}

/**
 * Load KAMI Engine WASM for GPU document rendering.
 *
 * Expects `kami_web.js` + `kami_web_bg.wasm` at `/pkg/` on the same origin,
 * or falls back to Canvas 2D if not available.
 */
export async function loadKamiEngine(): Promise<boolean> {
  if (kamiMod) return true;
  if (loadAttempted) return false;
  loadAttempted = true;
  try {
    const mod = await (Function('return import("/pkg/kami_web.js")')()) as KamiDocModule;
    await mod.default();
    kamiMod = mod;
    return true;
  } catch {
    console.warn("[kami-bridge] KAMI WASM not available, using Canvas 2D fallback");
    return false;
  }
}

/** Check if KAMI engine is loaded. */
export function isKamiReady(): boolean { return kamiMod !== null; }

/**
 * Convert a PptxSlide to JSON format expected by `render_document_frame`.
 *
 * Maps PptxSlide to DocumentSlide (Rust serde-compatible).
 */
function slideToDocumentJson(
  slide: PptxSlide,
  pres: PptxPresentation,
  selectedShapeIds: string[],
): string {
  return JSON.stringify({
    width: pres.width,
    height: pres.height,
    background: slide.background,
    shapes: slide.shapes.map((s: PptxShape) => ({
      id: s.id,
      type: s.type,
      x: s.x,
      y: s.y,
      w: s.w,
      h: s.h,
      rotation: s.rotation,
      fill: s.fill,
      stroke: s.stroke,
      strokeWidth: s.strokeWidth,
      cornerRadius: s.cornerRadius ?? null,
      visible: s.visible ?? true,
      text: s.textBody?.paragraphs.map(p => p.runs.map(r => r.text).join("")).join("\n") || null,
      textColor: s.textBody?.paragraphs[0]?.runs[0]?.color ?? null,
      textSize: s.textBody?.paragraphs[0]?.runs[0]?.size ?? null,
      textBold: s.textBody?.paragraphs[0]?.runs[0]?.bold ?? null,
    })),
    selectedIds: selectedShapeIds,
  });
}

/**
 * Render a slide using KAMI Engine wgpu (WebGPU + WebGL2 fallback).
 *
 * @param canvasId - HTML canvas element ID for wgpu surface.
 * @param slide - Slide to render.
 * @param pres - Parent presentation (for dimensions).
 * @param selectedShapeIds - Currently selected shape IDs (for selection handles).
 * @returns true if rendered via GPU, false if not available (use Canvas 2D fallback).
 */
export async function renderSlideGPU(
  canvasId: string,
  slide: PptxSlide,
  pres: PptxPresentation,
  selectedShapeIds: string[] = [],
): Promise<boolean> {
  if (!kamiMod) return false;
  try {
    const json = slideToDocumentJson(slide, pres, selectedShapeIds);
    await kamiMod.render_document_frame(canvasId, json);
    return true;
  } catch (err) {
    console.warn("[kami-bridge] GPU render failed, falling back to Canvas 2D:", err);
    return false;
  }
}
