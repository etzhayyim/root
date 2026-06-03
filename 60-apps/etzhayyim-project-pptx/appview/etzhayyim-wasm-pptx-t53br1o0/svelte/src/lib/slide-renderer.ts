/**
 * Slide Renderer — Canvas 2D rendering of PptxSlide for the editor viewport.
 *
 * Renders slides to an OffscreenCanvas or HTMLCanvasElement using Canvas 2D API.
 * This serves as the primary rendering path; KAMI Engine WebGPU integration
 * is loaded optionally when available for GPU-accelerated rendering.
 *
 * EMU (English Metric Unit) coordinate system: 1 inch = 914400 EMU.
 * All OOXML coordinates are in EMU; we convert to canvas pixels via a scale factor.
 */

import type {
  PptxPresentation,
  PptxSlide,
  PptxShape,
  PptxImage,
  PptxTextBody,
  Emu,
} from "./ooxml-parser";

import { renderHandles, unionBounds, getHandlePositions, type Bounds } from "./transform-handles";

/** Conversion factor from EMU to pixels at 96 DPI. */
const EMU_PER_INCH = 914400;
const PX_PER_INCH = 96;
const EMU_TO_PX = PX_PER_INCH / EMU_PER_INCH;

/** Convert EMU to canvas pixels, with optional viewport scale. */
export function emuToPx(emu: Emu, scale: number = 1): number {
  return emu * EMU_TO_PX * scale;
}

/** Compute the scale factor to fit a presentation into a viewport. */
export function computeFitScale(
  presWidth: Emu,
  presHeight: Emu,
  viewportWidth: number,
  viewportHeight: number,
  padding: number = 20,
): number {
  const pxW = emuToPx(presWidth);
  const pxH = emuToPx(presHeight);
  const scaleX = (viewportWidth - padding * 2) / pxW;
  const scaleY = (viewportHeight - padding * 2) / pxH;
  return Math.min(scaleX, scaleY, 1);
}

/** Image blob cache: imageId → ObjectURL. */
const imageBlobCache = new Map<string, string>();

/** Pre-cache image blobs as object URLs for rendering. */
export function cacheImageBlobs(slides: PptxSlide[]): void {
  for (const slide of slides) {
    for (const img of slide.images) {
      if (img.blob && !imageBlobCache.has(img.id)) {
        const blob = new Blob([img.blob.buffer as ArrayBuffer], { type: img.mime });
        imageBlobCache.set(img.id, URL.createObjectURL(blob));
      }
    }
  }
}

/** Release all cached image object URLs. */
export function releaseBlobCache(): void {
  for (const url of imageBlobCache.values()) {
    URL.revokeObjectURL(url);
  }
  imageBlobCache.clear();
}

/** Loaded HTMLImageElement cache for rendering. */
const loadedImages = new Map<string, HTMLImageElement>();

/** Load an image element from the blob cache. */
async function loadImage(imageId: string): Promise<HTMLImageElement | null> {
  if (loadedImages.has(imageId)) return loadedImages.get(imageId)!;

  const url = imageBlobCache.get(imageId);
  if (!url) return null;

  return new Promise((resolve) => {
    const el = new Image();
    el.onload = () => {
      loadedImages.set(imageId, el);
      resolve(el);
    };
    el.onerror = () => resolve(null);
    el.src = url;
  });
}

// ---------------------------------------------------------------------------
// Path2D cache for shape rendering performance
// ---------------------------------------------------------------------------

/** Cache entry for a shape's Path2D object. */
interface PathCacheEntry {
  path: Path2D;
  hash: string;
}

/** Path2D cache keyed by shape ID. */
const pathCache = new Map<string, PathCacheEntry>();

/** Generate a hash string for shape geometry. */
function shapeGeometryHash(shape: PptxShape, scale: number): string {
  return `${shape.type}_${shape.x}_${shape.y}_${shape.w}_${shape.h}_${shape.rotation}_${shape.cornerRadius ?? 0}_${scale}`;
}

/** Clear cache entries for shapes that no longer exist. */
export function prunePathCache(activeIds: Set<string>): void {
  for (const id of pathCache.keys()) {
    if (!activeIds.has(id)) pathCache.delete(id);
  }
}

// ---------------------------------------------------------------------------
// Grid overlay rendering
// ---------------------------------------------------------------------------

/**
 * Render a dot grid overlay on the slide canvas.
 *
 * @param ctx - Canvas 2D rendering context.
 * @param presWidth - Presentation width in EMU.
 * @param presHeight - Presentation height in EMU.
 * @param scale - Current viewport scale.
 * @param gridSize - Grid spacing in EMU (default: 114300 = 1/8 inch).
 */
