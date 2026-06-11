/**
 * kafun-bokumetsu — CF Worker thin dispatcher (Phase 1).
 *
 * Routes 3 XRPC commands through bpmn-dispatcher → LangGraph Server
 * (mitama-langgraph-pool, ADR-2605080600), then materialises the returned
 * rows into RisingWave via Hyperdrive (ADR-0036) under path-based actor DIDs
 * (ADR-0019).
 *
 *   com.etzhayyim.apps.kafun.agent.research → kafun.research.v1 → vertex_kafun_research[]
 *   com.etzhayyim.apps.kafun.agent.think    → kafun.think.v1    → vertex_kafun_insight + vertex_kafun_proposal[]
 *   com.etzhayyim.apps.kafun.agent.tick     → kafun.tick.v1     → vertex_kafun_action  (+ optional follow-on)
 *
 * No business logic lives here — this Worker is a 3-tier-write thin
 * dispatcher per `60-apps/CLAUDE.md` §App Implementation Pattern.
 *
 * Public-by-default policy:
 *   *Every* externally visible activity (research findings, proposals,
 *   dispatched actions, future emails / file uploads / generated content)
 *   MUST be mirrored to yoro.etzhayyim.com by dispatching `app.bsky.feed.post`
 *   under the appropriate path-based actor DID. yoro appview reads the
 *   PDS firehose for these collections and renders them. Use `publishToYoro`.
 */

import {
  asAgentTool,
  createKyselyDb,
  createWorkerExport,
  decodeJson,
  type HostSDK,
  nsid,
  withCapabilityTags,
  withOCELEvent,
} from "@etzhayyim/kotodama-host-sdk";

const DISPATCHER_BASE = "http://dispatcher.etzhayyim.com:8080";

const RESEARCHER_DID = "did:web:n97ik10n.etzhayyim.com:actor:researcher";
const PROPOSER_DID   = "did:web:n97ik10n.etzhayyim.com:actor:proposer";
const EXECUTOR_DID   = "did:web:n97ik10n.etzhayyim.com:actor:executor";
// Envoy = outbound communications (email / DM / external API). Every send
// MUST mirror to yoro via publishToYoro under this DID.
const ENVOY_DID      = "did:web:n97ik10n.etzhayyim.com:actor:envoy";
// Scout = satellite imagery ingest + ML canopy detection (L0-1a/b sub-DAG).
const SCOUT_DID      = "did:web:n97ik10n.etzhayyim.com:actor:scout";
// Cadastral = canopy → parcel → landowner resolution (L0-1c/d sub-DAG).
const CADASTRAL_DID  = "did:web:n97ik10n.etzhayyim.com:actor:cadastral";

const APP_DID = "did:web:n97ik10n.etzhayyim.com";

type Env = { HYPERDRIVE: unknown };
type Db = ReturnType<typeof createKyselyDb>;

