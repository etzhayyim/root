#!/usr/bin/env npx tsx
/**
 * Bulk domain data ingest pipeline.
 *
 * Reads local data from /Volumes/251220/domain-data/ and /Volumes/251220/graphResults/,
 * transforms into AT records, writes to PDS via XRPC.
 * Uses the shared Murakumo default model for entity extraction/enrichment.
 *
 * Usage:
 *   npx tsx scripts/ingest-domain-data.ts [--domain hanrei] [--limit 1000] [--dry-run]
 */
import { MURAKUMO_DEFAULT_MODEL } from "@etzhayyim/llm-models";
const PDS_URL = "https://atproto.etzhayyim.com";

// ADR-0023 P4: etzhayyim_TOKEN (sk_live_*) Bearer replaces spoofable
// x-magatama-verified header. Required for write operations.
const etzhayyim_TOKEN = process.env.etzhayyim_TOKEN;
if (!etzhayyim_TOKEN) {
  throw new Error("etzhayyim_TOKEN env var required — run `export etzhayyim_TOKEN=$(etzhayyim auth token)` first");
}
const AUTH_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${etzhayyim_TOKEN}`,
  "x-etzhayyim-org-id": "anon",
};
const MURAKUMO_URL = "https://murakumo.etzhayyim.com/api/openai/v1/chat/completions";
const DATA_BASE = "/Volumes/251220/domain-data";
const GRAPH_BASE = "/Volumes/251220/graphResults";

const CONCURRENCY = 4;  // Reduced to avoid overwhelming yata
const BATCH_SIZE = 50;
const THROTTLE_MS = 50; // 50ms between batches to give yata breathing room

// ── Domain → App mapping ──

interface DomainConfig {
  /** App nanoid */
  nanoid: string;
  /** AT Protocol collection prefix */
  collectionPrefix: string;
  /** Data sources to ingest */
  sources: DataSource[];
}

interface DataSource {
  /** Source type */
  type: "seed" | "rawJson" | "rawCsv" | "rawXml" | "jsonl" | "sql";
  /** File path (relative to DATA_BASE) */
  path: string;
  /** AT collection kind (camelCase) */
  kind: string;
  /** Parser function */
  parse: (data: string, limit: number) => Record<string, unknown>[];
  /** Optional: use murakumo for enrichment */
  enrich?: boolean;
}

// ── Parsers ──

function parseSeedJson(data: string, limit: number): Record<string, unknown>[] {
  const items = JSON.parse(data);
  return (Array.isArray(items) ? items : []).slice(0, limit);
}

function parseCsv(data: string, limit: number): Record<string, unknown>[] {
  const lines = data.trim().split("\n");
  return lines.slice(0, limit).map(line => {
    const parts = line.split(",");
    return { rank: parts[0], domain: parts[1] };
  });
}

function parseEgovLawsXml(data: string, limit: number): Record<string, unknown>[] {
  const json = JSON.parse(data);
  const xmlStr = json?.data?.rawXml ?? "";
  const laws: Record<string, unknown>[] = [];
  const re = /<LawId>([^<]+)<\/LawId>\s*<LawName>([^<]+)<\/LawName>\s*<LawNo>([^<]+)<\/LawNo>/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(xmlStr)) !== null && laws.length < limit) {
    laws.push({
      lawId: m[1],
      lawName: m[2],
      lawNo: m[3],
      source: "egov",
      sourceUrl: "https://laws.e-gov.go.jp/api/1",
      license: "CC BY 4.0",
      category: json?.categoryName ?? "",
      categoryJa: json?.categoryNameJa ?? "",
    });
  }
  return laws;
}

function barcodeDigits(value: string): string {
  return value.replace(/\D+/g, "");
}

function barcodeCheckDigitForBody(bodyDigits: string): number {
  let sum = 0;
  const reversed = bodyDigits.split("").reverse();
  for (let i = 0; i < reversed.length; i += 1) {
    const digit = Number(reversed[i] || "0");
    sum += digit * (i % 2 === 0 ? 3 : 1);
  }
  return (10 - (sum % 10)) % 10;
}

function classifyBarcode(raw: string): {
  valid: boolean;
  normalized: string;
  codeType: string;
  canonicalGtin14: string;
} {
  const normalized = barcodeDigits(raw);
  const codeType = normalized.length === 8 ? "gtin8"
    : normalized.length === 12 ? "upc"
    : normalized.length === 13 ? "ean_jan"
    : normalized.length === 14 ? "gtin14"
    : "unknown";
  if (!/^\d+$/.test(normalized) || ![8, 12, 13, 14].includes(normalized.length)) {
    return { valid: false, normalized, codeType, canonicalGtin14: "" };
  }
  const valid = barcodeCheckDigitForBody(normalized.slice(0, -1)) === Number(normalized.slice(-1));
  return {
    valid,
    normalized,
    codeType,
    canonicalGtin14: valid ? normalized.padStart(14, "0") : "",
  };
}

function parseGtinProducts(data: string, limit: number): Record<string, unknown>[] {
  const json = JSON.parse(data);
  const products = json?.products ?? [];
  return products.slice(0, limit).map((p: any) => {
    const barcode = String(p.code ?? "");
    const classified = classifyBarcode(barcode);
    return {
      barcode,
      gtin: classified.valid ? classified.normalized : "",
      jan: classified.valid && classified.codeType === "ean_jan" ? classified.normalized : "",
      upc: classified.valid && classified.codeType === "upc" ? classified.normalized : "",
      ean: classified.valid && classified.codeType === "ean_jan" ? classified.normalized : "",
      canonicalGtin14: classified.canonicalGtin14,
      barcodeType: classified.codeType,
      barcodeValid: classified.valid,
      productName: p.productName ?? "",
      brands: p.brands ?? "",
      categories: p.categories ?? "",
      countries: p.countries ?? "",
      nutritionGrade: p.nutritionGrades ?? "",
    };
  });
}

function parseOsmPoi(data: string, limit: number): Record<string, unknown>[] {
  const json = JSON.parse(data);
  const elements = json?.elements ?? [];
  return elements.slice(0, limit).map((e: any) => ({
    osmId: String(e.id),
    lat: String(e.lat ?? ""),
    lon: String(e.lon ?? ""),
    name: e.tags?.name ?? "",
    amenity: e.tags?.amenity ?? "",
    address: e.tags?.["addr:street"] ?? "",
    city: e.tags?.["addr:city"] ?? "",
  }));
}

function parseJsonl(data: string, limit: number): Record<string, unknown>[] {
  return data.trim().split("\n").slice(0, limit).filter(Boolean).map(line => JSON.parse(line));
}

function parseMusicBrainz(data: string, limit: number): Record<string, unknown>[] {
  const json = JSON.parse(data);
  const releases = json?.releases ?? json?.artists ?? [];
  return releases.slice(0, limit).map((r: any) => ({
    mbid: r.id ?? "",
    name: r.title ?? r.name ?? "",
    type: r.type ?? r["primary-type"] ?? "",
    date: r.date ?? "",
    country: r.country ?? "",
    score: String(r.score ?? "0"),
  }));
}

function parseNdcDrug(data: string, limit: number): Record<string, unknown>[] {
  const items = JSON.parse(data);
  return (Array.isArray(items) ? items : []).slice(0, limit);
}

function parseBlockchain(data: string, limit: number): Record<string, unknown>[] {
  const json = JSON.parse(data);
  return (Array.isArray(json) ? json : []).slice(0, limit).map((c: any) => ({
    coinId: c.id ?? "",
    symbol: c.symbol ?? "",
    name: c.name ?? "",
    platforms: JSON.stringify(c.platforms ?? {}),
  }));
}

function parseTreatyItems(data: string, limit: number): Record<string, unknown>[] {
  return parseSeedJson(data, limit);
}

function parseDemaeRestaurants(data: string, limit: number): Record<string, unknown>[] {
  const json = JSON.parse(data);
  const elements = json?.elements ?? [];
  return elements.slice(0, limit).map((e: any) => ({
    osmId: String(e.id),
    lat: String(e.lat ?? ""),
    lon: String(e.lon ?? ""),
    name: e.tags?.name ?? "",
    cuisine: e.tags?.cuisine ?? "",
    amenity: e.tags?.amenity ?? "",
    city: e.tags?.["addr:city"] ?? "",
  }));
}

// ── Domain configs ──

const DOMAINS: Record<string, DomainConfig> = {
  hanrei: {
    nanoid: "h4nr31jp",
    collectionPrefix: "com.etzhayyim.apps.hanrei",
    sources: [
      { type: "seed", path: "domains/hanrei/seed.json", kind: "court", parse: parseSeedJson },
      { type: "rawJson", path: "hanrei/egov/lawlist1Constitution20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
      { type: "rawJson", path: "hanrei/egov/lawlist2Act20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
      { type: "rawJson", path: "hanrei/egov/lawlist3CabinetOrder20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
      { type: "rawJson", path: "hanrei/egov/lawlist4ImperialOrder20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
      { type: "rawJson", path: "hanrei/egov/lawlist5MinisterialOrder20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
      { type: "rawJson", path: "hanrei/egov/lawlist6CabinetOfficialOrder20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
      { type: "rawJson", path: "hanrei/egov/lawlist7Rule20260328234616.json", kind: "egovLaw", parse: parseEgovLawsXml, enrich: true },
    ],
  },
  dns: {
    nanoid: "scndu0rf",
    collectionPrefix: "com.etzhayyim.apps.dns",
    sources: [
      { type: "seed", path: "domains/dns/seed.json", kind: "tld", parse: parseSeedJson },
      { type: "rawCsv", path: "dns/top-1m.csv", kind: "domain", parse: parseCsv },
    ],
  },
  legalEntity: {
    nanoid: "le01corp0",
    collectionPrefix: "com.etzhayyim.apps.legalEntity",
    sources: [
      { type: "seed", path: "domains/legalEntity/seed.json", kind: "jurisdiction", parse: parseSeedJson },
    ],
  },
  gtin: {
    nanoid: "gt1n4k7m",
    collectionPrefix: "com.etzhayyim.apps.gtin",
    sources: [
      { type: "seed", path: "domains/gtin/seed.json", kind: "prefixRange", parse: parseSeedJson },
    ],
  },
  isbn: {
    nanoid: "bn7k2m4x",
    collectionPrefix: "com.etzhayyim.apps.isbn",
    sources: [
      { type: "seed", path: "domains/isbn/seed.json", kind: "isbnGroup", parse: parseSeedJson },
    ],
  },
  pachinko: {
    nanoid: "k3rn5la4",
    collectionPrefix: "com.etzhayyim.apps.pachinko",
    sources: [
      { type: "seed", path: "domains/pachinko/seed.json", kind: "prefectureStore", parse: parseSeedJson },
    ],
  },
  autorace: {
    nanoid: "zcv937fk",
    collectionPrefix: "com.etzhayyim.apps.autorace",
    sources: [
      { type: "seed", path: "domains/autorace/seed.json", kind: "venue", parse: parseSeedJson },
    ],
  },
  keirin: {
    nanoid: "zub804qz",
    collectionPrefix: "com.etzhayyim.apps.keirin",
    sources: [
      { type: "seed", path: "domains/keirin/seed.json", kind: "velodrome", parse: parseSeedJson },
    ],
  },
  kyotei: {
    nanoid: "qv8yed1k",
    collectionPrefix: "com.etzhayyim.apps.kyotei",
    sources: [
      { type: "seed", path: "domains/kyotei/seed.json", kind: "boatRaceVenue", parse: parseSeedJson },
    ],
  },
  isin: {
    nanoid: "is1n8k2x",
    collectionPrefix: "com.etzhayyim.apps.isin",
    sources: [
      { type: "seed", path: "domains/isin/seed.json", kind: "nna", parse: parseSeedJson },
    ],
  },
  maps: {
    nanoid: "v1m9k2q8",
    collectionPrefix: "com.etzhayyim.apps.maps",
    sources: [
      { type: "seed", path: "domains/maps/seed.json", kind: "country", parse: parseSeedJson },
    ],
  },
  ndc: {
    nanoid: "nd7c3k9m",
    collectionPrefix: "com.etzhayyim.apps.ndc",
    sources: [
      { type: "seed", path: "domains/ndc/seed.json", kind: "atcLevel1", parse: parseSeedJson },
    ],
  },
  anima: {
    nanoid: "czj1f6yv",
    collectionPrefix: "com.etzhayyim.apps.anima",
    sources: [
      { type: "seed", path: "domains/anima/seed.json", kind: "kingdom", parse: parseSeedJson },
    ],
  },
  blockchain: {
    nanoid: "blkchn01",
    collectionPrefix: "com.etzhayyim.apps.blockchain",
    sources: [
      { type: "seed", path: "domains/blockchain/seed.json", kind: "chain", parse: parseSeedJson },
      { type: "rawJson", path: "blockchain/coingeckoCoinList.json", kind: "coin", parse: parseBlockchain },
    ],
  },
  treaty: {
    nanoid: "tr3aty01",
    collectionPrefix: "com.etzhayyim.apps.treaty",
    sources: [
      { type: "seed", path: "domains/treaty/seed.json", kind: "chapter", parse: parseTreatyItems },
    ],
  },
  chotatsu: {
    nanoid: "ch0t4ts1",
    collectionPrefix: "com.etzhayyim.apps.chotatsu",
    sources: [
      { type: "seed", path: "domains/chotatsu/seed.json", kind: "procurementNotice", parse: parseSeedJson },
    ],
  },
  cas: {
    nanoid: "cs4r7n2k",
    collectionPrefix: "com.etzhayyim.apps.cas",
    sources: [
      { type: "seed", path: "domains/cas/seed.json", kind: "substance", parse: parseSeedJson },
    ],
  },
  isco: {
    nanoid: "wfc8k3n1",
    collectionPrefix: "com.etzhayyim.apps.isco",
    sources: [
      { type: "seed", path: "domains/isco/seed.json", kind: "majorGroup", parse: parseSeedJson },
    ],
  },
  isic: {
    nanoid: "1s1c5c0a",
    collectionPrefix: "com.etzhayyim.apps.isic",
    sources: [
      { type: "seed", path: "domains/isic/seed.json", kind: "section", parse: parseSeedJson },
    ],
  },
  sovereign: {
    nanoid: "", // No app yet, write as graph entity
    collectionPrefix: "com.etzhayyim.apps.sovereign",
    sources: [
      { type: "seed", path: "domains/sovereign/seed.json", kind: "state", parse: parseSeedJson },
    ],
  },
};

// ── Raw data expansion (large files) ──

interface RawDataExpansion {
  domain: string;
  globPattern: string;
  kind: string;
  parse: (data: string, limit: number) => Record<string, unknown>[];
}

const RAW_EXPANSIONS: RawDataExpansion[] = [
  // GTIN: OpenFoodFacts bulk pages
  ...["snacks", "beverages", "dairies", "cereals", "meats", "fruits", "vegetables", "seafood", "sweets", "breads"].map(cat => ({
    domain: "gtin",
    globPattern: `gtin/openfoodfacts/${cat}/page_*.json`,
    kind: "product",
    parse: parseGtinProducts,
  })),
  // Maps: OSM POI per city
  ...["tokyo", "osaka", "newYork", "london", "paris", "berlin", "singapore", "sydney"].map(city => ({
    domain: "maps",
    globPattern: `maps/osmPoi/${city}/*.json`,
    kind: "poi",
    parse: parseOsmPoi,
  })),
  // Music: MusicBrainz releases
  { domain: "isbn", globPattern: "music/musicbrainz/releases/*.json", kind: "musicRelease", parse: parseMusicBrainz },
  // Demae: restaurant data
  ...["tokyo", "osaka", "newYork", "london", "paris", "berlin", "singapore", "sydney", "seoul", "bangkok"].map(city => ({
    domain: "maps",
    globPattern: `demae/${city}_restaurants.json`,
    kind: "restaurant",
    parse: parseDemaeRestaurants,
  })),
  // NDC: drug text data
  { domain: "ndc", globPattern: "domains/ndc/text/*.json", kind: "drugEntry", parse: parseNdcDrug },
  // Graph results (pre-processed entities)
  { domain: "hanrei", globPattern: "", kind: "graphEntity", parse: parseJsonl },
];

// ── Murakumo LLM enrichment ──

interface MurakumoResponse {
  choices: { message: { content: string } }[];
}

/** Murakumo job queue — retry with exponential backoff when fleet is busy. */
const MURAKUMO_API_KEY = process.env.MURAKUMO_API_KEY ?? "";
const MURAKUMO_MAX_RETRIES = 10;
const MURAKUMO_BASE_DELAY_MS = 5000; // 5s initial, then 10s, 20s, ...
let murakumoQueueDepth = 0;
let murakumoTotalProcessed = 0;
let murakumoTotalFailed = 0;

