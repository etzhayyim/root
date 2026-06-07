import {
  asAgentTool,
  createWorkerExport,
  withCapabilityTags,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  nowISO,
  createKyselyDb,
  str,
  sql,
  genID,
  nsid,
} from "@etzhayyim/kotodama-host-sdk";

let appId = "";

type QueryRow = Record<string, unknown>;

function mapIncidentRow(row: QueryRow): QueryRow {
  const incidentId = str(row.incidentId ?? row.incident_id ?? "");
  const sourceCaseId = str(row.sourceCaseId ?? row.source_case_id ?? "");
  const sourceApp = str(row.sourceApp ?? row.source_app ?? "");
  const chain = str(row.chain ?? "");
  const priority = str(row.priority ?? "");
  const status = str(row.status ?? "");
  const createdAt = str(row.createdAt ?? row.created_at ?? "");
  const walletAddresses = row.walletAddresses ?? row.wallet_addresses;
  return {
    incidentId,
    sourceCaseId,
    sourceApp,
    walletAddresses,
    chain,
    priority,
    status,
    createdAt,
  };
}

async function getFreezeIncidentById(incidentId: string): Promise<QueryRow | null> {
  const db = createKyselyDb();
  const rows = await db
    .selectFrom("vertex_crypto_asset_freeze_incident" as any)
    .select([
      "incident_id",
      "source_case_id",
      "source_app",
      "wallet_addresses",
      "chain",
      "priority",
      "status",
      "created_at",
    ])
    .where("incident_id", "=", incidentId)
    .limit(1)
    .execute();
  if (rows.length === 0) return null;
  return mapIncidentRow(rows[0] as QueryRow);
}

async function listFreezeIncidents(status: string, limit: number): Promise<QueryRow[]> {
  const db = createKyselyDb();
  let query = db
    .selectFrom("vertex_crypto_asset_freeze_incident" as any)
    .select([
      "incident_id",
      "source_case_id",
      "source_app",
      "wallet_addresses",
      "chain",
      "priority",
      "status",
      "created_at",
    ]);
  if (status) {
    query = query.where("status", "=", status);
  }
  const rows = await query
    .orderBy("created_at", "desc")
    .limit(limit)
    .execute();
  return rows.map((row) => mapIncidentRow(row as QueryRow));
}

async function hasBlockchainActor(nodeId: string): Promise<boolean> {
  const db = createKyselyDb();
  const rows = await db
    .selectFrom("vertex_blockchain_actor")
    .select(["vertex_id"])
    .where(sql<boolean>`coalesce(props::jsonb ->> 'nodeId', '') = ${nodeId}`)
    .limit(1)
    .execute();
  return rows.length > 0;
}

async function write(_sdk: HostSDK, collection: string, rec: Record<string, unknown>): Promise<void> {
  function camelToSnake(s: string): string { return s.replace(/[A-Z]/g, c => `_${c.toLowerCase()}`); }
  const tableMap: Record<string, string> = {
    incident: "vertex_crypto_asset_freeze_incident",
    freezeRequest: "vertex_crypto_asset_freeze_freeze_request",
    forensicTrace: "vertex_crypto_asset_freeze_forensic_trace",
  };
  const table = tableMap[collection] ?? `vertex_crypto_asset_freeze_${camelToSnake(collection)}`;
  const ownerDid = `did:web:qjp7mjyb.etzhayyim.com`;
  const rkey = str(rec.incidentId ?? rec.requestId ?? rec.traceId ?? "") || genID();
  const vertex_id = `at://${ownerDid}/com.etzhayyim.apps.cryptoAssetFreeze.${collection}/${rkey}`;
  const snakeRec = Object.fromEntries(Object.entries(rec).map(([k, v]) => [camelToSnake(k), v]));
  await createKyselyDb().insertInto(table as any).values({ vertex_id, sensitivity_ord: 2, owner_did: ownerDid, actor_id: appId, ...snakeRec }).execute();
}

function post(sdk: HostSDK, text: string): void {
  const rec = { $type: "app.bsky.feed.post", text: text.slice(0, 300), createdAt: nowISO() };
  const pds = sdk.pds as unknown as {
    createRecord?: (collection: string, record: Record<string, unknown>) => unknown;
    dispatch?: (msg: { type: string; payload: unknown }) => unknown;
  };
  if (typeof pds.createRecord === "function") { pds.createRecord("app.bsky.feed.post", rec); return; }
  pds.dispatch?.({ type: "app.bsky.feed.post", payload: rec });
}

// --- Graph Schema ---
// FreezeIncident:      { incident_id, source_case_id, source_app, status, priority, created_at }
// FreezeRequest:       { request_id, incident_id, exchange, wallet_address, chain, amount, currency, status, requested_at }
// FreezeResponse:      { response_id, request_id, exchange, status, frozen_amount, responded_at }
// ForensicTrace:       { trace_id, incident_id, wallet_address, chain, hops, total_value, traced_at }
// ExchangeNotification:{ notification_id, exchange, contact_method, status, sent_at }

