/**
 * kami kotoba — barrel.
 *
 * Per ADR-2606011400. The KAMI catalog (engineering workbench + game worlds) on
 * the etzhayyim substrate (AT PDS records; no RW).
 *
 *   project : createProject / getProject / listProjects
 *   design  : putDesign (upsert, FK→project, EDA/CAD/CAM/RTL/CAE, artifact CID) / getDesign / listDesigns
 *   world   : createWorld (guest-creatable, template) / listWorlds (q = app-layer search)
 *   coverage
 *
 * Creative/engineering work product; large artifacts/scenes referenced by CID.
 */

export * from "./types.js";
export {
  createProject,
  getProject,
  listProjects,
  putDesign,
  getDesign,
  listDesigns,
  createWorld,
  listWorlds,
  coverage,
} from "./registry.js";