export function renderGrid(
  ctx: CanvasRenderingContext2D,
  presWidth: Emu,
  presHeight: Emu,
  scale: number,
  gridSize: Emu,
): void {
  const slideW = emuToPx(presWidth, scale);
  const slideH = emuToPx(presHeight, scale);
  const stepPx = emuToPx(gridSize, scale);

  if (stepPx < 4) return; // Too dense to render

  ctx.fillStyle = "rgba(255, 255, 255, 0.08)";

  for (let gx = 0; gx <= slideW; gx += stepPx) {
    for (let gy = 0; gy <= slideH; gy += stepPx) {
      ctx.fillRect(Math.round(gx), Math.round(gy), 1, 1);
    }
  }
}

// ---------------------------------------------------------------------------
// Main render function
// ---------------------------------------------------------------------------

/** Options for grid overlay rendering. */
export interface GridOptions {
  showGrid: boolean;
  gridSize: number;
}

/** Render a single slide to a Canvas 2D context. */
export async function renderSlide(
  ctx: CanvasRenderingContext2D,
  slide: PptxSlide,
  pres: PptxPresentation,
  scale: number,
  selectedShapeIds: string[] = [],
  gridOptions?: GridOptions,
): Promise<void> {
  const w = emuToPx(pres.width, scale);
  const h = emuToPx(pres.height, scale);

  // Clear and draw slide background
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  // Center the slide
  const offsetX = (ctx.canvas.width - w) / 2;
  const offsetY = (ctx.canvas.height - h) / 2;

  ctx.save();
  ctx.translate(offsetX, offsetY);

  // Slide background
  ctx.fillStyle = slide.background ? `#${slide.background}` : "#ffffff";
  ctx.fillRect(0, 0, w, h);

  // Slide border
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 1;
  ctx.strokeRect(0, 0, w, h);

  // Grid overlay (between background and shapes)
  if (gridOptions?.showGrid) {
    renderGrid(ctx, pres.width, pres.height, scale, gridOptions.gridSize);
  }

  // Render images first (below shapes)
  for (const img of slide.images) {
    await renderImage(ctx, img, scale);
  }

  // Build selected set for quick lookup
  const selectedSet = new Set(selectedShapeIds);

  // Render shapes (skip hidden ones)
  for (const shape of slide.shapes) {
    if (shape.visible === false) continue;
    renderShape(ctx, shape, scale, false);
  }

  ctx.restore();

  // Render selection handles outside the slide transform
  if (selectedShapeIds.length > 0) {
    const selectedShapes = slide.shapes.filter((s) => selectedSet.has(s.id));
    if (selectedShapes.length === 1) {
      const s = selectedShapes[0];
      const crEmu = s.type === "roundRect" ? (s.cornerRadius ?? Math.round(Math.min(s.w, s.h) * 0.1)) : undefined;
      renderHandles(ctx, { x: s.x, y: s.y, w: s.w, h: s.h }, scale, offsetX, offsetY, s.rotation, crEmu);
    } else if (selectedShapes.length > 1) {
      const bounds = unionBounds(selectedShapes.map((s) => ({ x: s.x, y: s.y, w: s.w, h: s.h })));
      if (bounds) {
        renderHandles(ctx, bounds, scale, offsetX, offsetY, 0);
      }
    }
  }
}