async function murakumoCallWithRetry(
  systemPrompt: string,
  userPrompt: string,
  model = MURAKUMO_DEFAULT_MODEL,
): Promise<string | null> {
  if (!MURAKUMO_API_KEY) {
    throw new Error("MURAKUMO_API_KEY env var required");
  }
  for (let attempt = 0; attempt < MURAKUMO_MAX_RETRIES; attempt++) {
    try {
      const resp = await fetch(MURAKUMO_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": MURAKUMO_API_KEY,
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt },
          ],
          temperature: 0.1,
          maxTokens: 4096,
        }),
      });

      if (resp.ok) {
        const json = await resp.json() as MurakumoResponse;
        murakumoTotalProcessed++;
        return json.choices?.[0]?.message?.content ?? null;
      }

      const body = await resp.text().catch((error) => {
        console.warn("  [murakumo] failed to read error response body:", (error as Error).message?.slice(0, 80));
        return "";
      });

      // Fleet busy — queue and retry with backoff
      if (resp.status === 503 || body.includes("busy") || body.includes("no available workers")) {
        const delay = MURAKUMO_BASE_DELAY_MS * Math.pow(2, Math.min(attempt, 5));
        murakumoQueueDepth++;
        if (attempt === 0) process.stdout.write(`\n  [murakumo-queue] fleet busy, queuing (depth=${murakumoQueueDepth})...`);
        else process.stdout.write(`.`);
        await sleep(delay);
        murakumoQueueDepth = Math.max(0, murakumoQueueDepth - 1);
        continue;
      }

      // Auth or other error — don't retry
      console.warn(`  [murakumo] ${resp.status}: ${body.slice(0, 80)}`);
      murakumoTotalFailed++;
      return null;
    } catch (err) {
      const delay = MURAKUMO_BASE_DELAY_MS * Math.pow(2, Math.min(attempt, 5));
      if (attempt < MURAKUMO_MAX_RETRIES - 1) {
        await sleep(delay);
        continue;
      }
      console.warn(`  [murakumo] error after ${MURAKUMO_MAX_RETRIES} retries:`, (err as Error).message?.slice(0, 80));
      murakumoTotalFailed++;
      return null;
    }
  }
  murakumoTotalFailed++;
  return null;
}

