/**
 * Editor State — Svelte 5 rune-based reactive state for the PPTX editor.
 *
 * Uses a single exported `$state` object so properties can be mutated from imports.
 * Supports multi-select, pan/zoom, snap guides, and z-order operations.
 */

import type { PptxPresentation, PptxSlide, PptxShape } from "./ooxml-parser";

export type EditorTool = "select" | "rect" | "ellipse" | "roundRect" | "triangle" | "arrow" | "line" | "textBox" | "image";

export interface EditorSnapshot {
  presentation: PptxPresentation;
  selectedSlideIndex: number;
  selectedShapeIds: string[];
}

/** Module-level clipboard for copy/paste operations. */
let clipboard: PptxShape[] = [];

/** Reactive editor state container. */
export const editor = $state({
  presentation: null as PptxPresentation | null,
  selectedSlideIndex: 0,
  selectedShapeIds: [] as string[],
  activeTool: "select" as EditorTool,
  isDirty: false,
  statusMessage: "",
  zoom: 1.0,
  panX: 0,
  panY: 0,
  snapToShapes: true,
  showGuides: true,
  editingTextShapeId: null as string | null,
  showGrid: false,
  gridSize: 114300 as number,
  viewMode: "editor" as "editor" | "sorter",
});

// --- Undo / Redo ---

const MAX_HISTORY = 50;
let undoStack: string[] = [];
let redoStack: string[] = [];

/** Take a snapshot for undo. */
export function pushUndo(): void {
  if (!editor.presentation) return;
  const snap: EditorSnapshot = {
    presentation: structuredClone($state.snapshot(editor.presentation)),
    selectedSlideIndex: editor.selectedSlideIndex,
    selectedShapeIds: [...editor.selectedShapeIds],
  };
  undoStack.push(JSON.stringify(snap));
  if (undoStack.length > MAX_HISTORY) undoStack.shift();
  redoStack = [];
  editor.isDirty = true;
}

/** Undo the last action. */
export function undo(): void {
  if (undoStack.length === 0) return;
  if (editor.presentation) {
    const current: EditorSnapshot = {
      presentation: structuredClone($state.snapshot(editor.presentation)),
      selectedSlideIndex: editor.selectedSlideIndex,
      selectedShapeIds: [...editor.selectedShapeIds],
    };
    redoStack.push(JSON.stringify(current));
  }
  const snap: EditorSnapshot = JSON.parse(undoStack.pop()!);
  editor.presentation = snap.presentation;
  editor.selectedSlideIndex = snap.selectedSlideIndex;
  editor.selectedShapeIds = snap.selectedShapeIds;
  editor.statusMessage = "Undo";
}

/** Redo the last undone action. */
export function redo(): void {
  if (redoStack.length === 0) return;
  if (editor.presentation) {
    const current: EditorSnapshot = {
      presentation: structuredClone($state.snapshot(editor.presentation)),
      selectedSlideIndex: editor.selectedSlideIndex,
      selectedShapeIds: [...editor.selectedShapeIds],
    };
    undoStack.push(JSON.stringify(current));
  }
  const snap: EditorSnapshot = JSON.parse(redoStack.pop()!);
  editor.presentation = snap.presentation;
  editor.selectedSlideIndex = snap.selectedSlideIndex;
  editor.selectedShapeIds = snap.selectedShapeIds;
  editor.statusMessage = "Redo";
}

export function canUndo(): boolean { return undoStack.length > 0; }
export function canRedo(): boolean { return redoStack.length > 0; }

// --- Derived ---

/** Currently selected slide. */
export function currentSlide(): PptxSlide | null {
  const p = editor.presentation;
  if (!p || editor.selectedSlideIndex < 0 || editor.selectedSlideIndex >= p.slides.length) return null;
  return p.slides[editor.selectedSlideIndex];
}

/** Currently selected shape (first in selection). */
export function currentShape(): PptxShape | null {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return null;
  return slide.shapes.find((s) => s.id === editor.selectedShapeIds[0]) ?? null;
}

/** All currently selected shapes. */
export function currentShapes(): PptxShape[] {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return [];
  const idSet = new Set(editor.selectedShapeIds);
  return slide.shapes.filter((s) => idSet.has(s.id));
}

// --- Selection ---

/** Select a single shape (or deselect all if null). Selects entire group if shape is grouped. */
export function selectShape(id: string | null): void {
  if (!id) {
    editor.selectedShapeIds = [];
    return;
  }
  const slide = currentSlide();
  if (slide) {
    const shape = slide.shapes.find((s) => s.id === id);
    if (shape?.groupId) {
      const groupIds = slide.shapes.filter((s) => s.groupId === shape.groupId).map((s) => s.id);
      editor.selectedShapeIds = groupIds;
      return;
    }
  }
  editor.selectedShapeIds = [id];
}

