/**
 * ge kotoba — barrel.
 *
 * Per ADR-2606011400. Global Expansion & Organizational Intelligence (org/
 * project/resource planning metadata) on the etzhayyim substrate (AT PDS
 * records; no RW).
 *
 *   org        : createOrg (optional parent FK) / getOrg / listOrgs
 *   project    : createProject (FK→org) / setProjectStatus / listProjects
 *   assignment : assignResource (FK→project, role + headcount) / listResources
 *   getOrgMetrics (workforce rollup per org)
 *   coverage
 *
 * "Resources" are role/headcount units; employee PII lives elsewhere.
 */

export * from "./types.js";
export {
  createOrg,
  getOrg,
  listOrgs,
  createProject,
  setProjectStatus,
  listProjects,
  assignResource,
  listResources,
  getOrgMetrics,
  coverage,
} from "./registry.js";
