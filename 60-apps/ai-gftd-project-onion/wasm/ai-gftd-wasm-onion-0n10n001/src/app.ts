import {
  asAgentTool,
  createKyselyDb,
  createWorkerExport,
  withCapabilityTags,
  withOCELEvent,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  nowISO,
  str,
  nsid,
  parseLexiconInput,
} from "@gftd/magatama-host-sdk";

// ---------- graph schema note ----------
// vertex_onion_page  : onion_url, onion_host, title, content_hash, risk_score, category, crawled_at
// vertex_onion_site  : node_id, onion_host, first_seen, last_seen, category, risk_score, reachable, page_count
// vertex_onion_crawl : session_id, onion_host, started_at, finished_at, page_count, error_count, reachable
//
// ---------- crawl ownership ----------
// As of 2026-04-27 (ADR-0056) the active darkweb crawl is owned by LangServer BPMN-contract
// `etzhayyim-root/00-contracts/bpmn/ai/gftd/onion/crawlSeeds.bpmn` (timer-start `R/PT6H`) and
// the `pymagatama` k8s pod (`onion.crawl.{queueSeeds,processQueue}` task types,
// `20-actors/magatama/py/src/pymagatama/primitives/onion_crawl.py`). The Python
// worker calls `darkweb-proxy.gftd.ai/fetch` (Tor + Playwright CF Container)
// and writes vertex_onion_{site,page,crawl} directly via Hyperdrive.
//
// This CF Worker is now an L3 Dispatcher (per ADR-2604251830): it exposes
// read XRPCs and an `enqueue` path for `seedCrawl` that inserts a
// vertex_onion_site row with `last_seen = NULL` so the next BPMN tick claims
// it. No outbound HTTP to darkweb-proxy from this Worker.

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
  const req = parseLexiconInput("ai.gftd.apps.onion.seedCrawl", payload);
  const urls = (Array.isArray(req.urls) ? req.urls : []).map(String).filter(Boolean).slice(0, 50);
  if (urls.length === 0) return { error: "urls required" };
  const category = str(req.category ?? "") || null;

  const db = createKyselyDb((sdk.env as { HYPERDRIVE: unknown }).HYPERDRIVE);
  const startedAt = nowISO();
  const today = startedAt.slice(0, 10);
  const seq = Date.now();
  const hosts: string[] = [];
  let queued = 0;

  for (const url of urls) {
    const host = onionHostFromUrl(url);
    if (!host.endsWith(".onion")) continue;
    const slug = slugForHost(host);
    const vid = `at://did:web:onion.gftd.ai/ai.gftd.apps.onion.site/${slug}`;
    try {
      const result = await (db as unknown as {
        insertInto: (t: string) => {
          values: (v: Record<string, unknown>) => {
            onConflict: (cb: (oc: { column: (c: string) => { doNothing: () => unknown } }) => unknown) => {
              executeTakeFirst: () => Promise<{ numInsertedOrUpdatedRows?: bigint } | undefined>;
            };
          };
        };
      }).insertInto("vertex_onion_site").values({
        vertex_id: vid,
        _seq: seq,
        created_date: today,
        sensitivity_ord: 2,
        owner_did: "did:web:onion.gftd.ai",
        onion_host: host,
        node_id: `onion:site:${host}`,
        title: null,
        category,
        risk_score: 0,
        reachable: true,
        page_count: 0,
        first_seen: startedAt,
        last_seen: null, // NULL → next BPMN tick (R/PT6H) claims as stalest
        site_did: `did:web:onion.gftd.ai:${slug}`,
        mirror_clearnet: null,
        threat_actor_ref: null,
      }).onConflict((oc) => oc.column("vertex_id").doNothing()).executeTakeFirst();
      const inserted = Number(result?.numInsertedOrUpdatedRows ?? 0n);
      if (inserted > 0) queued++;
      hosts.push(host);
    } catch (e) {
      console.warn(`[onion] seedCrawl enqueue failed url=${url}: ${String(e)}`);
    }
  }

  return {
    seeded: queued,
    hosts,
    note: "Crawl is owned by LangServer BPMN-contract onion_crawl_seeds (R/PT6H). New seeds are picked up on the next tick.",
  };
}

