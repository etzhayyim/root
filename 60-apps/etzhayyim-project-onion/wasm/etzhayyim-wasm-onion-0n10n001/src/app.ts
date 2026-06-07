import {
  asAgentTool,
  createWorkerExport,
  withCapabilityTags,
  withOCELEvent,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  nowISO,
  str,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";

// ---------- graph schema note ----------
// vertex_onion_page  : onion_url, onion_host, title, content_hash, risk_score, category, crawled_at
// vertex_onion_site  : node_id, onion_host, first_seen, last_seen, category, risk_score, reachable, page_count
// vertex_onion_crawl : session_id, onion_host, started_at, finished_at, page_count, error_count, reachable
//
// ---------- storage (ADR-2606071800: kotoba-kqe, NOT Hyperdrive/Kysely) ----------
// Reads go through `sdk.graph.query` (kotoba-kqe over the canonical Datom log); writes go
// through `sdk.pds.dispatch(createRecord)` (PDS → kagami appends Datoms). This Worker holds
// no DB binding and never touches RisingWave/Hyperdrive/Kysely (substrate boundary).
//
// ---------- crawl ownership ----------
// As of 2026-04-27 (ADR-0056) the active darkweb crawl is owned by LangServer BPMN-contract
// `etzhayyim-root/00-contracts/bpmn/ai/etzhayyim/onion/crawlSeeds.bpmn` (timer-start `R/PT6H`) and
// the `kotodama` k8s pod (`onion.crawl.{queueSeeds,processQueue}` task types,
// `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/onion_crawl.py`). The Python
// worker calls `darkweb-proxy.etzhayyim.com/fetch` (Tor + Playwright CF Container).
//
// This CF Worker is now an L3 Dispatcher (per ADR-2604251830): it exposes read XRPCs and an
// `enqueue` path for `seedCrawl` that appends a vertex_onion_site record with `last_seen = NULL`
// so the next BPMN tick claims it. No outbound HTTP to darkweb-proxy from this Worker.

type Row = Record<string, unknown>;

// kotoba-kqe read over the canonical Datom log (loose-cast to the host binding; degrades to
// [] when the binding is absent). Materializes one Row per entity from its `:<entity>/<attr>`
// Datoms — no SQL projection, no Hyperdrive (ADR-2606071800).
async function kqeReadAll(sdk: HostSDK, entity: string): Promise<Row[]> {
  const graph = (sdk as unknown as {
    graph?: { query: (q: string) => Promise<Row[]> };
  }).graph;
  if (!graph) return [];
  try {
    return await graph.query(
      `[:find (pull ?e [*]) :where [?e :vertex/kind "${entity}"]]`,
    );
  } catch (e) {
    console.warn(`[onion] kqe read ${entity} failed: ${String(e)}`);
    return [];
  }
}

// PDS write — appends a record (PDS → kagami → Datoms). No direct DB write.
async function pdsCreateRecord(sdk: HostSDK, collection: string, record: Row): Promise<boolean> {
  const pds = (sdk as unknown as {
    pds?: { dispatch: (m: unknown) => Promise<unknown> };
  }).pds;
  if (!pds) return false;
  try {
    await pds.dispatch({ type: "com.atproto.repo.createRecord", payload: { collection, record } });
    return true;
  } catch (e) {
    console.warn(`[onion] pds createRecord ${collection} failed: ${String(e)}`);
    return false;
  }
}

function onionHostFromUrl(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

function slugForHost(host: string): string {
  const base = host.endsWith(".onion") ? host.slice(0, -6) : host;
  return base.replace(/[^a-zA-Z0-9]/g, "_").slice(0, 64);
}

// --- Commands ---

async function cmdSeedCrawl(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = parseLexiconInput("ai.etzhayyim.apps.onion.seedCrawl", payload);
  const urls = (Array.isArray(req.urls) ? req.urls : []).map(String).filter(Boolean).slice(0, 50);
  if (urls.length === 0) return { error: "urls required" };
  const category = str(req.category ?? "") || null;

  const startedAt = nowISO();
  const today = startedAt.slice(0, 10);
  const seq = Date.now();
  const hosts: string[] = [];
  let queued = 0;

  for (const url of urls) {
    const host = onionHostFromUrl(url);
    if (!host.endsWith(".onion")) continue;
    const slug = slugForHost(host);
    const vid = `at://did:web:onion.etzhayyim.com/ai.etzhayyim.apps.onion.site/${slug}`;
    // append the site record (last_seen = NULL → next BPMN tick R/PT6H claims as stalest)
    const ok = await pdsCreateRecord(sdk, "ai.etzhayyim.apps.onion.site", {
      vertex_id: vid,
      _seq: seq,
      created_date: today,
      sensitivity_ord: 2,
      owner_did: "did:web:onion.etzhayyim.com",
      onion_host: host,
      node_id: `onion:site:${host}`,
      title: null,
      category,
      risk_score: 0,
      reachable: true,
      page_count: 0,
      first_seen: startedAt,
      last_seen: null,
      site_did: `did:web:onion.etzhayyim.com:${slug}`,
      mirror_clearnet: null,
      threat_actor_ref: null,
    });
    if (ok) queued++;
    hosts.push(host);
  }

  return {
    seeded: queued,
    hosts,
    note: "Crawl is owned by LangServer BPMN-contract onion_crawl_seeds (R/PT6H). New seeds are picked up on the next tick.",
  };
}

async function cmdListSites(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = parseLexiconInput("ai.etzhayyim.apps.onion.listSites", payload);
  const limit = Math.min(Number(req.limit ?? 50), 100);
  const offset = Number(req.offset ?? 0);

  let rows = await kqeReadAll(sdk, "vertex_onion_site");
  if (req.category) rows = rows.filter((r) => r.category === str(req.category));
  if (typeof req.reachable === "boolean") {
    rows = rows.filter((r) => (r.reachable === true || r.reachable === 1) === req.reachable);
  }
  if (req.minRiskScore != null) rows = rows.filter((r) => Number(r.risk_score ?? 0) >= Number(req.minRiskScore));
  const page = rows.slice(offset, offset + limit);

  return { sites: page, total: rows.length, offset, limit };
}

async function cmdListPages(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = parseLexiconInput("ai.etzhayyim.apps.onion.listPages", payload);
  const limit = Math.min(Number(req.limit ?? 50), 100);
  const offset = Number(req.offset ?? 0);

  let rows = await kqeReadAll(sdk, "vertex_onion_page");
  if (req.onionHost) rows = rows.filter((r) => r.onion_host === str(req.onionHost));
  if (req.category) rows = rows.filter((r) => r.category === str(req.category));
  if (req.minRiskScore != null) rows = rows.filter((r) => Number(r.risk_score ?? 0) >= Number(req.minRiskScore));
  const page = rows.slice(offset, offset + limit);

  return { pages: page, total: rows.length, offset, limit };
}

async function cmdGetStats(sdk: HostSDK, _payload: Uint8Array): Promise<unknown> {
  const sites = await kqeReadAll(sdk, "vertex_onion_site");
  const pages = await kqeReadAll(sdk, "vertex_onion_page");
  const reachableSites = sites.filter((s) => s.reachable === true || s.reachable === 1).length;
  const highRiskPages = pages.filter((p) => Number(p.risk_score ?? 0) >= 50).length;
  return { totalSites: sites.length, totalPages: pages.length, reachableSites, highRiskPages };
}

// --- Reactive Pipeline ---
// malak.etzhayyim.com Follows onion.etzhayyim.com and receives onion.page / onion.site / onion.crawl
// records via handleComAtprotoSyncSubscribeReposCommit (design E follow-based input).
// onion is a source, not a consumer.

export async function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  commit: ComAtprotoSyncSubscribeReposCommit,
): Promise<{ ok: boolean }> {
  void commit;
  return { ok: true };
}

// --- SDK Factory ---

export default createWorkerExport((sdk) => {
  sdk.app
    .command(
      nsid("ai.etzhayyim.apps.onion.seedCrawl"),
      (_, b) => cmdSeedCrawl(sdk, b),
      asAgentTool("Enqueue one or more .onion URLs for the LangServer BPMN-contract onion_crawl_seeds worker (R/PT6H)"),
      withCapabilityTags("darkweb", "crawl", "onion", "tor", "enqueue"),
      withOCELEvent("onion.crawl.seeded"),
    )
    .command(
      nsid("ai.etzhayyim.apps.onion.listSites"),
      (_, b) => cmdListSites(sdk, b),
      asAgentTool("List discovered .onion sites with risk scores and categories"),
      withCapabilityTags("darkweb", "list", "intelligence"),
    )
    .command(
      nsid("ai.etzhayyim.apps.onion.listPages"),
      (_, b) => cmdListPages(sdk, b),
      asAgentTool("List crawled .onion pages, optionally filtered by host"),
      withCapabilityTags("darkweb", "list", "pages"),
    )
    .command(
      nsid("ai.etzhayyim.apps.onion.getStats"),
      (_, b) => cmdGetStats(sdk, b),
      asAgentTool("Get onion.etzhayyim.com crawl statistics"),
      withCapabilityTags("darkweb", "stats"),
    );
});
