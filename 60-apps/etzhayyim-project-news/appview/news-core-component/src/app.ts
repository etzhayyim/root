import {
  createWorkerExport,
  nowISO,
  str,
  createKyselyDb,
  sql,
  asAgentTool,
  withCapabilityTags,
  resolveHeartbeatCadence,
  createCadenceState,
  createInboxBuffer,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/magatama-host-sdk";

const APP_NANOID = "nwscr001";
const cadenceState = createCadenceState();
const inbox = createInboxBuffer();

// ── RSS Source Registry ──────────────────────────────────────────────────────

interface RssSource {
  id: string;
  name: string;
  lang: string; // ISO 639-1 source language
  categories: string[];
  feedUrl: string;
}

interface IntelSource {
  id: string;
  name: string;
  region: string;
  country: string;
  topics: string[];
  sourceType: string;
  official: boolean;
  primary: boolean;
  url: string;
}

interface LiveAudioSource {
  sourceId: string;
  sourceName: string;
  streamUrl: string;
  sourceUrl: string;
  sourceType: string;
  region: string;
  country: string;
  topic: string;
  topics: string[];
  lang: string;
  captureSeconds: number;
  maxBytes: number;
  cadenceSeconds: number;
  cooldownSeconds: number;
  retainAudio: boolean;
  retentionDays: number;
  rightsPolicy: string;
  status: "active" | "paused" | "disabled";
  createdAt: string;
  updatedAt: string;
}

interface LiveAudioScheduleState {
  sourceId: string;
  lastScheduledAt: string;
  lastDispatchOk: boolean;
  lastDispatchError: string;
  lastInstanceKey: string;
  consecutiveFailures: number;
  nextEligibleAt: string;
  updatedAt: string;
}

interface IntelReport {
  id: string;
  title: string;
  summary: string;
  classification: string;
  sourceFamily: string;
  collectionMethod: string;
  analyticLens: string;
  entities: Array<Record<string, unknown>>;
  facts: string[];
  findings: string[];
  sourceUrl: string;
  sourceId: string;
  sourceType: string;
  region: string;
  country: string;
  topic: string;
  credibility: number;
  priority: number;
  createdAt: string;
  socialPost?: string;
  socialArbitrageScore?: number;
  bridgeScores?: Record<string, number>;
}

interface NewsPolicyGate {
  rightsPolicy: string;
  country: string;
  allowPublish: boolean;
  allowMapsExport: boolean;
  allowAudioRetention: boolean;
  requestedRetainAudio?: boolean;
  effectiveRetainAudio?: boolean;
  requestedRetentionDays?: number;
  effectiveRetentionDays?: number;
  reasons: string[];
}

const RSS_SOURCES: RssSource[] = [
  {
    id: "4gamer",
    name: "4Gamer.net",
    lang: "ja",
    categories: ["game"],
    feedUrl: "https://www.4gamer.net/rss/index.xml",
  },
  {
    id: "ann-all",
    name: "Anime News Network",
    lang: "en",
    categories: ["anime"],
    feedUrl: "https://www.animenewsnetwork.com/all/rss.xml?ann-edition=us",
  },
  {
    id: "arstechnica",
    name: "Ars Technica",
    lang: "en",
    categories: ["tech"],
    feedUrl: "https://feeds.arstechnica.com/arstechnica/index",
  },
  {
    id: "comic-natalie",
    name: "コミックナタリー",
    lang: "ja",
    categories: ["anime"],
    feedUrl: "https://natalie.mu/comic/feed/news",
  },
  {
    id: "destructoid",
    name: "Destructoid",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://www.destructoid.com/feed/",
  },
  {
    id: "engadget",
    name: "Engadget",
    lang: "en",
    categories: ["tech"],
    feedUrl: "https://www.engadget.com/rss.xml",
  },
  {
    id: "eurogamer",
    name: "Eurogamer",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://www.eurogamer.net/feed",
  },
  {
    id: "gematsu",
    name: "Gematsu",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://www.gematsu.com/feed",
  },
  {
    id: "kotaku",
    name: "Kotaku",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://kotaku.com/feed",
  },
  {
    id: "mlit-press",
    name: "国土交通省",
    lang: "ja",
    categories: ["c1-automotive"],
    feedUrl: "https://www.mlit.go.jp/common/rss/news.xml",
  },
  {
    id: "myanimelist-news",
    name: "MyAnimeList News",
    lang: "en",
    categories: ["anime"],
    feedUrl: "https://myanimelist.net/rss/news.xml",
  },
  {
    id: "pcgamer",
    name: "PC Gamer",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://www.pcgamer.com/rss/",
  },
  {
    id: "polygon",
    name: "Polygon",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://www.polygon.com/feed/",
  },
  {
    id: "ps-blog",
    name: "PlayStation Blog",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://blog.playstation.com/feed/",
  },
  {
    id: "steam-news",
    name: "Steam News",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://store.steampowered.com/feeds/news.xml",
  },
  {
    id: "techcrunch",
    name: "TechCrunch",
    lang: "en",
    categories: ["tech"],
    feedUrl: "https://techcrunch.com/feed/",
  },
  {
    id: "theverge",
    name: "The Verge",
    lang: "en",
    categories: ["tech"],
    feedUrl: "https://www.theverge.com/rss/index.xml",
  },
  {
    id: "xbox-wire",
    name: "Xbox Wire",
    lang: "en",
    categories: ["game"],
    feedUrl: "https://news.xbox.com/en-us/feed/",
  },
];

const INTEL_SOURCES: IntelSource[] = [
  {
    id: "social-arbitrage",
    name: "etzhayyim Social Arbitrage Intel",
    region: "global",
    country: "multi",
    topics: [
      "social-arbitrage",
      "inequality",
      "loneliness",
      "separation",
      "public-services",
      "open-data",
    ],
    sourceType: "official",
    official: true,
    primary: true,
    url: "https://news.etzhayyim.com/",
  },
  {
    id: "un-news",
    name: "United Nations News",
    region: "global",
    country: "un",
    topics: ["world", "security", "humanitarian"],
    sourceType: "official",
    official: true,
    primary: true,
    url: "https://news.un.org/",
  },
  {
    id: "who-news",
    name: "World Health Organization",
    region: "global",
    country: "un",
    topics: ["health", "medical-devices", "pandemic"],
    sourceType: "regulator",
    official: true,
    primary: true,
    url: "https://www.who.int/news",
  },
  {
    id: "imf-news",
    name: "International Monetary Fund",
    region: "global",
    country: "un",
    topics: ["macro", "finance", "sovereign-risk"],
    sourceType: "official",
    official: true,
    primary: true,
    url: "https://www.imf.org/en/News",
  },
  {
    id: "worldbank-news",
    name: "World Bank",
    region: "global",
    country: "un",
    topics: ["development", "macro", "infrastructure"],
    sourceType: "official",
    official: true,
    primary: true,
    url: "https://www.worldbank.org/en/news",
  },
  {
    id: "eu-press",
    name: "European Commission Press Corner",
    region: "europe",
    country: "eu",
    topics: ["regulation", "trade", "technology"],
    sourceType: "regulator",
    official: true,
    primary: true,
    url: "https://ec.europa.eu/commission/presscorner/",
  },
  {
    id: "us-sec",
    name: "U.S. SEC Press Releases",
    region: "north-america",
    country: "us",
    topics: ["markets", "enforcement", "disclosure"],
    sourceType: "regulator",
    official: true,
    primary: true,
    url: "https://www.sec.gov/news/pressreleases",
  },
  {
    id: "us-cisa",
    name: "CISA News",
    region: "north-america",
    country: "us",
    topics: ["cyber", "infrastructure", "vulnerability"],
    sourceType: "regulator",
    official: true,
    primary: true,
    url: "https://www.cisa.gov/news-events/news",
  },
  {
    id: "meti-news",
    name: "METI News Releases",
    region: "asia",
    country: "jp",
    topics: ["industry", "energy", "semiconductor"],
    sourceType: "regulator",
    official: true,
    primary: true,
    url: "https://www.meti.go.jp/english/press/",
  },
  {
    id: "mofa-jp",
    name: "MOFA Japan Press Releases",
    region: "asia",
    country: "jp",
    topics: ["diplomacy", "security", "trade"],
    sourceType: "official",
    official: true,
    primary: true,
    url: "https://www.mofa.go.jp/press/release/",
  },
  {
    id: "pmda-news",
    name: "PMDA",
    region: "asia",
    country: "jp",
    topics: ["medical-devices", "pharma", "safety"],
    sourceType: "regulator",
    official: true,
    primary: true,
    url: "https://www.pmda.go.jp/english/",
  },
  {
    id: "company-ir",
    name: "Company investor relations",
    region: "global",
    country: "multi",
    topics: ["earnings", "strategy", "supply-chain"],
    sourceType: "press-release",
    official: true,
    primary: true,
    url: "https://example.com/ir",
  },
  {
    id: "standards-body",
    name: "Standards bodies",
    region: "global",
    country: "multi",
    topics: ["standards", "semiconductor", "industrial"],
    sourceType: "standards-body",
    official: true,
    primary: true,
    url: "https://www.iso.org/news.html",
  },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Path-based writer DID for a news source. */
function writerDID(sourceId: string): string {
  return `did:web:news.etzhayyim.com:writer:${sourceId}`;
}

function findIntelSource(
  sourceId: string,
  url: string
): IntelSource | undefined {
  if (sourceId) return INTEL_SOURCES.find((source) => source.id === sourceId);
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    return INTEL_SOURCES.find((source) => {
      try {
        return new URL(source.url).hostname.replace(/^www\./, "") === host;
      } catch {
        return false;
      }
    });
  } catch {
    return undefined;
  }
}

function keywordEntities(input: string): Array<Record<string, unknown>> {
  const entities = new Map<string, { name: string; type: string }>();
  for (const match of input.matchAll(
    /\b[A-Z][A-Za-z0-9&.-]{2,}(?:\s+[A-Z][A-Za-z0-9&.-]{2,}){0,3}\b/g
  )) {
    const name = match[0].trim();
    if (name.length <= 3 || /^(The|This|That|News|Press|Release)$/.test(name))
      continue;
    entities.set(name.toLowerCase(), { name, type: "org-or-place" });
  }
  return Array.from(entities.values()).slice(0, 8);
}

function extractFacts(text: string, title: string): string[] {
  const sentences = `${title}. ${text}`
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?。！？])\s+/)
    .map((x) => x.trim())
    .filter((x) => x.length >= 24 && x.length <= 260);
  return Array.from(new Set(sentences)).slice(0, 5);
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => str(item).trim())
    .filter((item) => item.length > 0)
    .slice(0, 10);
}

