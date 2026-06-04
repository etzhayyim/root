import * as fs from "node:fs";
import * as path from "node:path";

const DEFAULT_ENDPOINT = "https://yabai.etzhayyim.com";
const SERVICE_PATH = "/xrpc/etzhayyim.yabai.v1.YabaiService";
const BATCH_SIZE = 5;

async function main(): Promise<void> {
  const endpoint = process.argv[2] ?? DEFAULT_ENDPOINT;

  const repoRoot = findRepoRoot();
  const contentDir = path.join(repoRoot, "projects", "etzhayyim-project-yabai", "content");
  const watchlistPath = path.join(contentDir, "source", "watchlist.jsonld");

  // ── 1. Load watchlist ──
  const wlData = fs.readFileSync(watchlistPath, "utf-8");
  const wl = JSON.parse(wlData) as Record<string, unknown>;

  // ── 2. Seed data sources as YabaiSource entities ──
  const dataSources = (wl.dataSources ?? []) as Record<string, unknown>[];
  console.log(`Seeding ${dataSources.length} data sources as YabaiSource entities...`);

  for (const ds of dataSources) {
    const sourceID = getString(ds, "id");
    const sourceName = getString(ds, "name");
    const sourceURL = getString(ds, "url");
    const sourceFormat = getString(ds, "format");
    if (!sourceID || !sourceName) continue;

    try {
      const resp = await callAPI(endpoint, "IngestEntity", {
        'entityId': "src-" + sourceID.replaceAll("/", "-"),
        'entityType': "DataSource",
        'canonicalName': sourceName,
        aliases: [sourceID],
        websites: [sourceURL],
        evidences: [
          {
            category: "SourceRegistration",
            source: "yabai/registry",
            'sourceReliability': "A",
            jurisdiction: jurisdictionFromSource(sourceID),
            confidence: 0.99,
            severity: 1,
            summary: `Authoritative sanctions data source: ${sourceName} (format: ${sourceFormat})`,
          },
        ],
      });
      console.log(`  + ${sourceID} -> ${getString(resp, "entityId")}`);
    } catch (err) {
      console.error(`  source ${sourceID}: error ${err}`);
    }
  }

  // ── 3. Seed watchlist signals as entities via IngestBatch ──
  const signals = (wl.signals ?? []) as Record<string, unknown>[];
  console.log(`\nSeeding ${signals.length} watchlist entities in batches of ${BATCH_SIZE}...`);

  let total = 0;
  let success = 0;
  let errors = 0;

  for (let i = 0; i < signals.length; i += BATCH_SIZE) {
    const batch = signals.slice(i, i + BATCH_SIZE);
    const entities: Record<string, unknown>[] = [];

    for (const sig of batch) {
      const value = getString(sig, "value");
      const entityType = getString(sig, "entityType");
      const category = getString(sig, "category");
      const source = getString(sig, "source");
      const jurisdiction = getString(sig, "jurisdiction");
      const confidence = getFloat(sig, "confidence", 0.95);
      const severity = getFloat(sig, "severity", 5);

      // Compute risk inline
      let pen = severity * confidence * 20.0;
      if (pen > 100) pen = 100;
      let wb = 100.0 - pen * 0.6;
      if (wb < 0) wb = 0;
      let yr = 100.0 - wb + pen * 0.8;
      if (yr > 100) yr = 100;
      if (yr < 0) yr = 0;

      // Pack evidence+risk into contacts field for persistence
      const packed = JSON.stringify({
        ev: [
          {
            category,
            source,
            confidence,
            severity,
            jurisdiction,
            summary: `${jurisdiction} designation from ${source}`,
          },
        ],
        rk: {
          'wellBecomingScore': wb,
          'penaltyScore': pen,
          'yabaiRiskScore': yr,
          'infoRisk': 0,
        },
      });

      entities.push({
        'entityType': entityType,
        'canonicalName': value,
        aliases: [value],
        contacts: [packed],
        evidences: [
          {
            category,
            source,
            'sourceReliability': "A",
            jurisdiction,
            confidence,
            severity,
            summary: `${jurisdiction} designation from ${source}`,
          },
        ],
      });
    }

    let resp: Record<string, unknown> | null = null;
    let callErr: unknown = null;

    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        resp = await callAPI(endpoint, "IngestBatch", { entities });
        callErr = null;
        break;
      } catch (err) {
        callErr = err;
        await sleep(2000 * (attempt + 1));
      }
    }

    if (callErr) {
      console.error(`  batch ${i}-${i + batch.length}: error ${callErr}`);
      errors += batch.length;
      continue;
    }

    const batchSuccess = getInt(resp!, "success");
    const batchErrors = getInt(resp!, "errors");
    success += batchSuccess;
    errors += batchErrors;
    total += batch.length;

    const batchIndex = Math.floor(i / BATCH_SIZE);
    if (batchIndex % 20 === 0 || i + batch.length === signals.length) {
      console.log(`  [${i + batch.length}/${signals.length}] success=${success} errors=${errors}`);
    }

    // pace requests to avoid WASM memory pressure
    await sleep(200);
  }

  // ── 4. Create Source->Entity edges ──
  console.log(`\nCreating Source->Entity SOURCED_FROM edges...`);
  let edgeCount = 0;

  for (const sig of signals) {
    const source = getString(sig, "source");
    const parts = source.split("/");
    const sourcePrefix = parts.length > 1 ? parts.slice(0, 2).join("/") : parts[0];

    let sourceEntityID = "";
    for (const ds of dataSources) {
      const dsID = getString(ds, "id");
      if (source.startsWith(dsID) || dsID === sourcePrefix) {
        sourceEntityID = "src-" + dsID.replaceAll("/", "-");
        break;
      }
    }
    if (!sourceEntityID) continue;
    edgeCount++;
  }

  // ── 5. Build graph relationships ──
  console.log(`\nBuilding graph relationships...`);
  try {
    const resp = await callAPI(endpoint, "BuildGraph", {});
    console.log(`  edgesCreated=${resp.edgesCreated}`);
  } catch (err) {
    console.error(`  BuildGraph error: ${err}`);
  }

  console.log(`\n=== Summary ===`);
  console.log(`Total signals: ${total}`);
  console.log(`Success: ${success}`);
  console.log(`Errors: ${errors}`);
  console.log(`Data sources: ${dataSources.length}`);
  console.log(`Source->Entity potential edges: ${edgeCount}`);
}

