import { createKyselyDb, createWorkerExport, nsid, type HostSDK } from "@etzhayyim/magatama-host-sdk";
import type { Database } from "@etzhayyim/graph-schema";
// CHARTER-VIOLATION §substrate (centralized DB forbidden): migrate to AT MST + IPFS + Base L2 anchor
import { Kysely } from "kysely";

type CoverageRow = {
  domain: string;
  did_count: number | null;
  record_count: number | null;
  vertex_count: number | null;
  collected: number | null;
  world_total: number | null;
  coverage_rate: number | null;
};

type PriorityRow = {
  domain: string;
  collected: number;
  worldTotal: number;
  coverageRate: number;
  remaining: number;
};

function asNumber(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "bigint") return Number(value);
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return 0;
}

function summarize(rows: CoverageRow[]) {
  const normalized = rows.map((row) => {
    const collected = asNumber(row.collected);
    const worldTotal = asNumber(row.world_total);
    const coverageRate = typeof row.coverage_rate === "number" && Number.isFinite(row.coverage_rate)
      ? row.coverage_rate
      : (worldTotal > 0 ? collected / worldTotal : 0);
    return {
      domain: row.domain,
      didCount: asNumber(row.did_count),
      recordCount: asNumber(row.record_count),
      vertexCount: asNumber(row.vertex_count),
      collected,
      worldTotal,
      coverageRate,
      remaining: Math.max(worldTotal - collected, 0),
    };
  });

  const summary = normalized.reduce((acc, row) => {
    acc.domains += 1;
    acc.sumCollected += row.collected;
    acc.sumWorldTotal += row.worldTotal;
    acc.sumDidCount += row.didCount;
    acc.sumRecordCount += row.recordCount;
    acc.sumVertexCount += row.vertexCount;
    if (row.collected > 0) acc.nonzeroDomains += 1;
    if (row.collected === 0) acc.zeroDomains += 1;
    if (row.worldTotal > 0 && row.coverageRate >= 1) acc.fullOrOverDomains += 1;
    return acc;
  }, {
    domains: 0,
    nonzeroDomains: 0,
    zeroDomains: 0,
    fullOrOverDomains: 0,
    sumCollected: 0,
    sumWorldTotal: 0,
    sumDidCount: 0,
    sumRecordCount: 0,
    sumVertexCount: 0,
  });

  const overallCoverageRate = summary.sumWorldTotal > 0
    ? summary.sumCollected / summary.sumWorldTotal
    : 0;

  const zeroCoverage = normalized
    .filter((row) => row.collected === 0)
    .sort((a, b) => b.worldTotal - a.worldTotal)
    .slice(0, 12);

  const strategicBacklog = normalized
    .filter((row) => row.coverageRate > 0 && row.coverageRate < 0.01)
    .sort((a, b) => b.remaining - a.remaining)
    .slice(0, 12);

  const nearWins = normalized
    .filter((row) => row.coverageRate >= 0.4 && row.coverageRate < 1)
    .sort((a, b) => b.coverageRate - a.coverageRate || a.remaining - b.remaining)
    .slice(0, 12);

  const denominatorAlerts = normalized
    .filter((row) => row.worldTotal > 0 && row.collected > row.worldTotal)
    .sort((a, b) => (b.collected - b.worldTotal) - (a.collected - a.worldTotal))
    .slice(0, 20);

  const smallestCoverage = normalized
    .filter((row) => row.coverageRate > 0)
    .sort((a, b) => a.coverageRate - b.coverageRate || b.worldTotal - a.worldTotal)
    .slice(0, 12);

  return {
    evaluatedAt: new Date().toISOString(),
    summary: {
      ...summary,
      overallCoverageRate,
    },
    priorities: {
      zeroCoverage,
      strategicBacklog,
      nearWins,
      smallestCoverage,
      denominatorAlerts,
    },
    rows: normalized,
  };
}

async function loadWorldCoverage(sdk: HostSDK) {
  const db = createKyselyDb((sdk.env as any).HYPERDRIVE) as unknown as Kysely<Database>;
  const rows = await db
    .selectFrom("mv_world_coverage_live")
    .select([
      "domain",
      "did_count",
      "record_count",
      "vertex_count",
      "collected",
      "world_total",
      "coverage_rate",
    ])
    .execute() as CoverageRow[];
  return summarize(rows);
}

