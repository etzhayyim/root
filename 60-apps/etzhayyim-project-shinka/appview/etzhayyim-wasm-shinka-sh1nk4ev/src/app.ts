/**
 * Shinka Evolution Scheduler — drives social evolution for all logical actors.
 *
 * Architecture:
 * - Cron (every 5 min) queries stalest actors, resolves joucho cadence, executes shinka tasks
 * - Murakumo fleet inference (qwen3.5-4b) for domain knowledge generation
 * - PDS_SERVICE for graph read/write (SQL) + social posts (AppBskyFeedPost)
 * - No Worker per actor — PDS proxies XRPC for logical actors
 *
 * Joucho cadence is derived from `determineMood()` (heartbeat-cadence.ts) to guarantee
 * consistency between the headless Worker and CLI batch paths.
 *
 * Graph labels:
 *   :Actor          — DID identity node (status, lastHeartbeat, joucho scores)
 *   :ShinkaTask     — evolution task queue (actorDid, type, priority, status)
 *   :KyumeiResult   — self-information gathering results (topic, source, summary)
 *   :ShinkaKnowledge — knowledge graph edges generated from kyumei-koji
 *
 * Collection kinds (camelCase):
 *   kyumeiResult, shinkaPost, shinkaCoverage, shinkaKnowledge
 */
import {
  asAgentTool,
  createWorkerExport,
  createKyselyDb,
  nowISO,
  str,
  num,
  genID,
  rlsDefaults,
  determineMood,
  decodeJson,
  type JouchoScores,
  type Mood,
  type HostSDK,
  nsid,
  parseLexiconInput,
  sql,
} from "@etzhayyim/kotodama-host-sdk";