async function callAPI(endpoint: string, method: string, body: Record<string, unknown>): Promise<Record<string, unknown>> {
  const url = endpoint + SERVICE_PATH + "/" + method;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Connect-Protocol-Version": "1",
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30_000),
  });

  const respBody = await resp.text();
  if (!resp.ok) {
    throw new Error(`status ${resp.status}: ${respBody.substring(0, 200)}`);
  }

  return JSON.parse(respBody) as Record<string, unknown>;
}

function jurisdictionFromSource(src: string): string {
  if (src.startsWith("ofac") || src.startsWith("justice")) return "US";
  if (src.startsWith("un")) return "UN";
  if (src.startsWith("eu")) return "EU";
  if (src.startsWith("uk")) return "UK";
  if (src.startsWith("mof") || src.startsWith("meti")) return "JP";
  return "";
}

function getString(m: Record<string, unknown>, key: string): string {
  const v = m[key];
  return typeof v === "string" ? v : "";
}

function getFloat(m: Record<string, unknown>, key: string, def: number): number {
  const v = m[key];
  return typeof v === "number" ? v : def;
}

function getInt(m: Record<string, unknown>, key: string): number {
  const v = m[key];
  return typeof v === "number" ? Math.trunc(v) : 0;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function findRepoRoot(): string {
  let dir = process.cwd();
  while (true) {
    if (fs.existsSync(path.join(dir, ".git"))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) throw new Error("repo root not found");
    dir = parent;
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
