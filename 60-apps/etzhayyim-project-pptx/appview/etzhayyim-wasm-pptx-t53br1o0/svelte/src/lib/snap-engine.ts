/**
 * Snap Engine — Smart guides and snapping for Figma-like editing UX.
 *
 * Detects alignment of shape edges/centers against all other shapes on the slide,
 * returning snapped positions and guide lines to render.
 * Equal spacing detection finds matching gaps between consecutive shapes.
 */

import type { Emu } from "./ooxml-parser";

/** A guide line to render on the canvas. */
export interface GuideLine {
  /** Axis this guide runs along. */
  axis: "x" | "y";
  /** Position in EMU on the perpendicular axis. */
  position: Emu;
  /** Type of alignment detected. */
  type: "edge" | "center" | "spacing";
}

/** Shape bounds used for snapping calculations. */
export interface ShapeBounds {
  id: string;
  x: Emu;
  y: Emu;
  w: Emu;
  h: Emu;
}

/** Options for snap computation. */
export interface SnapOptions {
  /** Snap threshold in CSS pixels (converted to EMU via scale). Default: 5. */
  threshold?: number;
  /** Enable edge snapping. Default: true. */
  snapEdges?: boolean;
  /** Enable center snapping. Default: true. */
  snapCenters?: boolean;
  /** Enable equal spacing detection. Default: true. */
  snapSpacing?: boolean;
}

/** Result from snap computation. */
export interface SnapResult {
  /** Snapped X position in EMU (or original if no snap). */
  snappedX: Emu;
  /** Snapped Y position in EMU (or original if no snap). */
  snappedY: Emu;
  /** Guide lines to render. */
  guides: GuideLine[];
}

/** EMU conversion constants. */
const EMU_PER_INCH = 914400;
const PX_PER_INCH = 96;

/**
 * Convert CSS pixel threshold to EMU given the current viewport scale.
 * @param cssPx - Threshold in CSS pixels.
 * @param scale - Current viewport scale factor.
 */
function pxToEmu(cssPx: number, scale: number): Emu {
  return Math.round((cssPx / (PX_PER_INCH * scale)) * EMU_PER_INCH);
}

/**
 * Compute snap guides for a moving shape against all other shapes on the slide.
 *
 * Checks alignment of left, right, top, bottom, centerX, centerY of the moving
 * shape against corresponding edges/centers of all other shapes.
 * Also detects equal spacing between consecutive shapes on each axis.
 *
 * @param movingBounds - Current bounds of the shape being moved.
 * @param allShapes - All shapes on the slide (moving shape is excluded by id).
 * @param scale - Current viewport scale.
 * @param options - Snap options.
 * @returns Snapped position and guide lines.
 */