/** Toggle a shape in/out of the multi-selection (shift+click). */
export function toggleShapeSelection(id: string): void {
  const idx = editor.selectedShapeIds.indexOf(id);
  if (idx >= 0) {
    editor.selectedShapeIds = editor.selectedShapeIds.filter((_, i) => i !== idx);
  } else {
    editor.selectedShapeIds = [...editor.selectedShapeIds, id];
  }
}

/** Select multiple shapes by ID (rubber band). */
export function selectShapes(ids: string[]): void {
  editor.selectedShapeIds = ids;
}

/** Select all shapes on the current slide. */
export function selectAllShapes(): void {
  const slide = currentSlide();
  if (!slide) return;
  editor.selectedShapeIds = slide.shapes.map((s) => s.id);
}

// --- Mutations ---

let idCounter = Date.now();
function nextId(prefix: string): string {
  return `${prefix}_${++idCounter}_${Math.random().toString(36).slice(2, 6)}`;
}

/** Load a new presentation. */
export function loadPresentation(pres: PptxPresentation): void {
  undoStack = [];
  redoStack = [];
  editor.presentation = pres;
  editor.selectedSlideIndex = 0;
  editor.selectedShapeIds = [];
  editor.isDirty = false;
  editor.panX = 0;
  editor.panY = 0;
  editor.statusMessage = `Loaded: ${pres.title} (${pres.slides.length} slides)`;
}

export function selectSlide(index: number): void {
  editor.selectedSlideIndex = index;
  editor.selectedShapeIds = [];
}

/** Add a new blank slide. */
export function addSlide(afterIndex?: number): void {
  const p = editor.presentation;
  if (!p) return;
  pushUndo();
  const idx = afterIndex ?? p.slides.length;
  const newSlide: PptxSlide = { id: nextId("slide"), order: idx, layoutRef: "blank", background: null, shapes: [], images: [] };
  p.slides.splice(idx + 1, 0, newSlide);
  for (let i = 0; i < p.slides.length; i++) p.slides[i].order = i;
  editor.selectedSlideIndex = idx + 1;
  editor.selectedShapeIds = [];
  editor.statusMessage = "Slide added";
}

/** Delete a slide. */
export function deleteSlide(index: number): void {
  const p = editor.presentation;
  if (!p || p.slides.length <= 1) return;
  pushUndo();
  p.slides.splice(index, 1);
  for (let i = 0; i < p.slides.length; i++) p.slides[i].order = i;
  if (editor.selectedSlideIndex >= p.slides.length) editor.selectedSlideIndex = p.slides.length - 1;
  editor.selectedShapeIds = [];
  editor.statusMessage = "Slide deleted";
}

/** Move a slide from one index to another (drag reorder). */
export function moveSlide(fromIndex: number, toIndex: number): void {
  const p = editor.presentation;
  if (!p || fromIndex === toIndex) return;
  if (fromIndex < 0 || fromIndex >= p.slides.length) return;
  if (toIndex < 0 || toIndex >= p.slides.length) return;
  pushUndo();
  const [slide] = p.slides.splice(fromIndex, 1);
  p.slides.splice(toIndex, 0, slide);
  for (let i = 0; i < p.slides.length; i++) p.slides[i].order = i;
  editor.selectedSlideIndex = toIndex;
  editor.selectedShapeIds = [];
  editor.statusMessage = `Moved slide ${fromIndex + 1} to ${toIndex + 1}`;
}

/** Add a shape to the current slide. */
export function addShape(type: PptxShape["type"]): void {
  const slide = currentSlide();
  if (!slide) return;
  pushUndo();
  const shape: PptxShape = {
    id: nextId("shape"), slideId: slide.id, type, name: type,
    x: 2000000, y: 2000000, w: 2000000, h: 1500000, rotation: 0,
    fill: type === "line" ? null : "4472C4", stroke: "2F5597", strokeWidth: 12700,
    textBody: (type === "textBox" || type === "rect" || type === "roundRect")
      ? { align: "center", verticalAlign: "middle", paragraphs: [{ level: 0, spacing: 0, runs: [{ text: "Text", bold: false, italic: false, underline: false, size: 1800, color: "FFFFFF", font: "Calibri" }] }] }
      : null,
  };
  slide.shapes.push(shape);
  editor.selectedShapeIds = [shape.id];
  editor.statusMessage = `Added ${type}`;
}

