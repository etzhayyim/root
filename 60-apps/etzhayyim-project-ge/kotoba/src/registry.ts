/**
 * ge kotoba — org + project + resource-assignment registries + org-metrics
 * rollup + coverage. AT PDS records (no RW). Projects FK→org, assignments
 * FK→project; org parent (optional) FK→org. Planning metadata only.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ASSIGNMENT_COLLECTION,
  ORG_COLLECTION,
  PROJECT_COLLECTION,
  assignmentDidFor,
  assignmentRkey,
  isPosInt,
  orgDidFor,
  orgRkey,
  projectDidFor,
  projectRkey,
  type AssignmentRecord,
  type AssignmentView,
  type AssignResourceInput,
  type AssignResourceOutput,
  type CoverageInput,
  type CoverageOutput,
  type CreateOrgInput,
  type CreateOrgOutput,
  type CreateProjectInput,
  type CreateProjectOutput,
  type GetOrgInput,
  type GetOrgMetricsInput,
  type GetOrgMetricsOutput,
  type GetOrgOutput,
  type ListOrgsInput,
  type ListOrgsOutput,
  type ListProjectsInput,
  type ListProjectsOutput,
  type ListResourcesInput,
  type ListResourcesOutput,
  type OrgRecord,
  type OrgView,
  type ProjectRecord,
  type ProjectStatus,
  type ProjectView,
  type SetProjectStatusInput,
  type SetProjectStatusOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;
const PROJECT_STATUSES: ReadonlySet<string> = new Set(["planned", "active", "completed", "cancelled"]);

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

// ─── Org ────────────────────────────────────────────────────────────

export async function createOrg(e: Etzhayyim, input: CreateOrgInput): Promise<CreateOrgOutput> {
  if (!input.orgId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  if (input.parentOrgId && !(await exists(e, ORG_COLLECTION, orgRkey(input.parentOrgId)))) {
    return { status: "parentNotFound", error: `parentNotFound:${input.parentOrgId}` };
  }
  const rkey = orgRkey(input.orgId);
  const existing = await e.read<OrgRecord>({ collection: ORG_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", orgUri: existing.records[0].uri, did: existing.records[0].value.did, orgId: input.orgId };
  }
  const did = orgDidFor(input.orgId);
  const record: OrgRecord = {
    did,
    orgId: input.orgId,
    name: input.name,
    parentOrgId: input.parentOrgId,
    region: input.region,
    status: "active",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ORG_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", orgUri: receipt.uri, did, orgId: input.orgId };
}

export async function getOrg(e: Etzhayyim, input: GetOrgInput): Promise<GetOrgOutput> {
  if (!input.orgId) return { error: "invalidOrgId" };
  const resp = await e.read<OrgRecord>({ collection: ORG_COLLECTION, rkey: orgRkey(input.orgId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { org: { ...r.value, orgUri: r.uri } };
}

export async function listOrgs(e: Etzhayyim, input: ListOrgsInput = {}): Promise<ListOrgsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<OrgRecord>({ collection: ORG_COLLECTION, cursor: input.cursor, limit });
  const items: OrgView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.parentOrgId && v.parentOrgId !== input.parentOrgId) return false;
      if (input.region && v.region !== input.region) return false;
      if (input.status && v.status !== input.status) return false;
      return true;
    })
    .map((r) => ({ ...r.value, orgUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Project ────────────────────────────────────────────────────────

export async function createProject(e: Etzhayyim, input: CreateProjectInput): Promise<CreateProjectOutput> {
  if (!input.projectId || !input.orgId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  if (!(await exists(e, ORG_COLLECTION, orgRkey(input.orgId)))) {
    return { status: "orgNotFound", error: `orgNotFound:${input.orgId}` };
  }
  const rkey = projectRkey(input.projectId);
  const existing = await e.read<ProjectRecord>({ collection: PROJECT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", projectUri: existing.records[0].uri, did: existing.records[0].value.did, projectId: input.projectId };
  }
  const did = projectDidFor(input.projectId);
  const record: ProjectRecord = {
    did,
    projectId: input.projectId,
    orgId: input.orgId,
    name: input.name,
    status: "planned",
    startDate: input.startDate,
    endDate: input.endDate,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: PROJECT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", projectUri: receipt.uri, did, projectId: input.projectId };
}

export async function setProjectStatus(e: Etzhayyim, input: SetProjectStatusInput): Promise<SetProjectStatusOutput> {
  if (!input.projectId || !PROJECT_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  const rkey = projectRkey(input.projectId);
  const resp = await e.read<ProjectRecord>({ collection: PROJECT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const project = resp.records[0]?.value;
  if (!project) return { status: "notFound", error: "projectNotFound" };
  if (project.status === "completed" || project.status === "cancelled") {
    return { status: "rejected", error: `projectTerminal:${project.status}` };
  }
  await e.write({ collection: PROJECT_COLLECTION, record: { ...project, status: input.status } as unknown as Record<string, unknown>, rkey });
  return { status: "updated", projectId: input.projectId, newStatus: input.status };
}

export async function listProjects(e: Etzhayyim, input: ListProjectsInput = {}): Promise<ListProjectsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ProjectRecord>({ collection: PROJECT_COLLECTION, cursor: input.cursor, limit });
  const items: ProjectView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.orgId && v.orgId !== input.orgId) return false;
      if (input.status && v.status !== input.status) return false;
      return true;
    })
    .map((r) => ({ ...r.value, projectUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Resource assignment ────────────────────────────────────────────

export async function assignResource(e: Etzhayyim, input: AssignResourceInput): Promise<AssignResourceOutput> {
  if (!input.assignmentId || !input.projectId || !input.role) return { status: "rejected", error: "missingRequiredFields" };
  if (!isPosInt(input.headcount)) return { status: "rejected", error: "headcountMustBePosInt" };
  if (!(await exists(e, PROJECT_COLLECTION, projectRkey(input.projectId)))) {
    return { status: "projectNotFound", error: `projectNotFound:${input.projectId}` };
  }
  const rkey = assignmentRkey(input.assignmentId);
  const existing = await e.read<AssignmentRecord>({ collection: ASSIGNMENT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", assignmentUri: existing.records[0].uri, did: existing.records[0].value.did, assignmentId: input.assignmentId };
  }
  const did = assignmentDidFor(input.assignmentId);
  const record: AssignmentRecord = {
    did,
    assignmentId: input.assignmentId,
    projectId: input.projectId,
    role: input.role,
    headcount: input.headcount,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ASSIGNMENT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "assigned", assignmentUri: receipt.uri, did, assignmentId: input.assignmentId };
}

export async function listResources(e: Etzhayyim, input: ListResourcesInput = {}): Promise<ListResourcesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AssignmentRecord>({ collection: ASSIGNMENT_COLLECTION, cursor: input.cursor, limit });
  const items: AssignmentView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.projectId && v.projectId !== input.projectId) return false;
      if (input.role && v.role !== input.role) return false;
      return true;
    })
    .map((r) => ({ ...r.value, assignmentUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Org metrics / workforce (rollup) ───────────────────────────────

export async function getOrgMetrics(e: Etzhayyim, input: GetOrgMetricsInput): Promise<GetOrgMetricsOutput> {
  if (!input.orgId) return { error: "invalidOrgId" };
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const projectsByStatus: Record<string, number> = {};
  const projectIds = new Set<string>();
  const projScanned = await scanAll<ProjectRecord>(e, PROJECT_COLLECTION, maxScan, (v) => {
    if (v.orgId !== input.orgId) return;
    projectIds.add(v.projectId);
    projectsByStatus[v.status] = (projectsByStatus[v.status] ?? 0) + 1;
  });
  const headcountByRole: Record<string, number> = {};
  let totalHeadcount = 0;
  const asgScanned = await scanAll<AssignmentRecord>(e, ASSIGNMENT_COLLECTION, maxScan, (v) => {
    if (!projectIds.has(v.projectId)) return;
    totalHeadcount += v.headcount;
    headcountByRole[v.role] = (headcountByRole[v.role] ?? 0) + v.headcount;
  });
  return {
    orgId: input.orgId,
    projectCount: projectIds.size,
    projectsByStatus,
    totalHeadcount,
    headcountByRole,
    truncated: projScanned >= maxScan || asgScanned >= maxScan,
  };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const orgCount = await scanAll<OrgRecord>(e, ORG_COLLECTION, maxScan, () => {});
  const projectsByStatus: Record<string, number> = {};
  const projectCount = await scanAll<ProjectRecord>(e, PROJECT_COLLECTION, maxScan, (v) => {
    projectsByStatus[v.status] = (projectsByStatus[v.status] ?? 0) + 1;
  });
  let totalHeadcount = 0;
  const assignmentCount = await scanAll<AssignmentRecord>(e, ASSIGNMENT_COLLECTION, maxScan, (v) => {
    totalHeadcount += v.headcount;
  });
  return {
    orgCount,
    projectCount,
    assignmentCount,
    projectsByStatus,
    totalHeadcount,
    truncated: orgCount >= maxScan || projectCount >= maxScan || assignmentCount >= maxScan,
  };
}