export function computeSnapGuides(
  movingBounds: ShapeBounds,
  allShapes: ShapeBounds[],
  scale: number,
  options: SnapOptions = {},
): SnapResult {
  const threshold = pxToEmu(options.threshold ?? 5, scale);
  const snapEdges = options.snapEdges ?? true;
  const snapCenters = options.snapCenters ?? true;
  const snapSpacing = options.snapSpacing ?? true;

  const others = allShapes.filter((s) => s.id !== movingBounds.id);
  if (others.length === 0) {
    return { snappedX: movingBounds.x, snappedY: movingBounds.y, guides: [] };
  }

  const guides: GuideLine[] = [];
  let bestDx: number | null = null;
  let bestDxDist = Infinity;
  let bestDy: number | null = null;
  let bestDyDist = Infinity;

  const mLeft = movingBounds.x;
  const mRight = movingBounds.x + movingBounds.w;
  const mCx = movingBounds.x + movingBounds.w / 2;
  const mTop = movingBounds.y;
  const mBottom = movingBounds.y + movingBounds.h;
  const mCy = movingBounds.y + movingBounds.h / 2;

  for (const other of others) {
    const oLeft = other.x;
    const oRight = other.x + other.w;
    const oCx = other.x + other.w / 2;
    const oTop = other.y;
    const oBottom = other.y + other.h;
    const oCy = other.y + other.h / 2;

    if (snapEdges) {
      // X-axis edge snaps: left-left, left-right, right-left, right-right
      checkSnap(mLeft, oLeft, 0, threshold, "x", oLeft, "edge");
      checkSnap(mLeft, oRight, 0, threshold, "x", oRight, "edge");
      checkSnap(mRight, oLeft, -movingBounds.w, threshold, "x", oLeft, "edge");
      checkSnap(mRight, oRight, -movingBounds.w, threshold, "x", oRight, "edge");

      // Y-axis edge snaps: top-top, top-bottom, bottom-top, bottom-bottom
      checkSnap(mTop, oTop, 0, threshold, "y", oTop, "edge");
      checkSnap(mTop, oBottom, 0, threshold, "y", oBottom, "edge");
      checkSnap(mBottom, oTop, -movingBounds.h, threshold, "y", oTop, "edge");
      checkSnap(mBottom, oBottom, -movingBounds.h, threshold, "y", oBottom, "edge");
    }

    if (snapCenters) {
      // Center snaps
      const cxOffset = -movingBounds.w / 2;
      const cyOffset = -movingBounds.h / 2;
      checkSnap(mCx, oCx, cxOffset, threshold, "x", oCx, "center");
      checkSnap(mCy, oCy, cyOffset, threshold, "y", oCy, "center");
    }
  }

  // Equal spacing detection
  if (snapSpacing && others.length >= 2) {
    detectEqualSpacing(movingBounds, others, threshold);
  }

  const snappedX = bestDx !== null ? movingBounds.x + bestDx : movingBounds.x;
  const snappedY = bestDy !== null ? movingBounds.y + bestDy : movingBounds.y;

  return { snappedX, snappedY, guides };

  /**
   * Check a single snap candidate and update the best snap if closer.
   */
  function checkSnap(
    movingEdge: Emu,
    targetEdge: Emu,
    offsetToPos: Emu,
    thresh: Emu,
    axis: "x" | "y",
    guidePos: Emu,
    guideType: "edge" | "center",
  ): void {
    const dist = Math.abs(movingEdge - targetEdge);
    if (dist > thresh) return;

    const delta = targetEdge - movingEdge + offsetToPos - (axis === "x" ? 0 : 0);
    const actualDelta = targetEdge - movingEdge;

    if (axis === "x") {
      // delta to apply to movingBounds.x
      const dx = actualDelta + offsetToPos - 0;
      const candidateDx = targetEdge - movingEdge;
      // We want: new mLeft/mRight = targetEdge, so newX = movingBounds.x + (targetEdge - movingEdge) + offsetToPos...
      // Actually simpler: if we matched mLeft to targetEdge, newX = targetEdge.
      // If we matched mRight to targetEdge, newX = targetEdge - movingBounds.w.
      const newX = targetEdge + offsetToPos;
      const dxFromOrig = newX - movingBounds.x;
      if (Math.abs(dxFromOrig) < bestDxDist) {
        bestDxDist = Math.abs(dxFromOrig);
        bestDx = dxFromOrig;
        // Only add guide if not duplicate position
        if (!guides.some((g) => g.axis === "x" && g.position === guidePos)) {
          guides.push({ axis: "x", position: guidePos, type: guideType });
        }
      }
    } else {
      const newY = targetEdge + offsetToPos;
      const dyFromOrig = newY - movingBounds.y;
      if (Math.abs(dyFromOrig) < bestDyDist) {
        bestDyDist = Math.abs(dyFromOrig);
        bestDy = dyFromOrig;
        if (!guides.some((g) => g.axis === "y" && g.position === guidePos)) {
          guides.push({ axis: "y", position: guidePos, type: guideType });
        }
      }
    }
  }

  /**
   * Detect equal spacing opportunities between consecutive shapes on each axis.
   */
  function detectEqualSpacing(
    moving: ShapeBounds,
    otherShapes: ShapeBounds[],
    thresh: Emu,
  ): void {
    // Sort shapes by X for horizontal spacing
    const sortedX = [...otherShapes].sort((a, b) => a.x - b.x);
    const gapsX: number[] = [];
    for (let i = 1; i < sortedX.length; i++) {
      const gap = sortedX[i].x - (sortedX[i - 1].x + sortedX[i - 1].w);
      if (gap > 0) gapsX.push(gap);
    }

    if (gapsX.length > 0) {
      const avgGap = gapsX.reduce((s, g) => s + g, 0) / gapsX.length;
      // Check if placing moving shape creates a matching gap
      for (const other of otherShapes) {
        // To the right of other
        const candidateX = other.x + other.w + avgGap;
        const dist = Math.abs(moving.x - candidateX);
        if (dist < thresh && dist < bestDxDist) {
          bestDxDist = dist;
          bestDx = candidateX - moving.x;
          guides.push({ axis: "x", position: candidateX, type: "spacing" });
        }
        // To the left of other
        const candidateXLeft = other.x - avgGap - moving.w;
        const distLeft = Math.abs(moving.x - candidateXLeft);
        if (distLeft < thresh && distLeft < bestDxDist) {
          bestDxDist = distLeft;
          bestDx = candidateXLeft - moving.x;
          guides.push({ axis: "x", position: other.x - avgGap, type: "spacing" });
        }
      }
    }

    // Sort shapes by Y for vertical spacing
    const sortedY = [...otherShapes].sort((a, b) => a.y - b.y);
    const gapsY: number[] = [];
    for (let i = 1; i < sortedY.length; i++) {
      const gap = sortedY[i].y - (sortedY[i - 1].y + sortedY[i - 1].h);
      if (gap > 0) gapsY.push(gap);
    }

    if (gapsY.length > 0) {
      const avgGap = gapsY.reduce((s, g) => s + g, 0) / gapsY.length;
      for (const other of otherShapes) {
        const candidateY = other.y + other.h + avgGap;
        const dist = Math.abs(moving.y - candidateY);
        if (dist < thresh && dist < bestDyDist) {
          bestDyDist = dist;
          bestDy = candidateY - moving.y;
          guides.push({ axis: "y", position: candidateY, type: "spacing" });
        }
        const candidateYTop = other.y - avgGap - moving.h;
        const distTop = Math.abs(moving.y - candidateYTop);
        if (distTop < thresh && distTop < bestDyDist) {
          bestDyDist = distTop;
          bestDy = candidateYTop - moving.y;
          guides.push({ axis: "y", position: other.y - avgGap, type: "spacing" });
        }
      }
    }
  }
}

