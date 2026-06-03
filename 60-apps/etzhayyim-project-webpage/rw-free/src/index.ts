/**
 * webpage rw-free — barrel.
 *
 * Per ADR-2606011400. Web-page authoring & publishing (space → page) on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   space : registerSpace / listSpaces (page groups / sites)
 *   page  : createPage (FK→space, slug-validated) / updatePage / setPageStatus
 *           (draft→published→archived) / getPage / listPages (title+body search)
 *   coverage
 *
 * (a) content-editor product (editor/pptx/xlsx cluster). First-party user-
 * authored pages; published pages form a public searchable directory. No
 * hosting-of-others / custom domains / settlement (contrast `webya` (b)).
 */

export * from "./types.js";
export {
  registerSpace,
  listSpaces,
  createPage,
  updatePage,
  setPageStatus,
  getPage,
  listPages,
  coverage,
} from "./registry.js";
