<script lang="ts">
  import { parsePptx, type PptxPresentation, type PptxSlide, type PptxShape } from "./lib/ooxml-parser";
  import { exportPptx, downloadBlob } from "./lib/pptx-exporter";
  import {
    renderSlide,
    renderThumbnail,
    renderRubberBand,
    renderGrid,
    computeFitScale,
    hitTestShapes,
    hitTestRect,
    cacheImageBlobs,
    releaseBlobCache,
    emuToPx,
    prunePathCache,
  } from "./lib/slide-renderer";
  import { checkWebGPU, getGPUInfo, loadKamiEngine, isKamiReady, renderSlideGPU } from "./lib/kami-bridge";
  import { computeSnapGuides, renderGuides, type GuideLine } from "./lib/snap-engine";
  import {
    getHandlePositions,
    hitTestHandle,
    computeResize,
    computeRotation,
    computeCornerRadius,
    getHandleCursor,
    type HandleType,
  } from "./lib/transform-handles";
  import {
    editor,
    loadPresentation,
    selectSlide,
    selectShape,
    toggleShapeSelection,
    selectShapes,
    selectAllShapes,
    addSlide,
    deleteSlide,
    addShape,
    deleteSelectedShapes,
    updateShapeProperty,
    duplicateSelectedShapes,
    bringToFront,
    sendToBack,
    bringForward,
    sendBackward,
    copyShapes,
    pasteShapes,
    pushUndo,
    undo,
    redo,
    canUndo,
    canRedo,
    currentSlide,
    currentShape,
    currentShapes,
    resetEditor,
    alignShapes,
    distributeShapes,
    groupShapes,
    ungroupShapes,
    toggleShapeVisibility,
    toggleShapeLock,
    renameShape,
    moveSlide,
    type EditorTool,
  } from "./lib/editor-state.svelte";

  let mainCanvas: HTMLCanvasElement;
  let gpuCanvas: HTMLCanvasElement;
  let useGPU = $state(false);
  let fileInput: HTMLInputElement;
  let topRulerCanvas: HTMLCanvasElement;
  let leftRulerCanvas: HTMLCanvasElement;
  let textEditDiv: HTMLDivElement;
  let minimapCanvas: HTMLCanvasElement;

  // --- Text editing state ---
  let editingTextShapeId = $state<string | null>(null);
  let editingTextPos = $state({ x: 0, y: 0, w: 0, h: 0 });
  let editingTextBold = $state(false);
  let editingTextItalic = $state(false);
  let editingTextUnderline = $state(false);
  let editingTextFont = $state("Calibri");
  let editingTextSize = $state(18);
  let editingTextColor = $state("#FFFFFF");
  let editingTextAlign = $state<"left" | "center" | "right">("center");

  // --- Layer editing state ---
  let editingLayerNameId = $state<string | null>(null);

  // --- Drag state ---
  let isDragging = $state(false);
  let dragStartX = 0;
  let dragStartY = 0;
  let dragShapeOriginals: { id: string; x: number; y: number }[] = [];

  // --- Transform handle state ---
  let activeHandle: HandleType | null = $state(null);
  let handleOrigBounds: { x: number; y: number; w: number; h: number } | null = null;
  let handleStartX = 0;
  let handleStartY = 0;

  // --- Rubber band state ---
  let isRubberBanding = $state(false);
  let rubberBandStartX = 0;
  let rubberBandStartY = 0;
  let rubberBandEndX = 0;
  let rubberBandEndY = 0;

  // --- Pan state ---
  let spaceHeld = $state(false);
  let isPanning = $state(false);
  let panStartX = 0;
  let panStartY = 0;
  let panOrigX = 0;
  let panOrigY = 0;

  // --- Snap guides ---
  let activeGuides: GuideLine[] = $state([]);

  // --- Slide drag reorder ---
  let dragSlideIndex = $state<number | null>(null);
  let dropTargetIndex = $state<number | null>(null);

  // --- Corner radius drag ---
  let cornerRadiusOriginal = 0;

  // --- Cursor ---
  let canvasCursor = $state("default");

  let webgpuAvailable = $state(false);
  let kamiReady = $state(false);
  let gpuInfo = $state<string | null>(null);

  $effect(() => {
    checkWebGPU().then((ok: boolean) => { webgpuAvailable = ok; });
    getGPUInfo().then((info: string | null) => { gpuInfo = info; });
    loadKamiEngine().then((ok: boolean) => { kamiReady = ok; useGPU = ok; });
  });

  function renderThumb(canvas: HTMLCanvasElement, params: { slide: PptxSlide; pres: PptxPresentation }): { update: (p: typeof params) => void } {
    renderThumbnail(canvas, params.slide, params.pres);
    return { update(p) { renderThumbnail(canvas, p.slide, p.pres); } };
  }

  async function handleFileUpload(e: Event): Promise<void> {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const buffer = await file.arrayBuffer();
    const pres = parsePptx(buffer);
    pres.title = file.name.replace(/\.pptx$/i, "");
    cacheImageBlobs(pres.slides);
    loadPresentation(pres);
    requestRender();
  }

  function handleNew(): void {
    releaseBlobCache();
    const pres: PptxPresentation = {
      id: `pres_${Date.now()}`, title: "New Presentation", width: 9144000, height: 6858000,
      slides: [{ id: `slide_${Date.now()}`, order: 0, layoutRef: "blank", background: null, shapes: [], images: [] }],
      theme: null,
    };
    loadPresentation(pres);
    requestRender();
  }

  function handleExport(): void {
    if (!editor.presentation) return;
    const blob = exportPptx($state.snapshot(editor.presentation));
    downloadBlob(blob, `${editor.presentation.title || "presentation"}.pptx`);
  }

  let renderPending = false;
  function requestRender(): void {
    if (renderPending) return;
    renderPending = true;
    requestAnimationFrame(doRender);
  }

  /** Compute current scale from presentation + viewport + zoom. */
  function currentScale(rect: { width: number; height: number }): number {
    if (!editor.presentation) return 1;
    return computeFitScale(editor.presentation.width, editor.presentation.height, rect.width, rect.height) * editor.zoom;
  }

  /** EMU per pixel at current scale. */
  const EMU_PER_PX_RATIO = 914400 / 96;

  async function doRender(): Promise<void> {
    renderPending = false;
    if (!editor.presentation) return;
    const slide = currentSlide();
    if (!slide) return;

    const container = (mainCanvas ?? gpuCanvas)?.parentElement;
    const rect = container?.getBoundingClientRect();
    const viewW = rect?.width ?? 800;
    const viewH = rect?.height ?? 600;

    // --- GPU rendering path (WebGPU + WebGL2 fallback via KAMI wgpu) ---
    if (useGPU && gpuCanvas && isKamiReady()) {
      // Show GPU canvas, hide 2D canvas
      gpuCanvas.style.display = "block";
      if (mainCanvas) mainCanvas.style.display = "none";

      if (rect) {
        gpuCanvas.style.width = `${rect.width}px`;
        gpuCanvas.style.height = `${rect.height}px`;
        // wgpu manages its own pixel ratio
      }

      const ok = await renderSlideGPU("gpu-canvas", slide, editor.presentation, editor.selectedShapeIds);
      if (ok) return; // GPU render succeeded

      // GPU failed — fall through to Canvas 2D
      useGPU = false;
      console.warn("[renderer] GPU render failed, switching to Canvas 2D");
    }

    // --- Canvas 2D fallback ---
    if (!mainCanvas) return;
    if (gpuCanvas) gpuCanvas.style.display = "none";
    mainCanvas.style.display = "block";

    const ctx = mainCanvas.getContext("2d");
    if (!ctx) return;

    if (rect) {
      mainCanvas.width = rect.width * devicePixelRatio;
      mainCanvas.height = rect.height * devicePixelRatio;
      mainCanvas.style.width = `${rect.width}px`;
      mainCanvas.style.height = `${rect.height}px`;
      ctx.scale(devicePixelRatio, devicePixelRatio);
    }
    const scale = computeFitScale(editor.presentation.width, editor.presentation.height, viewW, viewH) * editor.zoom;

    // Apply pan offset by translating the context
    ctx.save();
    ctx.translate(editor.panX, editor.panY);
    await renderSlide(ctx, slide, editor.presentation, scale, editor.selectedShapeIds, {
      showGrid: editor.showGrid,
      gridSize: editor.gridSize,
    });

    // Render snap guides
    if (editor.showGuides && activeGuides.length > 0) {
      const slideW = emuToPx(editor.presentation.width, scale);
      const slideH = emuToPx(editor.presentation.height, scale);
      const offsetX = (viewW - slideW) / 2;
      const offsetY = (viewH - slideH) / 2;
      renderGuides(ctx, activeGuides, editor.presentation.width, editor.presentation.height, scale, offsetX, offsetY);
    }
    ctx.restore();

    // Rubber band is drawn without pan offset (screen space)
    if (isRubberBanding) {
      renderRubberBand(ctx, rubberBandStartX, rubberBandStartY, rubberBandEndX, rubberBandEndY);
    }
  }

  $effect(() => {
    void editor.presentation;
    void editor.selectedSlideIndex;
    void editor.selectedShapeIds;
    void editor.zoom;
    void editor.panX;
    void editor.panY;
    void editor.showGrid;
    void editor.viewMode;
    requestRender();
    renderRulers();
    renderMinimap();
  });

  $effect(() => {
    if (!mainCanvas?.parentElement) return;
    const observer = new ResizeObserver(() => { requestRender(); renderRulers(); });
    observer.observe(mainCanvas.parentElement);
    return () => observer.disconnect();
  });

  function handleCanvasMouseDown(e: MouseEvent): void {
    if (!editor.presentation || !mainCanvas) return;
    const rect = mainCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    // Adjust for pan
    const px = x - editor.panX;
    const py = y - editor.panY;
    const slide = currentSlide();
    if (!slide) return;
    const scale = currentScale(rect);

    // Space+drag → pan mode
    if (spaceHeld) {
      isPanning = true;
      panStartX = e.clientX;
      panStartY = e.clientY;
      panOrigX = editor.panX;
      panOrigY = editor.panY;
      canvasCursor = "grabbing";
      return;
    }

    if (editor.activeTool === "select") {
      // Check handle hit on selected shapes first
      if (editor.selectedShapeIds.length > 0) {
        const selected = currentShapes();
        let handleBounds: { x: number; y: number; w: number; h: number };
        let rotation = 0;
        let crEmu: number | undefined;
        if (selected.length === 1) {
          handleBounds = { x: selected[0].x, y: selected[0].y, w: selected[0].w, h: selected[0].h };
          rotation = selected[0].rotation;
          if (selected[0].type === "roundRect") {
            crEmu = selected[0].cornerRadius ?? Math.round(Math.min(selected[0].w, selected[0].h) * 0.1);
          }
        } else {
          const minX = Math.min(...selected.map(s => s.x));
          const minY = Math.min(...selected.map(s => s.y));
          const maxX = Math.max(...selected.map(s => s.x + s.w));
          const maxY = Math.max(...selected.map(s => s.y + s.h));
          handleBounds = { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
        }

        const slideW = emuToPx(editor.presentation.width, scale);
        const slideH = emuToPx(editor.presentation.height, scale);
        const offsetX = (rect.width - slideW) / 2 + editor.panX;
        const offsetY = (rect.height - slideH) / 2 + editor.panY;

        const positions = getHandlePositions(handleBounds, scale, offsetX, offsetY, crEmu);
        const hitHandle = hitTestHandle(positions, x, y);
        if (hitHandle) {
          activeHandle = hitHandle;
          handleOrigBounds = { ...handleBounds };
          handleStartX = x;
          handleStartY = y;
          if (hitHandle === "cornerRadius" && selected.length === 1) {
            cornerRadiusOriginal = selected[0].cornerRadius ?? Math.round(Math.min(selected[0].w, selected[0].h) * 0.1);
          }
          pushUndo();
          return;
        }
      }

      // Shape hit test
      const hit = hitTestShapes(slide, editor.presentation, px, py, rect.width, rect.height, scale);
      if (hit) {
        if (e.shiftKey) {
          toggleShapeSelection(hit.id);
        } else if (!editor.selectedShapeIds.includes(hit.id)) {
          selectShape(hit.id);
        }
        // Start dragging
        isDragging = true;
        dragStartX = x;
        dragStartY = y;
        const selected = currentShapes();
        dragShapeOriginals = selected.map(s => ({ id: s.id, x: s.x, y: s.y }));
        pushUndo();
      } else {
        // Click on empty → deselect or start rubber band
        if (!e.shiftKey) selectShape(null);
        isRubberBanding = true;
        rubberBandStartX = x;
        rubberBandStartY = y;
        rubberBandEndX = x;
        rubberBandEndY = y;
      }
    } else {
      addShape(editor.activeTool as PptxSlide["shapes"][0]["type"]);
      const shape = currentShape();
      if (shape) {
        const slideW = emuToPx(editor.presentation.width, scale);
        const slideH = emuToPx(editor.presentation.height, scale);
        const offsetX = (rect.width - slideW) / 2;
        const offsetY = (rect.height - slideH) / 2;
        shape.x = Math.max(0, Math.round((px - offsetX) / scale / (96 / 914400)));
        shape.y = Math.max(0, Math.round((py - offsetY) / scale / (96 / 914400)));
      }
      editor.activeTool = "select";
    }
    requestRender();
  }

  function handleCanvasMouseMove(e: MouseEvent): void {
    if (!editor.presentation || !mainCanvas) return;
    const rect = mainCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const px = x - editor.panX;
    const py = y - editor.panY;
    const scale = currentScale(rect);

    // Panning
    if (isPanning) {
      editor.panX = panOrigX + (e.clientX - panStartX);
      editor.panY = panOrigY + (e.clientY - panStartY);
      requestRender();
      return;
    }

    // Handle resize/rotate/cornerRadius
    if (activeHandle && handleOrigBounds) {
      const dxPx = x - handleStartX;
      const dyPx = y - handleStartY;

      if (activeHandle === "cornerRadius") {
        // Corner radius drag
        const dxEmu = Math.round(dxPx / scale * EMU_PER_PX_RATIO);
        const selected = currentShapes();
        if (selected.length === 1 && selected[0].type === "roundRect") {
          const maxR = Math.min(selected[0].w, selected[0].h) / 2;
          selected[0].cornerRadius = computeCornerRadius(cornerRadiusOriginal, dxEmu, maxR);
          editor.isDirty = true;
        }
        requestRender();
        return;
      } else if (activeHandle === "rotation") {
        // Rotation mode
        const emuToPxS = (emu: number): number => emu * (96 / 914400) * scale;
        const slideW = emuToPx(editor.presentation.width, scale);
        const slideH = emuToPx(editor.presentation.height, scale);
        const offsetX = (rect.width - slideW) / 2 + editor.panX;
        const offsetY = (rect.height - slideH) / 2 + editor.panY;
        const cx = offsetX + emuToPxS(handleOrigBounds.x + handleOrigBounds.w / 2);
        const cy = offsetY + emuToPxS(handleOrigBounds.y + handleOrigBounds.h / 2);
        const newRot = computeRotation(cx, cy, x, y, e.shiftKey);
        const selected = currentShapes();
        for (const s of selected) {
          s.rotation = newRot;
        }
        editor.isDirty = true;
      } else {
        // Resize mode
        const dxEmu = Math.round(dxPx / scale * EMU_PER_PX_RATIO);
        const dyEmu = Math.round(dyPx / scale * EMU_PER_PX_RATIO);
        const newBounds = computeResize(activeHandle, handleOrigBounds, dxEmu, dyEmu, e.shiftKey);
        const selected = currentShapes();
        if (selected.length === 1) {
          selected[0].x = newBounds.x;
          selected[0].y = newBounds.y;
          selected[0].w = newBounds.w;
          selected[0].h = newBounds.h;
        } else {
          // Multi-select resize: scale proportionally
          const sx = newBounds.w / (handleOrigBounds.w || 1);
          const sy = newBounds.h / (handleOrigBounds.h || 1);
          for (const s of selected) {
            const relX = s.x - handleOrigBounds.x;
            const relY = s.y - handleOrigBounds.y;
            s.x = newBounds.x + Math.round(relX * sx);
            s.y = newBounds.y + Math.round(relY * sy);
            s.w = Math.max(50000, Math.round(s.w * sx));
            s.h = Math.max(50000, Math.round(s.h * sy));
          }
        }
        editor.isDirty = true;
      }
      requestRender();
      return;
    }

    // Rubber band
    if (isRubberBanding) {
      rubberBandEndX = x;
      rubberBandEndY = y;
      requestRender();
      return;
    }

    // Dragging shapes
    if (isDragging) {
      const dxPx = x - dragStartX;
      const dyPx = y - dragStartY;
      const dxEmu = Math.round(dxPx / scale * EMU_PER_PX_RATIO);
      const dyEmu = Math.round(dyPx / scale * EMU_PER_PX_RATIO);

      const slide = currentSlide();
      if (!slide) return;
      const selected = currentShapes();

      // Apply base position from originals
      for (const orig of dragShapeOriginals) {
        const shape = selected.find(s => s.id === orig.id);
        if (shape) {
          shape.x = orig.x + dxEmu;
          shape.y = orig.y + dyEmu;
        }
      }

      // Snap guides
      if (editor.snapToShapes && selected.length === 1) {
        const moving = selected[0];
        const allBounds = slide.shapes.map(s => ({ id: s.id, x: s.x, y: s.y, w: s.w, h: s.h }));
        const snap = computeSnapGuides(
          { id: moving.id, x: moving.x, y: moving.y, w: moving.w, h: moving.h },
          allBounds,
          scale,
        );
        moving.x = snap.snappedX;
        moving.y = snap.snappedY;
        activeGuides = snap.guides;
      } else {
        activeGuides = [];
      }

      // Grid snap (when grid visible and snap enabled)
      if (editor.showGrid && editor.snapToShapes) {
        const gs = editor.gridSize;
        for (const s of selected) {
          s.x = Math.round(s.x / gs) * gs;
          s.y = Math.round(s.y / gs) * gs;
        }
      }

      editor.isDirty = true;
      requestRender();
      return;
    }

    // Cursor feedback (hover, no drag)
    if (editor.activeTool !== "select") {
      canvasCursor = "crosshair";
      return;
    }
    if (spaceHeld) {
      canvasCursor = "grab";
      return;
    }

    // Check handle hover
    if (editor.selectedShapeIds.length > 0) {
      const selected = currentShapes();
      let hBounds: { x: number; y: number; w: number; h: number };
      let rotation = 0;
      let hCrEmu: number | undefined;
      if (selected.length === 1) {
        hBounds = { x: selected[0].x, y: selected[0].y, w: selected[0].w, h: selected[0].h };
        rotation = selected[0].rotation;
        if (selected[0].type === "roundRect") {
          hCrEmu = selected[0].cornerRadius ?? Math.round(Math.min(selected[0].w, selected[0].h) * 0.1);
        }
      } else if (selected.length > 1) {
        const minX = Math.min(...selected.map(s => s.x));
        const minY = Math.min(...selected.map(s => s.y));
        const maxX = Math.max(...selected.map(s => s.x + s.w));
        const maxY = Math.max(...selected.map(s => s.y + s.h));
        hBounds = { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
      } else {
        canvasCursor = "default";
        return;
      }

      const slideW = emuToPx(editor.presentation.width, scale);
      const slideH = emuToPx(editor.presentation.height, scale);
      const offsetX = (rect.width - slideW) / 2 + editor.panX;
      const offsetY = (rect.height - slideH) / 2 + editor.panY;

      const positions = getHandlePositions(hBounds, scale, offsetX, offsetY, hCrEmu);
      const hoverHandle = hitTestHandle(positions, x, y);
      if (hoverHandle) {
        canvasCursor = getHandleCursor(hoverHandle, rotation);
        return;
      }
    }

    // Check shape hover
    const slide = currentSlide();
    if (slide) {
      const hit = hitTestShapes(slide, editor.presentation, px, py, rect.width, rect.height, scale);
      canvasCursor = hit ? "move" : "default";
    }
  }

  function handleCanvasMouseUp(e: MouseEvent): void {
    if (isPanning) {
      isPanning = false;
      canvasCursor = spaceHeld ? "grab" : "default";
      return;
    }

    if (isRubberBanding && editor.presentation) {
      isRubberBanding = false;
      const rect = mainCanvas.getBoundingClientRect();
      const scale = currentScale(rect);
      const slide = currentSlide();
      if (slide) {
        const rx = Math.min(rubberBandStartX, rubberBandEndX) - editor.panX;
        const ry = Math.min(rubberBandStartY, rubberBandEndY) - editor.panY;
        const rw = Math.abs(rubberBandEndX - rubberBandStartX);
        const rh = Math.abs(rubberBandEndY - rubberBandStartY);
        if (rw > 3 || rh > 3) {
          const hits = hitTestRect(slide, editor.presentation, rx, ry, rw, rh, rect.width, rect.height, scale);
          selectShapes(hits.map(s => s.id));
        }
      }
    }

    if (activeHandle) {
      activeHandle = null;
      handleOrigBounds = null;
    }

    isDragging = false;
    activeGuides = [];
    requestRender();
  }

  function handleCanvasWheel(e: WheelEvent): void {
    e.preventDefault();
    if (!editor.presentation || !mainCanvas) return;

    // If shapes are selected, scroll changes z-layer
    if (editor.selectedShapeIds.length > 0) {
      if (e.deltaY > 0) {
        sendBackward();
      } else {
        bringForward();
      }
      requestRender();
      return;
    }

    // No selection: zoom toward cursor
    const factor = e.deltaY > 0 ? 0.95 : 1.05;
    const newZoom = Math.max(0.1, Math.min(5.0, editor.zoom * factor));
    const rect = mainCanvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const ratio = newZoom / editor.zoom;
    editor.panX = mx - ratio * (mx - editor.panX);
    editor.panY = my - ratio * (my - editor.panY);
    editor.zoom = newZoom;
    requestRender();
  }

  function handleKeyDown(e: KeyboardEvent): void {
    if (e.key === " " && !e.repeat) {
      e.preventDefault();
      spaceHeld = true;
      if (!isDragging && !activeHandle) canvasCursor = "grab";
      return;
    }

    const meta = e.metaKey || e.ctrlKey;

    // Cmd+A select all
    if (meta && e.key === "a") { e.preventDefault(); selectAllShapes(); requestRender(); return; }

    // Cmd+C copy
    if (meta && e.key === "c") { e.preventDefault(); copyShapes(); return; }
    // Cmd+V paste
    if (meta && e.key === "v") { e.preventDefault(); pasteShapes(); requestRender(); return; }
    // Cmd+X cut
    if (meta && e.key === "x") { e.preventDefault(); copyShapes(); deleteSelectedShapes(); requestRender(); return; }

    // Cmd+Z undo, Cmd+Shift+Z / Cmd+Y redo
    if (meta && e.key === "z" && !e.shiftKey) { e.preventDefault(); undo(); requestRender(); return; }
    if (meta && (e.key === "y" || (e.key === "z" && e.shiftKey))) { e.preventDefault(); redo(); requestRender(); return; }

    // Delete/Backspace
    if ((e.key === "Delete" || e.key === "Backspace") && editor.selectedShapeIds.length > 0) { e.preventDefault(); deleteSelectedShapes(); requestRender(); return; }

    // Cmd+D duplicate
    if (meta && e.key === "d") { e.preventDefault(); duplicateSelectedShapes(); requestRender(); return; }

    // Cmd+G group, Cmd+Shift+G ungroup
    if (meta && e.key === "g" && !e.shiftKey) { e.preventDefault(); groupShapes(); requestRender(); return; }
    if (meta && e.key === "G" && e.shiftKey) { e.preventDefault(); ungroupShapes(); requestRender(); return; }

    // Cmd+S export
    if (meta && e.key === "s") { e.preventDefault(); handleExport(); return; }

    // Escape
    if (e.key === "Escape") {
      if (editingTextShapeId) { commitTextEdit(); return; }
      selectShape(null); editor.activeTool = "select"; requestRender(); return;
    }

    // Z-order: Cmd+] bring forward, Cmd+[ send backward
    if (meta && e.key === "]") { e.preventDefault(); bringForward(); requestRender(); return; }
    if (meta && e.key === "[") { e.preventDefault(); sendBackward(); requestRender(); return; }
    // Cmd+Shift+] bring to front, Cmd+Shift+[ send to back
    if (meta && e.shiftKey && e.key === "}") { e.preventDefault(); bringToFront(); requestRender(); return; }
    if (meta && e.shiftKey && e.key === "{") { e.preventDefault(); sendToBack(); requestRender(); return; }

    // Tool shortcuts (single letter, no modifier)
    if (!meta && !e.shiftKey && !e.altKey) {
      switch (e.key) {
        case "v": case "V": editor.activeTool = "select"; return;
        case "r": case "R": editor.activeTool = "rect"; return;
        case "o": case "O": editor.activeTool = "ellipse"; return;
        case "t": case "T": editor.activeTool = "textBox"; return;
        case "l": case "L": editor.activeTool = "line"; return;
      }
    }

    // Arrow nudge
    const nudgeAmount = e.shiftKey ? 127000 : 12700; // ~1.4" vs ~0.14"
    if (e.key === "ArrowLeft" && editor.selectedShapeIds.length > 0) {
      e.preventDefault(); pushUndo();
      for (const s of currentShapes()) s.x -= nudgeAmount;
      editor.isDirty = true; requestRender(); return;
    }
    if (e.key === "ArrowRight" && editor.selectedShapeIds.length > 0) {
      e.preventDefault(); pushUndo();
      for (const s of currentShapes()) s.x += nudgeAmount;
      editor.isDirty = true; requestRender(); return;
    }
    if (e.key === "ArrowUp" && editor.selectedShapeIds.length > 0) {
      e.preventDefault(); pushUndo();
      for (const s of currentShapes()) s.y -= nudgeAmount;
      editor.isDirty = true; requestRender(); return;
    }
    if (e.key === "ArrowDown" && editor.selectedShapeIds.length > 0) {
      e.preventDefault(); pushUndo();
      for (const s of currentShapes()) s.y += nudgeAmount;
      editor.isDirty = true; requestRender(); return;
    }
  }

  function handleKeyUp(e: KeyboardEvent): void {
    if (e.key === " ") {
      spaceHeld = false;
      if (!isPanning) canvasCursor = "default";
    }
  }

  /** Fit the slide to the viewport (reset pan and zoom). */
  function fitToSlide(): void {
    editor.zoom = 1.0;
    editor.panX = 0;
    editor.panY = 0;
    requestRender();
  }

  const tools: { id: EditorTool; label: string; icon: string; shortcut?: string }[] = [
    { id: "select", label: "Select", icon: "↖", shortcut: "V" },
    { id: "rect", label: "Rectangle", icon: "▬", shortcut: "R" },
    { id: "ellipse", label: "Ellipse", icon: "⬭", shortcut: "O" },
    { id: "roundRect", label: "Rounded Rect", icon: "▢" },
    { id: "triangle", label: "Triangle", icon: "△" },
    { id: "arrow", label: "Arrow", icon: "→" },
    { id: "line", label: "Line", icon: "╱", shortcut: "L" },
    { id: "textBox", label: "Text", icon: "T", shortcut: "T" },
  ];

  function handleFillChange(e: Event): void { updateShapeProperty("fill", (e.target as HTMLInputElement).value.replace("#", "")); requestRender(); }
  function handleStrokeChange(e: Event): void { updateShapeProperty("stroke", (e.target as HTMLInputElement).value.replace("#", "")); requestRender(); }
  function handleNameChange(e: Event): void { updateShapeProperty("name", (e.target as HTMLInputElement).value); }
  function handleRotationChange(e: Event): void { updateShapeProperty("rotation", parseFloat((e.target as HTMLInputElement).value) || 0); requestRender(); }

  /** Get icon symbol for a shape type. */
  function shapeIcon(type: string): string {
    switch (type) {
      case "rect": case "roundRect": return "\u25ac";
      case "ellipse": return "\u2b2d";
      case "textBox": return "T";
      case "line": return "\u2571";
      case "triangle": return "\u25b3";
      case "arrow": return "\u2192";
      default: return "\u25a0";
    }
  }

  /** Handle double-click on canvas to enter text editing mode. */
  function handleCanvasDblClick(e: MouseEvent): void {
    if (!editor.presentation || !mainCanvas) return;
    const rect = mainCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left - editor.panX;
    const y = e.clientY - rect.top - editor.panY;
    const slide = currentSlide();
    if (!slide) return;
    const scale = currentScale(rect);
    const hit = hitTestShapes(slide, editor.presentation, x, y, rect.width, rect.height, scale);
    if (hit && hit.textBody) {
      editingTextShapeId = hit.id;
      editor.editingTextShapeId = hit.id;

      // Compute screen position for the overlay
      const slideW = emuToPx(editor.presentation.width, scale);
      const slideH = emuToPx(editor.presentation.height, scale);
      const offsetX = (rect.width - slideW) / 2 + editor.panX;
      const offsetY = (rect.height - slideH) / 2 + editor.panY;
      editingTextPos = {
        x: offsetX + emuToPx(hit.x, scale),
        y: offsetY + emuToPx(hit.y, scale),
        w: emuToPx(hit.w, scale),
        h: emuToPx(hit.h, scale),
      };

      // Set initial formatting from first run
      const firstRun = hit.textBody.paragraphs[0]?.runs[0];
      if (firstRun) {
        editingTextBold = firstRun.bold;
        editingTextItalic = firstRun.italic;
        editingTextUnderline = firstRun.underline;
        editingTextFont = firstRun.font || "Calibri";
        editingTextSize = firstRun.size / 100;
        editingTextColor = `#${firstRun.color || "FFFFFF"}`;
      }
      editingTextAlign = hit.textBody.align === "justify" ? "left" : hit.textBody.align;

      // Focus the contenteditable after mount
      requestAnimationFrame(() => {
        if (textEditDiv) {
          textEditDiv.textContent = hit.textBody!.paragraphs.map((p) => p.runs.map((r) => r.text).join("")).join("\n");
          textEditDiv.focus();
          // Select all text
          const range = document.createRange();
          range.selectNodeContents(textEditDiv);
          const sel = window.getSelection();
          sel?.removeAllRanges();
          sel?.addRange(range);
        }
      });
      requestRender();
    }
  }

  /** Commit text edits back to the shape data model. */
  function commitTextEdit(): void {
    if (!editingTextShapeId) return;
    const slide = currentSlide();
    if (!slide) return;
    const shape = slide.shapes.find((s) => s.id === editingTextShapeId);
    if (shape?.textBody && textEditDiv) {
      pushUndo();
      const text = textEditDiv.textContent || "";
      const firstRun = shape.textBody.paragraphs[0]?.runs[0];
      if (firstRun) {
        firstRun.text = text;
        firstRun.bold = editingTextBold;
        firstRun.italic = editingTextItalic;
        firstRun.underline = editingTextUnderline;
        firstRun.font = editingTextFont;
        firstRun.size = editingTextSize * 100;
        firstRun.color = editingTextColor.replace("#", "");
      }
      shape.textBody.align = editingTextAlign;
    }
    editingTextShapeId = null;
    editor.editingTextShapeId = null;
    requestRender();
  }

  /** Handle keydown in the text editor. */
  function handleTextEditKeyDown(e: KeyboardEvent): void {
    if (e.key === "Escape") {
      commitTextEdit();
      e.stopPropagation();
    }
    // Prevent editor keyboard shortcuts from firing while text editing
    e.stopPropagation();
  }

  /** Toggle bold/italic/underline on the editing text. */
  function toggleTextFormat(fmt: "bold" | "italic" | "underline"): void {
    if (fmt === "bold") editingTextBold = !editingTextBold;
    if (fmt === "italic") editingTextItalic = !editingTextItalic;
    if (fmt === "underline") editingTextUnderline = !editingTextUnderline;
    if (textEditDiv) {
      textEditDiv.style.fontWeight = editingTextBold ? "bold" : "normal";
      textEditDiv.style.fontStyle = editingTextItalic ? "italic" : "normal";
      textEditDiv.style.textDecoration = editingTextUnderline ? "underline" : "none";
    }
  }

  // --- Minimap ---

  /** Render the minimap in the bottom-right corner. */
  async function renderMinimap(): Promise<void> {
    if (!minimapCanvas || !editor.presentation) return;
    const slide = currentSlide();
    if (!slide) return;
    const ctx = minimapCanvas.getContext("2d");
    if (!ctx) return;

    const presW = editor.presentation.width;
    const presH = editor.presentation.height;
    const aspectRatio = presW / presH;
    const mmW = 150;
    const mmH = Math.round(mmW / aspectRatio);
    minimapCanvas.width = mmW * devicePixelRatio;
    minimapCanvas.height = mmH * devicePixelRatio;
    minimapCanvas.style.width = `${mmW}px`;
    minimapCanvas.style.height = `${mmH}px`;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    // Dark background
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(0, 0, mmW, mmH);

    // Render slide thumbnail
    const thumbScale = computeFitScale(presW, presH, mmW, mmH, 2);
    await renderSlide(ctx, slide, editor.presentation, thumbScale);

    // Draw viewport rectangle
    if (mainCanvas?.parentElement) {
      const parentRect = mainCanvas.parentElement.getBoundingClientRect();
      const fullScale = computeFitScale(presW, presH, parentRect.width, parentRect.height) * editor.zoom;
      const slideWFull = emuToPx(presW, fullScale);
      const slideHFull = emuToPx(presH, fullScale);

      const slideWMini = emuToPx(presW, thumbScale);
      const slideHMini = emuToPx(presH, thumbScale);
      const miniOffX = (mmW - slideWMini) / 2;
      const miniOffY = (mmH - slideHMini) / 2;

      const viewportRatio = slideWMini / slideWFull;

      // Viewport origin in mini coordinates
      const vpX = miniOffX + (-editor.panX) * viewportRatio;
      const vpY = miniOffY + (-editor.panY) * viewportRatio;
      const vpW = parentRect.width * viewportRatio;
      const vpH = parentRect.height * viewportRatio;

      ctx.strokeStyle = "rgba(74, 108, 247, 0.8)";
      ctx.fillStyle = "rgba(74, 108, 247, 0.15)";
      ctx.lineWidth = 1.5;
      ctx.fillRect(vpX, vpY, vpW, vpH);
      ctx.strokeRect(vpX, vpY, vpW, vpH);
    }
  }

  /** Handle click on minimap to pan to that position. */
  function handleMinimapClick(e: MouseEvent): void {
    if (!minimapCanvas || !editor.presentation || !mainCanvas?.parentElement) return;
    const mmRect = minimapCanvas.getBoundingClientRect();
    const clickX = e.clientX - mmRect.left;
    const clickY = e.clientY - mmRect.top;

    const presW = editor.presentation.width;
    const presH = editor.presentation.height;
    const aspectRatio = presW / presH;
    const mmW = 150;
    const mmH = Math.round(mmW / aspectRatio);

    const thumbScale = computeFitScale(presW, presH, mmW, mmH, 2);
    const slideWMini = emuToPx(presW, thumbScale);
    const slideHMini = emuToPx(presH, thumbScale);
    const miniOffX = (mmW - slideWMini) / 2;
    const miniOffY = (mmH - slideHMini) / 2;

    const parentRect = mainCanvas.parentElement.getBoundingClientRect();
    const fullScale = computeFitScale(presW, presH, parentRect.width, parentRect.height) * editor.zoom;
    const slideWFull = emuToPx(presW, fullScale);

    const viewportRatio = slideWMini / slideWFull;

    // Convert minimap click to main canvas pan offset
    editor.panX = -(clickX - miniOffX) / viewportRatio + parentRect.width / 2;
    editor.panY = -(clickY - miniOffY) / viewportRatio + parentRect.height / 2;
    requestRender();
  }

  // --- Slide drag reorder handlers ---

  function handleSlideDragStart(e: DragEvent, index: number): void {
    dragSlideIndex = index;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", String(index));
    }
  }

  function handleSlideDragOver(e: DragEvent, index: number): void {
    e.preventDefault();
    if (dragSlideIndex === null || dragSlideIndex === index) {
      dropTargetIndex = null;
      return;
    }
    dropTargetIndex = index;
  }

  function handleSlideDrop(e: DragEvent, index: number): void {
    e.preventDefault();
    if (dragSlideIndex !== null && dragSlideIndex !== index) {
      moveSlide(dragSlideIndex, index);
      requestRender();
    }
    dragSlideIndex = null;
    dropTargetIndex = null;
  }

  function handleSlideDragEnd(): void {
    dragSlideIndex = null;
    dropTargetIndex = null;
  }

  // --- Font options for rich text toolbar ---
  const fontFamilies = ["Calibri", "Arial", "Times New Roman", "Helvetica", "Georgia", "Courier New"];
  const fontSizes = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48, 56, 64, 72, 80, 96];

  // --- Ruler rendering ---
  const RULER_SIZE = 20;
  const INCH_EMU = 914400;

  /** Render the top and left ruler canvases. */
  function renderRulers(): void {
    if (!editor.presentation) return;
    renderTopRuler();
    renderLeftRuler();
  }

  function renderTopRuler(): void {
    if (!topRulerCanvas || !editor.presentation) return;
    const parent = topRulerCanvas.parentElement;
    if (!parent) return;
    const w = parent.clientWidth;
    topRulerCanvas.width = w * devicePixelRatio;
    topRulerCanvas.height = RULER_SIZE * devicePixelRatio;
    topRulerCanvas.style.width = `${w}px`;
    topRulerCanvas.style.height = `${RULER_SIZE}px`;
    const ctx = topRulerCanvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, 0, w, RULER_SIZE);

    const viewW = w;
    const scale = computeFitScale(editor.presentation.width, editor.presentation.height, viewW, 600) * editor.zoom;
    const pxPerInch = (96 / 914400) * INCH_EMU * scale;
    const slideW = emuToPx(editor.presentation.width, scale);
    const origin = (viewW - slideW) / 2 + editor.panX;

    ctx.strokeStyle = "#555";
    ctx.fillStyle = "#888";
    ctx.font = "9px sans-serif";
    ctx.textAlign = "center";

    const slideInches = editor.presentation.width / INCH_EMU;
    const startInch = Math.floor(-origin / pxPerInch);
    const endInch = Math.ceil((w - origin) / pxPerInch);

    for (let i = startInch; i <= endInch; i++) {
      const px = origin + i * pxPerInch;
      // Major tick every inch
      ctx.beginPath();
      ctx.moveTo(px, RULER_SIZE);
      ctx.lineTo(px, RULER_SIZE - 10);
      ctx.stroke();
      if (i >= 0 && i <= slideInches) {
        ctx.fillText(`${i}`, px, 10);
      }
      // Minor ticks every 1/4 inch
      for (let q = 1; q < 4; q++) {
        const qx = px + (q * pxPerInch) / 4;
        ctx.beginPath();
        ctx.moveTo(qx, RULER_SIZE);
        ctx.lineTo(qx, RULER_SIZE - 5);
        ctx.stroke();
      }
    }
  }

  function renderLeftRuler(): void {
    if (!leftRulerCanvas || !editor.presentation) return;
    const parent = leftRulerCanvas.parentElement;
    if (!parent) return;
    const h = parent.clientHeight;
    leftRulerCanvas.width = RULER_SIZE * devicePixelRatio;
    leftRulerCanvas.height = h * devicePixelRatio;
    leftRulerCanvas.style.width = `${RULER_SIZE}px`;
    leftRulerCanvas.style.height = `${h}px`;
    const ctx = leftRulerCanvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, 0, RULER_SIZE, h);

    const viewH = h;
    const scale = computeFitScale(editor.presentation.width, editor.presentation.height, 800, viewH) * editor.zoom;
    const pxPerInch = (96 / 914400) * INCH_EMU * scale;
    const slideH = emuToPx(editor.presentation.height, scale);
    const origin = (viewH - slideH) / 2 + editor.panY;

    ctx.strokeStyle = "#555";
    ctx.fillStyle = "#888";
    ctx.font = "9px sans-serif";
    ctx.textAlign = "center";

    const slideInches = editor.presentation.height / INCH_EMU;
    const startInch = Math.floor(-origin / pxPerInch);
    const endInch = Math.ceil((h - origin) / pxPerInch);

    for (let i = startInch; i <= endInch; i++) {
      const py = origin + i * pxPerInch;
      ctx.beginPath();
      ctx.moveTo(RULER_SIZE, py);
      ctx.lineTo(RULER_SIZE - 10, py);
      ctx.stroke();
      if (i >= 0 && i <= slideInches) {
        ctx.save();
        ctx.translate(10, py);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(`${i}`, 0, 0);
        ctx.restore();
      }
      for (let q = 1; q < 4; q++) {
        const qy = py + (q * pxPerInch) / 4;
        ctx.beginPath();
        ctx.moveTo(RULER_SIZE, qy);
        ctx.lineTo(RULER_SIZE - 5, qy);
        ctx.stroke();
      }
    }
  }