export default createWorkerExport((sdk: HostSDK) => {
  appId = sdk.app.nanoid ?? "qjp7mjyb";

  // ── Commands ──

  sdk.app.command(nsid("com.etzhayyim.apps.cryptoAssetFreeze.createIncident"),
    async (_ctx, params) => {
      const sourceCaseId = str(params?.sourceCaseId ?? "");
      const sourceApp = str(params?.sourceApp ?? "malak");
      const walletAddresses = (params?.walletAddresses as string[]) ?? [];
      const chain = str(params?.chain ?? "btc");
      const priority = str(params?.priority ?? "high");

      const incidentId = `inc-${genID()}`;
      await write(sdk, "incident", {
        incidentId,
        sourceCaseId,
        sourceApp,
        walletAddresses: JSON.stringify(walletAddresses),
        chain,
        priority,
        status: "open",
        createdAt: nowISO(),
      });

      return { incidentId, status: "open", walletCount: walletAddresses.length };
    },
    asAgentTool("Create freeze incident from malak escalation"),
    withCapabilityTags("freeze", "incident", "law-enforcement"),
  );

  sdk.app.command(nsid("com.etzhayyim.apps.cryptoAssetFreeze.requestFreeze"),
    async (_ctx, params) => {
      const incidentId = str(params?.incidentId ?? "");
      const exchange = str(params?.exchange ?? "");
      const walletAddress = str(params?.walletAddress ?? "");
      const chain = str(params?.chain ?? "btc");
      if (!incidentId || !exchange || !walletAddress) {
        return { error: "incidentId, exchange, and walletAddress are required" };
      }

      const requestId = `freq-${genID()}`;
      await write(sdk, "freezeRequest", {
        requestId,
        incidentId,
        exchange,
        walletAddress,
        chain,
        status: "pending",
        requestedAt: nowISO(),
      });

      return { requestId, status: "pending", exchange, walletAddress };
    },
    asAgentTool("Request exchange to freeze wallet"),
    withCapabilityTags("freeze", "exchange"),
  );

  sdk.app.command(nsid("com.etzhayyim.apps.cryptoAssetFreeze.traceWallet"),
    async (_ctx, params) => {
      const walletAddress = str(params?.walletAddress ?? "");
      const chain = str(params?.chain ?? "btc");
      const maxHops = Number(params?.maxHops ?? 3);
      if (!walletAddress) return { error: "walletAddress is required" };

      // Query collector's blockchain data for transaction graph
      const existingData = await hasBlockchainActor(`bchain:${walletAddress}`);

      const traceId = `trace-${genID()}`;
      await write(sdk, "forensicTrace", {
        traceId,
        walletAddress,
        chain,
        maxHops,
        hops: 0,
        totalValue: "0",
        status: "initiated",
        tracedAt: nowISO(),
      });

      return { traceId, walletAddress, chain, existingData };
    },
    asAgentTool("Trace wallet transaction graph for forensic analysis"),
    withCapabilityTags("forensic", "blockchain", "tracing"),
  );

  sdk.app.command(nsid("com.etzhayyim.apps.cryptoAssetFreeze.getIncident"),
    async (_ctx, params) => {
      const incidentId = str(params?.incidentId ?? "");
      if (!incidentId) return { error: "incidentId is required" };
      return (await getFreezeIncidentById(incidentId)) ?? { error: "not found" };
    },
    asAgentTool("Get freeze incident details"),
  );

  sdk.app.command(nsid("com.etzhayyim.apps.cryptoAssetFreeze.listIncidents"),
    async (_ctx, params) => {
      const limit = Number(params?.limit ?? 20);
      const status = str(params?.status ?? "");
      const rows = await listFreezeIncidents(status, limit);
      return { incidents: rows, total: rows.length };
    },
    asAgentTool("List freeze incidents"),
  );

  // ── Reactive Pipeline (Design E) ──

  sdk.app.onCommit(handleComAtprotoSyncSubscribeReposCommit);
});

async function handleComAtprotoSyncSubscribeReposCommit(
  commit: ComAtprotoSyncSubscribeReposCommit,
): Promise<void> {
  if (commit.action !== "create") return;

  // malak freeze escalation → auto-create incident
  if (commit.collection === "com.etzhayyim.apps.malak.freezeEscalation") {
    const rec = commit.record as Record<string, unknown> | undefined;
    const caseId = str(rec?.case_id ?? rec?.caseId ?? "");
    const wallets = (rec?.wallet_addresses ?? rec?.walletAddresses ?? []) as string[];
    console.log(`[crypto-asset-freeze] Escalation received: case=${caseId}, wallets=${wallets.length}`);
  }

  // collector blockchain actor → enrich existing traces
  if (commit.collection === "com.etzhayyim.apps.collector.blockchainActor") {
    const rec = commit.record as Record<string, unknown> | undefined;
    const actorId = str(rec?.actor_id ?? rec?.actorId ?? "");
    if (actorId) {
      console.log(`[crypto-asset-freeze] Blockchain actor update: ${actorId}`);
    }
  }
}