/** Render a single shape (without selection indicators — handled separately). */
function renderShape(
  ctx: CanvasRenderingContext2D,
  shape: PptxShape,
  scale: number,
  _selected: boolean,
): void {
  const x = emuToPx(shape.x, scale);
  const y = emuToPx(shape.y, scale);
  const w = emuToPx(shape.w, scale);
  const h = emuToPx(shape.h, scale);

  ctx.save();

  // Apply rotation around shape center
  if (shape.rotation !== 0) {
    ctx.translate(x + w / 2, y + h / 2);
    ctx.rotate((shape.rotation * Math.PI) / 180);
    ctx.translate(-(x + w / 2), -(y + h / 2));
  }

  // Draw shape geometry
  ctx.beginPath();
  switch (shape.type) {
    case "ellipse":
      ctx.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, 0, Math.PI * 2);
      break;
    case "roundRect": {
      const rEmu = shape.cornerRadius ?? Math.round(Math.min(shape.w, shape.h) * 0.1);
      const r = emuToPx(rEmu, scale);
      ctx.roundRect(x, y, w, h, r);
      break;
    }
    case "triangle":
      ctx.moveTo(x + w / 2, y);
      ctx.lineTo(x + w, y + h);
      ctx.lineTo(x, y + h);
      ctx.closePath();
      break;
    case "line":
      ctx.moveTo(x, y);
      ctx.lineTo(x + w, y + h);
      break;
    case "arrow":
      drawArrow(ctx, x, y, w, h);
      break;
    default: // rect, textBox, freeform
      ctx.rect(x, y, w, h);
      break;
  }

  // Fill
  if (shape.fill && shape.type !== "line") {
    ctx.fillStyle = `#${shape.fill}`;
    ctx.fill();
  }

  // Stroke
  if (shape.stroke || shape.type === "line") {
    ctx.strokeStyle = shape.stroke ? `#${shape.stroke}` : "#000000";
    ctx.lineWidth = Math.max(1, emuToPx(shape.strokeWidth, scale));
    ctx.stroke();
  }

  // Text body
  if (shape.textBody) {
    renderTextBody(ctx, shape.textBody, x, y, w, h, scale);
  }

  ctx.restore();
}

/** Draw an arrow shape. */
function drawArrow(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
): void {
  const shaftH = h * 0.4;
  const headW = w * 0.3;
  ctx.moveTo(x, y + h / 2 - shaftH / 2);
  ctx.lineTo(x + w - headW, y + h / 2 - shaftH / 2);
  ctx.lineTo(x + w - headW, y);
  ctx.lineTo(x + w, y + h / 2);
  ctx.lineTo(x + w - headW, y + h);
  ctx.lineTo(x + w - headW, y + h / 2 + shaftH / 2);
  ctx.lineTo(x, y + h / 2 + shaftH / 2);
  ctx.closePath();
}

/** Render text body inside a shape bounding box. */
function renderTextBody(
  ctx: CanvasRenderingContext2D,
  tb: PptxTextBody,
  x: number,
  y: number,
  w: number,
  h: number,
  scale: number,
): void {
  const padding = 4 * scale;
  let textY = y + padding;

  // Vertical alignment offset
  const totalTextHeight = estimateTextHeight(tb, scale);
  if (tb.verticalAlign === "middle") {
    textY = y + (h - totalTextHeight) / 2;
  } else if (tb.verticalAlign === "bottom") {
    textY = y + h - totalTextHeight - padding;
  }

  ctx.save();
  ctx.rect(x, y, w, h);
  ctx.clip();

  for (const para of tb.paragraphs) {
    let lineX = x + padding;
    const lineMaxW = w - padding * 2;

    for (const run of para.runs) {
      const fontSize = (run.size / 100) * scale;
      const fontStyle = `${run.italic ? "italic " : ""}${run.bold ? "bold " : ""}${fontSize}px "${run.font}", sans-serif`;
      ctx.font = fontStyle;
      ctx.fillStyle = `#${run.color}`;
      ctx.textBaseline = "top";

      // Alignment
      const textWidth = ctx.measureText(run.text).width;
      if (tb.align === "center") {
        lineX = x + (w - textWidth) / 2;
      } else if (tb.align === "right") {
        lineX = x + w - padding - textWidth;
      }

      ctx.fillText(run.text, lineX, textY, lineMaxW);
      lineX += textWidth;
    }

    textY += estimateParaHeight(para, scale);
  }

  ctx.restore();
}

/** Estimate total text height for vertical alignment. */
function estimateTextHeight(tb: PptxTextBody, scale: number): number {
  let total = 0;
  for (const para of tb.paragraphs) {
    total += estimateParaHeight(para, scale);
  }
  return total;
}

/** Estimate paragraph height. */
function estimateParaHeight(para: { runs: { size: number }[] }, scale: number): number {
  const maxSize = Math.max(...para.runs.map((r) => r.size), 1800);
  return (maxSize / 100) * scale * 1.3; // 1.3x line height
}

/** Render an image element. */
async function renderImage(
  ctx: CanvasRenderingContext2D,
  img: PptxImage,
  scale: number,
): Promise<void> {
  const el = await loadImage(img.id);
  if (!el) return;

  const x = emuToPx(img.x, scale);
  const y = emuToPx(img.y, scale);
  const w = emuToPx(img.w, scale);
  const h = emuToPx(img.h, scale);

  ctx.drawImage(el, x, y, w, h);
}

// ---------------------------------------------------------------------------
// Rubber band renderer
// ---------------------------------------------------------------------------