async function cmdListSites(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = parseLexiconInput("ai.gftd.apps.onion.listSites", payload);
  const limit = Math.min(Number(req.limit ?? 50), 100);
  const offset = Number(req.offset ?? 0);

  const db = createKyselyDb((sdk.env as { HYPERDRIVE: unknown }).HYPERDRIVE);
  let q = db.selectFrom("vertex_onion_site" as never).selectAll() as unknown as {
    where: (...args: unknown[]) => unknown;
    offset: (n: number) => unknown;
    limit: (n: number) => unknown;
    execute: () => Promise<Array<Record<string, unknown>>>;
  };
  if (req.category) q = (q as unknown as { where: (a: string, b: string, c: string) => typeof q }).where("category", "=", str(req.category));
  if (typeof req.reachable === "boolean") q = (q as unknown as { where: (a: string, b: string, c: number) => typeof q }).where("reachable", "=", req.reachable ? 1 : 0);
  if (req.minRiskScore != null) q = (q as unknown as { where: (a: string, b: string, c: number) => typeof q }).where("risk_score", ">=", Number(req.minRiskScore));
  const rows: Array<Record<string, unknown>> = await (q as unknown as { offset: (n: number) => { limit: (n: number) => { execute: () => Promise<Array<Record<string, unknown>>> } } }).offset(offset).limit(limit).execute().catch(() => []);

  return { sites: rows, total: rows.length, offset, limit };
}

async function cmdListPages(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = parseLexiconInput("ai.gftd.apps.onion.listPages", payload);
  const limit = Math.min(Number(req.limit ?? 50), 100);
  const offset = Number(req.offset ?? 0);

  const db = createKyselyDb((sdk.env as { HYPERDRIVE: unknown }).HYPERDRIVE);
  let q = db.selectFrom("vertex_onion_page" as never).selectAll() as unknown as {
    where: (...args: unknown[]) => unknown;
    offset: (n: number) => unknown;
    limit: (n: number) => unknown;
    execute: () => Promise<Array<Record<string, unknown>>>;
  };
  if (req.onionHost) q = (q as unknown as { where: (a: string, b: string, c: string) => typeof q }).where("onion_host", "=", str(req.onionHost));
  if (req.category) q = (q as unknown as { where: (a: string, b: string, c: string) => typeof q }).where("category", "=", str(req.category));
  if (req.minRiskScore != null) q = (q as unknown as { where: (a: string, b: string, c: number) => typeof q }).where("risk_score", ">=", Number(req.minRiskScore));
  const rows: Array<Record<string, unknown>> = await (q as unknown as { offset: (n: number) => { limit: (n: number) => { execute: () => Promise<Array<Record<string, unknown>>> } } }).offset(offset).limit(limit).execute().catch(() => []);

  return { pages: rows, total: rows.length, offset, limit };
}

async function cmdGetStats(sdk: HostSDK, _payload: Uint8Array): Promise<unknown> {
  const db = createKyselyDb((sdk.env as { HYPERDRIVE: unknown }).HYPERDRIVE);
  try {
    const sites = await (db.selectFrom("vertex_onion_site" as never).selectAll() as unknown as { execute: () => Promise<Array<Record<string, unknown>>> }).execute().catch(() => []);
    const pages = await (db.selectFrom("vertex_onion_page" as never).selectAll() as unknown as { execute: () => Promise<Array<Record<string, unknown>>> }).execute().catch(() => []);
    const reachableSites = sites.filter((s) => s.reachable === true || s.reachable === 1).length;
    const highRiskPages = pages.filter((p) => Number(p.risk_score ?? 0) >= 50).length;
    return { totalSites: sites.length, totalPages: pages.length, reachableSites, highRiskPages };
  } catch {
    return { totalSites: 0, totalPages: 0, reachableSites: 0, highRiskPages: 0 };
  }
}

// --- Reactive Pipeline ---
// malak.gftd.ai Follows onion.gftd.ai and receives onion.page / onion.site / onion.crawl
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
      nsid("ai.gftd.apps.onion.seedCrawl"),
      (_, b) => cmdSeedCrawl(sdk, b),
      asAgentTool("Enqueue one or more .onion URLs for the LangServer BPMN-contract onion_crawl_seeds worker (R/PT6H)"),
      withCapabilityTags("darkweb", "crawl", "onion", "tor", "enqueue"),
      withOCELEvent("onion.crawl.seeded"),
    )
    .command(
      nsid("ai.gftd.apps.onion.listSites"),
      (_, b) => cmdListSites(sdk, b),
      asAgentTool("List discovered .onion sites with risk scores and categories"),
      withCapabilityTags("darkweb", "list", "intelligence"),
    )
    .command(
      nsid("ai.gftd.apps.onion.listPages"),
      (_, b) => cmdListPages(sdk, b),
      asAgentTool("List crawled .onion pages, optionally filtered by host"),
      withCapabilityTags("darkweb", "list", "pages"),
    )
    .command(
      nsid("ai.gftd.apps.onion.getStats"),
      (_, b) => cmdGetStats(sdk, b),
      asAgentTool("Get onion.gftd.ai crawl statistics"),
      withCapabilityTags("darkweb", "stats"),
    );
});
