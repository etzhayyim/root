/**
 * Transform Handles — Interactive resize and rotation handles for shape selection.
 *
 * Provides hit testing, position computation, resize/rotation math, cursor
 * feedback, and Canvas 2D rendering for 8 resize handles + 1 rotation handle.
 */

/** Handle types for the 8 resize corners/edges, 1 rotation handle, and 1 corner radius handle. */
export type HandleType = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w" | "rotation" | "cornerRadius";

/** Bounding rectangle in EMU or pixel coordinates. */
export interface Bounds {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** Canvas-space handle position with its type. */
export interface HandlePosition {
  type: HandleType;
  cx: number;
  cy: number;
}

/**
 * Compute canvas-space positions for all 9+ handles (8 resize + 1 rotation + optional cornerRadius).
 *
 * Rotation handle is placed 30px above the top-center handle.
 * Corner radius handle (orange) is placed at (x + cornerRadius, y) for roundRect shapes.
 *
 * @param bounds - Shape bounding rect in EMU.
 * @param scale - EMU-to-pixel scale factor (emuToPx scale).
 * @param offsetX - Canvas X offset for slide centering.
 * @param offsetY - Canvas Y offset for slide centering.
 * @param cornerRadiusEmu - Optional corner radius in EMU for roundRect shapes.
 * @returns Array of handle positions in canvas pixel space.
 */
export function getHandlePositions(
  bounds: Bounds,
  scale: number,
  offsetX: number,
  offsetY: number,
  cornerRadiusEmu?: number,
): HandlePosition[] {
  const emuToPx = (emu: number): number => emu * (96 / 914400) * scale;

  const x = offsetX + emuToPx(bounds.x);
  const y = offsetY + emuToPx(bounds.y);
  const w = emuToPx(bounds.w);
  const h = emuToPx(bounds.h);

  const mx = x + w / 2;
  const my = y + h / 2;
  const rotDist = 30;

  const handles: HandlePosition[] = [
    { type: "nw", cx: x, cy: y },
    { type: "n", cx: mx, cy: y },
    { type: "ne", cx: x + w, cy: y },
    { type: "e", cx: x + w, cy: my },
    { type: "se", cx: x + w, cy: y + h },
    { type: "s", cx: mx, cy: y + h },
    { type: "sw", cx: x, cy: y + h },
    { type: "w", cx: x, cy: my },
    { type: "rotation", cx: mx, cy: y - rotDist },
  ];

  if (cornerRadiusEmu !== undefined) {
    const crPx = emuToPx(cornerRadiusEmu);
    handles.push({ type: "cornerRadius", cx: x + crPx, cy: y });
  }

  return handles;
}

/**
 * Compute new corner radius from a drag delta.
 *
 * @param startRadius - Starting corner radius in EMU.
 * @param dx - Delta X in EMU from drag start.
 * @param maxRadius - Maximum allowed radius (min(w, h) / 2).
 * @returns Clamped corner radius in EMU.
 */
export function computeCornerRadius(startRadius: number, dx: number, maxRadius: number): number {
  return Math.max(0, Math.min(maxRadius, startRadius + dx));
}

/**
 * Hit test handle positions against a mouse coordinate.
 *
 * @param positions - Handle positions from getHandlePositions.
 * @param mouseX - Mouse X in canvas pixel space.
 * @param mouseY - Mouse Y in canvas pixel space.
 * @param handleSize - Hit area half-size in pixels. Default: 10.
 * @returns The HandleType if a handle was hit, or null.
 */
export function hitTestHandle(
  positions: HandlePosition[],
  mouseX: number,
  mouseY: number,
  handleSize: number = 10,
): HandleType | null {
  for (const pos of positions) {
    const dx = mouseX - pos.cx;
    const dy = mouseY - pos.cy;
    if (pos.type === "rotation" || pos.type === "cornerRadius") {
      // Circle hit test for rotation and corner radius handles
      if (dx * dx + dy * dy <= handleSize * handleSize) return pos.type;
    } else {
      if (Math.abs(dx) <= handleSize / 2 && Math.abs(dy) <= handleSize / 2) return pos.type;
    }
  }
  return null;
}

/**
 * Compute new bounds after a resize drag operation.
 *
 * Corner handles move the corner while fixing the opposite corner.
 * Edge handles change one dimension only.
 * Shift key constrains aspect ratio.
 *
 * @param handleType - Which handle is being dragged.
 * @param originalBounds - Original bounds before drag started (EMU).
 * @param dx - Delta X in EMU from drag start.
 * @param dy - Delta Y in EMU from drag start.
 * @param shiftHeld - Whether shift is held for aspect ratio constraint.
 * @returns New bounds in EMU.
 */
export function computeResize(
  handleType: HandleType,
  originalBounds: Bounds,
  dx: number,
  dy: number,
  shiftHeld: boolean,
): Bounds {
  let { x, y, w, h } = originalBounds;
  const aspect = w / (h || 1);

  switch (handleType) {
    case "nw":
      x += dx; y += dy; w -= dx; h -= dy;
      break;
    case "n":
      y += dy; h -= dy;
      break;
    case "ne":
      w += dx; y += dy; h -= dy;
      break;
    case "e":
      w += dx;
      break;
    case "se":
      w += dx; h += dy;
      break;
    case "s":
      h += dy;
      break;
    case "sw":
      x += dx; w -= dx; h += dy;
      break;
    case "w":
      x += dx; w -= dx;
      break;
  }

  // Enforce minimum size
  const minSize = 50000; // ~0.05 inches
  if (w < minSize) { if (handleType.includes("w")) x -= minSize - w; w = minSize; }
  if (h < minSize) { if (handleType.includes("n")) y -= minSize - h; h = minSize; }

  // Shift: constrain aspect ratio
  if (shiftHeld && (handleType === "nw" || handleType === "ne" || handleType === "se" || handleType === "sw")) {
    const newAspect = w / (h || 1);
    if (newAspect > aspect) {
      w = Math.round(h * aspect);
    } else {
      h = Math.round(w / aspect);
    }
    // Re-anchor for top-left handles
    if (handleType === "nw") {
      x = originalBounds.x + originalBounds.w - w;
      y = originalBounds.y + originalBounds.h - h;
    } else if (handleType === "ne") {
      y = originalBounds.y + originalBounds.h - h;
    } else if (handleType === "sw") {
      x = originalBounds.x + originalBounds.w - w;
    }
  }

  return { x, y, w, h };
}

/**
 * Compute rotation angle from center to mouse position.
 *
 * @param centerX - Shape center X in canvas pixels.
 * @param centerY - Shape center Y in canvas pixels.
 * @param mouseX - Current mouse X in canvas pixels.
 * @param mouseY - Current mouse Y in canvas pixels.
 * @param shiftHeld - Snap to 15-degree increments.
 * @returns Rotation in degrees (0-360).
 */
export function computeRotation(
  centerX: number,
  centerY: number,
  mouseX: number,
  mouseY: number,
  shiftHeld: boolean,
): number {
  let angle = Math.atan2(mouseX - centerX, -(mouseY - centerY)) * (180 / Math.PI);
  if (angle < 0) angle += 360;
  if (shiftHeld) {
    angle = Math.round(angle / 15) * 15;
  }
  return angle;
}

/** Cursor direction map for resize handles at 0 rotation. */
const BASE_CURSORS: Record<Exclude<HandleType, "rotation">, number> = {
  n: 0,
  ne: 1,
  e: 2,
  se: 3,
  s: 4,
  sw: 5,
  w: 6,
  nw: 7,
};

const CURSOR_NAMES = [
  "ns-resize",
  "nesw-resize",
  "ew-resize",
  "nwse-resize",
  "ns-resize",
  "nesw-resize",
  "ew-resize",
  "nwse-resize",
];

/**
 * Get the CSS cursor string for a handle type, adjusted for shape rotation.
 *
 * Rotates cursor direction by shape rotation in 45-degree increments.
 *
 * @param handleType - Handle being hovered.
 * @param rotation - Current shape rotation in degrees.
 * @returns CSS cursor string.
 */
export function getHandleCursor(handleType: HandleType, rotation: number): string {
  if (handleType === "rotation") return "grab";
  if (handleType === "cornerRadius") return "ew-resize";
  const baseIdx = BASE_CURSORS[handleType as Exclude<HandleType, "rotation" | "cornerRadius">];
  const rotSteps = Math.round(((rotation % 360) + 360) % 360 / 45);
  const idx = (baseIdx + rotSteps) % 8;
  return CURSOR_NAMES[idx];
}

/**
 * Render selection handles on the canvas for a shape.
 *
 * Draws white-fill, 1px #4a90d9 stroke, 8x8px squares for resize handles
 * and a 10px circle for the rotation handle, connected by a thin line.
 *
 * @param ctx - Canvas 2D rendering context.
 * @param bounds - Shape bounds in EMU.
 * @param scale - EMU-to-pixel scale factor.
 * @param offsetX - Canvas X offset for slide centering.
 * @param offsetY - Canvas Y offset for slide centering.
 * @param rotation - Shape rotation in degrees (used for visual rotation of handles).
 */
export function renderHandles(
  ctx: CanvasRenderingContext2D,
  bounds: Bounds,
  scale: number,
  offsetX: number,
  offsetY: number,
  rotation: number = 0,
  cornerRadiusEmu?: number,
): void {
  const positions = getHandlePositions(bounds, scale, offsetX, offsetY, cornerRadiusEmu);

  ctx.save();

  // If rotated, rotate the entire handle set around the shape center
  if (rotation !== 0) {
    const emuToPx = (emu: number): number => emu * (96 / 914400) * scale;
    const cx = offsetX + emuToPx(bounds.x) + emuToPx(bounds.w) / 2;
    const cy = offsetY + emuToPx(bounds.y) + emuToPx(bounds.h) / 2;
    ctx.translate(cx, cy);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.translate(-cx, -cy);
  }

  const handleSize = 8;
  const half = handleSize / 2;

  // Draw the dashed selection rectangle
  const emuToPx = (emu: number): number => emu * (96 / 914400) * scale;
  const rx = offsetX + emuToPx(bounds.x);
  const ry = offsetY + emuToPx(bounds.y);
  const rw = emuToPx(bounds.w);
  const rh = emuToPx(bounds.h);

  ctx.strokeStyle = "#4a90d9";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 3]);
  ctx.strokeRect(rx - 3, ry - 3, rw + 6, rh + 6);
  ctx.setLineDash([]);

  // Line from top-center to rotation handle
  const topCenter = positions.find((p) => p.type === "n")!;
  const rotHandle = positions.find((p) => p.type === "rotation")!;
  ctx.strokeStyle = "#4a90d9";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(topCenter.cx, topCenter.cy);
  ctx.lineTo(rotHandle.cx, rotHandle.cy);
  ctx.stroke();

  // Resize handles (squares) and corner radius handle (orange circle)
  for (const pos of positions) {
    if (pos.type === "rotation") continue;
    if (pos.type === "cornerRadius") {
      // Orange circle for corner radius handle
      ctx.fillStyle = "#ff8c00";
      ctx.strokeStyle = "#cc6600";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(pos.cx, pos.cy, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      continue;
    }
    ctx.fillStyle = "#ffffff";
    ctx.strokeStyle = "#4a90d9";
    ctx.lineWidth = 1;
    ctx.fillRect(pos.cx - half, pos.cy - half, handleSize, handleSize);
    ctx.strokeRect(pos.cx - half, pos.cy - half, handleSize, handleSize);
  }

  // Rotation handle (circle)
  ctx.fillStyle = "#ffffff";
  ctx.strokeStyle = "#4a90d9";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(rotHandle.cx, rotHandle.cy, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.restore();
}

/**
 * Compute the union bounding box for multiple shape bounds.
 *
 * @param shapes - Array of shape bounds in EMU.
 * @returns Union bounding box, or null if empty.
 */
export function unionBounds(shapes: Bounds[]): Bounds | null {
  if (shapes.length === 0) return null;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const s of shapes) {
    minX = Math.min(minX, s.x);
    minY = Math.min(minY, s.y);
    maxX = Math.max(maxX, s.x + s.w);
    maxY = Math.max(maxY, s.y + s.h);
  }
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}