export default createWorkerExport((sdk) => {
  sdk.app.query(nsid("com.etzhayyim.apps.coverage.getWorldCoverage"), async (_ctx, _body) => {
    return await loadWorldCoverage(sdk);
  });

  sdk.app.query(nsid("com.etzhayyim.apps.coverage.listLatentEntities"), async (_ctx, body) => {
    const args = body as Record<string, unknown>;
    const limit = Math.min(Number(args.limit ?? 50), 200);
    const offset = Number(args.offset ?? 0);
    const entityKind = typeof args.entityKind === "string" ? args.entityKind : undefined;
    const fissionOnly = args.fissionOnly === true || args.fissionOnly === "true";

    const db = createKyselyDb((sdk.env as any).HYPERDRIVE) as unknown as Kysely<Database>;
    let q = db.selectFrom("vertex_latent_entity" as any)
      .select([
        "vertex_id",
        "entity_kind",
        "canonical_label",
        "existence_probability",
        "k_evidence_count",
        "viewpoint_consensus",
        "fission_eligible",
        "status",
        "created_at",
      ] as any);
    if (entityKind) q = (q as any).where("entity_kind", "=", entityKind);
    if (fissionOnly) q = (q as any).where("fission_eligible", "=", true);
    const rows = await (q as any)
      .orderBy("existence_probability", "desc")
      .limit(limit)
      .offset(offset)
      .execute();

    const [countRow] = await (db as any)
      .selectFrom("vertex_latent_entity")
      .select((eb: any) => eb.fn.countAll().as("cnt"))
      .execute();

    return { entities: rows, total: Number(countRow?.cnt ?? 0), offset, limit };
  });

  sdk.app.query(nsid("com.etzhayyim.apps.coverage.getEntityEvidence"), async (_ctx, body) => {
    const args = body as Record<string, unknown>;
    const entityVid = String(args.entityVid ?? "");
    if (!entityVid) return { error: "entityVid required" };
    const limit = Math.min(Number(args.limit ?? 50), 200);

    const db = createKyselyDb((sdk.env as any).HYPERDRIVE) as unknown as Kysely<Database>;
    const evidenceRows = await (db as any)
      .selectFrom("edge_entity_evidence")
      .select(["edge_id", "src_vid", "dst_vid", "created_at"])
      .where("dst_vid", "=", entityVid)
      .orderBy("created_at", "desc")
      .limit(limit)
      .execute();

    const [entity] = await (db as any)
      .selectFrom("vertex_latent_entity")
      .select([
        "vertex_id", "entity_kind", "canonical_label",
        "existence_probability", "k_evidence_count",
        "viewpoint_consensus", "fission_eligible", "status",
      ])
      .where("vertex_id", "=", entityVid)
      .limit(1)
      .execute();

    return { entity: entity ?? null, evidence: evidenceRows };
  });

  sdk.app.query(nsid("com.etzhayyim.apps.coverage.getViewpointStats"), async (_ctx, _body) => {
    const db = createKyselyDb((sdk.env as any).HYPERDRIVE) as unknown as Kysely<Database>;
    const viewpoints = await (db as any)
      .selectFrom("vertex_lda_viewpoint")
      .select([
        "vertex_id", "viewpoint_kind", "description",
        "signal_vocab_size", "active", "created_at",
      ])
      .where("active", "=", true)
      .orderBy("viewpoint_kind", "asc")
      .execute();

    const entityStats = await (db as any)
      .selectFrom("vertex_latent_entity")
      .select([
        "entity_kind",
        (eb: any) => eb.fn.countAll().as("total"),
        (eb: any) => eb.fn.avg(eb.ref("existence_probability")).as("avg_probability"),
        (eb: any) => eb.fn.sum(
          eb.case().when("fission_eligible", "=", true).then(1).else(0).end()
        ).as("fission_ready_count"),
      ])
      .groupBy("entity_kind")
      .execute();

    return {
      viewpoints,
      entityStats,
      evaluatedAt: new Date().toISOString(),
    };
  });
});