// ── LangGraph dispatch helper ─────────────────────────────────────────────────
async function dispatch(graphNsid: string, input: unknown, timeoutMs = 180_000): Promise<Record<string, unknown>> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(`${DISPATCHER_BASE}/xrpc/${graphNsid}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ input }),
      signal: ctrl.signal,
    });
    if (!r.ok) throw new Error(`dispatcher ${graphNsid} → ${r.status}`);
    return (await r.json()) as Record<string, unknown>;
  } finally {
    clearTimeout(t);
  }
}

// ── yoro public-by-default helper ─────────────────────────────────────────────
// Every kafun activity is published to yoro.etzhayyim.com as an app.bsky.feed.post
// under the responsible path-based actor DID. yoro appview tails the PDS
// firehose for these collections; no separate yoro write API is required.
// For future emails/files/blob outputs: also call this helper with a short
// summary + the embed/blob ref so that the artefact stays publicly visible.
async function publishToYoro(
  sdk: HostSDK,
  actorDid: string,
  text: string,
  opts?: { reply?: { root: { uri: string; cid: string }; parent: { uri: string; cid: string } }; embed?: unknown },
): Promise<void> {
  const body: Record<string, unknown> = {
    type: "app.bsky.feed.post",
    did: actorDid,
    text: text.length > 280 ? text.slice(0, 277) + "..." : text,
  };
  if (opts?.reply) body.reply = opts.reply;
  if (opts?.embed) body.embed = opts.embed;
  try {
    await sdk.pds.dispatch(body as Parameters<typeof sdk.pds.dispatch>[0]);
  } catch (e) {
    console.error("[kafun] yoro publish failed:", (e as Error).message);
  }
}

// Upload a blob via PDS and publish a yoro post that embeds it. Use this for
// any file-bearing artefact (pdf, screenshot, attached email, generated image)
// that the project produces — keeps "no off-yoro side effect" invariant.
async function publishBlobToYoro(
  sdk: HostSDK,
  actorDid: string,
  fileName: string,
  mimeType: string,
  bytes: Uint8Array,
  caption: string,
): Promise<void> {
  const pdsClient = sdk.pds as unknown as {
    uploadBlob?: (args: { did: string; mimeType: string; bytes: Uint8Array }) => Promise<{ blob: unknown }>;
  };
  let blob: unknown = null;
  try {
    if (pdsClient.uploadBlob) {
      const r = await pdsClient.uploadBlob({ did: actorDid, mimeType, bytes });
      blob = r.blob;
    }
  } catch (e) {
    console.error("[kafun] uploadBlob failed:", (e as Error).message);
  }
  await publishToYoro(sdk, actorDid, `${caption} (${fileName})`, {
    embed: blob ? { $type: "app.bsky.embed.external", external: { uri: "", title: fileName, description: caption } } : undefined,
  });
}

// Send an email and immediately mirror the send to yoro under :actor:envoy.
// The body+recipient land on yoro as a public post; PII-bearing content must be
// redacted upstream before calling this.
async function sendEmailAndPublish(
  sdk: HostSDK,
  to: string,
  subject: string,
  body: string,
): Promise<void> {
  // Outbound mail goes through the microsoft.etzhayyim.com actor (`com.etzhayyim.apps.microsoft.sendMail`).
  // Direct dispatch is intentional — we route through host-imports invoke so the
  // microsoft actor handles tenant binding (root CLAUDE.md §etzhayyim Agent).
  const params = { to: [to], subject, body };
  const paramsJson = JSON.stringify(params);
  try {
    await (sdk.hostImports as unknown as { invoke?: (b: Uint8Array) => unknown }).invoke?.(
      new TextEncoder().encode(JSON.stringify({
        did: "did:web:microsoft.etzhayyim.com",
        method: "com.etzhayyim.apps.microsoft.sendMail",
        params: paramsJson,
      })),
    );
  } catch (e) {
    console.error("[kafun] sendMail failed:", (e as Error).message);
  }
  await publishToYoro(
    sdk,
    ENVOY_DID,
    `[email→${to}] ${subject}\n\n${body}`,
  );
}

// ── Row writers (T2 domain via Hyperdrive direct) ─────────────────────────────
type AnyRow = Record<string, unknown>;

async function writeRows(db: Db, table: string, rows: AnyRow[]): Promise<number> {
  if (!rows.length) return 0;
  // Re-INSERT = implicit upsert under record-log semantics; Kysely handles arrays.
  await (db as unknown as { insertInto: (t: string) => { values: (v: AnyRow[]) => { execute: () => Promise<unknown> } } })
    .insertInto(table).values(rows).execute();
  return rows.length;
}

// ── Commands ──────────────────────────────────────────────────────────────────

async function cmdResearch(sdk: HostSDK, body: Uint8Array): Promise<string> {
  const { category, query } = decodeJson(body, { category: "biology", query: "" }) as { category: string; query: string };
  const out = await dispatch("com.etzhayyim.apps.kafun.agent.research", { category, query });
  const findings = (out.findings ?? []) as AnyRow[];

  const db = createKyselyDb((sdk.env as Env).HYPERDRIVE);
  const written = await writeRows(db, "vertex_kafun_research", findings);

  // Publish to yoro: 1 summary post + 1 short post per finding (capped to 5).
  await publishToYoro(
    sdk,
    RESEARCHER_DID,
    `[research/${category}] ${query} → ${written} findings`,
  );
  for (const f of findings.slice(0, 5)) {
    const title = String(f.title ?? "");
    const summary = String(f.summary ?? "");
    await publishToYoro(sdk, RESEARCHER_DID, `${title}\n${summary}`);
  }
  return JSON.stringify({ ok: true, count: written, findings });
}

async function cmdThink(sdk: HostSDK, body: Uint8Array): Promise<string> {
  const { seed_findings = [] } = decodeJson(body, { seed_findings: [] as AnyRow[] });
  const out = await dispatch("com.etzhayyim.apps.kafun.agent.think", { seed_findings });
  const insight   = (out.insight ?? null) as AnyRow | null;
  const proposals = (out.proposals ?? []) as AnyRow[];

  const db = createKyselyDb((sdk.env as Env).HYPERDRIVE);
  const insightCount  = insight ? await writeRows(db, "vertex_kafun_insight", [insight]) : 0;
  const proposalCount = await writeRows(db, "vertex_kafun_proposal", proposals);

  // Publish to yoro under proposer DID (insight + every proposal).
  if (insight) {
    await publishToYoro(sdk, PROPOSER_DID, `[insight] ${String(insight.summary ?? "")}`);
  }
  for (const p of proposals) {
    const title = String(p.title ?? "");
    const action = String(p.action_type ?? "");
    const cost = Number(p.estimated_cost_jpy ?? 0);
    await publishToYoro(
      sdk,
      PROPOSER_DID,
      `[proposal/${action}] ${title}  (¥${cost.toLocaleString("ja-JP")})`,
    );
  }
  return JSON.stringify({ ok: true, insightCount, proposalCount, insight, proposals });
}

async function cmdTick(sdk: HostSDK): Promise<string> {
  const db = createKyselyDb((sdk.env as Env).HYPERDRIVE);

  // Tier A — pull the next ready node from the goal-DAG.
  // Selection is pure SQL on mv_agent_topo_ready (Theory-of-Constraints
  // ranking), so the LangGraph kafun.tick.v1 chain is bypassed when a topo
  // node is available.
  const ready = await (db as unknown as {
    selectFrom: (t: string) => {
      selectAll: () => {
        where: (c: string, op: string, v: unknown) => {
          orderBy: (c: string, d: string) => {
            orderBy: (c: string, d: string) => {
              orderBy: (c: string, d: string) => { limit: (n: number) => { execute: () => Promise<AnyRow[]> } };
            };
          };
        };
      };
    };
  })
    .selectFrom("mv_agent_topo_ready").selectAll()
    .where("app_did", "=", APP_DID)
    .orderBy("bottleneck_rank", "asc")
    .orderBy("layer", "asc")
    .orderBy("kpi_weight", "desc")
    .limit(1).execute();

  const topo = ready[0] ?? null;
  if (topo) {
    const now = new Date().toISOString();
    const nodeId = String(topo.node_id ?? "");
    const seedBytes = new TextEncoder().encode(`${nodeId}:${now}`);
    const hashBuf = await crypto.subtle.digest("SHA-256", seedBytes);
    const rkey = Array.from(new Uint8Array(hashBuf))
      .map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 24);
    const action: AnyRow = {
      vertex_id:        `at://${EXECUTOR_DID}/com.etzhayyim.apps.kafun.action/${rkey}`,
      actor_did:        EXECUTOR_DID,
      from_proposal_id: String(topo.vertex_id ?? ""),
      action_type:      String(topo.category ?? "execution"),
      cost_jpy:         0,
      status:           "dispatched",
      dispatch_hint:    JSON.stringify({ transport: "topo", node_id: nodeId, layer: topo.layer }),
      created_at:       now,
    };
    await writeRows(db, "vertex_kafun_action", [action]);
    await publishToYoro(
      sdk,
      EXECUTOR_DID,
      `[topo-tick] node=${nodeId} layer=L${topo.layer} cat=${topo.category} title="${String(topo.title ?? "")}"`,
    );
    return JSON.stringify({ ok: true, source: "topo", decision: action });
  }

  // Tier B fallback — legacy proposal-based selection via LangGraph.
  // Drains pre-topology proposals (created before r_20260510010000 applied).
  const pending = await (db as unknown as {
    selectFrom: (t: string) => {
      selectAll: () => {
        where: (c: string, op: string, v: unknown) => {
          orderBy: (c: string, d: string) => { limit: (n: number) => { execute: () => Promise<AnyRow[]> } };
        };
      };
    };
  })
    .selectFrom("vertex_kafun_proposal").selectAll()
    .where("status", "=", "draft").orderBy("priority", "asc").limit(50).execute();

  const fund_balance_jpy = 0;
  const out = await dispatch("com.etzhayyim.apps.kafun.agent.tick", { pending_proposals: pending, fund_balance_jpy });
  const decision = (out.decision ?? null) as AnyRow | null;
  if (!decision) return JSON.stringify({ ok: true, source: "proposal", decision: null });

  const row: AnyRow = { ...decision, dispatch_hint: JSON.stringify(decision.dispatch_hint ?? {}) };
  await writeRows(db, "vertex_kafun_action", [row]);

  const action = String(decision.action_type ?? "");
  const cost = Number(decision.cost_jpy ?? 0);
  await publishToYoro(
    sdk,
    EXECUTOR_DID,
    `[action/${action}] dispatched (¥${cost.toLocaleString("ja-JP")}) from=${String(decision.from_proposal_id ?? "")}`,
  );
  return JSON.stringify({ ok: true, source: "proposal", decision });
}

