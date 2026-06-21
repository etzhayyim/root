/**
 * kami kotoba — project + design + world registries + coverage. AT PDS records
 * (no RW). Designs FK-reference an existing project; putDesign upserts (version
 * bump). Worlds are guest-creatable. Artifacts/scenes referenced by CID.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  DESIGN_COLLECTION,
  DISCIPLINES,
  PROJECT_COLLECTION,
  TEMPLATES,
  WORLD_COLLECTION,
  designDidFor,
  designRkey,
  looksLikeCid,
  projectDidFor,
  projectRkey,
  worldDidFor,
  worldRkey,
  type CoverageInput,
  type CoverageOutput,
  type CreateProjectInput,
  type CreateProjectOutput,
  type CreateWorldInput,
  type CreateWorldOutput,
  type DesignRecord,
  type DesignView,
  type GetDesignInput,
  type GetDesignOutput,
  type GetProjectInput,
  type GetProjectOutput,
  type ListDesignsInput,
  type ListDesignsOutput,
  type ListProjectsInput,
  type ListProjectsOutput,
  type ListWorldsInput,
  type ListWorldsOutput,
  type ProjectRecord,
  type ProjectView,
  type PutDesignInput,
  type PutDesignOutput,
  type WorldRecord,
  type WorldView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

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

// ─── Project ────────────────────────────────────────────────────────

export async function createProject(e: Etzhayyim, input: CreateProjectInput): Promise<CreateProjectOutput> {
  if (!input.projectId || !input.name || !input.ownerDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!input.ownerDid.startsWith("did:")) return { status: "rejected", error: "invalidOwnerDid" };
  const rkey = projectRkey(input.projectId);
  const existing = await e.read<ProjectRecord>({ collection: PROJECT_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", projectUri: existing.records[0].uri, did: existing.records[0].value.did, projectId: input.projectId };
  }
  const did = projectDidFor(input.projectId);
  const record: ProjectRecord = {
    did,
    projectId: input.projectId,
    name: input.name,
    ownerDid: input.ownerDid,
    status: "active",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: PROJECT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", projectUri: receipt.uri, did, projectId: input.projectId };
}

export async function getProject(e: Etzhayyim, input: GetProjectInput): Promise<GetProjectOutput> {
  if (!input.projectId) return { error: "invalidProjectId" };
  const resp = await e.read<ProjectRecord>({ collection: PROJECT_COLLECTION, rkey: projectRkey(input.projectId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { project: { ...r.value, projectUri: r.uri } };
}

export async function listProjects(e: Etzhayyim, input: ListProjectsInput = {}): Promise<ListProjectsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ProjectRecord>({ collection: PROJECT_COLLECTION, cursor: input.cursor, limit });
  const items: ProjectView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.ownerDid && v.ownerDid !== input.ownerDid) return false;
      if (input.status && v.status !== input.status) return false;
      return true;
    })
    .map((r) => ({ ...r.value, projectUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Design ─────────────────────────────────────────────────────────

export async function putDesign(e: Etzhayyim, input: PutDesignInput): Promise<PutDesignOutput> {
  if (!input.designId || !input.projectId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  if (!DISCIPLINES.has(input.discipline)) return { status: "rejected", error: "invalidDiscipline" };
  if (input.artifactCid && !looksLikeCid(input.artifactCid)) return { status: "rejected", error: "invalidArtifactCid" };
  if (!(await exists(e, PROJECT_COLLECTION, projectRkey(input.projectId)))) {
    return { status: "projectNotFound", error: `projectNotFound:${input.projectId}` };
  }
  const rkey = designRkey(input.designId);
  const existing = await e.read<DesignRecord>({ collection: DESIGN_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const prev = existing.records[0]?.value;
  const now = new Date().toISOString();
  if (prev) {
    if (prev.projectId !== input.projectId) return { status: "rejected", error: "projectMismatch" };
    const updated: DesignRecord = { ...prev, discipline: input.discipline, name: input.name, artifactCid: input.artifactCid, version: prev.version + 1, updatedAt: now };
    const receipt = await e.write({ collection: DESIGN_COLLECTION, record: updated as unknown as Record<string, unknown>, rkey });
    return { status: "updated", designUri: receipt.uri, did: prev.did, designId: input.designId, version: updated.version };
  }
  const did = designDidFor(input.designId);
  const record: DesignRecord = {
    did,
    designId: input.designId,
    projectId: input.projectId,
    discipline: input.discipline,
    name: input.name,
    artifactCid: input.artifactCid,
    version: 1,
    createdAt: now,
    updatedAt: now,
  };
  const receipt = await e.write({ collection: DESIGN_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", designUri: receipt.uri, did, designId: input.designId, version: 1 };
}

export async function getDesign(e: Etzhayyim, input: GetDesignInput): Promise<GetDesignOutput> {
  if (!input.designId) return { error: "invalidDesignId" };
  const resp = await e.read<DesignRecord>({ collection: DESIGN_COLLECTION, rkey: designRkey(input.designId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { design: { ...r.value, designUri: r.uri } };
}

export async function listDesigns(e: Etzhayyim, input: ListDesignsInput = {}): Promise<ListDesignsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<DesignRecord>({ collection: DESIGN_COLLECTION, cursor: input.cursor, limit });
  const items: DesignView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.projectId && v.projectId !== input.projectId) return false;
      if (input.discipline && v.discipline !== input.discipline) return false;
      return true;
    })
    .map((r) => ({ ...r.value, designUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── World ──────────────────────────────────────────────────────────

export async function createWorld(e: Etzhayyim, input: CreateWorldInput): Promise<CreateWorldOutput> {
  if (!input.worldId || !input.name || !input.creatorDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!input.creatorDid.startsWith("did:")) return { status: "rejected", error: "invalidCreatorDid" };
  if (!TEMPLATES.has(input.template)) return { status: "rejected", error: "invalidTemplate" };
  if (input.sceneCid && !looksLikeCid(input.sceneCid)) return { status: "rejected", error: "invalidSceneCid" };
  const rkey = worldRkey(input.worldId);
  const existing = await e.read<WorldRecord>({ collection: WORLD_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", worldUri: existing.records[0].uri, did: existing.records[0].value.did, worldId: input.worldId };
  }
  const did = worldDidFor(input.worldId);
  const record: WorldRecord = {
    did,
    worldId: input.worldId,
    name: input.name,
    creatorDid: input.creatorDid,
    template: input.template,
    visibility: input.visibility ?? "public",
    sceneCid: input.sceneCid,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: WORLD_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", worldUri: receipt.uri, did, worldId: input.worldId };
}

export async function listWorlds(e: Etzhayyim, input: ListWorldsInput = {}): Promise<ListWorldsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<WorldRecord>({ collection: WORLD_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: WorldView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.creatorDid && v.creatorDid !== input.creatorDid) return false;
      if (input.template && v.template !== input.template) return false;
      if (input.visibility && v.visibility !== input.visibility) return false;
      if (q && !v.name.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, worldUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const projectCount = await scanAll<ProjectRecord>(e, PROJECT_COLLECTION, maxScan, () => {});
  const designsByDiscipline: Record<string, number> = {};
  const designCount = await scanAll<DesignRecord>(e, DESIGN_COLLECTION, maxScan, (v) => {
    designsByDiscipline[v.discipline] = (designsByDiscipline[v.discipline] ?? 0) + 1;
  });
  const worldsByTemplate: Record<string, number> = {};
  const worldCount = await scanAll<WorldRecord>(e, WORLD_COLLECTION, maxScan, (v) => {
    worldsByTemplate[v.template] = (worldsByTemplate[v.template] ?? 0) + 1;
  });
  return {
    projectCount,
    designCount,
    worldCount,
    designsByDiscipline,
    worldsByTemplate,
    truncated: projectCount >= maxScan || designCount >= maxScan || worldCount >= maxScan,
  };
}