function numericRecord(value: unknown): Record<string, number> | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return undefined;
  const out: Record<string, number> = {};
  for (const [key, raw] of Object.entries(value as Record<string, unknown>)) {
    const n = Number(raw);
    if (Number.isFinite(n)) out[key] = Math.max(0, Math.min(1, n));
  }
  return Object.keys(out).length > 0 ? out : undefined;
}

function objectArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) return [];
  return value
    .filter(
      (item): item is Record<string, unknown> =>
        Boolean(item) && typeof item === "object" && !Array.isArray(item)
    )
    .slice(0, 20);
}

function boundedScore(value: unknown): number | undefined {
  const n = Number(value);
  if (!Number.isFinite(n)) return undefined;
  return Math.max(0, Math.min(1, n));
}

function buildFindings(args: {
  title: string;
  topic: string;
  sourceType: string;
  official: boolean;
  primary: boolean;
  facts: string[];
}): string[] {
  const basis =
    args.official || args.primary
      ? "primary/official-source"
      : "secondary-source";
  const findings = [
    `${basis} signal for ${args.topic || "global"}: ${args.title}`,
    args.official
      ? "Official-source status lowers provenance risk but does not remove interpretation risk."
      : "Non-official source requires corroboration before high-confidence publication.",
  ];
  if (args.facts.length >= 2)
    findings.push(
      "Multiple extractable claims are present, making this suitable for follow-up corroboration."
    );
  return findings;
}

function heuristicCredibility(
  sourceType: string,
  official: boolean,
  primary: boolean
): number {
  let score = 0.45;
  if (primary) score += 0.25;
  if (official) score += 0.2;
  if (
    [
      "regulator",
      "official",
      "standards-body",
      "statistics",
      "clinical-registry",
    ].includes(sourceType)
  )
    score += 0.1;
  if (["rss", "platform"].includes(sourceType)) score -= 0.05;
  return Math.max(0, Math.min(1, Number(score.toFixed(3))));
}

function heuristicPriority(
  evidenceCount: number,
  officialCount: number,
  corroboratedCount: number,
  recencyHours: number,
  impact: number
): number {
  const freshness = Math.max(0, 1 - Math.max(0, recencyHours) / 168);
  const score =
    0.22 * Math.min(1, evidenceCount / 5) +
    0.24 * Math.min(1, officialCount / 2) +
    0.18 * Math.min(1, corroboratedCount / 3) +
    0.16 * freshness +
    0.2 * Math.max(0, Math.min(1, impact));
  return Math.max(0, Math.min(1, Number(score.toFixed(3))));
}

async function scoreIntelViaUdf(
  sourceType: string,
  official: boolean,
  primary: boolean,
  evidenceCount: number,
  recencyHours: number,
  impact: number
): Promise<{ credibility: number; priority: number }> {
  try {
    const db = createKyselyDb();
    const credibilityRows = await sql<{ credibility: number | null }>`
      SELECT news_source_credibility(${sourceType}::varchar, ${primary}::boolean, ${official}::boolean) AS credibility
    `.execute(db);
    const priorityRows = await sql<{ priority: number | null }>`
      SELECT news_intel_priority(${evidenceCount}::int, ${
      official ? 1 : 0
    }::int, ${
      primary ? 1 : 0
    }::int, ${recencyHours}::double precision, ${impact}::double precision) AS priority
    `.execute(db);
    const credibility = Number(credibilityRows.rows[0]?.credibility);
    const priority = Number(priorityRows.rows[0]?.priority);
    if (Number.isFinite(credibility) && Number.isFinite(priority))
      return { credibility, priority };
  } catch {
    // UDF may not be registered in local/dev environments. Keep command deterministic.
  }
  return {
    credibility: heuristicCredibility(sourceType, official, primary),
    priority: heuristicPriority(
      evidenceCount,
      official ? 1 : 0,
      primary ? 1 : 0,
      recencyHours,
      impact
    ),
  };
}

/** Stable dedup key for an article. */
function articleKey(sourceId: string, guid: string): string {
  // simple deterministic hash of sourceId + guid
  let h = 0;
  const s = `${sourceId}:${guid}`;
  for (let i = 0; i < s.length; i++)
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  return `art-${sourceId}-${Math.abs(h).toString(36)}`;
}

function stablePositiveInt(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h >>> 0) || 1;
}

function registryKey(id: string): string {
  return id
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 128);
}

function clampInt(value: unknown, fallback: number, min: number, max: number): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(Math.trunc(n), max));
}

function validatePublicHttpUrl(value: string, field: string): string {
  if (!value) return "";
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" && url.protocol !== "http:") {
      throw new Error(`${field} must use http or https`);
    }
    return url.toString();
  } catch (error) {
    if (error instanceof Error && error.message.includes("must use")) throw error;
    throw new Error(`${field} must be a valid URL`);
  }
}

function normalizeLiveAudioStatus(value: unknown): LiveAudioSource["status"] {
  const status = str(value || "active").toLowerCase();
  if (status === "paused" || status === "disabled") return status;
  return "active";
}