/**
 * Render snap guide lines on the canvas.
 *
 * Draws 1px magenta (#FF00FF) lines across the full slide extent for each guide.
 *
 * @param ctx - Canvas 2D rendering context.
 * @param guides - Guide lines to render.
 * @param presWidth - Presentation width in EMU.
 * @param presHeight - Presentation height in EMU.
 * @param scale - Current viewport scale.
 * @param offsetX - Canvas X offset for centering.
 * @param offsetY - Canvas Y offset for centering.
 */
export function renderGuides(
  ctx: CanvasRenderingContext2D,
  guides: GuideLine[],
  presWidth: Emu,
  presHeight: Emu,
  scale: number,
  offsetX: number,
  offsetY: number,
): void {
  if (guides.length === 0) return;

  const emuToPx = (emu: Emu): number => emu * (PX_PER_INCH / EMU_PER_INCH) * scale;

  ctx.save();
  ctx.strokeStyle = "#FF00FF";
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);

  const slideW = emuToPx(presWidth);
  const slideH = emuToPx(presHeight);

  for (const guide of guides) {
    ctx.beginPath();
    if (guide.axis === "x") {
      const px = offsetX + emuToPx(guide.position);
      ctx.moveTo(px, offsetY);
      ctx.lineTo(px, offsetY + slideH);
    } else {
      const py = offsetY + emuToPx(guide.position);
      ctx.moveTo(offsetX, py);
      ctx.lineTo(offsetX + slideW, py);
    }
    ctx.stroke();
  }

  ctx.setLineDash([]);
  ctx.restore();
}