async function murakumoEnrich(records: Record<string, unknown>[], kind: string): Promise<Record<string, unknown>[]> {
  const batchText = records.map((r, i) => `[${i}] ${JSON.stringify(r)}`).join("\n");
  const systemPrompt = `You are an entity extraction assistant. For each record, extract and add:
- summaryJa: 1-line Japanese summary
- summaryEn: 1-line English summary
- keywords: array of 3-5 keywords
- category: primary category
Return a JSON array of enriched records. Keep all original fields.`;

  const content = await murakumoCallWithRetry(
    systemPrompt,
    `Enrich these ${kind} records:\n${batchText}`,
  );

  if (!content) return records;

  const cleaned = content.startsWith("```") ? content.slice(content.indexOf("\n") + 1).replace(/```\s*$/, "").trim() : content.trim();
  try {
    const enriched = JSON.parse(cleaned);
    if (Array.isArray(enriched) && enriched.length === records.length) return enriched;
  } catch { /* fallback to original */ }
  return records;
}

// ── PDS XRPC writer ──

interface CreateRecordResult {
  uri: string;
  cid: string;
  rkey: string;
}

let totalWritten = 0;
let totalErrors = 0;

async function writeRecordToPDS(
  repo: string,
  collection: string,
  record: Record<string, unknown>,
): Promise<CreateRecordResult | null> {
  try {
    const resp = await fetch(`${PDS_URL}/xrpc/com.atproto.repo.createRecord`, {
      method: "POST",
      headers: AUTH_HEADERS,
      body: JSON.stringify({ repo, collection, record }),
    });

    if (!resp.ok) {
      const text = await resp.text().catch((error) => {
        console.warn("  [pds] failed to read error response body:", (error as Error).message?.slice(0, 80));
        return "";
      });
      if (resp.status === 429) {
        await sleep(2000);
        return writeRecordToPDS(repo, collection, record); // retry once
      }
      console.warn(`  [pds] ${resp.status}: ${text.slice(0, 100)}`);
      totalErrors++;
      return null;
    }

    totalWritten++;
    return await resp.json() as CreateRecordResult;
  } catch (err) {
    console.warn(`  [pds] error: ${(err as Error).message?.slice(0, 80)}`);
    totalErrors++;
    return null;
  }
}

async function writeBatch(
  repo: string,
  collection: string,
  records: Record<string, unknown>[],
): Promise<number> {
  let written = 0;
  // Process in chunks with concurrency control
  for (let i = 0; i < records.length; i += CONCURRENCY) {
    const chunk = records.slice(i, i + CONCURRENCY);
    const results = await Promise.all(
      chunk.map(rec => writeRecordToPDS(repo, collection, {
        ...rec,
        orgId: "anon",
        userId: "anon",
        actorId: repo,
        createdAt: new Date().toISOString(),
      })),
    );
    written += results.filter(Boolean).length;
    if (i > 0 && i % 100 === 0) process.stdout.write(`  ${i}/${records.length}...`);
    if (THROTTLE_MS > 0) await sleep(THROTTLE_MS);
  }
  return written;
}

// ── Graph results ingest ──

async function ingestGraphResults(dryRun: boolean, limit: number): Promise<number> {
  const fs = await import("fs");
  const path = await import("path");

  const sqlFiles = [
    "graphEntitiesQwen4b.sql",
    "did-graph-ingest-20260331.sql",
    "domain-data-legalEntity-20260331.sql",
    "domain-data-legalEntity.sql",
    "domain-data-manual-ingest.sql",
  ];

  let total = 0;

  for (const file of sqlFiles) {
    const filePath = path.join(GRAPH_BASE, file);
    if (!fs.existsSync(filePath)) continue;

    const content = fs.readFileSync(filePath, "utf-8");
    const lines = content.trim().split("\n").filter(l => l.startsWith("MERGE") || l.startsWith("MATCH"));
    console.log(`  ${file}: ${lines.length} SQL statements`);

    if (dryRun) {
      total += lines.length;
      continue;
    }

    // Execute SQL statements via PDS
    for (let i = 0; i < Math.min(lines.length, limit); i += CONCURRENCY) {
      const batch = lines.slice(i, i + CONCURRENCY);
      await Promise.all(batch.map(async (stmt) => {
        try {
          const resp = await fetch(`${PDS_URL}/xrpc/com.etzhayyim.kagami.sql`, {
            method: "POST",
            headers: AUTH_HEADERS,
            body: JSON.stringify({ sql: stmt, appId: "" }),
          });
          if (resp.ok) total++;
          else console.warn(`  [sql] ${resp.status}`);
        } catch (err) {
          console.warn(`  [sql] error: ${(err as Error).message?.slice(0, 60)}`);
        }
      }));
    }
  }

  // JSONL graph entities
  const jsonlFiles = ["graphEntitiesQwen4b.jsonl", "asher.jsonl", "issachar.jsonl", "joseph.jsonl", "judah.jsonl", "simeon.jsonl", "zebulun.jsonl"];
  for (const file of jsonlFiles) {
    const filePath = path.join(GRAPH_BASE, file);
    if (!fs.existsSync(filePath)) continue;
    const content = fs.readFileSync(filePath, "utf-8").trim();
    if (!content) continue;
    const items = content.split("\n").filter(Boolean).slice(0, limit);
    console.log(`  ${file}: ${items.length} entities`);
    if (dryRun) { total += items.length; continue; }

    for (const line of items) {
      try {
        const entity = JSON.parse(line);
        await writeRecordToPDS(
          `did:web:graph.etzhayyim.com`,
          "com.etzhayyim.apps.graph.entity",
          { ...entity, orgId: "anon", userId: "anon", actorId: "graph", createdAt: new Date().toISOString() },
        );
        total++;
      } catch { /* skip malformed */ }
    }
  }

  return total;
}

// ── Helpers ──

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function findFiles(pattern: string): Promise<string[]> {
  const fs = await import("fs");
  const path = await import("path");

  // Simple glob: split on *, scan directory, filter by extension
  const fullPattern = path.join(DATA_BASE, pattern);
  const parts = fullPattern.split("*");
  const dir = parts[0].replace(/\/$/, "");
  const ext = parts.length > 1 ? parts[parts.length - 1] : "";

  if (!fs.existsSync(dir)) return [];

  try {
    const files = fs.readdirSync(dir);
    return files
      .filter((f: string) => !ext || f.endsWith(ext.replace(/^\//, "")))
      .map((f: string) => path.join(dir, f))
      .filter((f: string) => fs.statSync(f).isFile());
  } catch {
    return [];
  }
}

// ── Main ──

async function main() {
  const fs = await import("fs");
  const path = await import("path");

  const args = process.argv.slice(2);
  const domainFilter = args.includes("--domain") ? args[args.indexOf("--domain") + 1] : null;
  const limit = args.includes("--limit") ? parseInt(args[args.indexOf("--limit") + 1]) : 10000;
  const dryRun = args.includes("--dry-run");
  const skipLlm = args.includes("--skip-llm");
  const enrichBatchSize = 10;

  console.log("═══════════════════════════════════════════════════");
  console.log("  Domain Data Ingest Pipeline");
  console.log("  PDS:", PDS_URL);
  console.log("  Murakumo:", MURAKUMO_URL, `(${MURAKUMO_DEFAULT_MODEL})`);
  console.log("  Limit:", limit, "per source");
  console.log("  Dry run:", dryRun);
  console.log("  Domain filter:", domainFilter ?? "all");
  console.log("═══════════════════════════════════════════════════\n");

  const results: { domain: string; kind: string; count: number; enriched: boolean }[] = [];
  const enrichmentJobs: { jobId: string; domain: string; kind: string; count: number }[] = [];

  // 1. Process seed + raw data per domain
  for (const [domainName, config] of Object.entries(DOMAINS)) {
    if (domainFilter && domainFilter !== domainName) continue;
    if (!config.nanoid) {
      console.log(`[SKIP] ${domainName}: no nanoid`);
      continue;
    }

    const repo = `did:web:${config.nanoid}.etzhayyim.com`;
    console.log(`\n── ${domainName} (${repo}) ──`);

    for (const source of config.sources) {
      const filePath = path.join(DATA_BASE, source.path);
      if (!fs.existsSync(filePath)) {
        console.log(`  [SKIP] ${source.path}: file not found`);
        continue;
      }

      const data = fs.readFileSync(filePath, "utf-8");
      let records = source.parse(data, limit);
      console.log(`  ${source.kind}: ${records.length} records from ${source.path}`);

      if (records.length === 0) continue;

      // LLM enrichment: write enrichment jobs to PDS queue (murakumo processes async)
      if (source.enrich && !skipLlm && !dryRun) {
        const jobId = `enrich-${domainName}-${source.kind}-${Date.now()}`;
        console.log(`  [murakumo-job] queuing enrichment job ${jobId} (${records.length} records)`);
        await writeRecordToPDS(repo, `${config.collectionPrefix}.enrichmentJob`, {
          id: jobId,
          kind: source.kind,
          model: MURAKUMO_DEFAULT_MODEL,
          recordCount: records.length,
          status: "pending",
          orgId: "anon",
          userId: "anon",
          actorId: repo,
          createdAt: new Date().toISOString(),
        });
        enrichmentJobs.push({ jobId, domain: domainName, kind: source.kind, count: records.length });
      }

      if (dryRun) {
        console.log(`  [DRY RUN] would write ${records.length} records to ${config.collectionPrefix}.${source.kind}`);
        results.push({ domain: domainName, kind: source.kind, count: records.length, enriched: !!source.enrich });
        continue;
      }

      const collection = `${config.collectionPrefix}.${source.kind}`;
      const written = await writeBatch(repo, collection, records);
      console.log(`  -> wrote ${written}/${records.length} to ${collection}`);
      results.push({ domain: domainName, kind: source.kind, count: written, enriched: !!source.enrich });
    }
  }

  // 2. Process raw data expansions (large files)
  if (!domainFilter || RAW_EXPANSIONS.some(e => e.domain === domainFilter)) {
    console.log("\n── Raw Data Expansions ──");
    for (const expansion of RAW_EXPANSIONS) {
      if (domainFilter && expansion.domain !== domainFilter) continue;
      const config = DOMAINS[expansion.domain];
      if (!config?.nanoid) continue;

      if (expansion.globPattern) {
        const files = await findFiles(expansion.globPattern);
        if (files.length === 0) continue;

        const repo = `did:web:${config.nanoid}.etzhayyim.com`;
        const collection = `${config.collectionPrefix}.${expansion.kind}`;
        let totalForExpansion = 0;

        console.log(`  ${expansion.domain}/${expansion.kind}: ${files.length} files`);

        for (const file of files) {
          if (totalForExpansion >= limit) break;
          try {
            const data = fs.readFileSync(file, "utf-8");
            const remaining = limit - totalForExpansion;
            const records = expansion.parse(data, remaining);
            if (records.length === 0) continue;

            if (dryRun) {
              totalForExpansion += records.length;
              continue;
            }

            const written = await writeBatch(repo, collection, records);
            totalForExpansion += written;
          } catch (err) {
            console.warn(`    [error] ${path.basename(file)}: ${(err as Error).message?.slice(0, 60)}`);
          }
        }
        if (totalForExpansion > 0) {
          console.log(`  -> ${expansion.domain}/${expansion.kind}: ${totalForExpansion} records`);
          results.push({ domain: expansion.domain, kind: expansion.kind, count: totalForExpansion, enriched: false });
        }
      }
    }
  }

  // 3. Process graph results
  if (!domainFilter || domainFilter === "graph") {
    console.log("\n── Graph Results ──");
    const graphTotal = await ingestGraphResults(dryRun, limit);
    if (graphTotal > 0) {
      results.push({ domain: "graph", kind: "entity", count: graphTotal, enriched: false });
    }
  }

  // 4. Process murakumo enrichment job queue
  if (enrichmentJobs.length > 0 && !dryRun) {
    console.log(`\n── Murakumo Enrichment Queue (${enrichmentJobs.length} jobs) ──`);
    for (const job of enrichmentJobs) {
      const config = DOMAINS[job.domain];
      if (!config) continue;
      const repo = `did:web:${config.nanoid}.etzhayyim.com`;
      const collection = `${config.collectionPrefix}.${job.kind}`;

      console.log(`  [job] ${job.jobId}: ${job.count} ${job.kind} records`);

      // Re-read the records we just wrote (query from PDS)
      // For simplicity, re-read from local files and enrich
      const source = config.sources.find(s => s.kind === job.kind && s.enrich);
      if (!source) continue;

      const filePath = (await import("path")).join(DATA_BASE, source.path);
      const fs = await import("fs");
      if (!fs.existsSync(filePath)) continue;

      const data = fs.readFileSync(filePath, "utf-8");
      const records = source.parse(data, limit);
      let enrichedCount = 0;

      // Process in batches through murakumo queue
      for (let i = 0; i < records.length; i += enrichBatchSize) {
        const batch = records.slice(i, i + enrichBatchSize);
        const enriched = await murakumoEnrich(batch, job.kind);

        // Write enriched records as separate collection
        for (const rec of enriched) {
          await writeRecordToPDS(repo, `${config.collectionPrefix}.${job.kind}Enriched`, {
            ...rec,
            enrichmentJobId: job.jobId,
            enrichedModel: MURAKUMO_DEFAULT_MODEL,
            orgId: "anon",
            userId: "anon",
            actorId: repo,
            createdAt: new Date().toISOString(),
          });
          enrichedCount++;
        }

        if (i > 0 && i % 50 === 0) process.stdout.write(`    ${i}/${records.length}...`);
      }

      // Update job status
      await writeRecordToPDS(repo, `${config.collectionPrefix}.enrichmentJob`, {
        id: job.jobId,
        kind: job.kind,
        model: MURAKUMO_DEFAULT_MODEL,
        recordCount: job.count,
        enrichedCount,
        status: enrichedCount > 0 ? "complete" : "failed",
        orgId: "anon",
        userId: "anon",
        actorId: repo,
        completedAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      });
      console.log(`  [job] ${job.jobId}: enriched ${enrichedCount}/${job.count}`);
      results.push({ domain: job.domain, kind: `${job.kind}Enriched`, count: enrichedCount, enriched: true });
    }
  }

  // Summary
  console.log("\n═══════════════════════════════════════════════════");
  console.log("  INGEST SUMMARY");
  console.log("═══════════════════════════════════════════════════");
  let grandTotal = 0;
  for (const r of results) {
    const enrichTag = r.enriched ? " [murakumo enriched]" : "";
    console.log(`  ${r.domain}.${r.kind}: ${r.count}${enrichTag}`);
    grandTotal += r.count;
  }
  console.log("───────────────────────────────────────────────────");
  console.log(`  Total records: ${grandTotal}`);
  console.log(`  PDS written: ${totalWritten}, PDS errors: ${totalErrors}`);
  console.log(`  Murakumo processed: ${murakumoTotalProcessed}, failed: ${murakumoTotalFailed}`);
  console.log("═══════════════════════════════════════════════════");
}

main().catch(err => {
  console.error("Fatal:", err);
  process.exit(1);
});
