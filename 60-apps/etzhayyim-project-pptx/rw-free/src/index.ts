/**
 * pptx rw-free — barrel.
 *
 * Per ADR-2606011400. The pptx presentation document tree on the etzhayyim
 * substrate (AT PDS records; no RW).
 *
 *   presentation : createPresentation / getPresentation / listPresentations (q = app-layer search)
 *   slide        : addSlide (FK→presentation) / listSlides
 *   shape        : addShape (FK→slide, EMU geometry, content CID) / listShapes
 *   textRun      : addTextRun (FK→shape, half-point font) / listTextRuns
 *   coverage
 *
 * Creative document work product; large blobs referenced by CID.
 */

export * from "./types.js";
export {
  createPresentation,
  getPresentation,
  listPresentations,
  addSlide,
  listSlides,
  addShape,
  listShapes,
  addTextRun,
  listTextRuns,
  coverage,
} from "./registry.js";
