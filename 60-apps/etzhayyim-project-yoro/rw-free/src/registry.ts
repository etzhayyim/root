import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ProjectEntityRecord,
  productResearchDid,
  productResearchRkey,
  projectEntityDid,
  projectEntityRkey,
  activitySeenDid,
  activitySeenRkey,
  appRkey,
  shinkaEvolutionDid,
  shinkaEvolutionRkey,
  shinkaKnowledgeDid,
  shinkaKnowledgeRkey,
  productCategoryDid,
  productCategoryRkey,
  postDid,
  postRkey,
  type ActivitySeenRecord,
  type ShinkaEvolutionRecord,
  type ShinkaKnowledgeRecord,
  type ProductCategoryRecord,
  type PostRecord,
  type HealthOutput,
  type StatsOutput,
  type ListAppsOutput,
  type ListPostsOutput,
  type ListProductResearchOutput,
  type IngestProductCategoryInput,
  type IngestProductCategoryOutput,
  type ProductResearchRecord,
} from "./types.js";

export async function projectEntity(
  e: Etzhayyim,
  input: { projectId: string; entityType: string; entityId: string }
): Promise<{ uri?: string; rkey?: string; error?: string }> {
  const record: ProjectEntityRecord = {
    projectId: input.projectId,
    entityType: input.entityType,
    entityId: input.entityId,
  };
  const rkey = projectEntityRkey(input.projectId, input.entityId);
  try {
    const result = await e.write({
      collection: "com.etzhayyim.yoro.projectEntity",
      record,
      rkey,
    });
    return { uri: result.uri, rkey };
  } catch (err) {
    return { error: String(err) };
  }
}

export async function productResearch(
  e: Etzhayyim,
  input: Omit<ProductResearchRecord, "capturedAt"> & { jobId: string }
): Promise<{ uri?: string; rkey?: string; error?: string }> {
  const record: ProductResearchRecord = {
    ...input,
    capturedAt: new Date().toISOString(),
  };
  const rkey = productResearchRkey(input.jobId);
  try {
    const result = await e.write({
      collection: "com.etzhayyim.yoro.productResearch",
      record,
      rkey,
    });
    return { uri: result.uri, rkey };
  } catch (err) {
    return { error: String(err) };
  }
}

export async function activitySeen(
  e: Etzhayyim,
  input: { objectId: string }
): Promise<{ uri?: string; rkey?: string; error?: string }> {
  const record: ActivitySeenRecord = {
    seenAt: new Date().toISOString(),
  };
  const rkey = activitySeenRkey(input.objectId);
  try {
    const result = await e.write({
      collection: "com.etzhayyim.yoro.activitySeen",
      record,
      rkey,
    });
    return { uri: result.uri, rkey };
  } catch (err) {
    return { error: String(err) };
  }
}

export async function shinkaEvolution(
  e: Etzhayyim,
  input: { nanoid: string; evolutionData: unknown }
): Promise<{ uri?: string; rkey?: string; error?: string }> {
  const record: ShinkaEvolutionRecord = {
    nanoid: input.nanoid,
    evolutionData: input.evolutionData,
  };
  const rkey = shinkaEvolutionRkey(input.nanoid);
  try {
    const result = await e.write({
      collection: "com.etzhayyim.yoro.shinkaEvolution",
      record,
      rkey,
    });
    return { uri: result.uri, rkey };
  } catch (err) {
    return { error: String(err) };
  }
}

export async function shinkaKnowledge(
  e: Etzhayyim,
  input: { nanoid: string; knowledgeData: unknown }
): Promise<{ uri?: string; rkey?: string; error?: string }> {
  const record: ShinkaKnowledgeRecord = {
    nanoid: input.nanoid,
    knowledgeData: input.knowledgeData,
  };
  const rkey = shinkaKnowledgeRkey(input.nanoid);
  try {
    const result = await e.write({
      collection: "com.etzhayyim.yoro.shinkaKnowledge",
      record,
      rkey,
    });
    return { uri: result.uri, rkey };
  } catch (err) {
    return { error: String(err) };
  }
}

export async function ingestProductCategory(
  _e: Etzhayyim,
  _input: IngestProductCategoryInput
): Promise<IngestProductCategoryOutput> {
  const jobId = `job-${Date.now()}`;
  return {
    jobId,
    status: "enqueued",
    researchVertexId: `vertex-${jobId}`,
  };
}

export async function listApps(
  _e: Etzhayyim,
  _input?: { limit?: number; cursor?: string }
): Promise<ListAppsOutput> {
  return {
    items: [],
    total: 0,
  };
}

export async function health(
  _e: Etzhayyim
): Promise<HealthOutput> {
  return {
    ok: true,
    app: "yoro",
    ts: new Date().toISOString(),
  };
}

export async function stats(
  _e: Etzhayyim
): Promise<StatsOutput> {
  return {
    posts: 0,
    profiles: 0,
    ts: new Date().toISOString(),
  };
}

export async function listPosts(
  _e: Etzhayyim,
  _input?: { limit?: number }
): Promise<ListPostsOutput> {
  return {
    items: [],
    count: 0,
  };
}

export async function listProductResearch(
  _e: Etzhayyim,
  _input?: { actorDid?: string; category?: string; query?: string; limit?: number; offset?: number }
): Promise<ListProductResearchOutput> {
  return {
    items: [],
    total: 0,
    offset: _input?.offset ?? 0,
    limit: _input?.limit ?? 50,
  };
}