function evaluateNewsPolicy(args: {
  rightsPolicy?: unknown;
  country?: unknown;
  sourceType?: unknown;
  retainAudio?: unknown;
  retentionDays?: unknown;
}): NewsPolicyGate {
  const rightsPolicy = str(args.rightsPolicy ?? "transcript-only-public-broadcast").trim().toLowerCase();
  const country = str(args.country ?? "").trim().toLowerCase();
  const sourceType = str(args.sourceType ?? "").trim().toLowerCase();
  const requestedRetainAudio = args.retainAudio === true;
  const requestedRetentionDays = clampInt(args.retentionDays, 0, 0, 30);
  const allowAudioRetention = ["audio-retention-allowed", "archive-allowed", "public-domain", "cc-by"].includes(rightsPolicy);
  const effectiveRetainAudio = requestedRetainAudio && allowAudioRetention;
  const effectiveRetentionDays = effectiveRetainAudio ? requestedRetentionDays : 0;
  let allowPublish = ["public-domain", "cc-by", "transcript-publication-allowed", "transcript-only-public-broadcast"].includes(rightsPolicy);
  let allowMapsExport = !["no-derived-data", "internal-only"].includes(rightsPolicy);
  if (["jp", "jpn", "de", "deu", "fr", "fra", "eu"].includes(country) && rightsPolicy === "transcript-only-public-broadcast") {
    allowPublish = false;
  }
  if (sourceType === "private" || sourceType === "meeting") {
    allowPublish = false;
    allowMapsExport = false;
  }
  const reasons: string[] = [];
  if (!allowPublish) reasons.push("publication-requires-source-specific-rights");
  if (!allowMapsExport) reasons.push("maps-export-disabled-by-rights-policy");
  if (!allowAudioRetention) reasons.push("audio-retention-blocked-by-default");
  return {
    rightsPolicy,
    country,
    allowPublish,
    allowMapsExport,
    allowAudioRetention,
    requestedRetainAudio,
    effectiveRetainAudio,
    requestedRetentionDays,
    effectiveRetentionDays,
    reasons,
  };
}

function liveAudioPolicyGate(source: Record<string, unknown>): NewsPolicyGate {
  return evaluateNewsPolicy({
    rightsPolicy: source.rightsPolicy,
    country: source.country,
    sourceType: source.sourceType,
    retainAudio: source.retainAudio,
    retentionDays: source.retentionDays,
  });
}

function liveAudioRecordFromArgs(args: Record<string, unknown>): LiveAudioSource {
  const sourceId = registryKey(str(args.sourceId ?? ""));
  const sourceName = str(args.sourceName ?? sourceId).trim();
  const streamUrl = validatePublicHttpUrl(str(args.streamUrl ?? "").trim(), "streamUrl");
  if (!sourceId || !sourceName || !streamUrl) {
    throw new Error("sourceId, sourceName and streamUrl required");
  }
  const topic = str(args.topic ?? "world").trim() || "world";
  const topics = stringArray(args.topics);
  if (!topics.includes(topic)) topics.unshift(topic);
  const now = nowISO();
  return {
    sourceId,
    sourceName,
    streamUrl,
    sourceUrl: validatePublicHttpUrl(str(args.sourceUrl ?? "").trim(), "sourceUrl"),
    sourceType: str(args.sourceType ?? "broadcast").trim() || "broadcast",
    region: str(args.region ?? "global").trim() || "global",
    country: str(args.country ?? "multi").trim() || "multi",
    topic,
    topics,
    lang: str(args.lang ?? "").trim(),
    captureSeconds: clampInt(args.captureSeconds, 30, 5, 180),
    maxBytes: clampInt(args.maxBytes, 8 * 1024 * 1024, 256 * 1024, 50 * 1024 * 1024),
    cadenceSeconds: clampInt(args.cadenceSeconds, 900, 60, 24 * 60 * 60),
    cooldownSeconds: clampInt(args.cooldownSeconds, 600, 0, 24 * 60 * 60),
    retainAudio: args.retainAudio === true,
    retentionDays: clampInt(args.retentionDays, 0, 0, 30),
    rightsPolicy: str(args.rightsPolicy ?? "transcript-only-public-broadcast").trim(),
    status: normalizeLiveAudioStatus(args.status),
    createdAt: now,
    updatedAt: now,
  };
}

function dateMs(value: unknown): number {
  const ms = Date.parse(str(value ?? ""));
  return Number.isFinite(ms) ? ms : 0;
}

function isoFromMs(ms: number): string {
  return new Date(ms).toISOString();
}

function liveAudioDueReason(
  source: Record<string, unknown>,
  state: Record<string, unknown> | undefined,
  nowMs: number,
  force: boolean
): { due: boolean; reason: string; nextEligibleAt: string } {
  if (force) return { due: true, reason: "forced", nextEligibleAt: isoFromMs(nowMs) };
  const nextEligibleMs = dateMs(state?.nextEligibleAt);
  if (nextEligibleMs > nowMs) {
    return {
      due: false,
      reason: "cooldown",
      nextEligibleAt: isoFromMs(nextEligibleMs),
    };
  }
  const lastScheduledMs = dateMs(state?.lastScheduledAt);
  const cadenceMs = clampInt(source.cadenceSeconds, 900, 60, 24 * 60 * 60) * 1000;
  if (lastScheduledMs > 0 && nowMs - lastScheduledMs < cadenceMs) {
    return {
      due: false,
      reason: "cadence",
      nextEligibleAt: isoFromMs(lastScheduledMs + cadenceMs),
    };
  }
  return { due: true, reason: lastScheduledMs > 0 ? "cadence-elapsed" : "never-scheduled", nextEligibleAt: isoFromMs(nowMs) };
}

function nextScheduleState(
  source: Record<string, unknown>,
  previous: Record<string, unknown> | undefined,
  dispatch: { ok: boolean; error?: string; instanceKey?: string },
  nowMs: number
): LiveAudioScheduleState {
  const previousFailures = clampInt(previous?.consecutiveFailures, 0, 0, 1000);
  const consecutiveFailures = dispatch.ok ? 0 : previousFailures + 1;
  const cooldownSeconds = clampInt(source.cooldownSeconds, 600, 0, 24 * 60 * 60);
  const cadenceSeconds = clampInt(source.cadenceSeconds, 900, 60, 24 * 60 * 60);
  const backoffSeconds = dispatch.ok
    ? cooldownSeconds
    : Math.min(6 * 60 * 60, Math.max(cooldownSeconds, 60) * 2 ** Math.min(consecutiveFailures - 1, 6));
  return {
    sourceId: str(source.sourceId),
    lastScheduledAt: isoFromMs(nowMs),
    lastDispatchOk: dispatch.ok,
    lastDispatchError: dispatch.error ?? "",
    lastInstanceKey: dispatch.instanceKey ?? "",
    consecutiveFailures,
    nextEligibleAt: isoFromMs(nowMs + Math.max(cadenceSeconds, backoffSeconds) * 1000),
    updatedAt: isoFromMs(nowMs),
  };
}

async function envString(value: unknown): Promise<string> {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (typeof (value as { get?: unknown }).get === "function") {
    return str(await (value as { get: () => Promise<unknown> }).get());
  }
  if (typeof (value as { text?: unknown }).text === "function") {
    return str(await (value as { text: () => Promise<unknown> }).text());
  }
  return str(value);
}

