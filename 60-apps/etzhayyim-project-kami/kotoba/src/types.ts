/**
 * kami kotoba — KAMI catalog record types (engineering workbench + game worlds).
 *
 * Per ADR-2606011400. KAMI is a WebGPU game engine + world-building workbench
 * plus a browser engineering workbench (EDA/CAD/CAM/RTL/CAE). This package models
 * the unified creative/engineering catalog:
 *   - project — an engineering/creative project container (kami.eng.project)
 *   - design  — a design artifact across disciplines (eda/cad/cam/rtl/cae), by CID
 *   - world   — a KAMI game world (template-based, guest-creatable)
 * Registry on AT PDS records (replaces RW). ADR-2605172000 kotoba.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean — creative/engineering work product
 * (like editor/bim/cad), guest-accessible (guest DIDs). No personal PII, no
 * settlement, no fulfillment liability. Large artifacts/scenes referenced by CID
 * (IPFS), not inlined.
 *
 * AT-Lexicon: no float. Design version is an integer.
 *
 * Identity hierarchy:
 *   did:web:kami.etzhayyim.com                          — controller
 *   did:web:kami.etzhayyim.com:project:{projectId}      — a project
 *   did:web:kami.etzhayyim.com:design:{designId}        — a design artifact
 *   did:web:kami.etzhayyim.com:world:{worldId}          — a game world
 */

export const KAMI_DID_PREFIX = "did:web:kami.etzhayyim.com:" as const;

export const PROJECT_COLLECTION = "com.etzhayyim.apps.kami.eng.project";
export const DESIGN_COLLECTION = "com.etzhayyim.apps.kami.eng.design";
export const WORLD_COLLECTION = "com.etzhayyim.apps.kami.world";

// ─── Project ────────────────────────────────────────────────────────

export type ProjectStatus = "active" | "archived";

export interface ProjectRecord {
  did: string;
  projectId: string;
  name: string;
  ownerDid: string;
  status: ProjectStatus;
  createdAt: string;
}
export interface ProjectView extends ProjectRecord {
  projectUri: string;
}
export interface CreateProjectInput {
  projectId: string;
  name: string;
  ownerDid: string;
}
export interface CreateProjectOutput {
  status: "created" | "alreadyExists" | "rejected";
  projectUri?: string;
  did?: string;
  projectId?: string;
  error?: string;
}
export interface GetProjectInput {
  projectId: string;
}
export interface GetProjectOutput {
  project?: ProjectView;
  error?: string;
}
export interface ListProjectsInput {
  ownerDid?: string;
  status?: ProjectStatus;
  limit?: number;
  cursor?: string;
}
export interface ListProjectsOutput {
  items: ProjectView[];
  cursor?: string;
  total: number;
}

// ─── Design artifact ────────────────────────────────────────────────

export type Discipline =
  | "eda-schematic"
  | "eda-pcb"
  | "cad-model"
  | "cad-assembly"
  | "cam-job"
  | "rtl-module"
  | "cae-analysis";

export interface DesignRecord {
  did: string;
  designId: string;
  /** FK → project projectId. */
  projectId: string;
  discipline: Discipline;
  name: string;
  /** IPFS CID of the design artifact, optional. */
  artifactCid?: string;
  /** Bumps on each put. */
  version: number;
  createdAt: string;
  updatedAt: string;
}
export interface DesignView extends DesignRecord {
  designUri: string;
}
export interface PutDesignInput {
  designId: string;
  projectId: string;
  discipline: Discipline;
  name: string;
  artifactCid?: string;
}
export interface PutDesignOutput {
  status: "created" | "updated" | "rejected" | "projectNotFound";
  designUri?: string;
  did?: string;
  designId?: string;
  version?: number;
  error?: string;
}
export interface GetDesignInput {
  designId: string;
}
export interface GetDesignOutput {
  design?: DesignView;
  error?: string;
}
export interface ListDesignsInput {
  projectId?: string;
  discipline?: Discipline;
  limit?: number;
  cursor?: string;
}
export interface ListDesignsOutput {
  items: DesignView[];
  cursor?: string;
  total: number;
}

// ─── Game world ─────────────────────────────────────────────────────

export type WorldTemplate = "minecraft" | "fortnite" | "roblox" | "blank" | "ai-generated";
export type Visibility = "public" | "private";

export interface WorldRecord {
  did: string;
  worldId: string;
  name: string;
  creatorDid: string;
  template: WorldTemplate;
  visibility: Visibility;
  /** IPFS CID of the published scene, optional. */
  sceneCid?: string;
  createdAt: string;
}
export interface WorldView extends WorldRecord {
  worldUri: string;
}
export interface CreateWorldInput {
  worldId: string;
  name: string;
  creatorDid: string;
  template: WorldTemplate;
  visibility?: Visibility;
  sceneCid?: string;
}
export interface CreateWorldOutput {
  status: "created" | "alreadyExists" | "rejected";
  worldUri?: string;
  did?: string;
  worldId?: string;
  error?: string;
}
export interface ListWorldsInput {
  creatorDid?: string;
  template?: WorldTemplate;
  visibility?: Visibility;
  /** App-layer substring match over name. */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListWorldsOutput {
  items: WorldView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  projectCount?: number;
  designCount?: number;
  worldCount?: number;
  designsByDiscipline?: Record<string, number>;
  worldsByTemplate?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const DISCIPLINES: ReadonlySet<string> = new Set([
  "eda-schematic", "eda-pcb", "cad-model", "cad-assembly", "cam-job", "rtl-module", "cae-analysis",
]);
export const TEMPLATES: ReadonlySet<string> = new Set(["minecraft", "fortnite", "roblox", "blank", "ai-generated"]);

export function looksLikeCid(s: string): boolean {
  return /^b[a-z2-7]{20,}$/.test(s) || /^Qm[1-9A-HJ-NP-Za-km-z]{20,}$/.test(s);
}

export function projectDidFor(id: string): string {
  return `${KAMI_DID_PREFIX}project:${id.toLowerCase()}`;
}
export function projectRkey(id: string): string {
  return `project-${id.toLowerCase()}`;
}
export function designDidFor(id: string): string {
  return `${KAMI_DID_PREFIX}design:${id.toLowerCase()}`;
}
export function designRkey(id: string): string {
  return `design-${id.toLowerCase()}`;
}
export function worldDidFor(id: string): string {
  return `${KAMI_DID_PREFIX}world:${id.toLowerCase()}`;
}
export function worldRkey(id: string): string {
  return `world-${id.toLowerCase()}`;
}