/**
 * Render a rubber band selection rectangle on the canvas.
 *
 * @param ctx - Canvas 2D rendering context.
 * @param startX - Start X in canvas pixels.
 * @param startY - Start Y in canvas pixels.
 * @param endX - End X in canvas pixels.
 * @param endY - End Y in canvas pixels.
 */
export function renderRubberBand(
  ctx: CanvasRenderingContext2D,
  startX: number,
  startY: number,
  endX: number,
  endY: number,
): void {
  const x = Math.min(startX, endX);
  const y = Math.min(startY, endY);
  const w = Math.abs(endX - startX);
  const h = Math.abs(endY - startY);

  ctx.save();
  ctx.fillStyle = "rgba(74, 144, 249, 0.1)";
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = "rgba(74, 144, 249, 0.6)";
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 2]);
  ctx.strokeRect(x, y, w, h);
  ctx.setLineDash([]);
  ctx.restore();
}

// ---------------------------------------------------------------------------
// Thumbnail renderer
// ---------------------------------------------------------------------------

/** Render a small thumbnail of a slide (for slide panel). */
export async function renderThumbnail(
  canvas: HTMLCanvasElement,
  slide: PptxSlide,
  pres: PptxPresentation,
): Promise<void> {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const thumbScale = computeFitScale(pres.width, pres.height, canvas.width, canvas.height, 4);
  await renderSlide(ctx, slide, pres, thumbScale);
}

// ---------------------------------------------------------------------------
// Hit testing for editor interaction
// ---------------------------------------------------------------------------

/** Find which shape (if any) is at the given canvas coordinates. */
export function hitTestShapes(
  slide: PptxSlide,
  pres: PptxPresentation,
  canvasX: number,
  canvasY: number,
  canvasWidth: number,
  canvasHeight: number,
  scale: number,
): PptxShape | null {
  const w = emuToPx(pres.width, scale);
  const h = emuToPx(pres.height, scale);
  const offsetX = (canvasWidth - w) / 2;
  const offsetY = (canvasHeight - h) / 2;

  // Convert to slide coordinate space
  const sx = canvasX - offsetX;
  const sy = canvasY - offsetY;

  // Iterate in reverse (top-most shape first), skip locked/hidden shapes
  for (let i = slide.shapes.length - 1; i >= 0; i--) {
    const shape = slide.shapes[i];
    if (shape.locked || shape.visible === false) continue;
    const x = emuToPx(shape.x, scale);
    const y = emuToPx(shape.y, scale);
    const sw = emuToPx(shape.w, scale);
    const sh = emuToPx(shape.h, scale);

    if (sx >= x && sx <= x + sw && sy >= y && sy <= y + sh) {
      return shape;
    }
  }

  return null;
}

/**
 * Find all shapes that intersect with a rectangle in canvas coordinates.
 *
 * @param slide - Current slide.
 * @param pres - Current presentation.
 * @param rectX - Rectangle X in canvas pixels.
 * @param rectY - Rectangle Y in canvas pixels.
 * @param rectW - Rectangle width in canvas pixels.
 * @param rectH - Rectangle height in canvas pixels.
 * @param canvasWidth - Canvas width.
 * @param canvasHeight - Canvas height.
 * @param scale - Current scale.
 * @returns Array of shapes within the rectangle.
 */
export function hitTestRect(
  slide: PptxSlide,
  pres: PptxPresentation,
  rectX: number,
  rectY: number,
  rectW: number,
  rectH: number,
  canvasWidth: number,
  canvasHeight: number,
  scale: number,
): PptxShape[] {
  const w = emuToPx(pres.width, scale);
  const h = emuToPx(pres.height, scale);
  const offsetX = (canvasWidth - w) / 2;
  const offsetY = (canvasHeight - h) / 2;

  const rx1 = rectX - offsetX;
  const ry1 = rectY - offsetY;
  const rx2 = rx1 + rectW;
  const ry2 = ry1 + rectH;

  const result: PptxShape[] = [];
  for (const shape of slide.shapes) {
    if (shape.locked || shape.visible === false) continue;
    const sx1 = emuToPx(shape.x, scale);
    const sy1 = emuToPx(shape.y, scale);
    const sx2 = sx1 + emuToPx(shape.w, scale);
    const sy2 = sy1 + emuToPx(shape.h, scale);

    // Intersection test
    if (sx1 < rx2 && sx2 > rx1 && sy1 < ry2 && sy2 > ry1) {
      result.push(shape);
    }
  }
  return result;
}