/** Delete all currently selected shapes. */
export function deleteSelectedShapes(): void {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return;
  pushUndo();
  const idSet = new Set(editor.selectedShapeIds);
  slide.shapes = slide.shapes.filter((s) => !idSet.has(s.id));
  editor.selectedShapeIds = [];
  editor.statusMessage = `Deleted ${idSet.size} shape(s)`;
}

/** Backward-compatible alias for deleteSelectedShapes. */
export const deleteSelectedShape = deleteSelectedShapes;

/** Update a property on the selected shape. */
export function updateShapeProperty<K extends keyof PptxShape>(key: K, value: PptxShape[K]): void {
  const shape = currentShape();
  if (!shape) return;
  pushUndo();
  (shape as unknown as Record<string, unknown>)[key] = value;
  editor.isDirty = true;
}

/** Duplicate all currently selected shapes. */
export function duplicateSelectedShapes(): void {
  const slide = currentSlide();
  const shapes = currentShapes();
  if (!slide || shapes.length === 0) return;
  pushUndo();
  const newIds: string[] = [];
  for (const shape of shapes) {
    const clone: PptxShape = { ...structuredClone($state.snapshot(shape)), id: nextId("shape"), x: shape.x + 200000, y: shape.y + 200000 };
    slide.shapes.push(clone);
    newIds.push(clone.id);
  }
  editor.selectedShapeIds = newIds;
  editor.statusMessage = `Duplicated ${shapes.length} shape(s)`;
}

/** Backward-compatible alias for duplicateSelectedShapes. */
export const duplicateSelectedShape = duplicateSelectedShapes;

// --- Z-order operations ---

/** Move selected shapes to the front (top) of the z-order. */
export function bringToFront(): void {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return;
  pushUndo();
  const idSet = new Set(editor.selectedShapeIds);
  const selected = slide.shapes.filter((s) => idSet.has(s.id));
  const rest = slide.shapes.filter((s) => !idSet.has(s.id));
  slide.shapes = [...rest, ...selected];
  editor.statusMessage = "Brought to front";
}

/** Move selected shapes to the back (bottom) of the z-order. */
export function sendToBack(): void {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return;
  pushUndo();
  const idSet = new Set(editor.selectedShapeIds);
  const selected = slide.shapes.filter((s) => idSet.has(s.id));
  const rest = slide.shapes.filter((s) => !idSet.has(s.id));
  slide.shapes = [...selected, ...rest];
  editor.statusMessage = "Sent to back";
}

/** Move selected shapes one step forward in z-order. */
export function bringForward(): void {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return;
  pushUndo();
  const idSet = new Set(editor.selectedShapeIds);
  const shapes = slide.shapes;
  for (let i = shapes.length - 2; i >= 0; i--) {
    if (idSet.has(shapes[i].id) && !idSet.has(shapes[i + 1].id)) {
      [shapes[i], shapes[i + 1]] = [shapes[i + 1], shapes[i]];
    }
  }
  editor.statusMessage = "Brought forward";
}

/** Move selected shapes one step backward in z-order. */
export function sendBackward(): void {
  const slide = currentSlide();
  if (!slide || editor.selectedShapeIds.length === 0) return;
  pushUndo();
  const idSet = new Set(editor.selectedShapeIds);
  const shapes = slide.shapes;
  for (let i = 1; i < shapes.length; i++) {
    if (idSet.has(shapes[i].id) && !idSet.has(shapes[i - 1].id)) {
      [shapes[i], shapes[i - 1]] = [shapes[i - 1], shapes[i]];
    }
  }
  editor.statusMessage = "Sent backward";
}

// --- Clipboard ---

/** Copy currently selected shapes to the module clipboard. */
export function copyShapes(): void {
  const shapes = currentShapes();
  if (shapes.length === 0) return;
  clipboard = shapes.map((s) => structuredClone($state.snapshot(s)));
  editor.statusMessage = `Copied ${shapes.length} shape(s)`;
}

/** Paste shapes from the module clipboard onto the current slide. */
export function pasteShapes(): void {
  const slide = currentSlide();
  if (!slide || clipboard.length === 0) return;
  pushUndo();
  const newIds: string[] = [];
  for (const shape of clipboard) {
    const clone: PptxShape = { ...structuredClone(shape), id: nextId("shape"), x: shape.x + 200000, y: shape.y + 200000 };
    slide.shapes.push(clone);
    newIds.push(clone.id);
  }
  editor.selectedShapeIds = newIds;
  editor.statusMessage = `Pasted ${clipboard.length} shape(s)`;
}