async function dispatchLiveAudioIngest(
  sdk: HostSDK,
  source: Record<string, unknown>,
  dryRun: boolean
): Promise<{
  ok: boolean;
  dryRun: boolean;
  instanceKey?: string;
  error?: string;
  policyGate?: NewsPolicyGate;
  effectiveRetainAudio?: boolean;
  effectiveRetentionDays?: number;
}> {
  const policyGate = liveAudioPolicyGate(source);
  const payload = {
    sourceId: str(source.sourceId),
    sourceName: str(source.sourceName),
    streamUrl: str(source.streamUrl),
    sourceUrl: str(source.sourceUrl),
    sourceType: str(source.sourceType || "broadcast"),
    region: str(source.region || "global"),
    country: str(source.country || "multi"),
    topic: str(source.topic || "world"),
    lang: str(source.lang || ""),
    captureSeconds: clampInt(source.captureSeconds, 30, 5, 180),
    maxBytes: clampInt(source.maxBytes, 8 * 1024 * 1024, 256 * 1024, 50 * 1024 * 1024),
    retainAudio: policyGate.effectiveRetainAudio === true,
    retentionDays: policyGate.effectiveRetentionDays ?? 0,
    rightsPolicy: policyGate.rightsPolicy,
    publish: false,
  };
  if (dryRun) {
    return {
      ok: true,
      dryRun: true,
      policyGate,
      effectiveRetainAudio: payload.retainAudio,
      effectiveRetentionDays: payload.retentionDays,
    };
  }
  const baseUrl = (await envString(
    (sdk.env as Record<string, unknown>).NEWS_BPMN_URL ||
      (sdk.env as Record<string, unknown>).BPMN_URL ||
      "https://dispatcher.etzhayyim.com"
  )).replace(/\/+$/, "");
  const dispatcherSecret = await envString((sdk.env as Record<string, unknown>).BPMN_DISPATCHER_SECRET);
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (dispatcherSecret) headers["x-internal-trust"] = dispatcherSecret;
  const res = await fetch(`${baseUrl}/xrpc/com.etzhayyim.apps.news.liveAudioIngest`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  let body: Record<string, unknown> = {};
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { raw: text };
  }
  if (!res.ok) {
    return {
      ok: false,
      dryRun: false,
      error: str(body.error || body.message || text || res.statusText),
      policyGate,
      effectiveRetainAudio: payload.retainAudio,
      effectiveRetentionDays: payload.retentionDays,
    };
  }
  return {
    ok: true,
    dryRun: false,
    instanceKey: str(body.instanceKey || body.processInstanceKey || body.process_instance_key || ""),
    policyGate,
    effectiveRetainAudio: payload.retainAudio,
    effectiveRetentionDays: payload.retentionDays,
  };
}

function normalizeIntelEntities(
  supplied: Array<Record<string, unknown>>,
  fallbackText: string
): Array<Record<string, unknown>> {
  const normalized = supplied
    .map((entity) => {
      const name = str(entity.name ?? entity.label ?? entity.text ?? entity.value).trim();
      if (!name) return null;
      return {
        ...entity,
        name,
        type: str(entity.type ?? entity.kind ?? "unknown").trim() || "unknown",
      };
    })
    .filter((entity): entity is Record<string, unknown> => Boolean(entity));
  return normalized.length > 0 ? normalized.slice(0, 12) : keywordEntities(fallbackText);
}

function isSpatialEntityCandidate(entity: Record<string, unknown>): boolean {
  const haystack = `${str(entity.type)} ${str(entity.kind)} ${str(entity.name)}`.toLowerCase();
  if (Number.isFinite(Number(entity.lat)) && Number.isFinite(Number(entity.lng))) return true;
  return /(place|location|geo|city|country|region|province|prefecture|district|facility|airport|port|station|road|river|incident|event|disaster|quake|fire|flood|storm|attack|protest)/.test(haystack);
}