// ── SDK Factory ───────────────────────────────────────────────────────────────

export default createWorkerExport((sdk: HostSDK) => {
  const did = sdk.did as unknown as {
    create?: (suffix: string, spec: Record<string, unknown>) => unknown;
  };

  // Idempotent path-based DID registration (ADR-0019).
  void did.create?.("actor:researcher", {
    displayName: "Kafun Researcher",
    description: "kafun-bokumetsu research actor — collects findings on Japanese cedar/cypress pollen eradication.",
    avatar: "🔬",
    category: "research",
    isBot: true,
    operator: "etzhayyim",
  });
  void did.create?.("actor:proposer", {
    displayName: "Kafun Proposer",
    description: "kafun-bokumetsu proposer actor — synthesises findings into actionable proposals.",
    avatar: "💡",
    category: "research",
    isBot: true,
    operator: "etzhayyim",
  });
  void did.create?.("actor:executor", {
    displayName: "Kafun Executor",
    description: "kafun-bokumetsu executor actor — selects and dispatches the next pollen-eradication action.",
    avatar: "⚙️",
    category: "research",
    isBot: true,
    operator: "etzhayyim",
  });
  void did.create?.("actor:envoy", {
    displayName: "Kafun Envoy",
    description: "kafun-bokumetsu envoy actor — outbound communications (email / DM / external API). Every send is mirrored to yoro.",
    avatar: "✉️",
    category: "communications",
    isBot: true,
    operator: "etzhayyim",
  });
  void did.create?.("actor:scout", {
    displayName: "Kafun Scout",
    description: "kafun-bokumetsu scout actor — satellite imagery ingest (Sentinel-2 / ALOS / ASTER) + ML canopy detection over Japanese sugi/hinoki.",
    avatar: "🛰️",
    category: "research",
    isBot: true,
    operator: "etzhayyim",
  });
  void did.create?.("actor:cadastral", {
    displayName: "Kafun Cadastral",
    description: "kafun-bokumetsu cadastral actor — resolves detected canopy polygons to 不動産登記 parcels and landowners (国 / 都道府県 / 市町村 / 民有).",
    avatar: "📜",
    category: "research",
    isBot: true,
    operator: "etzhayyim",
  });

  sdk.app
    .command(
      nsid("com.etzhayyim.apps.kafun.agent.research"),
      (_: unknown, b: Uint8Array) => cmdResearch(sdk, b),
      asAgentTool("Run kafun research StateGraph (researcher actor)"),
      withCapabilityTags("kafun", "research", "langgraph"),
      withOCELEvent("kafun.research.completed"),
    )
    .command(
      nsid("com.etzhayyim.apps.kafun.agent.think"),
      (_: unknown, b: Uint8Array) => cmdThink(sdk, b),
      asAgentTool("Run kafun think StateGraph (proposer actor)"),
      withCapabilityTags("kafun", "think", "langgraph"),
      withOCELEvent("kafun.think.completed"),
    )
    .command(
      nsid("com.etzhayyim.apps.kafun.agent.tick"),
      (_: unknown, _b: Uint8Array) => cmdTick(sdk),
      asAgentTool("Run kafun tick StateGraph (executor actor; cron-driven)"),
      withCapabilityTags("kafun", "tick", "langgraph"),
      withOCELEvent("kafun.tick.completed"),
    );
});
