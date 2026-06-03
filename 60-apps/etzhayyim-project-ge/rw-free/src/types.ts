/**
 * ge rw-free — Global Expansion & Organizational Intelligence record types.
 *
 * Per ADR-2606011400. ge is an org/project/resource planning platform: orgs
 * (structure) + projects (FK→org) + resource assignments (FK→project, role +
 * headcount) + workforce rollup. Registry on AT PDS records (replaces RW).
 * ADR-2605172000 RW-free.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean — planning metadata only. "Resources"
 * are role/headcount UNITS, not named employees; employee PII lives in
 * business-person / natural-person, never here. No settlement, no liability.
 *
 * AT-Lexicon: no float. Headcount is an integer.
 *
 * Identity hierarchy:
 *   did:web:ge.etzhayyim.com                              — controller
 *   did:web:ge.etzhayyim.com:org:{orgId}                  — an organization
 *   did:web:ge.etzhayyim.com:project:{projectId}          — a project
 *   did:web:ge.etzhayyim.com:assignment:{assignmentId}    — a resource assignment
 */

export const GE_DID_PREFIX = "did:web:ge.etzhayyim.com:" as const;

export const ORG_COLLECTION = "com.etzhayyim.apps.ge.org";
export const PROJECT_COLLECTION = "com.etzhayyim.apps.ge.project";
export const ASSIGNMENT_COLLECTION = "com.etzhayyim.apps.ge.assignment";

// ─── Org ────────────────────────────────────────────────────────────

export type OrgStatus = "active" | "dissolved";

export interface OrgRecord {
  did: string;
  orgId: string;
  name: string;
  /** Parent org (hierarchy), optional. */
  parentOrgId?: string;
  /** Region / market, optional. */
  region?: string;
  status: OrgStatus;
  createdAt: string;
}
export interface OrgView extends OrgRecord {
  orgUri: string;
}
export interface CreateOrgInput {
  orgId: string;
  name: string;
  parentOrgId?: string;
  region?: string;
}
export interface CreateOrgOutput {
  status: "created" | "alreadyExists" | "rejected" | "parentNotFound";
  orgUri?: string;
  did?: string;
  orgId?: string;
  error?: string;
}
export interface GetOrgInput {
  orgId: string;
}
export interface GetOrgOutput {
  org?: OrgView;
  error?: string;
}
export interface ListOrgsInput {
  parentOrgId?: string;
  region?: string;
  status?: OrgStatus;
  limit?: number;
  cursor?: string;
}
export interface ListOrgsOutput {
  items: OrgView[];
  cursor?: string;
  total: number;
}

// ─── Project ────────────────────────────────────────────────────────

export type ProjectStatus = "planned" | "active" | "completed" | "cancelled";

export interface ProjectRecord {
  did: string;
  projectId: string;
  /** FK → org orgId. */
  orgId: string;
  name: string;
  status: ProjectStatus;
  startDate?: string;
  endDate?: string;
  createdAt: string;
}
export interface ProjectView extends ProjectRecord {
  projectUri: string;
}
export interface CreateProjectInput {
  projectId: string;
  orgId: string;
  name: string;
  startDate?: string;
  endDate?: string;
}
export interface CreateProjectOutput {
  status: "created" | "alreadyExists" | "rejected" | "orgNotFound";
  projectUri?: string;
  did?: string;
  projectId?: string;
  error?: string;
}
export interface SetProjectStatusInput {
  projectId: string;
  status: ProjectStatus;
}
export interface SetProjectStatusOutput {
  status: "updated" | "notFound" | "rejected";
  projectId?: string;
  newStatus?: ProjectStatus;
  error?: string;
}
export interface ListProjectsInput {
  orgId?: string;
  status?: ProjectStatus;
  limit?: number;
  cursor?: string;
}
export interface ListProjectsOutput {
  items: ProjectView[];
  cursor?: string;
  total: number;
}

// ─── Resource assignment ────────────────────────────────────────────

export interface AssignmentRecord {
  did: string;
  assignmentId: string;
  /** FK → project projectId. */
  projectId: string;
  /** Role / function (not a named person). */
  role: string;
  /** Headcount units (≥1, integer). */
  headcount: number;
  createdAt: string;
}
export interface AssignmentView extends AssignmentRecord {
  assignmentUri: string;
}
export interface AssignResourceInput {
  assignmentId: string;
  projectId: string;
  role: string;
  headcount: number;
}
export interface AssignResourceOutput {
  status: "assigned" | "alreadyExists" | "rejected" | "projectNotFound";
  assignmentUri?: string;
  did?: string;
  assignmentId?: string;
  error?: string;
}
export interface ListResourcesInput {
  projectId?: string;
  role?: string;
  limit?: number;
  cursor?: string;
}
export interface ListResourcesOutput {
  items: AssignmentView[];
  cursor?: string;
  total: number;
}

// ─── Org metrics / workforce (rollup) ───────────────────────────────

export interface GetOrgMetricsInput {
  orgId: string;
  maxScan?: number;
}
export interface GetOrgMetricsOutput {
  orgId?: string;
  projectCount?: number;
  projectsByStatus?: Record<string, number>;
  totalHeadcount?: number;
  headcountByRole?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  orgCount?: number;
  projectCount?: number;
  assignmentCount?: number;
  projectsByStatus?: Record<string, number>;
  totalHeadcount?: number;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isPosInt(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n > 0;
}

export function orgDidFor(id: string): string {
  return `${GE_DID_PREFIX}org:${id.toLowerCase()}`;
}
export function orgRkey(id: string): string {
  return `org-${id.toLowerCase()}`;
}
export function projectDidFor(id: string): string {
  return `${GE_DID_PREFIX}project:${id.toLowerCase()}`;
}
export function projectRkey(id: string): string {
  return `project-${id.toLowerCase()}`;
}
export function assignmentDidFor(id: string): string {
  return `${GE_DID_PREFIX}assignment:${id.toLowerCase()}`;
}
export function assignmentRkey(id: string): string {
  return `assignment-${id.toLowerCase()}`;
}