async function exportNewsEntitiesToMaps(
  sdk: HostSDK,
  report: IntelReport,
  transcriptText: string,
  policyGate: NewsPolicyGate
): Promise<Record<string, unknown>> {
  if (str((sdk.env as Record<string, unknown>).NEWS_MAPS_SPATIAL_EXPORT_DISABLED).toLowerCase() === "true") {
    return { ok: true, disabled: true, candidates: 0, exported: 0, items: [] };
  }
  if (!policyGate.allowMapsExport) {
    return { ok: true, disabled: true, reason: "policy", candidates: 0, exported: 0, items: [] };
  }
  const candidates = report.entities.filter(isSpatialEntityCandidate).slice(0, 5);
  if (candidates.length === 0) {
    return { ok: true, candidates: 0, exported: 0, items: [] };
  }
  const baseUrl = (await envString(
    (sdk.env as Record<string, unknown>).NEWS_MAPS_BPMN_URL ||
      (sdk.env as Record<string, unknown>).BPMN_URL ||
      "https://dispatcher.etzhayyim.com"
  )).replace(/\/+$/, "");
  const dispatcherSecret = await envString((sdk.env as Record<string, unknown>).BPMN_DISPATCHER_SECRET);
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (dispatcherSecret) headers["x-internal-trust"] = dispatcherSecret;
  const items: Array<Record<string, unknown>> = [];
  for (const entity of candidates) {
    const name = str(entity.name);
    const payload: Record<string, unknown> = {
      entityId: stablePositiveInt(`${report.id}:${name}`),
      eventType: "news.broadcast.entityMention",
      severity: "info",
      description: [
        `Broadcast mention: ${name}`,
        `Source: ${report.sourceId}`,
        `Title: ${report.title}`,
        `Summary: ${report.summary || transcriptText.slice(0, 220)}`,
        `URL: ${report.sourceUrl}`,
      ].join("\n").slice(0, 1800),
    };
    const lat = Number(entity.lat ?? entity.latitude);
    const lng = Number(entity.lng ?? entity.lon ?? entity.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      payload.lat = lat;
      payload.lng = lng;
    }
    try {
      const res = await fetch(`${baseUrl}/xrpc/com.etzhayyim.apps.maps.spatialEventRecord`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const text = await res.text();
      let body: Record<string, unknown> = {};
      try {
        body = text ? JSON.parse(text) : {};
      } catch {
        body = { raw: text };
      }
      items.push({
        name,
        ok: res.ok,
        status: res.status,
        nodeId: body.nodeId ?? "",
        error: res.ok ? "" : str(body.error || body.message || text || res.statusText),
      });
    } catch (error) {
      items.push({ name, ok: false, error: error instanceof Error ? error.message : String(error) });
    }
  }
  return {
    ok: items.every((item) => item.ok === true),
    candidates: candidates.length,
    exported: items.filter((item) => item.ok === true).length,
    items,
  };
}

async function publishIntelPost(
  sdk: HostSDK,
  report: Pick<
    IntelReport,
    | "id"
    | "title"
    | "summary"
    | "sourceUrl"
    | "sourceId"
    | "socialPost"
  > & {
    writerDid?: string;
  }
): Promise<{
  ok: boolean;
  published: boolean;
  writerDid: string;
  postText: string;
  error?: string;
}> {
  const writerDid = report.writerDid || writerDID(report.sourceId || "intel");
  sdk.pds.dispatch({
    type: "identity-create",
    payload: {
      path: `writer:${report.sourceId || "intel"}`,
      displayName: "etzhayyim Intel Desk",
      description: "news.etzhayyim.com intel writer DID",
    },
  });
  const postText = (report.socialPost
    ? report.socialPost.includes(report.sourceUrl)
      ? report.socialPost
      : `${report.socialPost}\n\n${report.sourceUrl}`
    : `Intel: ${report.title}\n\n${report.summary}\n\nSource: ${report.sourceUrl}`
  ).slice(0, 300);
  try {
    await (sdk.env as any).PDS_RPC.comAtprotoRepoCreateRecord(
      writerDid,
      "app.bsky.feed.post",
      {
        $type: "app.bsky.feed.post",
        text: postText,
        langs: ["en"],
        embed: {
          $type: "app.bsky.embed.external",
          external: {
            uri: report.sourceUrl,
            title: report.title,
            description: report.summary.slice(0, 200),
          },
        },
        createdAt: nowISO(),
      }
    );
    return { ok: true, published: true, writerDid, postText };
  } catch (e) {
    return {
      ok: false,
      published: false,
      writerDid,
      postText,
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

// ── Commands ─────────────────────────────────────────────────────────────────

async function cmdIngest(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.ingest", body);
  const sourceId = str(args.sourceId ?? "");
  // Allow targeting a single source or all sources
  const targets = sourceId
    ? RSS_SOURCES.filter((s) => s.id === sourceId)
    : RSS_SOURCES;
  if (targets.length === 0) return { error: `unknown sourceId: ${sourceId}` };

  return {
    ok: false,
    movedToLangServer: true,
    processId: "news_rss_ingest",
    taskTypes: ["news.rss.resolveSources", "news.rss.ingestSource"],
    sources: targets.map((source) => source.id),
    ts: nowISO(),
  };
}

async function cmdLiveAudioIngest(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.liveAudioIngest", body);
  const sourceId = str(args.sourceId ?? "").trim();
  const sourceName = str(args.sourceName ?? sourceId).trim();
  const streamUrl = str(args.streamUrl ?? "").trim();
  if (!sourceId || !sourceName || !streamUrl) {
    return { ok: false, error: "sourceId, sourceName and streamUrl required" };
  }
  return {
    ok: false,
    movedToLangServer: true,
    processId: "news_live_audio_ingest",
    taskTypes: [
      "news.liveAudio.transcribeWindow",
      "generic.llm.json",
      "xrpc.com.etzhayyim.apps.news.analyzeIntel",
      "xrpc.com.etzhayyim.apps.news.publishIntel",
      "generic.audit.emit",
    ],
    sourceId,
    sourceName,
    streamUrl,
    captureSeconds: Number(args.captureSeconds ?? 30),
    maxBytes: Number(args.maxBytes ?? 8 * 1024 * 1024),
    retainAudio: args.retainAudio === true,
    ts: nowISO(),
  };
}

async function cmdRegisterLiveAudioSource(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  let record: LiveAudioSource;
  try {
    record = liveAudioRecordFromArgs(
      parseLexiconInput("com.etzhayyim.apps.news.registerLiveAudioSource", body)
    );
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : String(error) };
  }
  const rkey = registryKey(record.sourceId);
  try {
    await sdk.pds.comAtprotoRepoPutRecord(
      "com.etzhayyim.apps.news.liveAudioSource",
      rkey,
      {
        $type: "com.etzhayyim.apps.news.liveAudioSource",
        ...record,
      }
    );
  } catch (error) {
    return { ok: false, sourceId: record.sourceId, rkey, error: error instanceof Error ? error.message : String(error) };
  }
  return {
    ok: true,
    sourceId: record.sourceId,
    rkey,
    record,
    policyGate: liveAudioPolicyGate(record as unknown as Record<string, unknown>),
  };
}

async function cmdCommitArticle(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.commitArticle", body);
  const sourceId = str(args.sourceId ?? "").trim();
  const sourceName = str(args.sourceName ?? sourceId).trim();
  const lang = str(args.lang ?? "en").trim() || "en";
  const title = str(args.title ?? "").trim();
  const link = str(args.link ?? "").trim();
  if (!sourceId || !title || !link)
    return { ok: false, error: "sourceId, title and link required" };

  const description = str(args.description ?? "").trim();
  const guid = str(args.guid ?? link).trim() || link;
  const rkey = articleKey(sourceId, guid)
    .replace(/[^a-zA-Z0-9-]/g, "")
    .slice(0, 64);
  const writerDid = writerDID(sourceId);
  const categories = Array.isArray(args.categories)
    ? args.categories.map((item) => str(item)).filter(Boolean)
    : [];
  const translations =
    args.translations && typeof args.translations === "object"
      ? (args.translations as Record<string, unknown>)
      : { [lang]: title };

  const db = createKyselyDb();
  const exists = await db
    .selectFrom("vertex_article")
    .select("rkey")
    .where("repo", "=", writerDid)
    .where("rkey", "=", rkey)
    .limit(1)
    .execute();
  if (exists.length > 0) {
    return { ok: true, rkey, writerDid, published: false, skipped: true };
  }

  sdk.pds.dispatch({
    type: "identity-create",
    payload: {
      path: `writer:${sourceId}`,
      displayName: sourceName || sourceId,
      description: `News writer DID for ${sourceName || sourceId}`,
    },
  });

  const props = {
    sourceId,
    sourceName,
    lang,
    categories,
    link,
    pubDate: str(args.pubDate ?? nowISO()),
    translations,
    pipeline: "langserver-rss",
  };
  try {
    await sdk.pds.comAtprotoRepoPutRecord(
      "com.etzhayyim.apps.news.article",
      rkey,
      {
        $type: "com.etzhayyim.apps.news.article",
        displayName: title.slice(0, 1024),
        description: description.slice(0, 4096),
        text: str(args.text ?? `${title} ${description}`).slice(0, 8192),
        did: writerDid,
        props: JSON.stringify(props),
        createdAt: nowISO(),
      },
      writerDid
    );
  } catch (e) {
    return {
      ok: false,
      rkey,
      writerDid,
      published: false,
      error: e instanceof Error ? e.message : String(e),
    };
  }

  let published = false;
  if (args.publish !== false) {
    const socialPost = str(args.socialPost ?? `${title}\n\n${link}`).slice(
      0,
      300
    );
    try {
      await sdk.pds.comAtprotoRepoCreateRecord(
        "app.bsky.feed.post",
        {
          $type: "app.bsky.feed.post",
          text: socialPost,
          langs: [lang],
          embed: {
            $type: "app.bsky.embed.external",
            external: {
              uri: link,
              title,
              description: description.slice(0, 200),
            },
          },
          createdAt: nowISO(),
        },
        writerDid
      );
      published = true;
    } catch {
      // Domain record is the durable outcome; social posting can be retried.
      published = false;
    }
  }

  return { ok: true, rkey, writerDid, published, skipped: false };
}

async function cmdListArticles(
  _sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.listArticles", body);
  const limit = Math.min(Number(args.limit) || 50, 200);
  const offset = Number(args.offset) || 0;
  const db = createKyselyDb();
  let q = db.selectFrom("vertex_article").selectAll();
  if (args.sourceId) {
    q = q.where("repo", "=", writerDID(str(args.sourceId))) as typeof q;
  } else {
    const repos = RSS_SOURCES.map((s) => writerDID(s.id));
    q = q.where("repo", "in", repos) as typeof q;
  }
  const rows = await q.offset(offset).limit(limit).execute();
  return { items: rows, offset, limit };
}

async function cmdGetArticle(
  _sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.getArticle", body);
  const id = str(args.id ?? "");
  if (!id) return { error: "id required" };
  const db = createKyselyDb();
  const rows = await db
    .selectFrom("vertex_article")
    .selectAll()
    .where("rkey", "=", id)
    .limit(1)
    .execute();
  return rows[0] ?? { error: "not found" };
}

async function cmdListSources(
  _sdk: HostSDK,
  _body: Uint8Array
): Promise<unknown> {
  return {
    sources: RSS_SOURCES.map((s) => ({
      id: s.id,
      name: s.name,
      lang: s.lang,
      categories: s.categories,
      writerDid: writerDID(s.id),
    })),
    total: RSS_SOURCES.length,
  };
}

async function cmdListIntelSources(
  _sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  let args: Record<string, unknown> = {};
  try {
    args = JSON.parse(new TextDecoder().decode(body || new Uint8Array()));
  } catch {
    args = {};
  }
  const region = str(args.region ?? "").toLowerCase();
  const topic = str(args.topic ?? "").toLowerCase();
  const officialOnly =
    args.officialOnly === true ||
    str(args.officialOnly).toLowerCase() === "true";
  const sources = INTEL_SOURCES.filter((source) => {
    if (region && source.region !== region && source.country !== region)
      return false;
    if (topic && !source.topics.some((t) => t.toLowerCase().includes(topic)))
      return false;
    if (officialOnly && !source.official) return false;
    return true;
  });
  return { sources, total: sources.length };
}

async function cmdListLiveAudioSources(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.listLiveAudioSources", body);
  const limit = clampInt(args.limit, 50, 1, 100);
  const status = str(args.status ?? "").toLowerCase();
  const region = str(args.region ?? "").toLowerCase();
  const topic = str(args.topic ?? "").toLowerCase();
  try {
    const result = await sdk.pds.listRecords("com.etzhayyim.apps.news.liveAudioSource", {
      limit,
      cursor: str(args.cursor ?? "") || undefined,
      reverse: true,
    });
    const records = (result.records ?? []) as Array<{
      uri?: string;
      cid?: string;
      value?: Record<string, unknown>;
    }>;
    const sources = records
      .map((record) => {
        const source = {
          uri: record.uri,
          cid: record.cid,
          ...(record.value ?? {}),
        };
        return {
          ...source,
          policyGate: liveAudioPolicyGate(source),
        };
      })
      .filter((source) => {
        if (status && str(source.status).toLowerCase() !== status) return false;
        if (region) {
          const sourceRegion = str(source.region).toLowerCase();
          const sourceCountry = str(source.country).toLowerCase();
          if (sourceRegion !== region && sourceCountry !== region) return false;
        }
        if (topic) {
          const sourceTopic = str(source.topic).toLowerCase();
          const sourceTopics = Array.isArray(source.topics)
            ? source.topics.map((item) => str(item).toLowerCase())
            : [];
          if (sourceTopic !== topic && !sourceTopics.includes(topic)) return false;
        }
        return true;
      });
    return {
      sources,
      total: sources.length,
      cursor: result.cursor ?? "",
      policySummary: {
        publishBlocked: sources.filter((source) => !(source.policyGate as NewsPolicyGate).allowPublish).length,
        mapsExportBlocked: sources.filter((source) => !(source.policyGate as NewsPolicyGate).allowMapsExport).length,
        audioRetentionBlocked: sources.filter((source) => !(source.policyGate as NewsPolicyGate).allowAudioRetention).length,
      },
    };
  } catch (error) {
    return {
      sources: [],
      total: 0,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function cmdAuditLiveAudioPolicies(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.auditLiveAudioPolicies", body);
  const limit = clampInt(args.limit, 100, 1, 100);
  const status = str(args.status ?? "").toLowerCase();
  const region = str(args.region ?? "").toLowerCase();
  const topic = str(args.topic ?? "").toLowerCase();
  const onlyBlocked = args.onlyBlocked === true;
  try {
    const result = await sdk.pds.listRecords("com.etzhayyim.apps.news.liveAudioSource", {
      limit,
      cursor: str(args.cursor ?? "") || undefined,
      reverse: true,
    });
    const records = (result.records ?? []) as Array<{
      uri?: string;
      cid?: string;
      value?: Record<string, unknown>;
    }>;
    const items = records
      .map((record) => {
        const source = {
          uri: record.uri,
          cid: record.cid,
          ...(record.value ?? {}),
        };
        const policyGate = liveAudioPolicyGate(source);
        const blocked = {
          publish: !policyGate.allowPublish,
          mapsExport: !policyGate.allowMapsExport,
          audioRetention: !policyGate.allowAudioRetention,
        };
        return {
          sourceId: registryKey(str(source.sourceId ?? "")),
          sourceName: str(source.sourceName ?? ""),
          status: normalizeLiveAudioStatus(source.status),
          region: str(source.region ?? "global"),
          country: str(source.country ?? "multi"),
          topic: str(source.topic ?? "world"),
          sourceType: str(source.sourceType ?? "broadcast"),
          rightsPolicy: policyGate.rightsPolicy,
          requestedRetainAudio: policyGate.requestedRetainAudio === true,
          requestedRetentionDays: policyGate.requestedRetentionDays ?? 0,
          effectiveRetainAudio: policyGate.effectiveRetainAudio === true,
          effectiveRetentionDays: policyGate.effectiveRetentionDays ?? 0,
          blocked,
          reasons: policyGate.reasons,
          policyGate,
        };
      })
      .filter((item) => {
        if (status && item.status !== status) return false;
        if (region && item.region.toLowerCase() !== region && item.country.toLowerCase() !== region) return false;
        if (topic && item.topic.toLowerCase() !== topic) return false;
        if (onlyBlocked && !item.blocked.publish && !item.blocked.mapsExport && !item.blocked.audioRetention) return false;
        return true;
      });
    return {
      ok: true,
      total: items.length,
      cursor: result.cursor ?? "",
      summary: {
        publishBlocked: items.filter((item) => item.blocked.publish).length,
        mapsExportBlocked: items.filter((item) => item.blocked.mapsExport).length,
        audioRetentionBlocked: items.filter((item) => item.blocked.audioRetention).length,
        activeSources: items.filter((item) => item.status === "active").length,
      },
      items,
    };
  } catch (error) {
    return {
      ok: false,
      total: 0,
      summary: {
        publishBlocked: 0,
        mapsExportBlocked: 0,
        audioRetentionBlocked: 0,
        activeSources: 0,
      },
      items: [],
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

async function cmdScheduleLiveAudioIngest(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.scheduleLiveAudioIngest", body);
  const sourceId = registryKey(str(args.sourceId ?? ""));
  const region = str(args.region ?? "").toLowerCase();
  const topic = str(args.topic ?? "").toLowerCase();
  const limit = clampInt(args.limit, 50, 1, 100);
  const maxLaunches = clampInt(args.maxLaunches, 5, 1, 25);
  const dryRun = args.dryRun === true;
  const force = args.force === true;
  const nowMs = Date.now();
  try {
    const [sourceResult, stateResult] = await Promise.all([
      sdk.pds.listRecords("com.etzhayyim.apps.news.liveAudioSource", {
        limit,
        reverse: true,
      }),
      sdk.pds.listRecords("com.etzhayyim.apps.news.liveAudioScheduleState", {
        limit: 100,
        reverse: true,
      }),
    ]);
    const states = new Map<string, Record<string, unknown>>();
    for (const item of (stateResult.records ?? []) as Array<{ value?: Record<string, unknown> }>) {
      const value = item.value ?? {};
      const id = registryKey(str(value.sourceId ?? ""));
      if (id) states.set(id, value);
    }
    const sources = ((sourceResult.records ?? []) as Array<{
      uri?: string;
      cid?: string;
      value?: Record<string, unknown>;
    }>)
      .map((record) => ({
        uri: record.uri,
        cid: record.cid,
        ...(record.value ?? {}),
      }))
      .filter((source) => {
        if (str(source.status || "active").toLowerCase() !== "active") return false;
        if (sourceId && registryKey(str(source.sourceId)) !== sourceId) return false;
        if (region) {
          const sourceRegion = str(source.region).toLowerCase();
          const sourceCountry = str(source.country).toLowerCase();
          if (sourceRegion !== region && sourceCountry !== region) return false;
        }
        if (topic) {
          const sourceTopic = str(source.topic).toLowerCase();
          const sourceTopics = Array.isArray(source.topics)
            ? source.topics.map((item) => str(item).toLowerCase())
            : [];
          if (sourceTopic !== topic && !sourceTopics.includes(topic)) return false;
        }
        return true;
      });

    const items: Array<Record<string, unknown>> = [];
    let launched = 0;
    for (const source of sources) {
      const id = registryKey(str(source.sourceId));
      const state = states.get(id);
      const due = liveAudioDueReason(source, state, nowMs, force);
      const policyGate = liveAudioPolicyGate(source);
      if (!due.due || launched >= maxLaunches) {
        items.push({
          sourceId: id,
          action: "skip",
          reason: due.due ? "maxLaunches" : due.reason,
          policyGate,
          nextEligibleAt: due.nextEligibleAt,
        });
        continue;
      }
      const dispatch = await dispatchLiveAudioIngest(sdk, source, dryRun);
      const nextState = nextScheduleState(source, state, dispatch, nowMs);
      if (!dryRun) {
        await sdk.pds.comAtprotoRepoPutRecord(
          "com.etzhayyim.apps.news.liveAudioScheduleState",
          id,
          {
            $type: "com.etzhayyim.apps.news.liveAudioScheduleState",
            ...nextState,
          }
        );
      }
      launched += dispatch.ok ? 1 : 0;
      items.push({
        sourceId: id,
        action: dispatch.ok ? "dispatch" : "dispatch-failed",
        dryRun,
        instanceKey: dispatch.instanceKey ?? "",
        error: dispatch.error ?? "",
        policyGate: dispatch.policyGate ?? policyGate,
        effectiveRetainAudio: dispatch.effectiveRetainAudio === true,
        effectiveRetentionDays: dispatch.effectiveRetentionDays ?? 0,
        nextEligibleAt: nextState.nextEligibleAt,
      });
    }
    return {
      ok: true,
      checked: sources.length,
      launched,
      skipped: items.filter((item) => item.action === "skip").length,
      policySummary: {
        publishBlocked: items.filter((item) => !((item.policyGate as NewsPolicyGate | undefined)?.allowPublish)).length,
        mapsExportBlocked: items.filter((item) => !((item.policyGate as NewsPolicyGate | undefined)?.allowMapsExport)).length,
        audioRetentionBlocked: items.filter((item) => !((item.policyGate as NewsPolicyGate | undefined)?.allowAudioRetention)).length,
      },
      items,
    };
  } catch (error) {
    return { ok: false, checked: 0, launched: 0, skipped: 0, items: [], error: error instanceof Error ? error.message : String(error) };
  }
}

async function cmdAnalyzeIntel(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.analyzeIntel", body);
  const title = str(args.title ?? "").trim();
  const sourceUrl = str(args.url ?? "").trim();
  if (!title || !sourceUrl)
    return { ok: false, error: "title and url required" };

  const knownSource = findIntelSource(str(args.sourceId ?? ""), sourceUrl);
  const sourceId = str(args.sourceId ?? knownSource?.id ?? "intel");
  const sourceType = str(
    args.sourceType ?? knownSource?.sourceType ?? "unknown"
  );
  const topic = str(args.topic ?? knownSource?.topics[0] ?? "world");
  const region = str(args.region ?? knownSource?.region ?? "global");
  const country = str(args.country ?? knownSource?.country ?? "multi");
  const rightsPolicy = str(args.rightsPolicy ?? "transcript-only-public-broadcast");
  const policyGate = evaluateNewsPolicy({
    rightsPolicy,
    country,
    sourceType,
    retainAudio: args.retainAudio,
    retentionDays: args.retentionDays,
  });
  const text = str(args.text ?? args.summary ?? "");
  const summary = str(args.summary ?? "") || text.slice(0, 360) || title;
  const publishedAt = str(args.publishedAt ?? "");
  const official =
    Boolean(knownSource?.official) ||
    [
      "official",
      "regulator",
      "standards-body",
      "statistics",
      "clinical-registry",
      "press-release",
    ].includes(sourceType);
  const primary = Boolean(knownSource?.primary) || official;
  const extractedFacts = extractFacts(text, title);
  const facts = Array.from(
    new Set([...stringArray(args.facts), ...extractedFacts])
  ).slice(0, 10);
  const findings = Array.from(
    new Set([
      ...stringArray(args.findings),
      ...buildFindings({
        title,
        topic,
        sourceType,
        official,
        primary,
        facts,
      }),
    ])
  ).slice(0, 10);
  const entities = normalizeIntelEntities(objectArray(args.entities), `${title} ${summary} ${text}`);
  const recencyHours = publishedAt
    ? Math.max(0, (Date.now() - Date.parse(publishedAt)) / 3_600_000)
    : 24;
  const socialPost = str(args.socialPost ?? "").trim();
  const bridgeScores = numericRecord(args.bridgeScores);
  const socialArbitrageScore = boundedScore(args.socialArbitrageScore);
  const impact = Math.min(
    1,
    0.35 +
      entities.length / 20 +
      facts.length / 20 +
      (socialArbitrageScore ?? 0) * 0.2 +
      (official ? 0.15 : 0)
  );
  const suppliedCredibility = boundedScore(args.credibility);
  const suppliedPriority = boundedScore(args.priority);
  const score =
    suppliedCredibility !== undefined && suppliedPriority !== undefined
      ? { credibility: suppliedCredibility, priority: suppliedPriority }
      : await scoreIntelViaUdf(
          sourceType,
          official,
          primary,
          facts.length,
          recencyHours,
          impact
        );
  const id = articleKey(sourceId, `${sourceUrl}:${title}`);
  const createdAt = nowISO();
  const report: IntelReport = {
    id,
    title,
    summary,
    classification:
      score.credibility >= 0.75
        ? "high-confidence-open-source"
        : "needs-corroboration",
    sourceFamily: sourceType,
    collectionMethod: primary ? "primary-source-xrpc" : "open-source-xrpc",
    analyticLens: `news-intel/${topic}`,
    entities,
    facts,
    findings,
    sourceUrl,
    sourceId,
    sourceType,
    region,
    country,
    topic,
    credibility: score.credibility,
    priority: score.priority,
    createdAt,
    socialPost: socialPost || undefined,
    socialArbitrageScore,
    bridgeScores,
  };

  try {
    await (sdk.env as any).PDS_RPC.comAtprotoRepoPutRecord(
      sdk.pds.selfRepo,
      "com.etzhayyim.apps.intel.report",
      id.replace(/[^a-zA-Z0-9-]/g, "").slice(0, 64),
      {
        $type: "com.etzhayyim.apps.intel.report",
        title: report.title,
        summary: report.summary,
        classification: report.classification,
        sourceFamily: report.sourceFamily,
        collectionMethod: report.collectionMethod,
        analyticLens: report.analyticLens,
        entities: report.entities,
        facts: report.facts,
        findings: report.findings,
        status: "ready",
        orgId: "etzhayyim.com",
        userId: "system",
        actorId: "did:web:news.etzhayyim.com",
        createdAt,
        props: JSON.stringify({
          sourceUrl,
          sourceId,
          sourceType,
          region,
          country,
          topic,
          credibility: score.credibility,
          priority: score.priority,
          socialPost: report.socialPost,
          socialArbitrageScore: report.socialArbitrageScore,
          bridgeScores: report.bridgeScores,
          spatialEntityCandidates: report.entities.filter(isSpatialEntityCandidate).length,
          policyGate,
        }),
      }
    );
  } catch (e) {
    return {
      ok: false,
      id,
      status: "record-failed",
      report,
      error: e instanceof Error ? e.message : String(e),
    };
  }
  const spatialEventExport = await exportNewsEntitiesToMaps(sdk, report, text, policyGate);

  const shouldPublish =
    args.publish !== false &&
    policyGate.allowPublish &&
    score.credibility >= 0.7 &&
    score.priority >= 0.45;
  const publishResult = shouldPublish
    ? await publishIntelPost(sdk, report)
    : { published: false, postText: "" };
  return {
    ok: true,
    id,
    status: "ready",
    report,
    policyGate,
    policyAllowPublish: policyGate.allowPublish,
    spatialEventExport,
    published: Boolean(publishResult.published),
    postText: str(publishResult.postText ?? ""),
  };
}

async function cmdPublishIntel(
  sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.publishIntel", body);
  const title = str(args.title ?? "").trim();
  const sourceUrl = str(args.url ?? "").trim();
  if (!title || !sourceUrl)
    return { ok: false, published: false, error: "title and url required" };
  return publishIntelPost(sdk, {
    id: str(
      args.id ??
        articleKey(str(args.sourceId ?? "intel"), `${sourceUrl}:${title}`)
    ),
    title,
    summary: str(args.summary ?? title),
    sourceUrl,
    sourceId: str(args.sourceId ?? "intel"),
    writerDid: str(args.writerDid ?? ""),
    socialPost: str(args.socialPost ?? ""),
  });
}

async function cmdStats(_sdk: HostSDK, _body: Uint8Array): Promise<unknown> {
  const db = createKyselyDb();
  const repos = RSS_SOURCES.map((s) => writerDID(s.id));
  const counts = await db
    .selectFrom("mv_vertex_article_count_by_repo" as any)
    .select(["repo", "cnt"])
    .where("repo", "in", repos)
    .execute();
  const total = counts.reduce((sum, r) => sum + (Number(r.cnt) || 0), 0);
  return { total, bySource: counts };
}

/** Diagnostic: sample Article nodes to check their properties */
async function cmdArticleDiag(
  _sdk: HostSDK,
  body: Uint8Array
): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.articleDiag", body);
  const rkey = str(args.rkey ?? "");
  // Sample Articles - check all accessible properties
  const db = createKyselyDb();
  const sample = rkey
    ? await db
        .selectFrom("vertex_article")
        .selectAll()
        .where("rkey", "=", rkey)
        .limit(1)
        .execute()
    : await db
        .selectFrom("vertex_article")
        .selectAll()
        .where("repo", "=", writerDID("gematsu"))
        .limit(3)
        .execute();
  return { rkey, count: sample.length, sample: sample.slice(0, 3) };
}

/** Diagnostic: list PDS records directly (bypasses graph, checks PDS write path) */
async function cmdPdsDiag(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.news.pdsDiag", body);
  const sourceId = str(args.sourceId ?? "gematsu");
  const writerRepo = writerDID(sourceId);
  const primaryRepo = sdk.pds.selfRepo;

  // Try listing records for writer DID and primary DID
  const results: Record<string, unknown> = { writerRepo, primaryRepo };
  for (const [key, repo] of [
    ["writer", writerRepo],
    ["primary", primaryRepo],
  ] as const) {
    try {
      const result = await sdk.pds.listRecords("com.etzhayyim.apps.news.article", {
        repo,
        limit: 3,
      });
      const recs = result as { records?: unknown[] };
      results[key] = {
        count: recs.records?.length ?? 0,
        sample: recs.records?.slice(0, 1),
      };
    } catch (e) {
      const err = e as Record<string, unknown>;
      results[key] = {
        error: err?.message ?? JSON.stringify(err).slice(0, 200),
      };
    }
  }
  return results;
}

// ── Reactive Pipeline (Layer 1: ComAtprotoSyncSubscribeRepos) ─────────────────

function handleComAtprotoSyncSubscribeReposCommit(
  sdk: HostSDK,
  commit: ComAtprotoSyncSubscribeReposCommit
): { ok: true; detail: string } {
  if (commit.action !== "create")
    return { ok: true, detail: "skip non-create" };
  const collection = str(commit.collection ?? "");

  if (collection === "com.etzhayyim.apps.news.article") {
    // Own article created — social evolution (like/repost by nwscr001 primary DID)
    return { ok: true, detail: "ownArticle" };
  }

  if (
    collection === "app.bsky.feed.like" ||
    collection === "app.bsky.feed.repost"
  ) {
    // Engagement on writer DID posts — handled by shinka layer (Layer 3)
    return { ok: true, detail: "engagement" };
  }

  if (collection === "app.bsky.feed.post") {
    // agent mention — social evolution handles
    return { ok: true, detail: "mention" };
  }

  return { ok: true, detail: "commit accepted" };
}

// ── Shinka Heartbeat (Layer 3) ────────────────────────────────────────────────

export async function runHeartbeat(
  sdk: HostSDK
): Promise<{ ok: boolean; actions: Array<Record<string, unknown>> }> {
  const actions: Array<Record<string, unknown>> = [];
  const ts = nowISO();
  const cadence = await resolveHeartbeatCadence(
    `did:web:${APP_NANOID}.etzhayyim.com`,
    cadenceState,
    inbox
  );
  actions.push({
    action: "cadenceResolved",
    mood: cadence.mood,
    reason: cadence.reason,
    ts,
  });

  // Periodic ingest triggered by heartbeat cadence (supplement to CF cron)
  if (cadence.mood === "active" || cadence.mood === "curious") {
    if (str((sdk.env as Record<string, unknown>).NEWS_LIVE_AUDIO_SCHEDULER_DISABLED).toLowerCase() === "true") {
      actions.push({
        action: "liveAudioScheduler",
        detail: "disabled",
        ts,
      });
    } else {
      const scheduled = await cmdScheduleLiveAudioIngest(
        sdk,
        new TextEncoder().encode(JSON.stringify({ maxLaunches: 3 }))
      );
      actions.push({
        action: "liveAudioScheduler",
        result: scheduled as Record<string, unknown>,
        ts,
      });
    }
  }

  return { ok: true, actions };
}

// ── App Export ────────────────────────────────────────────────────────────────

export { handleComAtprotoSyncSubscribeReposCommit };

// RSS fetch/parse/translation now belongs to the LangServer pipeline.
// This worker remains the edge command surface plus PDS write boundary.

const _workerInner = createWorkerExport((sdk) => {
  sdk.app
    .command(
      nsid("com.etzhayyim.apps.news.ingest"),
      (_ctx, body) => cmdIngest(sdk, body),
      asAgentTool(
        "Start RSS ingest through the LangServer pipeline. Edge worker no longer fetches/translates feeds directly."
      ),
      withCapabilityTags("pipeline", "ingest", "rss")
    )
    .command(
      nsid("com.etzhayyim.apps.news.liveAudioIngest"),
      (_ctx, body) => cmdLiveAudioIngest(sdk, body),
      asAgentTool(
        "Start public live-news/radio audio ingestion through LangServer: capture, transcribe, extract, and analyze as news intel."
      ),
      withCapabilityTags("pipeline", "ingest", "audio", "radio", "intel")
    )
    .command(
      nsid("com.etzhayyim.apps.news.registerLiveAudioSource"),
      (_ctx, body) => cmdRegisterLiveAudioSource(sdk, body),
      asAgentTool(
        "Register or update a public live-news/radio stream source for scheduled live audio ingest."
      ),
      withCapabilityTags("write", "news", "sources", "audio", "radio")
    )
    .command(
      nsid("com.etzhayyim.apps.news.scheduleLiveAudioIngest"),
      (_ctx, body) => cmdScheduleLiveAudioIngest(sdk, body),
      asAgentTool(
        "Dispatch due active live-news/radio sources to the live audio ingest BPMN process with cadence and cooldown state."
      ),
      withCapabilityTags("pipeline", "scheduler", "news", "audio", "radio")
    )
    .command(
      nsid("com.etzhayyim.apps.news.commitArticle"),
      (_ctx, body) => cmdCommitArticle(sdk, body),
      asAgentTool(
        "Thin edge write boundary for LangServer RSS pipeline. Writes article record and optional social post."
      ),
      withCapabilityTags("edge", "write", "news", "rss")
    )
    .command(
      nsid("com.etzhayyim.apps.news.listArticles"),
      (_ctx, body) => cmdListArticles(sdk, body),
      asAgentTool(
        "List ingested news articles (filter by sourceId, lang, category)"
      ),
      withCapabilityTags("query", "news")
    )
    .command(
      nsid("com.etzhayyim.apps.news.getArticle"),
      (_ctx, body) => cmdGetArticle(sdk, body),
      asAgentTool("Get news article by ID"),
      withCapabilityTags("query", "news")
    )
    .command(
      nsid("com.etzhayyim.apps.news.listSources"),
      (_ctx, body) => cmdListSources(sdk, body),
      asAgentTool("List all RSS sources with writer DIDs"),
      withCapabilityTags("query", "news", "sources")
    )
    .command(
      nsid("com.etzhayyim.apps.news.stats"),
      (_ctx, body) => cmdStats(sdk, body),
      asAgentTool("News ingestion stats (total articles, per-source counts)"),
      withCapabilityTags("analytics", "news")
    )
    .query(nsid("com.etzhayyim.apps.news.listIntelSources"), (_ctx, body) =>
      cmdListIntelSources(sdk, body)
    )
    .query(nsid("com.etzhayyim.apps.news.listLiveAudioSources"), (_ctx, body) =>
      cmdListLiveAudioSources(sdk, body)
    )
    .query(nsid("com.etzhayyim.apps.news.auditLiveAudioPolicies"), (_ctx, body) =>
      cmdAuditLiveAudioPolicies(sdk, body)
    )
    .command(
      nsid("com.etzhayyim.apps.news.analyzeIntel"),
      (_ctx, body) => cmdAnalyzeIntel(sdk, body),
      asAgentTool(
        "Analyze primary/official-source evidence into an attributed intel report and optionally publish it."
      ),
      withCapabilityTags("pipeline", "intel", "analysis")
    )
    .command(
      nsid("com.etzhayyim.apps.news.publishIntel"),
      (_ctx, body) => cmdPublishIntel(sdk, body),
      asAgentTool(
        "Publish a prepared intel brief through a news.etzhayyim.com writer DID."
      ),
      withCapabilityTags("publish", "intel", "news")
    )
    .command(
      nsid("com.etzhayyim.apps.news.articleDiag"),
      (_ctx, body) => cmdArticleDiag(sdk, body),
      asAgentTool(
        "Diagnostic: sample Article nodes to inspect their properties"
      ),
      withCapabilityTags("debug", "news")
    )
    .command(
      nsid("com.etzhayyim.apps.news.pdsDiag"),
      (_ctx, body) => cmdPdsDiag(sdk, body),
      asAgentTool("Diagnostic: check PDS records directly for a source"),
      withCapabilityTags("debug", "news")
    );
});

export default _workerInner;