/** Reset the editor. */
export function resetEditor(): void {
  editor.presentation = null;
  editor.selectedSlideIndex = 0;
  editor.selectedShapeIds = [];
  editor.activeTool = "select";
  editor.isDirty = false;
  editor.panX = 0;
  editor.panY = 0;
  undoStack = [];
  redoStack = [];
  editor.statusMessage = "";
}

// --- Align / Distribute ---

/**
 * Align selected shapes along the specified axis.
 * Uses the union bounding box of all selected shapes as the reference.
 */
export function alignShapes(axis: "left" | "center" | "right" | "top" | "middle" | "bottom"): void {
  const shapes = currentShapes();
  if (shapes.length < 2) return;
  pushUndo();

  const minX = Math.min(...shapes.map((s) => s.x));
  const minY = Math.min(...shapes.map((s) => s.y));
  const maxX = Math.max(...shapes.map((s) => s.x + s.w));
  const maxY = Math.max(...shapes.map((s) => s.y + s.h));

  for (const s of shapes) {
    switch (axis) {
      case "left": s.x = minX; break;
      case "center": s.x = minX + (maxX - minX) / 2 - s.w / 2; break;
      case "right": s.x = maxX - s.w; break;
      case "top": s.y = minY; break;
      case "middle": s.y = minY + (maxY - minY) / 2 - s.h / 2; break;
      case "bottom": s.y = maxY - s.h; break;
    }
  }
  editor.isDirty = true;
  editor.statusMessage = `Aligned ${axis}`;
}

/**
 * Distribute selected shapes evenly along the specified axis.
 * Sorts shapes by position and spaces them with equal gaps.
 */
export function distributeShapes(axis: "horizontal" | "vertical"): void {
  const shapes = currentShapes();
  if (shapes.length < 3) return;
  pushUndo();

  if (axis === "horizontal") {
    const sorted = [...shapes].sort((a, b) => a.x - b.x);
    const totalShapeW = sorted.reduce((sum, s) => sum + s.w, 0);
    const minX = sorted[0].x;
    const maxX = Math.max(...sorted.map((s) => s.x + s.w));
    const gap = (maxX - minX - totalShapeW) / (sorted.length - 1);
    let cx = minX;
    for (const s of sorted) {
      s.x = Math.round(cx);
      cx += s.w + gap;
    }
  } else {
    const sorted = [...shapes].sort((a, b) => a.y - b.y);
    const totalShapeH = sorted.reduce((sum, s) => sum + s.h, 0);
    const minY = sorted[0].y;
    const maxY = Math.max(...sorted.map((s) => s.y + s.h));
    const gap = (maxY - minY - totalShapeH) / (sorted.length - 1);
    let cy = minY;
    for (const s of sorted) {
      s.y = Math.round(cy);
      cy += s.h + gap;
    }
  }
  editor.isDirty = true;
  editor.statusMessage = `Distributed ${axis}`;
}

// --- Group / Ungroup ---

let groupCounter = 0;

/** Group all currently selected shapes under a shared groupId. */
export function groupShapes(): void {
  const shapes = currentShapes();
  if (shapes.length < 2) return;
  pushUndo();
  const gid = `grp_${++groupCounter}_${Date.now()}`;
  for (const s of shapes) {
    s.groupId = gid;
  }
  editor.isDirty = true;
  editor.statusMessage = `Grouped ${shapes.length} shapes`;
}

/** Remove groupId from all currently selected shapes. */
export function ungroupShapes(): void {
  const shapes = currentShapes();
  if (shapes.length === 0) return;
  pushUndo();
  for (const s of shapes) {
    s.groupId = undefined;
  }
  editor.isDirty = true;
  editor.statusMessage = `Ungrouped ${shapes.length} shapes`;
}

/** Toggle visibility of a shape by ID. */
export function toggleShapeVisibility(id: string): void {
  const slide = currentSlide();
  if (!slide) return;
  const shape = slide.shapes.find((s) => s.id === id);
  if (!shape) return;
  pushUndo();
  shape.visible = shape.visible === false ? true : false;
  editor.isDirty = true;
}

/** Toggle lock state of a shape by ID. */
export function toggleShapeLock(id: string): void {
  const slide = currentSlide();
  if (!slide) return;
  const shape = slide.shapes.find((s) => s.id === id);
  if (!shape) return;
  pushUndo();
  shape.locked = !shape.locked;
  editor.isDirty = true;
}

/** Rename a shape by ID. */
export function renameShape(id: string, newName: string): void {
  const slide = currentSlide();
  if (!slide) return;
  const shape = slide.shapes.find((s) => s.id === id);
  if (!shape) return;
  pushUndo();
  shape.name = newName;
  editor.isDirty = true;
}