</script>

<svelte:window onkeydown={handleKeyDown} onkeyup={handleKeyUp} />

<div class="editor">
  {#if !editor.presentation}
    <div class="landing">
      <div class="landing-card">
        <h1>PPTX Editor</h1>
        <p>Upload a PowerPoint file or create a new presentation</p>
        <div class="landing-actions">
          <button class="btn btn-primary" onclick={() => fileInput?.click()}>Upload .pptx</button>
          <button class="btn btn-secondary" onclick={handleNew}>New Presentation</button>
        </div>
        <input bind:this={fileInput} type="file" accept=".pptx" style="display:none" onchange={handleFileUpload} />
      </div>
    </div>
  {:else}
    <div class="toolbar">
      <div class="toolbar-group">
        <button class="btn btn-sm" onclick={() => fileInput?.click()}>Open</button>
        <button class="btn btn-sm" onclick={handleNew}>New</button>
        <button class="btn btn-sm" onclick={handleExport}>Export</button>
        <input bind:this={fileInput} type="file" accept=".pptx" style="display:none" onchange={handleFileUpload} />
      </div>
      <div class="toolbar-separator"></div>
      <div class="toolbar-group">
        <button class="btn btn-sm" onclick={() => { undo(); requestRender(); }} disabled={!canUndo()}>Undo</button>
        <button class="btn btn-sm" onclick={() => { redo(); requestRender(); }} disabled={!canRedo()}>Redo</button>
      </div>
      <div class="toolbar-separator"></div>
      <div class="toolbar-group">
        {#each tools as tool}
          <button class="btn btn-sm tool-btn" class:active={editor.activeTool === tool.id} onclick={() => editor.activeTool = tool.id} title={tool.shortcut ? `${tool.label} (${tool.shortcut})` : tool.label}>
            <span class="tool-icon">{tool.icon}</span>
          </button>
        {/each}
      </div>
      <div class="toolbar-separator"></div>
      <div class="toolbar-group">
        <button class="btn btn-sm" onclick={() => addSlide(editor.selectedSlideIndex)}>+ Slide</button>
        <button class="btn btn-sm" onclick={() => deleteSlide(editor.selectedSlideIndex)} disabled={editor.presentation.slides.length <= 1}>- Slide</button>
      </div>
      <div class="toolbar-spacer"></div>
      <div class="toolbar-group">
        <button class="badge" class:badge-ok={useGPU} class:badge-off={!useGPU} title={gpuInfo ?? (kamiReady ? "Click to toggle GPU/Canvas2D" : "KAMI WASM not loaded")} onclick={() => { if (kamiReady) { useGPU = !useGPU; requestRender(); } }} style="cursor: {kamiReady ? 'pointer' : 'default'}; border: none;">
          {useGPU ? "wgpu" : "Canvas2D"}
        </button>
        {#if kamiReady}<span class="badge badge-ok">KAMI</span>{/if}
      </div>
      <div class="toolbar-group">
        <button class="btn btn-sm" class:active={editor.showGrid} onclick={() => { editor.showGrid = !editor.showGrid; requestRender(); }} title="Toggle grid overlay">Grid</button>
        <button class="btn btn-sm" class:active={editor.viewMode === "sorter"} onclick={() => { editor.viewMode = editor.viewMode === "sorter" ? "editor" : "sorter"; }} title="Slide Sorter View">Sorter</button>
      </div>
      <div class="toolbar-group">
        <button class="btn btn-sm" onclick={() => editor.zoom = Math.max(0.1, editor.zoom - 0.1)}>-</button>
        <button class="btn btn-sm zoom-label" onclick={fitToSlide} title="Fit to slide">{Math.round(editor.zoom * 100)}%</button>
        <button class="btn btn-sm" onclick={() => editor.zoom = Math.min(5, editor.zoom + 0.1)}>+</button>
      </div>
    </div>

    {#if editor.viewMode === "sorter"}
      <!-- Slide Sorter View -->
      <div class="sorter-view">
        {#each editor.presentation.slides as slide, i}
          <button
            class="sorter-thumb"
            class:selected={i === editor.selectedSlideIndex}
            draggable="true"
            ondragstart={(e) => handleSlideDragStart(e, i)}
            ondragover={(e) => handleSlideDragOver(e, i)}
            ondrop={(e) => handleSlideDrop(e, i)}
            ondragend={handleSlideDragEnd}
            onclick={() => { selectSlide(i); requestRender(); }}
            ondblclick={() => { selectSlide(i); editor.viewMode = "editor"; requestRender(); }}
          >
            <canvas width="240" height="135" class="sorter-canvas" use:renderThumb={{ slide, pres: editor.presentation }}></canvas>
            <span class="sorter-num">{i + 1}</span>
            {#if dropTargetIndex === i && dragSlideIndex !== null && dragSlideIndex !== i}
              <div class="sorter-drop-indicator"></div>
            {/if}
          </button>
        {/each}
      </div>
    {:else}
    <div class="editor-body">
      <div class="slide-panel">
        {#each editor.presentation.slides as slide, i}
          <button
            class="slide-thumb"
            class:selected={i === editor.selectedSlideIndex}
            draggable="true"
            ondragstart={(e) => handleSlideDragStart(e, i)}
            ondragover={(e) => handleSlideDragOver(e, i)}
            ondrop={(e) => handleSlideDrop(e, i)}
            ondragend={handleSlideDragEnd}
            onclick={() => { selectSlide(i); requestRender(); }}
          >
            <span class="slide-num">{i + 1}</span>
            <canvas width="160" height="90" class="thumb-canvas" use:renderThumb={{ slide, pres: editor.presentation }}></canvas>
            {#if dropTargetIndex === i && dragSlideIndex !== null && dragSlideIndex !== i}
              <div class="slide-drop-indicator"></div>
            {/if}
          </button>
        {/each}
      </div>

      <div class="canvas-area">
        <div class="ruler-corner"></div>
        <div class="ruler-top">
          <canvas bind:this={topRulerCanvas}></canvas>
        </div>
        <div class="ruler-left">
          <canvas bind:this={leftRulerCanvas}></canvas>
        </div>
        <div class="canvas-container">
          <!-- GPU canvas (wgpu WebGPU/WebGL2) — used when KAMI is loaded -->
          <canvas
            id="gpu-canvas"
            bind:this={gpuCanvas}
            onmousedown={handleCanvasMouseDown}
            onmousemove={handleCanvasMouseMove}
            onmouseup={handleCanvasMouseUp}
            onmouseleave={handleCanvasMouseUp}
            ondblclick={handleCanvasDblClick}
            onwheel={handleCanvasWheel}
            style="cursor: {canvasCursor}; display: {useGPU ? 'block' : 'none'};"
          ></canvas>
          <!-- Canvas 2D fallback -->
          <canvas
            bind:this={mainCanvas}
            onmousedown={handleCanvasMouseDown}
            onmousemove={handleCanvasMouseMove}
            onmouseup={handleCanvasMouseUp}
            onmouseleave={handleCanvasMouseUp}
            ondblclick={handleCanvasDblClick}
            onwheel={handleCanvasWheel}
            style="cursor: {canvasCursor}; display: {useGPU ? 'none' : 'block'};"
          ></canvas>
          {#if editingTextShapeId}
            {@const editShape = currentSlide()?.shapes.find(s => s.id === editingTextShapeId)}
            {#if editShape?.textBody}
              <div class="text-edit-toolbar" style="left: {editingTextPos.x}px; top: {editingTextPos.y - 36}px;">
                <select class="fmt-select" value={editingTextFont} onchange={(e) => { editingTextFont = (e.target as HTMLSelectElement).value; if (textEditDiv) textEditDiv.style.fontFamily = editingTextFont; }}>
                  {#each fontFamilies as ff}
                    <option value={ff}>{ff}</option>
                  {/each}
                </select>
                <select class="fmt-select fmt-size-select" value={String(editingTextSize)} onchange={(e) => { editingTextSize = parseInt((e.target as HTMLSelectElement).value, 10); if (textEditDiv) textEditDiv.style.fontSize = `${editingTextSize * editor.zoom}px`; }}>
                  {#each fontSizes as fs}
                    <option value={String(fs)}>{fs}</option>
                  {/each}
                </select>
                <input class="fmt-color" type="color" value={editingTextColor} oninput={(e) => { editingTextColor = (e.target as HTMLInputElement).value; if (textEditDiv) textEditDiv.style.color = editingTextColor; }} title="Text color" />
                <div class="fmt-divider"></div>
                <button class="fmt-btn" class:fmt-active={editingTextBold} onclick={() => toggleTextFormat("bold")} title="Bold">B</button>
                <button class="fmt-btn" class:fmt-active={editingTextItalic} onclick={() => toggleTextFormat("italic")} title="Italic"><i>I</i></button>
                <button class="fmt-btn" class:fmt-active={editingTextUnderline} onclick={() => toggleTextFormat("underline")} title="Underline"><u>U</u></button>
                <div class="fmt-divider"></div>
                <button class="fmt-btn" class:fmt-active={editingTextAlign === "left"} onclick={() => { editingTextAlign = "left"; if (textEditDiv) textEditDiv.style.textAlign = "left"; }} title="Align Left">{"\u2190"}</button>
                <button class="fmt-btn" class:fmt-active={editingTextAlign === "center"} onclick={() => { editingTextAlign = "center"; if (textEditDiv) textEditDiv.style.textAlign = "center"; }} title="Align Center">{"\u2194"}</button>
                <button class="fmt-btn" class:fmt-active={editingTextAlign === "right"} onclick={() => { editingTextAlign = "right"; if (textEditDiv) textEditDiv.style.textAlign = "right"; }} title="Align Right">{"\u2192"}</button>
              </div>
              <div
                bind:this={textEditDiv}
                class="text-edit-overlay"
                contenteditable="true"
                onblur={commitTextEdit}
                onkeydown={handleTextEditKeyDown}
                style="left: {editingTextPos.x}px; top: {editingTextPos.y}px; width: {editingTextPos.w}px; height: {editingTextPos.h}px; font-family: '{editingTextFont}', sans-serif; font-size: {editingTextSize * editor.zoom}px; color: {editingTextColor}; text-align: {editingTextAlign}; font-weight: {editingTextBold ? 'bold' : 'normal'}; font-style: {editingTextItalic ? 'italic' : 'normal'}; text-decoration: {editingTextUnderline ? 'underline' : 'none'};"
              ></div>
            {/if}
          {/if}
          <!-- Minimap -->
          <div class="minimap-container">
            <canvas bind:this={minimapCanvas} onclick={handleMinimapClick}></canvas>
          </div>
        </div>
      </div>

      <div class="props-panel">
        {#if currentShape()}
          {@const shape = currentShape()!}
          <h3>Shape Properties {editor.selectedShapeIds.length > 1 ? `(${editor.selectedShapeIds.length})` : ""}</h3>
          <label class="prop-row"><span>Name</span><input type="text" value={shape.name} oninput={handleNameChange} /></label>
          <label class="prop-row"><span>Type</span><span class="prop-val">{shape.type}</span></label>
          <label class="prop-row"><span>Fill</span><input type="color" value={shape.fill ? `#${shape.fill}` : "#4472C4"} oninput={handleFillChange} /></label>
          <label class="prop-row"><span>Stroke</span><input type="color" value={shape.stroke ? `#${shape.stroke}` : "#2F5597"} oninput={handleStrokeChange} /></label>
          <label class="prop-row"><span>Rotation</span><input type="number" value={shape.rotation} step="1" oninput={handleRotationChange} /></label>
          <label class="prop-row"><span>Position</span><span class="prop-val">{Math.round(shape.x / 914400 * 100) / 100}" x {Math.round(shape.y / 914400 * 100) / 100}"</span></label>
          <label class="prop-row"><span>Size</span><span class="prop-val">{Math.round(shape.w / 914400 * 100) / 100}" x {Math.round(shape.h / 914400 * 100) / 100}"</span></label>
          <div class="prop-actions">
            <button class="btn btn-sm btn-danger" onclick={() => { deleteSelectedShapes(); requestRender(); }}>Delete</button>
            <button class="btn btn-sm" onclick={() => { duplicateSelectedShapes(); requestRender(); }}>Duplicate</button>
          </div>
          <div class="prop-actions">
            <button class="btn btn-sm" onclick={() => { bringForward(); requestRender(); }} title="Cmd+]">Fwd</button>
            <button class="btn btn-sm" onclick={() => { sendBackward(); requestRender(); }} title="Cmd+[">Bwd</button>
            <button class="btn btn-sm" onclick={() => { bringToFront(); requestRender(); }}>Front</button>
            <button class="btn btn-sm" onclick={() => { sendToBack(); requestRender(); }}>Back</button>
          </div>
          {#if editor.selectedShapeIds.length >= 2}
            <h3 class="section-title">Align</h3>
            <div class="prop-actions">
              <button class="btn btn-sm" onclick={() => { alignShapes("left"); requestRender(); }} title="Align Left">{"\u2b05"} L</button>
              <button class="btn btn-sm" onclick={() => { alignShapes("center"); requestRender(); }} title="Center H">{"\u2194"} C</button>
              <button class="btn btn-sm" onclick={() => { alignShapes("right"); requestRender(); }} title="Align Right">{"\u27a1"} R</button>
            </div>
            <div class="prop-actions">
              <button class="btn btn-sm" onclick={() => { alignShapes("top"); requestRender(); }} title="Align Top">{"\u2b06"} T</button>
              <button class="btn btn-sm" onclick={() => { alignShapes("middle"); requestRender(); }} title="Middle V">{"\u2195"} M</button>
              <button class="btn btn-sm" onclick={() => { alignShapes("bottom"); requestRender(); }} title="Align Bottom">{"\u2b07"} B</button>
            </div>
            <h3 class="section-title">Distribute</h3>
            <div class="prop-actions">
              <button class="btn btn-sm" onclick={() => { distributeShapes("horizontal"); requestRender(); }} title="Distribute H">{"\u21d4"} H</button>
              <button class="btn btn-sm" onclick={() => { distributeShapes("vertical"); requestRender(); }} title="Distribute V">{"\u21d5"} V</button>
            </div>
          {/if}
          <h3 class="section-title">Group</h3>
          <div class="prop-actions">
            {#if editor.selectedShapeIds.length >= 2}
              <button class="btn btn-sm" onclick={() => { groupShapes(); requestRender(); }} title="Cmd+G">Group</button>
            {/if}
            {#if currentShapes().some(s => s.groupId)}
              <button class="btn btn-sm" onclick={() => { ungroupShapes(); requestRender(); }} title="Cmd+Shift+G">Ungroup</button>
            {/if}
          </div>
        {:else}
          <h3>Slide Properties</h3>
          {#if currentSlide()}
            <label class="prop-row"><span>Slide</span><span class="prop-val">#{editor.selectedSlideIndex + 1} of {editor.presentation.slides.length}</span></label>
            <label class="prop-row"><span>Shapes</span><span class="prop-val">{currentSlide()?.shapes.length ?? 0}</span></label>
            <label class="prop-row"><span>Images</span><span class="prop-val">{currentSlide()?.images.length ?? 0}</span></label>
          {/if}
          <p class="hint">Select a shape to edit its properties</p>
        {/if}

        <!-- Layers Panel -->
        {#if currentSlide() && (currentSlide()?.shapes.length ?? 0) > 0}
          <h3 class="section-title layers-title">Layers</h3>
          <div class="layers-list">
            {#each [...(currentSlide()?.shapes ?? [])].reverse() as layerShape (layerShape.id)}
              <div
                class="layer-row"
                class:layer-selected={editor.selectedShapeIds.includes(layerShape.id)}
                class:layer-hidden={layerShape.visible === false}
                class:layer-locked={layerShape.locked === true}
                onclick={() => { selectShape(layerShape.id); requestRender(); }}
              >
                <span class="layer-icon">{shapeIcon(layerShape.type)}</span>
                {#if editingLayerNameId === layerShape.id}
                  <input
                    class="layer-name-input"
                    type="text"
                    value={layerShape.name}
                    onblur={(e) => { renameShape(layerShape.id, (e.target as HTMLInputElement).value); editingLayerNameId = null; }}
                    onkeydown={(e) => { if (e.key === "Enter") { renameShape(layerShape.id, (e.target as HTMLInputElement).value); editingLayerNameId = null; } e.stopPropagation(); }}
                    onclick={(e) => e.stopPropagation()}
                  />
                {:else}
                  <span class="layer-name" ondblclick={(e) => { e.stopPropagation(); editingLayerNameId = layerShape.id; }}>{layerShape.name}</span>
                {/if}
                <button class="layer-btn" onclick={(e) => { e.stopPropagation(); toggleShapeVisibility(layerShape.id); requestRender(); }} title="Toggle visibility">
                  {layerShape.visible === false ? "\uD83D\uDC41\u200D\uD83D\uDDE8" : "\uD83D\uDC41"}
                </button>
                <button class="layer-btn" onclick={(e) => { e.stopPropagation(); toggleShapeLock(layerShape.id); requestRender(); }} title="Toggle lock">
                  {layerShape.locked ? "\uD83D\uDD12" : "\uD83D\uDD13"}
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
    {/if}

    <div class="status-bar">
      <span>{editor.statusMessage}</span>
      <span class="status-spacer"></span>
      <span>{editor.isDirty ? "Modified" : "Saved"}</span>
      <span>{editor.presentation.slides.length} slides</span>
      <span>{Math.round(editor.presentation.width / 914400 * 10) / 10}" x {Math.round(editor.presentation.height / 914400 * 10) / 10}"</span>
    </div>
  {/if}
</div>

<style>
  .editor { display: flex; flex-direction: column; width: 100vw; height: 100vh; background: #1a1a2e; color: #e0e0e0; overflow: hidden; }
  .landing { display: flex; align-items: center; justify-content: center; flex: 1; }
  .landing-card { text-align: center; padding: 48px; background: #16213e; border-radius: 16px; border: 1px solid #2a2a4a; }
  .landing-card h1 { font-size: 32px; font-weight: 700; margin-bottom: 12px; }
  .landing-card p { color: #888; margin-bottom: 24px; }
  .landing-actions { display: flex; gap: 12px; justify-content: center; }
  .btn { padding: 8px 16px; border: 1px solid #3a3a5a; border-radius: 6px; background: #2a2a4a; color: #e0e0e0; cursor: pointer; font-size: 13px; transition: background 0.15s; }
  .btn:hover { background: #3a3a6a; }
  .btn:disabled { opacity: 0.4; cursor: default; }
  .btn-primary { background: #4a6cf7; border-color: #5a7cff; }
  .btn-primary:hover { background: #5a7cff; }
  .btn-secondary { background: #333; border-color: #555; }
  .btn-sm { padding: 4px 10px; font-size: 12px; }
  .btn-danger { background: #a03030; border-color: #c04040; }
  .btn-danger:hover { background: #c04040; }
  .toolbar { display: flex; align-items: center; gap: 4px; padding: 6px 12px; background: #16213e; border-bottom: 1px solid #2a2a4a; flex-shrink: 0; }
  .toolbar-group { display: flex; gap: 2px; align-items: center; }
  .toolbar-separator { width: 1px; height: 24px; background: #3a3a5a; margin: 0 6px; }
  .toolbar-spacer { flex: 1; }
  .tool-btn.active, .btn-sm.active { background: #4a6cf7; border-color: #5a7cff; }
  .tool-icon { font-size: 14px; }
  .zoom-label { font-size: 12px; min-width: 40px; text-align: center; }
  .badge { font-size: 10px; padding: 2px 6px; border-radius: 3px; font-weight: 600; }
  .badge-ok { background: #1a5c2a; color: #6fcf7c; }
  .badge-off { background: #3a3a3a; color: #888; }
  .editor-body { display: flex; flex: 1; overflow: hidden; }
  .slide-panel { width: 180px; flex-shrink: 0; background: #0f1729; border-right: 1px solid #2a2a4a; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 8px; }
  .slide-thumb { position: relative; border: 2px solid transparent; border-radius: 6px; cursor: pointer; background: #1a1a2e; padding: 4px; text-align: left; }
  .slide-thumb.selected { border-color: #4a6cf7; }
  .slide-thumb:hover { background: #22224a; }
  .slide-num { position: absolute; top: 6px; left: 8px; font-size: 10px; color: #888; }
  .thumb-canvas { width: 100%; height: auto; border-radius: 3px; }
  /* Canvas area with rulers */
  .canvas-area { flex: 1; display: grid; grid-template-columns: 20px 1fr; grid-template-rows: 20px 1fr; overflow: hidden; }
  .ruler-corner { width: 20px; height: 20px; background: #16213e; border-right: 1px solid #2a2a4a; border-bottom: 1px solid #2a2a4a; }
  .ruler-top { overflow: hidden; background: #16213e; border-bottom: 1px solid #2a2a4a; }
  .ruler-top canvas { display: block; width: 100%; height: 20px; }
  .ruler-left { overflow: hidden; background: #16213e; border-right: 1px solid #2a2a4a; }
  .ruler-left canvas { display: block; width: 20px; height: 100%; }
  .canvas-container { position: relative; overflow: hidden; background: #111; }
  .canvas-container canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }

  /* Text editing overlay */
  .text-edit-overlay { position: absolute; box-sizing: border-box; padding: 4px; outline: 2px solid #4a6cf7; background: rgba(0,0,0,0.5); color: #fff; overflow: hidden; white-space: pre-wrap; word-break: break-word; display: flex; align-items: center; justify-content: center; z-index: 10; font-family: "Calibri", sans-serif; }
  .text-edit-toolbar { position: absolute; z-index: 11; display: flex; gap: 2px; background: #16213e; border: 1px solid #3a3a5a; border-radius: 4px; padding: 2px; }
  .fmt-btn { width: 24px; height: 24px; border: 1px solid transparent; border-radius: 3px; background: none; color: #e0e0e0; cursor: pointer; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
  .fmt-btn:hover { background: #2a2a4a; }
  .fmt-active { background: #4a6cf7; border-color: #5a7cff; }

  /* Props panel */
  .props-panel { width: 240px; flex-shrink: 0; background: #0f1729; border-left: 1px solid #2a2a4a; padding: 16px; overflow-y: auto; }
  .props-panel h3 { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #ccc; }
  .section-title { margin-top: 16px; font-size: 12px; font-weight: 600; color: #999; border-top: 1px solid #2a2a4a; padding-top: 8px; }
  .prop-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 12px; }
  .prop-row span:first-child { color: #888; }
  .prop-val { color: #aaa; }
  .prop-row input[type="text"], .prop-row input[type="number"] { width: 100px; padding: 3px 6px; background: #1a1a2e; border: 1px solid #3a3a5a; border-radius: 4px; color: #e0e0e0; font-size: 12px; }
  .prop-row input[type="color"] { width: 32px; height: 24px; border: 1px solid #3a3a5a; border-radius: 4px; background: none; cursor: pointer; }
  .prop-actions { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
  .hint { font-size: 11px; color: #666; margin-top: 12px; }

  /* Layers panel */
  .layers-title { margin-top: 16px; }
  .layers-list { display: flex; flex-direction: column; gap: 1px; }
  .layer-row { display: flex; align-items: center; gap: 4px; height: 28px; padding: 0 4px; border-radius: 4px; cursor: pointer; font-size: 11px; background: #1a1a2e; }
  .layer-row:hover { background: #22224a; }
  .layer-selected { background: #2a3a6a !important; }
  .layer-hidden { opacity: 0.5; }
  .layer-locked { }
  .layer-icon { width: 16px; text-align: center; font-size: 12px; color: #888; flex-shrink: 0; }
  .layer-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #ccc; cursor: text; }
  .layer-name-input { flex: 1; background: #111; border: 1px solid #4a6cf7; border-radius: 2px; color: #e0e0e0; font-size: 11px; padding: 1px 4px; outline: none; min-width: 0; }
  .layer-btn { background: none; border: none; cursor: pointer; font-size: 12px; padding: 0 2px; line-height: 1; flex-shrink: 0; }
  .layer-btn:hover { opacity: 0.7; }

  /* Slide drag reorder indicator */
  .slide-drop-indicator { position: absolute; left: 4px; right: 4px; bottom: -5px; height: 2px; background: #4a6cf7; border-radius: 1px; pointer-events: none; }
  .slide-thumb { position: relative; }

  /* Sorter view */
  .sorter-view { flex: 1; display: flex; flex-wrap: wrap; gap: 16px; padding: 24px; overflow-y: auto; background: #111; align-content: flex-start; justify-content: center; }
  .sorter-thumb { position: relative; border: 2px solid transparent; border-radius: 8px; cursor: pointer; background: #1a1a2e; padding: 8px; text-align: center; transition: border-color 0.15s; }
  .sorter-thumb.selected { border-color: #4a6cf7; }
  .sorter-thumb:hover { background: #22224a; }
  .sorter-canvas { width: 240px; height: 135px; border-radius: 4px; display: block; }
  .sorter-num { display: block; margin-top: 4px; font-size: 11px; color: #888; }
  .sorter-drop-indicator { position: absolute; top: 0; bottom: 0; left: -9px; width: 2px; background: #4a6cf7; border-radius: 1px; pointer-events: none; }

  /* Minimap */
  .minimap-container { position: absolute; bottom: 8px; right: 8px; border: 1px solid #3a3a5a; border-radius: 4px; overflow: hidden; cursor: pointer; z-index: 5; background: rgba(0, 0, 0, 0.7); }
  .minimap-container canvas { display: block; }

  /* Rich text toolbar */
  .fmt-select { height: 24px; padding: 0 4px; background: #1a1a2e; border: 1px solid #3a3a5a; border-radius: 3px; color: #e0e0e0; font-size: 11px; cursor: pointer; }
  .fmt-size-select { width: 48px; }
  .fmt-color { width: 24px; height: 24px; border: 1px solid #3a3a5a; border-radius: 3px; background: none; cursor: pointer; padding: 0; }
  .fmt-divider { width: 1px; height: 20px; background: #3a3a5a; margin: 2px 2px; }

  .status-bar { display: flex; align-items: center; gap: 16px; padding: 4px 12px; background: #16213e; border-top: 1px solid #2a2a4a; font-size: 11px; color: #888; flex-shrink: 0; }
  .status-spacer { flex: 1; }
</style>