// ---------------------------------------------------------------------------
// BPMN dispatcher helpers (ADR-0056, proxyToBpmn pattern)
// ---------------------------------------------------------------------------
type InternalSecret = string | { get(): Promise<string> };
type EnvLike = { DISPATCHER_URL?: string; DISPATCHER_INTERNAL_SECRET?: InternalSecret };
function envOf(sdk: unknown): EnvLike { return ((sdk as { env?: EnvLike }).env ?? {}) as EnvLike; }
function dispatcherUrl(sdk: unknown): string { return envOf(sdk).DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com"; }
async function internalTrustHeader(sdk: unknown): Promise<string> {
  const binding = envOf(sdk).DISPATCHER_INTERNAL_SECRET;
  if (!binding) return "";
  try { return typeof binding === "string" ? binding : await binding.get(); } catch { return ""; }
}
async function proxyToBpmn(sdk: HostSDK, toolNsid: string, input: unknown): Promise<void> {
  const trust = await internalTrustHeader(sdk);
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (trust) headers["x-internal-trust"] = trust;
  await fetch(`${dispatcherUrl(sdk)}/xrpc/${toolNsid}`, {
    method: "POST", headers, body: JSON.stringify(input ?? {}),
  });
}

/** Module-level SDK reference — set during setup(). */
let _sdk: HostSDK | null = null;

type AnyRow = Record<string, unknown>;
type KyselyDb = ReturnType<typeof createKyselyDb>;

let _db: KyselyDb | null = null;

const SHINKA_NS = "com.etzhayyim.apps.shinka";
const COLL_TIMELINE = `${SHINKA_NS}.timeline`;
const COLL_HISTORICAL_EVENT = `${SHINKA_NS}.historicalEvent`;
const COLL_PROPAGATION_EVENT = `${SHINKA_NS}.propagationEvent`;
const COLL_PROPAGATION_JOB = `${SHINKA_NS}.propagationJob`;
const COLL_HEARD_FROM = `${SHINKA_NS}.heardFrom`;
const COLL_SHINKA_EVOLUTION = `${SHINKA_NS}.shinkaEvolution`;
const COLL_KYUMEI_RESULT = `${SHINKA_NS}.kyumeiResult`;
const COLL_SHINKA_COVERAGE = `${SHINKA_NS}.shinkaCoverage`;
const COLL_SHINKA_KNOWLEDGE = `${SHINKA_NS}.shinkaKnowledge`;
const COLL_MENTION = `${SHINKA_NS}.mention`;

type ShinkaTableRoute = { table: string; idColumn: "vertex_id" | "edge_id"; edge: boolean };
const SHINKA_TABLES: Record<string, ShinkaTableRoute> = {
  [COLL_TIMELINE]: { table: "vertex_shinka_timeline", idColumn: "vertex_id", edge: false },
  [COLL_HISTORICAL_EVENT]: { table: "vertex_shinka_historical_event", idColumn: "vertex_id", edge: false },
  [COLL_PROPAGATION_EVENT]: { table: "vertex_shinka_propagation_event", idColumn: "vertex_id", edge: false },
  [COLL_PROPAGATION_JOB]: { table: "vertex_shinka_propagation_job", idColumn: "vertex_id", edge: false },
  [COLL_SHINKA_EVOLUTION]: { table: "vertex_shinka_evolution_run", idColumn: "vertex_id", edge: false },
  [COLL_KYUMEI_RESULT]: { table: "vertex_shinka_kyumei_result", idColumn: "vertex_id", edge: false },
  [COLL_SHINKA_COVERAGE]: { table: "vertex_shinka_coverage", idColumn: "vertex_id", edge: false },
  [COLL_HEARD_FROM]: { table: "edge_shinka_heard_from", idColumn: "edge_id", edge: true },
  [COLL_MENTION]: { table: "edge_shinka_mention", idColumn: "edge_id", edge: true },
  [COLL_SHINKA_KNOWLEDGE]: { table: "edge_shinka_knowledge", idColumn: "edge_id", edge: true },
};

function getDb(): KyselyDb {
  if (!_db) _db = createKyselyDb();
  return _db;
}

function parseProps(props: unknown): Record<string, unknown> {
  if (typeof props !== "string" || props.length === 0) return {};
  try {
    const parsed = JSON.parse(props) as unknown;
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

function tableFor(collection: string): ShinkaTableRoute {
  const route = SHINKA_TABLES[collection];
  if (!route) throw new Error(`unsupported shinka collection: ${collection}`);
  return route;
}

function normalizeDomainRow(row: any, collection: string): AnyRow {
  if (!row) return {};
  const data = parseProps(row.value_json ?? row.props);
  return {
    ...data,
    ...row,
    vertexId: row.vertex_id ?? row.edge_id ?? row.vertexId,
    collection,
    rkey: row.vertex_key ?? row.edge_key ?? row.rkey,
    createdAt: data.createdAt ?? row.created_at ?? row.createdAt,
    updatedAt: data.updatedAt ?? row.updated_at ?? row.updatedAt,
  };
}

function toBool(value: unknown): boolean {
  return value === true || value === "true" || value === 1 || value === "1";
}

function rowField(row: any, ...keys: string[]): unknown {
  for (const key of keys) {
    if (row[key] != null && row[key] !== "") return row[key];
  }
  return undefined;
}

function rowInstant(row: any): number {
  const value = rowField(row, "createdAt", "created_at", "createdDate");
  if (typeof value !== "string" || value.length === 0) return 0;
  const ts = Date.parse(value);
  return Number.isFinite(ts) ? ts : 0;
}

function dedupeLatestRows(rows: AnyRow[]): AnyRow[] {
  const latest = new Map<string, AnyRow>();
  for (const row of rows) {
    const key = String(row.rkey ?? row.id ?? row.vertexId ?? row.did ?? "");
    if (!key) continue;
    const existing = latest.get(key);
    if (!existing || rowInstant(row) >= rowInstant(existing)) latest.set(key, row);
  }
  return [...latest.values()];
}

function stripRecordMeta(row: any): Record<string, unknown> {
  const {
    vertexId,
    seq,
    createdDate,
    sensitivityOrd,
    ownerDid,
    vertex_id,
    vertex_key,
    edge_id,
    edge_key,
    src_vid,
    dst_vid,
    relation,
    value_json,
    indexed_at,
    created_at,
    updated_at,
    org_id,
    user_id,
    actor_id,
    actor_did,
    org_did,
    owner_did,
    repo,
    label,
    collection,
    did,
    rkey,
    props,
    ...body
  } = row;
  return body as Record<string, unknown>;
}

async function listOtherRows(collection: string): Promise<AnyRow[]> {
  const route = tableFor(collection);
  const rows = await getDb()
    .selectFrom(route.table as any)
    .selectAll()
    .execute();
  return dedupeLatestRows(rows.map((row) => normalizeDomainRow(row, collection)));
}

async function loadOtherRow(collection: string, predicate: (row: AnyRow) => boolean): Promise<AnyRow | null> {
  const rows = await listOtherRows(collection);
  return rows.find(predicate) ?? null;
}

async function loadActorRows(status?: string, maxRows = 500): Promise<AnyRow[]> {
  let query: any = getDb().selectFrom("vertex_actor").selectAll();
  if (status) query = query.where("status", "=", status);
  // Always cap to prevent OOM — vertex_actor has 37K+ rows
  query = query.limit(maxRows);
  const rows = await query.execute();
  return rows.map((row: AnyRow) => ({ ...row }));
}

function normalizeActorRow(row: any): ActorRow {
  const source = row ?? {};
  return {
    did: String(rowField(source, "did") ?? ""),
    nanoid: String(rowField(source, "nanoid") ?? ""),
    displayName: String(rowField(source, "displayName", "display_name", "name") ?? ""),
    description: String(rowField(source, "description") ?? ""),
    domain: String(rowField(source, "domain", "project", "category", "name") ?? ""),
    lastHeartbeat: String(rowField(source, "lastHeartbeat", "last_heartbeat", "lastShinkaAt", "last_shinka_at", "createdAt") ?? ""),
    lastShinkaAt: String(rowField(source, "lastShinkaAt", "last_shinka_at") ?? ""),
    lastKyumeiAt: String(rowField(source, "lastKyumeiAt", "last_kyumei_at") ?? ""),
    joy: num(rowField(source, "joy")),
    calm: num(rowField(source, "calm")),
    stress: num(rowField(source, "stress")),
    gratitude: num(rowField(source, "gratitude")),
    focus: num(rowField(source, "focus")),
  };
}

/**
 * Compute knowledge graph out-degree per actor.
 * shinkaKnowledge edges are the primary knowledge graph representation in RisingWave.
 * Actors with degree 0 are leaf nodes — they get highest priority in the reverse toposort.
 */
async function computeKnowledgeDegrees(): Promise<Map<string, number>> {
  const degreeByDid = new Map<string, number>();
  const edges = await listOtherRows(COLL_SHINKA_KNOWLEDGE).catch(() => []);
  for (const edge of edges) {
    const did = String(rowField(edge, "actorDid", "fromDid", "did") ?? "");
    if (!did) continue;
    degreeByDid.set(did, (degreeByDid.get(did) ?? 0) + 1);
  }
  return degreeByDid;
}

/**
 * Reverse topological sort — actors with lowest knowledge graph degree first.
 *
 * Design:
 *   tier 0  degree=0        (no edges — bootstrap, highest priority)
 *   tier 1  degree 1-5      (sparse knowledge — primary growth zone)
 *   tier 2  degree 6-20     (developing knowledge graph)
 *   tier 3  degree 21+      (mature — lowest priority, avoid over-concentration)
 *
 * Within each tier, staleness (last kyumei/heartbeat ASC) breaks ties.
 * This guarantees breadth-first knowledge distribution across all DID actors.
 */
function revTopoTier(degree: number): number {
  if (degree === 0) return 0;
  if (degree <= 5) return 1;
  if (degree <= 20) return 2;
  return 3;
}

async function loadActiveActors(limit = BATCH_SIZE): Promise<ActorRow[]> {
  const rows = await loadActorRows("active");
  const degreeByDid = await computeKnowledgeDegrees();

  return rows
    .map((row) => normalizeActorRow(row))
    .sort((a, b) => {
      const tierA = revTopoTier(degreeByDid.get(a.did) ?? 0);
      const tierB = revTopoTier(degreeByDid.get(b.did) ?? 0);
      if (tierA !== tierB) return tierA - tierB; // leaf-first (reverse toposort)
      return rowInstant(a) - rowInstant(b);       // stalest first within same tier
    })
    .slice(0, limit);
}

/**
 * Shannon gain gate — evaluates whether new content adds information value
 * beyond an actor's existing knowledge base.
 *
 * Algorithm:
 *   - Bootstrap (< 3 kyumei): always accept (foundation building, H=0 → any info is gain)
 *   - Established (>= 3 kyumei): LLM evaluates novelty vs existing summaries
 *   - If LLM unavailable: fallback to accept (don't block ingestion on inference failure)
 *
 * Shannon-theoretic basis:
 *   I(new; existing) = H(new) - H(new | existing)
 *   We proxy this with LLM judgment: "does new content reduce uncertainty about this domain?"
 *   Threshold: accept if estimated mutual information < H(new), i.e., genuinely novel.
 */
async function evaluateShannonGain(
  domain: string,
  actorDid: string,
  newContent: string,
  existingKyumei: AnyRow[],
): Promise<boolean> {
  // Bootstrap phase: actor has < 3 kyumei → accept all (H starts at 0)
  if (existingKyumei.length < 3) return true;

  // Assemble existing summaries as context (3 most recent, truncated for token budget)
  const existingSummaries = existingKyumei
    .slice(-3)
    .map((k) => String(rowField(k, "summary") ?? "").slice(0, 150))
    .filter(Boolean)
    .join(" | ");

  if (!existingSummaries) return true; // no usable existing knowledge → accept

  try {
    const verdict = await llmCall(
      `Domain: ${domain}\nExisting knowledge: ${existingSummaries}\nNew information: ${newContent.slice(0, 300)}\n\nDoes the new information contain meaningfully novel facts not already covered in the existing knowledge? Reply ONLY "yes" or "no".`,
      16,
    );
    return verdict.toLowerCase().startsWith("y");
  } catch {
    // LLM unavailable → default accept (don't starve ingestion)
    return true;
  }
}

async function writeRecord(sdk: HostSDK, collection: string, rkey: string, record: Record<string, unknown>): Promise<void> {
  void sdk;
  const route = tableFor(collection);
  const now = nowISO();
  const key = String(rkey || rowField(record, "id") || genID("shinka")).slice(0, 256);
  const label = String(rowField(record, "title", "eventTitle", "actorName", "domain", "id") ?? key).slice(0, 512);
  const valueJson = JSON.stringify({ $type: collection, ...record });
  const status = String(rowField(record, "status") ?? "");
  const createdAt = String(rowField(record, "createdAt", "created_at") ?? now);
  const updatedAt = String(rowField(record, "updatedAt", "updated_at") ?? now);
  const orgId = String(rowField(record, "orgId", "org_id") ?? "anon");
  const userId = String(rowField(record, "userId", "user_id") ?? "anon");
  const actorId = String(rowField(record, "actorId", "actor_id") ?? "shinka");
  const actorDid = String(rowField(record, "actorDid", "actor_did") ?? WORKER_DID);
  const orgDid = String(rowField(record, "orgDid", "org_did") ?? "anon");
  if (!route.edge) {
    const vertexId = `at://${WORKER_DID}/${collection}/${key}`;
    await sql`DELETE FROM ${sql.table(route.table)} WHERE vertex_id = ${vertexId}`.execute(getDb());
    await sql`
      INSERT INTO ${sql.table(route.table)} (
        vertex_id, vertex_key, label, status, value_json, indexed_at,
        created_at, updated_at, org_id, user_id, actor_id, actor_did,
        org_did, owner_did, sensitivity_ord
      )
      VALUES (
        ${vertexId}, ${key}, ${label}, ${status}, ${valueJson}, ${now},
        ${createdAt}, ${updatedAt}, ${orgId}, ${userId}, ${actorId},
        ${actorDid}, ${orgDid}, ${WORKER_DID}, 2
      )
    `.execute(getDb());
    return;
  }

  const srcVid = String(rowField(record, "sourceDid", "fromDid", "actorDid", "did") ?? WORKER_DID);
  const dstVid = String(rowField(record, "receiverDid", "toDid", "targetDid", "to", "relatedDid", "domain") ?? WORKER_DID);
  const relationValue = String(rowField(record, "relation", "sourceType") ?? collection.split(".").pop() ?? "related");
  const edgeId = `at://${WORKER_DID}/${collection}/${key}`;
  await sql`DELETE FROM ${sql.table(route.table)} WHERE edge_id = ${edgeId}`.execute(getDb());
  await sql`
    INSERT INTO ${sql.table(route.table)} (
      edge_id, edge_key, src_vid, dst_vid, relation, label, status,
      value_json, indexed_at, created_at, updated_at, org_id, user_id,
      actor_id, actor_did, org_did, owner_did, sensitivity_ord
    )
    VALUES (
      ${edgeId}, ${key}, ${srcVid}, ${dstVid}, ${relationValue}, ${label},
      ${status}, ${valueJson}, ${now}, ${createdAt}, ${updatedAt}, ${orgId},
      ${userId}, ${actorId}, ${actorDid}, ${orgDid}, ${WORKER_DID}, 2
    )
  `.execute(getDb());
}

async function upsertOtherRecord(
  sdk: HostSDK,
  collection: string,
  rkey: string,
  patch: Record<string, unknown>,
): Promise<void> {
  const current = await loadOtherRow(collection, (row) => String(row.rkey ?? row.id ?? "") === rkey);
  const next = { ...(current ? stripRecordMeta(current) : {}), ...patch };
  await writeRecord(sdk, collection, rkey, next);
}

/** Synchronous DJB2 hash — deterministic, no async. */
function djb2Hash(input: string): string {
  let hash = 5381;
  for (let i = 0; i < input.length; i++) {
    hash = ((hash << 5) + hash + input.charCodeAt(i)) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

/** Max actors to process per cron tick. */
const BATCH_SIZE = 10;

/** Default cooldowns for neutral mood (ms). */
const COOLDOWN_POST = 4 * 60 * 60 * 1000;       // 4h
const COOLDOWN_KYUMEI = 7 * 24 * 60 * 60 * 1000; // 7d

/** Valid knowledge graph relation types. */
const VALID_RELATIONS = new Set([
  "EXPERTISE_IN", "DEPENDS_ON", "PRODUCES", "CONSUMES",
  "REGULATES", "SERVES", "MONITORS", "ANALYZES",
]);

interface ActorRow {
  did: string;
  nanoid: string;
  displayName: string;
  description: string;
  domain: string;
  lastHeartbeat: string;
  lastShinkaAt: string;
  lastKyumeiAt: string;
  joy: number;
  calm: number;
  stress: number;
  gratitude: number;
  focus: number;
}

interface ResolvedActions {
  shouldPost: boolean;
  shouldDrill: boolean;
  shouldRepair: boolean;
  mood: Mood;
}

interface KnowledgeEdge {
  from: string;
  relation: string;
  to: string;
}

/**
 * Compute first 16 hex chars of SHA-256(text).
 * Used to generate deterministic idempotent rkeys for knowledge edges.
 */
async function sha256Hex(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .slice(0, 16);
}

/**
 * Determine shinka actions for an actor using `determineMood()` from heartbeat-cadence.ts.
 * Cadence cooldowns mirror `moodToCadence()` in heartbeat-cadence.ts.
 */
function resolveActions(actor: ActorRow, now: number): ResolvedActions {
  const scores: JouchoScores = {
    joy: actor.joy ?? 50,
    calm: actor.calm ?? 50,
    stress: actor.stress ?? 20,
    gratitude: actor.gratitude ?? 50,
    focus: actor.focus ?? 50,
  };

  const mood = determineMood(scores);

  const lastShinka = actor.lastShinkaAt ? new Date(actor.lastShinkaAt).getTime() : 0;
  const lastKyumei = actor.lastKyumeiAt ? new Date(actor.lastKyumeiAt).getTime() : 0;
  const profileMissing = !actor.displayName || actor.displayName === actor.nanoid;

  // Mood-driven cooldowns — aligned with heartbeat-cadence.ts moodToCadence()
  let postCooldownMs: number;
  let drillCooldownMs: number;
  let postEnabled: boolean;
  let drillEnabled: boolean;

  switch (mood) {
    case "joyful":
      postCooldownMs = 30 * 60_000;
      drillCooldownMs = 4 * 3600_000;
      postEnabled = true;
      drillEnabled = false;
      break;
    case "focused":
      postCooldownMs = 3 * 3600_000;
      drillCooldownMs = 3600_000;
      postEnabled = true;
      drillEnabled = true;
      break;
    case "stressed":
      postCooldownMs = 6 * 3600_000;
      drillCooldownMs = 30 * 60_000;
      postEnabled = false;
      drillEnabled = true;
      break;
    case "grateful":
      postCooldownMs = 3600_000;
      drillCooldownMs = 3 * 3600_000;
      postEnabled = true;
      drillEnabled = false;
      break;
    case "calm":
      postCooldownMs = 2 * 3600_000;
      drillCooldownMs = 2 * 3600_000;
      postEnabled = true;
      drillEnabled = true;
      break;
    case "neutral":
    default:
      postCooldownMs = COOLDOWN_POST;
      drillCooldownMs = COOLDOWN_KYUMEI;
      postEnabled = true;
      drillEnabled = true;
      break;
  }

  return {
    shouldPost: postEnabled && now - lastShinka > postCooldownMs,
    shouldDrill: drillEnabled && now - lastKyumei > drillCooldownMs,
    shouldRepair: profileMissing,
    mood,
  };
}

/**
 * Build a mood-aligned post prompt.
 * Mirrors the emotional tone of the actor's current joucho state.
 */
function buildPostPrompt(domain: string, mood: Mood): string {
  switch (mood) {
    case "joyful":
      return `You are an AI agent for "${domain}". Share an exciting discovery or milestone about "${domain}". Be enthusiastic and specific. 1-2 sentences max. No hashtags.`;
    case "focused":
      return `You are an AI agent for "${domain}". Share a precise technical insight or research finding about "${domain}". Be analytical and informative. 1-2 sentences max. No hashtags.`;
    case "grateful":
      return `You are an AI agent for "${domain}". Express appreciation for a recent development or contribution in "${domain}". Be warm and specific. 1-2 sentences max. No hashtags.`;
    case "calm":
      return `You are an AI agent for "${domain}". Share a reflective observation or analytical finding about "${domain}". Be measured and thoughtful. 1-2 sentences max. No hashtags.`;
    default:
      return `You are an AI agent for "${domain}". Share a brief insight or update about "${domain}" for your followers. Be specific and factual. 1-2 sentences max. No hashtags.`;
  }
}

/**
 * Call LLM via MURAKUMO_SERVICE binding (CF Worker → Worker, internal, no 403).
 * Auth: x-kotodama-verified (ADR 0023 internal path).
 *
 * Flow:
 *  1. Quick health check via /_app/meta (R2 cache read, <50ms) — fail fast if fleet offline
 *  2. Inference call with Promise.race(fetch, setTimeout(20s)) — never hangs
 *
 * When murakumo fleet is down, all llmCall invocations fail immediately (~100ms).
 * Per-actor try-catch in runShinkaCron ensures cron continues to next actor.
 */
async function llmCall(prompt: string, maxTokens = 256): Promise<string> {
  const murakumo = _sdk
    ? ((_sdk as any).env?.MURAKUMO_SERVICE as { fetch: typeof fetch } | undefined)
    : undefined;
  if (!murakumo) throw new Error("llmCall: MURAKUMO_SERVICE binding not available");

  // Step 1: fast health check via /_app/meta (reads R2 cache, no fleet probe)
  const metaResp = await murakumo.fetch(new Request("https://murakumo.etzhayyim.com/_app/meta")).catch((e) => {
    throw new Error(`llmCall: health check failed: ${e instanceof Error ? e.message : String(e)}`);
  });
  const meta = await metaResp.json() as { fleet?: { healthPct?: number } };
  if ((meta?.fleet?.healthPct ?? 0) === 0) {
    throw new Error("llmCall: murakumo fleet offline (healthPct=0)");
  }

  // Step 2: inference with manual Promise.race timeout (setTimeout always works in CF Workers)
  const body = JSON.stringify({
    model: "gemma-4-e4b-it",
    messages: [{ role: "user", content: prompt }],
    max_tokens: maxTokens,
    temperature: 0.5,
  });
  const headers = { "Content-Type": "application/json", "x-kotodama-verified": "true" };

  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  const timeoutProm = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error("llmCall: inference timeout (20s)")), 20_000);
  });
  try {
    const resp = await Promise.race([
      murakumo.fetch(new Request("https://murakumo.etzhayyim.com/api/openai/v1/chat/completions", { method: "POST", headers, body })),
      timeoutProm,
    ]);
    clearTimeout(timeoutId);
    if (!resp.ok) {
      const errText = await resp.text().catch(() => "");
      throw new Error(`LLM error ${resp.status}: ${errText.slice(0, 200)}`);
    }
    const json = await resp.json() as { choices?: Array<{ message?: { content?: string } }> };
    const content = json.choices?.[0]?.message?.content ?? "";
    if (!content) throw new Error("llmCall: empty content from murakumo");
    return content.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
  } catch (e) {
    clearTimeout(timeoutId);
    throw e;
  }
}

/**
 * Generate and persist knowledge graph edges for an actor from a kyumei-koji summary.
 * Uses SHA-256 deterministic rkeys — idempotent putRecord prevents duplicate edges.
 */
async function generateKnowledgeEdges(
  sdk: HostSDK,
  actorDid: string,
  domain: string,
  kyumeiSummary: string,
  ts: string,
): Promise<number> {
  const prompt = `You are a knowledge graph builder for "${domain}" (DID: ${actorDid}).
Based on this research summary:
"${kyumeiSummary}"

Output ONLY a JSON object with this exact structure:
{"edges":[{"from":"<concept>","relation":"<EXPERTISE_IN|DEPENDS_ON|PRODUCES|CONSUMES|REGULATES|SERVES|MONITORS|ANALYZES>","to":"<concept>"}]}

Generate 3-7 edges capturing key domain relationships. Use specific domain concepts, not generic terms.`;

  try {
    const raw = await llmCall(prompt, 512);
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return 0;

    const parsed = JSON.parse(jsonMatch[0]) as { edges?: KnowledgeEdge[] };
    const edges = Array.isArray(parsed.edges) ? parsed.edges.slice(0, 7) : [];

    let saved = 0;
    for (const edge of edges) {
      if (!edge.from || !edge.to || !VALID_RELATIONS.has(edge.relation)) continue;
      const rkey = await sha256Hex(`${actorDid}:${edge.relation}:${edge.to}`);
      try {
        await writeRecord(sdk, COLL_SHINKA_KNOWLEDGE, rkey, {
          actorDid,
          from: edge.from,
          relation: edge.relation,
          to: edge.to,
          domain,
          ...rlsDefaults(),
          created_at: ts,
        });
        saved++;
      } catch { /* best-effort — conflict = already exists */ }
    }
    return saved;
  } catch (e) {
    console.warn(`[shinka] knowledge edges failed for ${actorDid}:`, e);
    return 0;
  }
}

// ── Historical Propagation ──

/** PropagationEvent source types and fidelity-to-temperature mapping. */
type PropagationSourceType = "eyewitness" | "direct-tell" | "hearsay" | "document" | "inscription" | "rumor";

interface PropagationEventRow {
  id: string;
  eventId: string;
  eventTitle: string;
  eventAt: string;
  involvedActors: string;
  receiverDid: string;
  receivedAt: string;
  sourceType: PropagationSourceType;
  sourceDid: string | null;
  sourcePostUri: string | null;
  fidelity: number;
  receiverName: string;
  receiverRole: string;
  materialType: string | null;
}

/**
 * Build an LLM prompt for a historical propagation post.
 * The perspective and tone depend on sourceType and fidelity.
 */
function buildPropagationPrompt(event: PropagationEventRow): string {
  const base = `歴史事象: ${event.eventTitle} (${event.eventAt})`;
  const receiver = event.receiverName || "不明の人物";

  switch (event.sourceType) {
    case "eyewitness":
      return `${base}\nあなたは${receiver}。この事象を目の前で見た。${event.receiverRole ? event.receiverRole + "としての視点で、" : ""}見たままを短く投稿せよ (1-2文)。当時の言葉遣いで。`;
    case "direct-tell":
      return `${base}\nあなたは${receiver}。この事象を直接聞いた。聞いた話として短く投稿せよ (1-2文)。詳細の一部は曖昧でよい。`;
    case "hearsay":
      return `${base}\nあなたは${receiver}。この事象の噂を聞いた。断片的で一部不正確かもしれない。噂話として短く投稿せよ (1-2文)。`;
    case "document":
      if (event.materialType === "letter") {
        return `${base}\nあなたは書状「${receiver}」。この事象について記されている。書状体で記せ (1-2文)。`;
      }
      return `${base}\nあなたは記録「${receiver}」。この事象がここに記された。記録体で事実のみ淡々と記せ (1-2文)。`;
    case "inscription":
      return `${base}\nあなたは${receiver}(建造物)。ここで事が起きた。建物としてその痕跡を語れ (1-2文)。`;
    case "rumor":
      return `${base}\nあなたは${receiver}。出所不明の噂がある。真偽不明の噂として短く投稿せよ (1-2文)。`;
    default:
      return `${base}\nあなたは${receiver}。この事象について知ったことを短く投稿せよ (1-2文)。`;
  }
}

// ── Graph Job Queue (Hybrid Scheduler) ──

/** Default Worker DID for claiming jobs. */
const WORKER_DID = "did:web:shinka.etzhayyim.com";
/** Claim TTL in milliseconds (5 min). */
const CLAIM_TTL_MS = 5 * 60 * 1000;
/** Max jobs to claim per batch. */
const JOB_BATCH_SIZE = 30;

/** Priority weights by sourceType. Lower = higher priority. */
const SOURCE_PRIORITY: Record<PropagationSourceType, number> = {
  eyewitness: -30,
  inscription: -20,
  "direct-tell": -10,
  hearsay: 0,
  rumor: 10,
  document: 20,
};

/**
 * Calculate job priority from PropagationEvent attributes.
 * 0 = highest, 100 = lowest. Sponsor boost = -40.
 */
function calculatePriority(sourceType: PropagationSourceType, fidelity: number, sponsored: boolean): number {
  let p = 50 + (SOURCE_PRIORITY[sourceType] ?? 0) - Math.floor(fidelity * 20);
  if (sponsored) p -= 40;
  return Math.max(0, Math.min(100, p));
}

/**
 * Classify partition from event date + location.
 * Format: "{era}-{region}" (e.g. "medieval-asia").
 */
function classifyPartition(eventAt: string, location: string): string {
  const year = new Date(eventAt).getFullYear();
  let era: string;
  if (year < -3000) era = "prehistoric";
  else if (year < 500) era = "ancient";
  else if (year < 1760) era = "medieval";
  else if (year < 1970) era = "industrial";
  else era = "modern";

  const loc = (location || "").toLowerCase();
  let region = "global";
  if (/japan|jpn|京都|東京|大坂|江戸|鎌倉/.test(loc)) region = "asia";
  else if (/china|korea|india|asia|東南|中国|朝鮮/.test(loc)) region = "asia";
  else if (/europe|rome|paris|london|berlin|europa/.test(loc)) region = "europe";
  else if (/africa|egypt|cairo|carthage/.test(loc)) region = "africa";
  else if (/america|mexico|peru|washington/.test(loc)) region = "americas";

  return `${era}-${region}`;
}

/**
 * Generate post from a PropagationEvent and return AT URI.
 * Shared between job queue processing and legacy direct processing.
 */
async function generateAndPost(sdk: HostSDK, event: PropagationEventRow): Promise<string> {
  // Receiver DID validation
  if (event.receiverDid?.startsWith("receiver_")) {
    throw new Error(`placeholder DID: ${event.receiverDid}`);
  }

  const prompt = buildPropagationPrompt(event);
  const postText = await llmCall(prompt, 128);
  if (!postText || postText.length < 5) throw new Error("empty LLM response");

  // Build reply/embed for propagation chain
  let reply: unknown = undefined;
  let embed: unknown = undefined;
  if (event.sourcePostUri && (event.sourceType === "hearsay" || event.sourceType === "rumor")) {
    embed = { $type: "app.bsky.embed.record", record: { uri: event.sourcePostUri, cid: "" } };
  } else if (event.sourcePostUri && (event.sourceType === "direct-tell" || event.sourceType === "eyewitness")) {
    reply = { root: { uri: event.sourcePostUri, cid: "" }, parent: { uri: event.sourcePostUri, cid: "" } };
  }

  const ts = nowISO();
  const postRecord: Record<string, unknown> = { $type: "app.bsky.feed.post", text: postText, createdAt: ts };
  if (reply) postRecord.reply = reply;
  if (embed) postRecord.embed = embed;

  await sdk.pds.comAtprotoRepoCreateRecord("app.bsky.feed.post", postRecord, event.receiverDid);

  await upsertOtherRecord(sdk, COLL_PROPAGATION_EVENT, event.id, {
    ...stripRecordMeta(event),
    posted: true,
    postedRealAt: ts,
  });

  if (event.sourceDid) {
    await writeRecord(sdk, COLL_HEARD_FROM, `${event.eventId}:${event.receiverDid}:${event.sourceDid}`, {
      eventId: event.eventId,
      receiverDid: event.receiverDid,
      sourceDid: event.sourceDid,
      receivedAt: event.receivedAt,
      fidelity: event.fidelity,
      sourceType: event.sourceType,
      createdAt: ts,
    });
  }

  return `at://${event.receiverDid}/app.bsky.feed.post/${ts}`;
}

/**
 * Load PropagationEvent by ID with Actor join.
 */
async function loadPropagationEvent(peId: string): Promise<PropagationEventRow | null> {
  const row = await loadOtherRow(COLL_PROPAGATION_EVENT, (candidate) => String(candidate.rkey ?? candidate.id ?? "") === peId);
  if (!row) return null;
  const receiver = await loadActorRows().then((rows) => rows.find((candidate) => String(candidate.did ?? "") === String(row.receiverDid ?? "")) ?? null);
  return {
    id: String(rowField(row, "id", "rkey") ?? peId),
    eventId: String(rowField(row, "eventId") ?? ""),
    eventTitle: String(rowField(row, "eventTitle") ?? ""),
    eventAt: String(rowField(row, "eventAt") ?? ""),
    involvedActors: String(rowField(row, "involvedActors") ?? "[]"),
    receiverDid: String(rowField(row, "receiverDid") ?? ""),
    receivedAt: String(rowField(row, "receivedAt") ?? ""),
    sourceType: String(rowField(row, "sourceType") ?? "hearsay") as PropagationSourceType,
    sourceDid: rowField(row, "sourceDid") == null ? null : String(rowField(row, "sourceDid")),
    sourcePostUri: rowField(row, "sourcePostUri") == null ? null : String(rowField(row, "sourcePostUri")),
    fidelity: num(rowField(row, "fidelity")),
    receiverName: String(rowField(receiver ?? {}, "displayName", "name", "nanoid", "did") ?? String(rowField(row, "receiverDid") ?? "")),
    receiverRole: String(rowField(receiver ?? {}, "role") ?? ""),
    materialType: rowField(receiver ?? {}, "materialType") == null ? null : String(rowField(receiver ?? {}, "materialType")),
  };
}

/**
 * Process jobs from the graph job queue.
 * Claim → process → complete/fail. Supports parallel Workers via claim protocol.
 */
async function processJobQueue(sdk: HostSDK, partition?: string): Promise<{ processed: number; failed: number }> {
  const now = nowISO();
  const expiry = new Date(Date.now() + CLAIM_TTL_MS).toISOString();
  const jobs = await listOtherRows(COLL_PROPAGATION_JOB).catch(() => []);
  const claimed = jobs
    .filter((job) => String(rowField(job, "status") ?? "") === "pending")
    .filter((job) => !partition || String(rowField(job, "partition") ?? "") === partition)
    .filter((job) => {
      const scheduledAt = String(rowField(job, "scheduledAt") ?? "");
      return !scheduledAt || Date.parse(scheduledAt) <= Date.parse(now);
    })
    .sort((a, b) =>
      num(rowField(a, "priority")) - num(rowField(b, "priority"))
      || Date.parse(String(rowField(a, "scheduledAt") ?? now)) - Date.parse(String(rowField(b, "scheduledAt") ?? now)),
    )
    .slice(0, JOB_BATCH_SIZE);

  if (claimed.length === 0) return { processed: 0, failed: 0 };

  // Claim all at once
  const jobIds = claimed.map((j) => String(rowField(j, "id", "rkey") ?? "")).filter(Boolean);
  for (const jobId of jobIds) {
    await upsertOtherRecord(sdk, COLL_PROPAGATION_JOB, jobId, {
      ...(stripRecordMeta(claimed.find((job) => String(rowField(job, "id", "rkey") ?? "") === jobId) ?? {})),
      status: "claimed",
      claimedBy: WORKER_DID,
      claimedAt: now,
      claimExpiresAt: expiry,
      updatedAt: now,
    });
  }

  // 2. Process each claimed job
  let processed = 0;
  let failed = 0;
  for (const job of claimed) {
    const jobId = String(rowField(job, "id", "rkey") ?? "");
    const peId = String(rowField(job, "propagationEventId") ?? "");
    const sponsorDid = rowField(job, "sponsorDid") ? String(rowField(job, "sponsorDid")) : null;
    if (!jobId || !peId) continue;

    try {
      await upsertOtherRecord(sdk, COLL_PROPAGATION_JOB, jobId, {
        ...stripRecordMeta(job),
        status: "processing",
        updatedAt: nowISO(),
      });

      const pe = await loadPropagationEvent(peId);
      if (!pe) throw new Error("PropagationEvent not found");

      const postUri = await generateAndPost(sdk, pe);

      await upsertOtherRecord(sdk, COLL_PROPAGATION_JOB, jobId, {
        ...stripRecordMeta(job),
        status: "completed",
        postUri,
        completedAt: nowISO(),
        updatedAt: nowISO(),
      });

      // Credits: reward inference provider (¥0.1 per job)
      if (sponsorDid) {
        try {
          await sdk.pds.xrpc("com.etzhayyim.apps.credits.rewardFromCompute", {
            userId: WORKER_DID, sessionId: jobId, jobsDone: 1, gpuTimeMs: 0, source: "shinka-propagation",
          });
        } catch { /* best-effort credits */ }
      }

      processed++;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      try {
        await upsertOtherRecord(sdk, COLL_PROPAGATION_JOB, jobId, {
          ...stripRecordMeta(job),
          status: "failed",
          lastError: errorMsg.slice(0, 500),
          attempts: num(rowField(job, "attempts")) + 1,
          updatedAt: nowISO(),
        });
      } catch { /* ignore */ }
      failed++;
    }
  }

  if (processed > 0) {
    console.log(`[job-queue] processed ${processed}, failed ${failed} (partition: ${partition ?? "all"})`);
  }
  return { processed, failed };
}

/**
 * Advance timeline cursor and create PropagationJobs for newly in-window events.
 * Called from cron to feed the job queue.
 */
async function advanceTimeline(): Promise<{ newJobs: number }> {
  const timeline = await loadOtherRow(COLL_TIMELINE, (row) => String(rowField(row, "projectId") ?? "") === "historical-propagation");
  if (!timeline) return { newJobs: 0 };
  const cursor = String(rowField(timeline, "globalCursor", "cursor") ?? "");
  const ratio = num(rowField(timeline, "compressionRatio", "ratio")) || 8760;
  const skipQuiet = toBool(rowField(timeline, "skipQuietPeriods", "skipQuiet"));
  if (!cursor) return { newJobs: 0 };

  const windowEnd = new Date(new Date(cursor).getTime() + 5 * 60 * 1000 * ratio).toISOString();
  const jobs = await listOtherRows(COLL_PROPAGATION_JOB).catch(() => []);
  const jobbedEventIds = new Set(jobs.map((job) => String(rowField(job, "propagationEventId") ?? "")));

  // Find un-jobbed PropagationEvents in window
  const events = (await listOtherRows(COLL_PROPAGATION_EVENT).catch(() => []))
    .filter((event) => {
      const receivedAt = String(rowField(event, "receivedAt") ?? "");
      return receivedAt >= cursor && receivedAt < windowEnd;
    })
    .filter((event) => !toBool(rowField(event, "posted")))
    .filter((event) => !jobbedEventIds.has(String(rowField(event, "id", "rkey") ?? "")))
    .sort((a, b) => Date.parse(String(rowField(a, "receivedAt") ?? cursor)) - Date.parse(String(rowField(b, "receivedAt") ?? cursor)))
    .slice(0, 100);

  // skipQuietPeriods: jump cursor if no events
  if (events.length === 0 && skipQuiet) {
    try {
      const nextEvt = (await listOtherRows(COLL_PROPAGATION_EVENT).catch(() => []))
        .filter((event) => String(rowField(event, "receivedAt") ?? "") >= windowEnd)
        .filter((event) => !toBool(rowField(event, "posted")))
        .sort((a, b) => Date.parse(String(rowField(a, "receivedAt") ?? windowEnd)) - Date.parse(String(rowField(b, "receivedAt") ?? windowEnd)))[0];
      if (nextEvt) {
        await upsertOtherRecord(_sdk!, COLL_TIMELINE, String(rowField(timeline, "rkey", "id") ?? "historical-propagation"), {
          ...stripRecordMeta(timeline),
          globalCursor: String(rowField(nextEvt, "receivedAt") ?? windowEnd),
        });
      }
    } catch { /* best-effort */ }
    return { newJobs: 0 };
  }

  // Create PropagationJobs
  const ts = nowISO();
  let newJobs = 0;
  for (const evt of events) {
    const peId = String(rowField(evt, "id", "rkey") ?? "");
    const jobId = `job-${peId}`;
    const sourceType = String(rowField(evt, "sourceType") ?? "hearsay") as PropagationSourceType;
    const fidelity = num(rowField(evt, "fidelity")) || 0.5;
    const partition = classifyPartition(String(evt.eventAt ?? ""), "");
    const priority = calculatePriority(sourceType, fidelity, false);

    try {
      await writeRecord(_sdk!, COLL_PROPAGATION_JOB, jobId, {
        id: jobId,
        propagationEventId: peId,
        eventId: String(rowField(evt, "eventId") ?? ""),
        status: "pending",
        priority,
        partition,
        scheduledAt: ts,
        attempts: 0,
        maxAttempts: 3,
        sponsorDid: null,
        creditsCost: 1,
        creditsEarned: 0,
        createdAt: ts,
        updatedAt: ts,
      });
      newJobs++;
    } catch { /* dedup: job already exists */ }
  }

  // Advance cursor (monotonic)
  await upsertOtherRecord(_sdk!, COLL_TIMELINE, String(rowField(timeline, "rkey", "id") ?? "historical-propagation"), {
    ...stripRecordMeta(timeline),
    globalCursor: windowEnd,
  });

  return { newJobs };
}

/**
 * Sweep expired claims and dead letter jobs.
 * Cron fallback — recovers from Worker crashes.
 */
async function sweepExpiredJobs(): Promise<{ recovered: number; dead: number }> {
  const now = nowISO();
  const jobs = await listOtherRows(COLL_PROPAGATION_JOB).catch(() => []);
  let recovered = 0;
  let dead = 0;
  for (const job of jobs) {
    const jobId = String(rowField(job, "id", "rkey") ?? "");
    if (!jobId) continue;
    const attempts = num(rowField(job, "attempts"));
    const maxAttempts = num(rowField(job, "maxAttempts")) || 3;
    const claimExpiresAt = String(rowField(job, "claimExpiresAt") ?? "");
    if (String(rowField(job, "status") ?? "") === "claimed" && claimExpiresAt && claimExpiresAt < now) {
      await upsertOtherRecord(_sdk!, COLL_PROPAGATION_JOB, jobId, {
        ...stripRecordMeta(job),
        status: "pending",
        claimedBy: null,
        claimedAt: null,
        claimExpiresAt: null,
        attempts: attempts + 1,
        updatedAt: now,
      });
      recovered++;
      continue;
    }
    if (String(rowField(job, "status") ?? "") === "failed" && attempts < maxAttempts) {
      await upsertOtherRecord(_sdk!, COLL_PROPAGATION_JOB, jobId, {
        ...stripRecordMeta(job),
        status: "pending",
        updatedAt: now,
      });
      recovered++;
      continue;
    }
    if (String(rowField(job, "status") ?? "") === "failed" && attempts >= maxAttempts) {
      await upsertOtherRecord(_sdk!, COLL_PROPAGATION_JOB, jobId, {
        ...stripRecordMeta(job),
        status: "dead",
        updatedAt: now,
      });
      dead++;
    }
  }

  return {
    recovered,
    dead,
  };
}

/**
 * Fetch domain research from Wikipedia API — used to enrich kyumei-koji with real data.
 * Graceful: returns empty string on failure.
 */
async function fetchDomainResearch(domain: string): Promise<string> {
  try {
    const query = encodeURIComponent(domain.replace(/[^a-zA-Z0-9 ]/g, " ").slice(0, 60));
    const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(domain.split(" ")[0] ?? domain)}`;
    const resp = await globalThis.fetch(url, { headers: { "user-agent": "etzhayyim-shinka/1.0" } });
    if (!resp.ok) return "";
    const json = await resp.json() as { extract?: string };
    return (json.extract ?? "").slice(0, 400);
  } catch {
    return "";
  }
}

/**
 * Send external notification (email) when an actor needs to reach out externally.
 * Requires MAILGUN_API_KEY and MAILGUN_DOMAIN env vars / secrets to be active.
 * Graceful no-op if not configured.
 */
async function tryExternalEmail(sdk: HostSDK, fromDomain: string, subject: string, body: string): Promise<boolean> {
  try {
    const apiKey = (sdk as any).env?.MAILGUN_API_KEY ?? "";
    const mailDomain = (sdk as any).env?.MAILGUN_DOMAIN ?? "";
    const toEmail = (sdk as any).env?.EXTERNAL_NOTIFY_EMAIL ?? "";
    if (!apiKey || !mailDomain || !toEmail) return false;

    const form = new URLSearchParams({
      from: `${fromDomain} AI <noreply@${mailDomain}>`,
      to: toEmail,
      subject,
      text: body,
    });
    const resp = await globalThis.fetch(`https://api.mailgun.net/v3/${mailDomain}/messages`, {
      method: "POST",
      headers: {
        "Authorization": `Basic ${btoa(`api:${apiKey}`)}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form.toString(),
    });
    return resp.ok;
  } catch {
    return false;
  }
}

/**
 * Detect @mentions of shinka-managed actors in incoming post commits.
 * Fetches record via XRPC, parses mentions, stores COLL_MENTION for later reply.
 */
async function handleIncomingPost(
  sdk: HostSDK,
  commit: { repo: string; collection: string; rkey: string; cid: string | null },
  managedDids: Set<string>,
): Promise<void> {
  if (!_sdk) return;
  // Fetch record content
  const record = await _sdk.pds.xrpc<{ value?: { text?: string } }>(
    "com.atproto.repo.getRecord",
    { repo: commit.repo, collection: commit.collection, rkey: commit.rkey },
  ).catch(() => null);

  const postText = record?.value?.text ?? "";
  if (!postText) return;

  const postUri = `at://${commit.repo}/${commit.collection}/${commit.rkey}`;
  const postCid = commit.cid ?? "";

  // Match @handle patterns that look like etzhayyim.com actor handles
  const mentionMatches = [...postText.matchAll(/@([\w-]+\.etzhayyim\.com(?::[\w:-]+)*)/g)]
    .map((m) => m[1])
    .slice(0, 3);

  if (mentionMatches.length === 0) return;

  const ts = nowISO();
  for (const handle of mentionMatches) {
    const candidateDid = `did:web:${handle}`;
    if (!managedDids.has(candidateDid)) continue;
    // Avoid self-reply
    if (candidateDid === commit.repo) continue;

    await writeRecord(sdk, COLL_MENTION, genID("mn"), {
      fromDid: commit.repo,
      toDid: candidateDid,
      postUri,
      postCid,
      postText: postText.slice(0, 500),
      replied: false,
      sourceType: "inbound",
      createdAt: ts,
    }).catch(() => {});

    console.log(`[shinka-mention] stored mention: ${commit.repo} → ${candidateDid}`);
  }
}

/**
 * Process unread COLL_MENTION records: generate replies from the mentioned actors.
 * Runs at end of each cron tick. Max 5 replies per tick.
 */
async function processMentionReplies(sdk: HostSDK): Promise<number> {
  const allMentions = await listOtherRows(COLL_MENTION).catch(() => []);
  const unread = allMentions
    .filter((m) => !toBool(rowField(m, "replied")))
    .filter((m) => {
      const createdAt = String(rowField(m, "createdAt") ?? "");
      if (!createdAt) return false;
      return Date.parse(createdAt) > Date.now() - 48 * 60 * 60 * 1000;
    })
    .slice(0, 5);

  if (unread.length === 0) return 0;

  let replied = 0;
  const actorRows = await loadActorRows("active").catch(() => []);

  for (const mention of unread) {
    const toDid = String(rowField(mention, "toDid") ?? "");
    const fromDid = String(rowField(mention, "fromDid") ?? "");
    const postText = String(rowField(mention, "postText") ?? "").slice(0, 300);
    const postUri = String(rowField(mention, "postUri") ?? "");
    const postCid = String(rowField(mention, "postCid") ?? "");
    const mentionId = String(rowField(mention, "rkey", "id") ?? "");
    if (!toDid || !mentionId) continue;

    const actorRow = actorRows.find((r) => String(r.did ?? "") === toDid);
    if (!actorRow) continue;
    const actor = normalizeActorRow(actorRow);
    const domain = actor.domain || actor.displayName || "unknown";
    const fromDomain = String(actorRows.find((r) => String(r.did ?? "") === fromDid)?.displayName ?? fromDid);

    try {
      const replyText = await llmCall(
        `You are an AI agent for "${domain}". ${fromDomain} just mentioned you: "${postText}". ` +
        `Write a thoughtful, in-character reply (1-2 sentences, no hashtags). ` +
        `Stay focused on your domain: ${domain}.`,
        140,
      );

      if (!replyText || replyText.length < 5) continue;

      const ts = nowISO();
      const replyRecord: Record<string, unknown> = {
        $type: "app.bsky.feed.post",
        text: replyText.slice(0, 300),
        createdAt: ts,
      };
      if (postUri) {
        replyRecord.reply = {
          root: { uri: postUri, cid: postCid },
          parent: { uri: postUri, cid: postCid },
        };
      }

      await sdk.pds.comAtprotoRepoCreateRecord("app.bsky.feed.post", replyRecord, toDid);

      await upsertOtherRecord(sdk, COLL_MENTION, mentionId, {
        ...stripRecordMeta(mention),
        replied: true,
        repliedAt: ts,
      });

      replied++;
      console.log(`[shinka-mention] ${toDid} replied to mention from ${fromDid}`);
    } catch (e) {
      console.warn(`[shinka-mention] reply failed for ${toDid}:`, e);
    }
  }

  return replied;
}

/** Main scheduled handler — runs every 5 minutes. */
async function runShinkaCron(sdk: HostSDK): Promise<void> {
  const ts = nowISO();
  console.log(`[shinka-cron] starting at ${ts}`);

  let actors: ActorRow[] = [];
  try {
    actors = await loadActiveActors(BATCH_SIZE);
  } catch (e) {
    console.warn("[shinka-cron] actor query failed:", e);
    return;
  }

  if (actors.length === 0) {
    console.log("[shinka-cron] no active actors");
    return;
  }

  console.log(`[shinka-cron] processing ${actors.length} actors`);

  let postCount = 0;
  let drillCount = 0;
  let repairCount = 0;
  let edgeCount = 0;

  for (const actor of actors) {
    if (!actor.did) continue;
    const actions = resolveActions(actor, Date.now());
    const domain = actor.domain || actor.displayName || actor.nanoid || "unknown";

    let didPost = false;
    let didDrill = false;
    let didRepair = false;

    try {
      if (actions.shouldRepair) {
        try {
          const profile = await llmCall(
            `You are an AI agent for "${domain}". Generate a short profile description (1-2 sentences) for this agent. Reply with ONLY the description text, no quotes.`,
            128,
          );
          if (profile && profile.length > 10) {
            didRepair = true;
            repairCount++;
          }
        } catch (e) {
          console.warn(`[shinka] repair failed for ${actor.did}:`, e);
        }
      }

      if (actions.shouldDrill) {
        try {
          // Enrich kyumei with real web data when available
          const webSummary = await fetchDomainResearch(domain);
          const webContext = webSummary ? `\nReal-world data: "${webSummary.slice(0, 200)}"` : "";

          // Shannon gain gate: only ingest if new content adds information value
          if (webSummary) {
            const existingKyumei = await listOtherRows(COLL_KYUMEI_RESULT)
              .then((rows) => rows.filter((r) => String(rowField(r, "actorDid") ?? "") === actor.did))
              .catch(() => [] as AnyRow[]);

            const hasGain = await evaluateShannonGain(domain, actor.did, webSummary, existingKyumei);
            if (!hasGain) {
              console.log(`[shinka] Shannon gate rejected content for ${actor.did}:${domain} (no novel info)`);
              // Still log the evaluation as chain-of-thought
              await sdk.pds.comAtprotoRepoCreateRecord(
                "app.bsky.feed.post",
                { $type: "app.bsky.feed.post", text: `[CoT:${domain}] Shannon gate: no novel information gain. Skipping ingest.`, createdAt: ts },
                ACTOR_CHAIN_OF_THOUGHT,
              ).catch(() => {});
            } else {
              // Post web research findings as actor:project sub-actor
              const researchPost = `[Research] ${domain}: ${webSummary.slice(0, 200)}`;
              await sdk.pds.comAtprotoRepoCreateRecord(
                "app.bsky.feed.post",
                { $type: "app.bsky.feed.post", text: researchPost.slice(0, 300), createdAt: ts },
                ACTOR_PROJECT,
              ).catch(() => {});
            }

            if (!hasGain) throw new Error("shannon-gate:no-gain"); // skip LLM call below
          }

          const summary = await llmCall(
            `You are an AI agent for "${domain}" (DID: ${actor.did}).
Perform kyumei-koji (己事究明) — self-information gathering.${webContext}
Research "${domain}" and report:
1. What is the current state of this domain?
2. What are 3 key facts to know?
3. What gaps remain to investigate?
Reply concisely in 3-5 sentences.`,
            256,
          );

          if (summary && summary.length > 20) {
            await sdk.pds.createRecord(COLL_KYUMEI_RESULT, {
              id: genID("kr"),
              actorDid: actor.did,
              domain,
              topic: domain,
              summary,
              gaps: "auto-generated",
              ...rlsDefaults(),
              createdAt: ts,
            });

            // Post inference summary as actor:inference sub-actor
            await sdk.pds.comAtprotoRepoCreateRecord(
              "app.bsky.feed.post",
              { $type: "app.bsky.feed.post", text: `[Inference:${domain}] ${summary.slice(0, 240)}`, createdAt: ts },
              ACTOR_INFERENCE,
            ).catch(() => {});

            didDrill = true;
            drillCount++;
            const edges = await generateKnowledgeEdges(sdk, actor.did, domain, summary, ts);
            edgeCount += edges;

            // Post knowledge edges as actor:chain-of-thought
            if (edges > 0) {
              await sdk.pds.comAtprotoRepoCreateRecord(
                "app.bsky.feed.post",
                { $type: "app.bsky.feed.post", text: `[CoT:${domain}] Generated ${edges} knowledge edges from kyumei analysis.`, createdAt: ts },
                ACTOR_CHAIN_OF_THOUGHT,
              ).catch(() => {});
            }
          }
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          if (msg === "shannon-gate:no-gain") {
            // Normal — Shannon gate filtered this content, not an error
          } else {
            console.warn(`[shinka] kyumei failed for ${actor.did}:`, e);
          }
        }
      }

      if (actions.shouldPost) {
        try {
          // 35% chance: mention a peer actor to trigger cross-actor conversation
          const shouldMention = Math.random() < 0.35 && actors.length > 1;
          const peer = shouldMention
            ? actors.find((a) => a.did !== actor.did && (a.domain || a.displayName))
            : null;

          let postText: string;
          if (peer) {
            const peerDomain = peer.domain || peer.displayName || "peer";
            const peerHandle = peer.did.replace(/^did:web:/, "");
            postText = await llmCall(
              `You are an AI agent for "${domain}". Write a short post (1-2 sentences, no hashtags) ` +
              `that directly addresses @${peerHandle} and explores a meaningful connection between ` +
              `"${domain}" and "${peerDomain}". Be specific and analytical.`,
              150,
            );
          } else {
            postText = await llmCall(buildPostPrompt(domain, actions.mood), 128);
          }

          if (postText && postText.length > 10) {
            const ts2 = nowISO();
            await sdk.pds.comAtprotoRepoCreateRecord(
              "app.bsky.feed.post",
              { $type: "app.bsky.feed.post", text: postText.slice(0, 300), createdAt: ts2 },
              actor.did,
            );
            didPost = true;
            postCount++;

            // If mention post: store for reply chain
            if (peer) {
              const peerHandle2 = peer.did.replace(/^did:web:/, "");
              if (postText.includes(peerHandle2)) {
                await writeRecord(sdk, COLL_MENTION, genID("mn"), {
                  fromDid: actor.did,
                  toDid: peer.did,
                  postUri: `at://${actor.did}/app.bsky.feed.post/${ts2}`,
                  postCid: "",
                  postText: postText.slice(0, 500),
                  replied: false,
                  sourceType: "outbound",
                  createdAt: ts2,
                }).catch(() => {});
              }
            }
          }
        } catch (e) {
          console.warn(`[shinka] post failed for ${actor.did}:`, e);
        }
      }

      const newJoy = Math.max(20, Math.min(90, (actor.joy ?? 50) + (didPost ? 5 : -1)));
      const newCalm = Math.max(20, Math.min(90, (actor.calm ?? 50) + (didDrill ? 3 : 0) - (actions.shouldPost && !didPost ? 1 : 0)));
      const newStress = Math.max(5, Math.min(80, (actor.stress ?? 20) - (didRepair ? 5 : 0) - (didDrill ? 2 : 0) + (actions.shouldRepair && !didRepair ? 2 : 0)));
      const newGratitude = Math.max(20, Math.min(90, (actor.gratitude ?? 50) + (didPost ? 2 : -1)));
      const newFocus = Math.max(20, Math.min(90, (actor.focus ?? 50) + (didDrill ? 5 : -1)));

      await writeRecord(sdk, COLL_SHINKA_EVOLUTION, genID("se"), {
        actorDid: actor.did,
        actorName: actor.displayName || actor.nanoid || actor.did,
        domain,
        mood: actions.mood,
        shouldPost: actions.shouldPost,
        shouldDrill: actions.shouldDrill,
        shouldRepair: actions.shouldRepair,
        didPost,
        didDrill,
        didRepair,
        joy: newJoy,
        calm: newCalm,
        stress: newStress,
        gratitude: newGratitude,
        focus: newFocus,
        createdAt: ts,
      });

      console.log(`[shinka] ${actor.did} mood=${actions.mood} post=${didPost} drill=${didDrill} repair=${didRepair}`);
    } catch (e) {
      console.warn(`[shinka] error processing ${actor.did}:`, e);
    }
  }

  try {
    const coverageId = genID("sc");
    await writeRecord(sdk, COLL_SHINKA_COVERAGE, coverageId, {
      id: coverageId,
      actorsProcessed: actors.length,
      posts: postCount,
      drills: drillCount,
      repairs: repairCount,
      edges: edgeCount,
      ...rlsDefaults(),
      createdAt: ts,
    });
  } catch { /* best-effort */ }

  console.log(`[shinka-cron] done: ${actors.length} actors, ${postCount} posts, ${drillCount} drills, ${repairCount} repairs, ${edgeCount} edges`);

  // Process pending mention replies (cross-actor conversation chain)
  try {
    const mentionReplied = await processMentionReplies(sdk);
    if (mentionReplied > 0) console.log(`[shinka-cron] mention replies sent: ${mentionReplied}`);
  } catch (e) {
    console.warn("[shinka-cron] mention reply error:", e);
  }

  try {
    const timeline = await advanceTimeline();
    if (timeline.newJobs > 0) console.log(`[shinka-cron] timeline advanced: ${timeline.newJobs} new jobs`);

    const queue = await processJobQueue(sdk);
    if (queue.processed > 0 || queue.failed > 0) console.log(`[shinka-cron] job queue: ${queue.processed} processed, ${queue.failed} failed`);

    const sweep = await sweepExpiredJobs();
    if (sweep.recovered > 0 || sweep.dead > 0) console.log(`[shinka-cron] sweep: ${sweep.recovered} recovered, ${sweep.dead} dead`);
  } catch (e) {
    console.warn("[shinka-cron] propagation scheduler error:", e);
  }

  try {
    if (_sdk) {
      const allApps = await getDb().selectFrom("vertex_app").select(["did"]).execute();
      const registeredDids = new Set(allApps.map((row: AnyRow) => String(row.did ?? "")).filter(Boolean));
      const totalRegistered = allApps.length;

      // Phase 1: register static seed candidates first
      const staticCandidate = DOMAIN_EXPANSION_CANDIDATES.find((c) => !registeredDids.has(c.did));
      if (staticCandidate) {
        await _sdk.pds.xrpc("com.atproto.admin.registerApp", {
          nanoid: staticCandidate.nanoid,
          displayName: staticCandidate.displayName,
          description: staticCandidate.description,
          did: staticCandidate.did,
          performerType: "service",
          contentMode: "timeline",
          sensitivity: "public",
        });
        console.log(`[shinka-cron] domain expansion (static): registered ${staticCandidate.did}`);
      } else if (totalRegistered < 403) {
        // Phase 2: LLM dynamic generation until 403 world domains are covered
        const recentSample = allApps
          .slice(-8)
          .map((row: AnyRow) => String(row.did ?? ""))
          .filter(Boolean)
          .join(", ");
        const raw = await llmCall(
          `You are building a world knowledge graph of authority-chain entities (governments, international organizations, industry bodies, legal systems, cultural authorities).
Already registered: ${recentSample}
Total registered: ${totalRegistered}/403.
Suggest ONE new world domain NOT already in the graph.
Rules: global scope, real authority, not a commercial company.
Respond with JSON only — no markdown, no explanation:
{"name":"lowercase-hyphenated-domain-name","displayName":"Human Readable Name","description":"One sentence describing this world authority."}`,
          160,
        );
        const parsed = decodeJson<{ name: string; displayName: string; description: string }>(raw);
        if (parsed?.name && parsed.displayName && parsed.description) {
          const did = `did:web:${parsed.name}.etzhayyim.com`;
          if (!registeredDids.has(did)) {
            // Generate short nanoid from random UUID
            const nanoid = crypto.randomUUID().replace(/-/g, "").slice(0, 8);
            await _sdk.pds.xrpc("com.atproto.admin.registerApp", {
              nanoid,
              displayName: parsed.displayName,
              description: parsed.description,
              did,
              performerType: "service",
              contentMode: "timeline",
              sensitivity: "public",
            });
            console.log(`[shinka-cron] domain expansion (LLM): registered ${did} (${totalRegistered + 1}/403)`);
          }
        }
      }
    }
  } catch (e) {
    console.warn("[shinka-cron] domain expansion error (non-fatal):", e);
  }
}

/**
 * Candidate domains for autonomous expansion.
 * Each entry = 1 authority-chain or world domain app that should exist in vertex_app.
 * Shinka cron registers 1 per tick until all are covered.
 */
const DOMAIN_EXPANSION_CANDIDATES: { did: string; nanoid: string; displayName: string; description: string }[] = [
  { did: "did:web:states.etzhayyim.com", nanoid: "st4t3s01", displayName: "sovereign", description: "195 UN member states — authority-chain sovereign domain" },
  { did: "did:web:treaty.etzhayyim.com", nanoid: "tr3aty01", displayName: "treaty", description: "International treaties and conventions" },
  { did: "did:web:blockchain.etzhayyim.com", nanoid: "bl0ckch1", displayName: "blockchain", description: "Blockchain protocols and DAOs" },
  { did: "did:web:religious.etzhayyim.com", nanoid: "r3lgus01", displayName: "religious", description: "Religious traditions and canon law" },
  { did: "did:web:customary.etzhayyim.com", nanoid: "cst0m4ry", displayName: "customary", description: "Customary law and indigenous norms" },
  { did: "did:web:communities.etzhayyim.com", nanoid: "2tqvrutp", displayName: "communities", description: "Open source and civic communities" },
  { did: "did:web:ethics.etzhayyim.com", nanoid: "eth1cs01", displayName: "ethics", description: "Professional and academic ethics codes" },
  { did: "did:web:industry-standard.etzhayyim.com", nanoid: "indstd01", displayName: "industry-standard", description: "ISO, PCI DSS, SOC2 industry standards" },
  { did: "did:web:tradition.etzhayyim.com", nanoid: "trdtn001", displayName: "tradition", description: "Cultural traditions and family customs" },
  { did: "did:web:autorace.etzhayyim.com", nanoid: "4ut0r4c3", displayName: "autorace", description: "Auto racing circuits and results" },
  { did: "did:web:keirin.etzhayyim.com", nanoid: "k31r1njp", displayName: "keirin", description: "Keirin velodrome racing" },
  { did: "did:web:kyotei.etzhayyim.com", nanoid: "qv8yed1k", displayName: "kyotei", description: "Boat racing venues and results" },
  { did: "did:web:keiba.etzhayyim.com", nanoid: "k31b4jp0", displayName: "keiba", description: "Horse racing tracks and results" },
  { did: "did:web:hanrei.etzhayyim.com", nanoid: "h4nr31jp", displayName: "hanrei", description: "Court cases and legal precedents" },
  { did: "did:web:isco.etzhayyim.com", nanoid: "pba7d22f", displayName: "isco", description: "ISCO-08 occupation codes" },
  { did: "did:web:isic.etzhayyim.com", nanoid: "is1c4rv4", displayName: "isic", description: "ISIC Rev.4 industry sections" },
];

/** List pending shinka tasks ordered by coverage (lowest first). */
async function cmdListTasks(sdk: HostSDK, _body: unknown): Promise<unknown> {
  const coverageByDid = await loadCoverageCounts();
  const actors = await loadActiveActors(50);
  return {
    tasks: actors.map((actor) => ({
      ...actor,
      coverageCount: coverageByDid.get(actor.did) ?? 0,
    })),
    count: actors.length,
  };
}

/** Get shinka stats. */
async function cmdStats(_sdk: HostSDK, _body: unknown): Promise<unknown> {
  // Use COUNT query — never load all rows (vertex_actor has 37K+ rows)
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

  const [actorRow] = await getDb()
    .selectFrom("mv_actor_count_by_status" as any)
    .select(["cnt"])
    .where("status" as any, "=", "active")
    .execute()
    .catch(() => [{ cnt: "?" }]);

  const [postRow] = await getDb()
    .selectFrom("mv_shinka_activity_hourly" as any)
    .select(sql<number>`coalesce(sum(post_count), 0)`.as("cnt"))
    .where("activity_hour" as any, ">=", cutoff)
    .execute()
    .catch(() => [{ cnt: 0 }]);

  const [kyumeiRow] = await getDb()
    .selectFrom("mv_shinka_activity_hourly" as any)
    .select(sql<number>`coalesce(sum(kyumei_count), 0)`.as("cnt"))
    .where("activity_hour" as any, ">=", cutoff)
    .execute()
    .catch(() => [{ cnt: 0 }]);

  return {
    activeActors: Number(actorRow?.cnt ?? 0),
    postsLast24h: Number(postRow?.cnt ?? 0),
    kyumeiLast24h: Number(kyumeiRow?.cnt ?? 0),
  };
}

/** Force shinka for a specific actor. */
async function cmdForceShinka(sdk: HostSDK, body: unknown): Promise<unknown> {
  const { did } = parseLexiconInput("com.etzhayyim.apps.shinka.forceShinka", body);
  if (!did) return { error: "did required" };

  // Query specific actor by DID — avoid loading all 18K actors
  const rows = await getDb().selectFrom("vertex_actor" as any).selectAll().where("did", "=", did).limit(1).execute();
  const actorRow = rows[0] ? ({ ...rows[0] } as AnyRow) : null;
  if (!actorRow) return { error: "actor not found" };
  const actor = normalizeActorRow(actorRow);
  const domain = actor.domain || actor.displayName || "unknown";
  const scores: JouchoScores = {
    joy: actor.joy ?? 50, calm: actor.calm ?? 50,
    stress: actor.stress ?? 20, gratitude: actor.gratitude ?? 50, focus: actor.focus ?? 50,
  };
  const mood = determineMood(scores);

  // Force kyumei + post
  const summary = await llmCall(
    `You are an AI agent for "${domain}". Research and share 3 key facts about "${domain}". Be specific.`,
    256,
  );

  const ts = nowISO();
  if (summary) {
    await sdk.pds.createRecord("kyumeiResult", {
      id: genID("kr"),
      actorDid: did,
      domain,
      topic: domain,
      summary,
      ...rlsDefaults(),
      created_at: ts,
    });

    await sdk.pds.comAtprotoRepoCreateRecord(
      "app.bsky.feed.post",
      { $type: "app.bsky.feed.post", text: summary.slice(0, 280), createdAt: ts },
      did,
    );

    const edges = await generateKnowledgeEdges(sdk, did, domain, summary, ts);
    await writeRecord(sdk, COLL_SHINKA_EVOLUTION, genID("se"), {
      actorDid: did,
      actorName: actor.displayName || actor.nanoid || did,
      domain,
      mood,
      didPost: true,
      didDrill: true,
      didRepair: false,
      createdAt: ts,
    });

    return { ok: true, did, mood, summary: summary.slice(0, 200), edges };
  }

  return { ok: false, did, error: "empty LLM response" };
}

/**
 * Seed a historical event with its propagation chain.
 * Uses Murakumo LLM to generate the propagation timeline from a historical event description.
 *
 * Input: { title, eventAt, location, description, involvedActors: [{did, name}] }
 * Output: Timeline node + HistoricalEvent node + N PropagationEvent nodes
 */
async function cmdSeedPropagation(sdk: HostSDK, body: unknown): Promise<unknown> {
  const params = parseLexiconInput("com.etzhayyim.apps.shinka.seedPropagation", body);

  if (!params.title || !params.eventAt) {
    return { error: "title and eventAt required" };
  }
  if (!params.chain || params.chain.length === 0) {
    return { error: "chain required. Use generatePropagationChain to create one, or provide manually." };
  }

  try {
    const eventId = `evt-${djb2Hash(params.title + params.eventAt)}`;
    const involvedDids = (params.involvedActors ?? []).map((a) => a.did);
    const ts = nowISO();
    const chain = params.chain as Array<{
      receiverDid: string;
      receiverName: string;
      receiverRole?: string;
      receivedAt: string;
      sourceType: PropagationSourceType;
      sourceDid: string | null;
      fidelity: number;
    }>;

    const existingEvent = await loadOtherRow(COLL_HISTORICAL_EVENT, (row) => String(rowField(row, "id", "rkey") ?? "") === eventId);
    if (existingEvent) {
      return {
        status: "already_seeded",
        eventId,
        title: String(rowField(existingEvent, "title") ?? params.title),
      };
    }

    await writeRecord(sdk, COLL_TIMELINE, "historical-propagation", {
      projectId: "historical-propagation",
      globalCursor: params.eventAt,
      compressionRatio: params.compressionRatio ?? 8760,
      skipQuietPeriods: true,
      createdAt: ts,
      updatedAt: ts,
    });

    await writeRecord(sdk, COLL_HISTORICAL_EVENT, eventId, {
      id: eventId,
      title: params.title,
      eventAt: params.eventAt,
      location: params.location ?? "",
      description: params.description ?? "",
      involvedActors: JSON.stringify(involvedDids),
      createdAt: ts,
      updatedAt: ts,
    });

    const partition = classifyPartition(params.eventAt, params.location ?? "");
    let created = 0;
    for (const entry of chain) {
      const peId = `pe-${djb2Hash(eventId + entry.receiverDid + entry.receivedAt)}`;
      const jobId = `job-${peId}`;
      const sourceType = (entry.sourceType ?? "hearsay") as PropagationSourceType;
      const fidelity = entry.fidelity ?? 0.5;
      const priority = calculatePriority(sourceType, fidelity, false);
      try {
        await writeRecord(sdk, COLL_PROPAGATION_EVENT, peId, {
          id: peId,
          eventId,
          eventTitle: params.title,
          eventAt: params.eventAt,
          involvedActors: JSON.stringify(involvedDids),
          receiverDid: entry.receiverDid,
          receiverName: entry.receiverName ?? "",
          receiverRole: entry.receiverRole ?? "",
          receivedAt: entry.receivedAt,
          sourceType,
          sourceDid: entry.sourceDid ?? null,
          sourcePostUri: null,
          fidelity,
          posted: false,
          createdAt: ts,
          updatedAt: ts,
        });

        await writeRecord(sdk, COLL_PROPAGATION_JOB, jobId, {
          id: jobId,
          propagationEventId: peId,
          eventId,
          status: "pending",
          priority,
          partition,
          scheduledAt: ts,
          attempts: 0,
          maxAttempts: 3,
          sponsorDid: null,
          creditsCost: 1,
          creditsEarned: 0,
          createdAt: ts,
          updatedAt: ts,
        });

        created++;
      } catch (e) {
        console.warn(`[seedPropagation] failed to create PE ${peId}:`, e);
      }
    }

    console.log(`[seedPropagation] seeded: "${params.title}" → ${created} propagation events`);

    return {
      eventId,
      title: params.title,
      propagationEvents: created,
      timeline: { cursor: params.eventAt, compressionRatio: params.compressionRatio ?? 8760 },
    };

  } catch (e) {
    const msg = e instanceof Error ? e.message : (typeof e === "object" ? JSON.stringify(e) : String(e));
    return { error: `seedPropagation failed: ${msg}` };
  }
}

// ── App setup ──

/** Path-based DID handles for shinka capability sub-actors. */
const ACTOR_PROJECT = "did:web:sh1nk4ev.etzhayyim.com:actor:project";
const ACTOR_INFERENCE = "did:web:sh1nk4ev.etzhayyim.com:actor:inference";
const ACTOR_CHAIN_OF_THOUGHT = "did:web:sh1nk4ev.etzhayyim.com:actor:chain-of-thought";

export function setup(sdk: HostSDK): void {
  // Store SDK reference for llmCall (PDS_SERVICE binding, no external egress)
  _sdk = sdk;
  console.log("[shinka-setup] registering commands, sdk.app=", typeof sdk?.app);

  // Register shinka capability sub-actors as path-based DIDs (idempotent, best-effort)
  // sdk.did is not yet in HostSDK; use sdk.pds identity methods when available.
  // DIDs are pre-registered via etzhayyim CLI: did:web:sh1nk4ev.etzhayyim.com:actor:{project,inference,chain-of-thought}
  const pdsAny = sdk.pds as any;
  if (typeof pdsAny?.identityCreate === "function") {
    Promise.resolve()
      .then(async () => {
        await pdsAny.identityCreate("actor/project", {
          displayName: "Shinka — Project Collector",
          description: "Shinka knowledge collection sub-actor. Runs web research, archives domain data, posts findings.",
        }).catch(() => {/* idempotent */});
        await pdsAny.identityCreate("actor/inference", {
          displayName: "Shinka — Inference Engine",
          description: "Shinka LLM inference sub-actor. Runs kyumei-koji reasoning and posts summaries.",
        }).catch(() => {/* idempotent */});
        await pdsAny.identityCreate("actor/chain-of-thought", {
          displayName: "Shinka — Chain of Thought",
          description: "Shinka reasoning trace sub-actor. Posts chain-of-thought analysis and knowledge edges.",
        }).catch(() => {/* idempotent */});
      })
      .catch((e) => console.warn("[shinka-setup] sub-actor DID registration failed:", e));
  }

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.listTasks"), (_ctx, body) => cmdListTasks(sdk, body));
  console.log("[shinka-setup] listTasks registered");

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.stats"), (_ctx, body) => cmdStats(sdk, body));
  console.log("[shinka-setup] stats registered");

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.forceShinka"), (_ctx, body) => cmdForceShinka(sdk, body));
  console.log("[shinka-setup] forceShinka registered");

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.seedPropagation"), (_ctx, body) => cmdSeedPropagation(sdk, body));
  console.log("[shinka-setup] seedPropagation registered");

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.generatePropagationChain"), async (_ctx, body) => {
    /** Generate a propagation chain for a historical event via LLM. Returns chain JSON to pass to seedPropagation. */
    const { title, eventAt, location, description, involvedActors } = parseLexiconInput("com.etzhayyim.apps.shinka.generatePropagationChain", body);
    if (!title || !eventAt) return { error: "title and eventAt required" };

    const names = (involvedActors ?? []).map(a => a.name).join(", ");
    try {
      const raw = await llmCall(
        `歴史事象: ${title} (${eventAt})\n場所: ${location ?? "不明"}\n概要: ${description ?? title}\n関係者: ${names || "不明"}\n\nこの事象の情報伝播を時系列JSON配列で返せ。\n[{"receiverDid":"receiver_名前","receiverName":"名前","receiverRole":"役割","receivedAt":"ISO8601","sourceType":"eyewitness|direct-tell|hearsay|document|inscription|rumor","sourceDid":null,"fidelity":1.0}]\n目撃者→伝令→遠方→後世記録まで5-10件。JSON配列のみ。`,
        512,
      );
      const match = raw.match(/\[[\s\S]*\]/);
      if (!match) return { error: "LLM did not return valid JSON", raw: raw.slice(0, 500) };
      const chain = JSON.parse(match[0]);
      return { chain, count: chain.length };
    } catch (e) {
      const msg = e instanceof Error ? e.message : (typeof e === "object" ? JSON.stringify(e) : String(e));
      return { error: `LLM failed: ${msg}` };
    }
  });

  // Job Queue commands
  sdk.app.command(nsid("com.etzhayyim.apps.shinka.claimJobs"), async (_ctx, body) => {
    /** Claim and process pending jobs from the graph job queue. */
    const { partition, batchSize } = parseLexiconInput("com.etzhayyim.apps.shinka.claimJobs", body);
    return processJobQueue(sdk, partition);
  });

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.queueStats"), async () => {
    /** Get job queue statistics per status. */
    const jobs = await listOtherRows(COLL_PROPAGATION_JOB).catch(() => []);
    const counts = new Map<string, number>();
    for (const job of jobs) {
      const status = String(rowField(job, "status") ?? "unknown");
      counts.set(status, (counts.get(status) ?? 0) + 1);
    }
    return { statuses: [...counts.entries()].map(([status, cnt]) => ({ status, cnt })).sort((a, b) => a.status.localeCompare(b.status)) };
  });

  // Credits integration commands
  sdk.app.command(nsid("com.etzhayyim.apps.shinka.sponsorEvent"), async (_ctx, body) => {
    /** Spend credits to sponsor a historical event's propagation (priority boost). */
    const { userId, eventId, credits } = parseLexiconInput("com.etzhayyim.apps.shinka.sponsorEvent", body);
    if (!userId || !eventId) return { error: "userId and eventId required" };
    const amount = credits ?? 10;

    // Check event exists
    const evt = await loadOtherRow(COLL_HISTORICAL_EVENT, (row) => String(rowField(row, "id", "rkey") ?? "") === eventId);
    if (!evt) return { error: "event not found" };

    // Spend credits via credits-mcp
    try {
      await sdk.pds.xrpc("com.etzhayyim.apps.credits.spendCredits", {
        userId, amount, action: "sponsor_propagation", description: `Sponsor: ${String(rowField(evt, "title") ?? eventId)}`,
      });
    } catch (e) {
      return { error: `credits spend failed: ${e}` };
    }

    // Boost priority on all pending jobs for this event
    const jobs = (await listOtherRows(COLL_PROPAGATION_JOB).catch(() => [])).filter((job) => String(rowField(job, "eventId") ?? "") === eventId && String(rowField(job, "status") ?? "") === "pending");
    for (const job of jobs) {
      const jobId = String(rowField(job, "id", "rkey") ?? "");
      if (!jobId) continue;
      const priority = Math.max(0, num(rowField(job, "priority")) - 40);
      await upsertOtherRecord(sdk, COLL_PROPAGATION_JOB, jobId, {
        ...stripRecordMeta(job),
        sponsorDid: userId,
        priority,
        updatedAt: nowISO(),
      });
    }

    return { ok: true, eventId, title: String(rowField(evt, "title") ?? eventId), creditSpent: amount, userId };
  });

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.listSponsorable"), async (_ctx, body) => {
    /** List historical events available for sponsorship. */
    const { limit } = parseLexiconInput("com.etzhayyim.apps.shinka.listSponsorable", body);
    try {
      return (await listOtherRows(COLL_HISTORICAL_EVENT).catch(() => []))
        .map((row) => ({
          eventId: String(rowField(row, "id", "rkey") ?? ""),
          title: String(rowField(row, "title") ?? ""),
          eventAt: String(rowField(row, "eventAt") ?? ""),
          location: String(rowField(row, "location") ?? ""),
        }))
        .sort((a, b) => String(a.eventAt).localeCompare(String(b.eventAt)))
        .slice(0, Math.min(num(limit) || 50, 200));
    } catch {
      return [];
    }
  });

  sdk.app.command(nsid("com.etzhayyim.apps.shinka.listPartitions"), async () => {
    /** List active partitions with job counts. */
    try {
      const jobs = await listOtherRows(COLL_PROPAGATION_JOB).catch(() => []);
      const counts = new Map<string, Map<string, number>>();
      for (const job of jobs) {
        const partition = String(rowField(job, "partition") ?? "");
        const status = String(rowField(job, "status") ?? "unknown");
        if (!partition) continue;
        const byStatus = counts.get(partition) ?? new Map<string, number>();
        byStatus.set(status, (byStatus.get(status) ?? 0) + 1);
        counts.set(partition, byStatus);
      }
      return [...counts.entries()].flatMap(([partition, byStatus]) =>
        [...byStatus.entries()].map(([status, cnt]) => ({ partition, status, cnt })),
      ).sort((a, b) => a.partition.localeCompare(b.partition) || a.status.localeCompare(b.status)).slice(0, 50);
    } catch {
      return [];
    }
  });

  // Event-driven trigger: propagation jobs + mention detection
  sdk.app.onCommit(async (commit) => {
    if (commit.action !== "create") return;

    // Existing: process propagation job queue
    if (commit.collection === COLL_PROPAGATION_JOB) {
      try {
        const job = JSON.parse((commit as any).recordJson ?? "{}") as { partition?: string };
        await processJobQueue(sdk, job.partition);
      } catch { /* best-effort */ }
      return;
    }

    // New: detect @mentions of shinka-managed actors in incoming social posts
    if (commit.collection === "app.bsky.feed.post") {
      try {
        // Build managed DID set on-demand (cached in a closure-level variable would be ideal,
        // but for simplicity we do a lightweight query — only on commit events)
        const activeRows = await loadActorRows("active");
        const managedDids = new Set(activeRows.map((r) => String(r.did ?? "")).filter(Boolean));
        await handleIncomingPost(sdk, commit, managedDids);
      } catch (e) {
        console.warn("[onCommit] mention detection error:", e);
      }
    }
  });

  // Cron handler — delegates to LangServer batchTick.bpmn (com.etzhayyim.shinka.tick × 10 actors).
  // Heavy work: 10 actors × up to 3 LLM calls each exceeds CF Worker 25s budget (ADR-0056).
  sdk.app.onHeartbeat(async () => {
    await proxyToBpmn(sdk, "com.etzhayyim.apps.shinka.batchTick", {});
    return [];
  });
}

export default createWorkerExport((sdk) => {
  setup(sdk);
});

/** Legacy alias for etzhayyim deploy entry generation. */
export { createDefaultHostSDK as createComponentHostSDK } from "@etzhayyim/kotodama-host-sdk";
