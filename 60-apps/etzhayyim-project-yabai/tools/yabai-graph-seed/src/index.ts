import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";

const YABAI_CONTEXT = "https://yabai.etzhayyim.com/ontology/context.jsonld";
const YABAI_BASE_ID = "https://yabai.etzhayyim.com/content";
const EMAIL_RE = /[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}/gi;

// ── Types ──

interface CrawlPage {
  identifier: string;
  url: string;
  name: string;
  httpStatus: number;
}

interface TIIndicator {
  type: string;
  value: string;
  severity: string;
  source: string;
  tags: string[];
}

interface WatchlistSignal {
  entityType: string;
  value: string;
  category: string;
  source: string;
  confidence: number;
  severity: number;
  probability: number;
  jurisdiction: string;
}

interface Entity {
  id: string;
  entityID: string;
  type: string;
  canonicalName: string;
  aliases: Set<string>;
  contacts: Set<string>;
  websites: Set<string>;
  evidenceIDs: string[];
}

interface Evidence {
  id: string;
  evidenceID: string;
  entityID: string;
  category: string;
  source: string;
  sourceReliability: string;
  occurredAt: string;
  confidence: number;
  severity: number;
  probability: number;
  jurisdiction: string;
  summary: string;
}

interface RiskScore {
  entityID: string;
  wellBecomingScore: number;
  penaltyScore: number;
  yabaiRiskScore: number;
  infoRisk: number;
  scoredAt: string;
}

// ── Main ──

function main(): void {
  const args = parseArgs();

  const repoRoot = findRepoRoot();
  const resourcesRoot = args.resourcesRoot || path.join(repoRoot, "projects", "etzhayyim-project-resources", "content");
  const outputRoot = args.outputRoot || path.join(repoRoot, "projects", "etzhayyim-project-yabai", "content");

  const entities = new Map<string, Entity>();
  const evidences: Evidence[] = [];
  const now = new Date().toISOString();

  const crawlPages = readCrawlPages(resourcesRoot);
  for (const p of crawlPages) {
    applyCrawlPage(entities, evidences, p, now);
  }

  const tiIndicators = readTIIndicators(resourcesRoot);
  for (const i of tiIndicators) {
    applyTIIndicator(entities, evidences, i, now);
  }

  const watchSignals = readWatchlistSignals(outputRoot);
  for (const ws of watchSignals) {
    applyWatchlistSignal(entities, evidences, ws, now);
  }

  const legalHits = readLegalSignals(resourcesRoot);
  evidences.push(...legalHits);

  const riskByEntity = scoreAll(entities, evidences, now);
  const topRisk = sortedTopRisk(riskByEntity, 20);

  if (args.dryRun) {
    console.log(`resourcesRoot: ${resourcesRoot}`);
    console.log(`output: ${outputRoot}`);
    console.log(`crawlPages: ${crawlPages.length}`);
    console.log(`tiIndicators: ${tiIndicators.length}`);
    console.log(`watchlistSignals: ${watchSignals.length}`);
    console.log(`entities: ${entities.size}`);
    console.log(`evidences: ${evidences.length}`);
    console.log(`riskScores: ${riskByEntity.size}`);
    console.log(`topRisk: ${topRisk.join(",")}`);
    return;
  }

  writeOutput(outputRoot, entities, evidences, riskByEntity, resourcesRoot, now, topRisk);
  console.log(`wrote yabai output: entities=${entities.size} evidences=${evidences.length} risk=${riskByEntity.size}`);
}

// ── CLI Args ──

function parseArgs(): { resourcesRoot: string; outputRoot: string; dryRun: boolean } {
  const result = { resourcesRoot: "", outputRoot: "", dryRun: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--resources-root" && argv[i + 1]) {
      result.resourcesRoot = argv[++i];
    } else if (argv[i] === "--output" && argv[i + 1]) {
      result.outputRoot = argv[++i];
    } else if (argv[i] === "--dry-run") {
      result.dryRun = true;
    }
  }
  return result;
}

// ── File Readers ──

function readCrawlPages(resourcesRoot: string): CrawlPage[] {
  const pagesDir = path.join(resourcesRoot, "crawl", "page");
  if (!fs.existsSync(pagesDir)) return [];

  const pages: CrawlPage[] = [];
  walkJsonld(pagesDir, (filePath) => {
    const body = fs.readFileSync(filePath, "utf-8");
    try {
      const p = JSON.parse(body) as CrawlPage;
      if (p.url) pages.push(p);
    } catch {
      // skip malformed
    }
  });
  return pages;
}

function readTIIndicators(resourcesRoot: string): TIIndicator[] {
  const tiDir = path.join(resourcesRoot, "ti", "indicator");
  if (!fs.existsSync(tiDir)) return [];

  const items: TIIndicator[] = [];
  walkJsonld(tiDir, (filePath) => {
    const body = fs.readFileSync(filePath, "utf-8");
    try {
      const parsed = JSON.parse(body);
      const x: TIIndicator = {
        type: strV(parsed.type),
        value: strV(parsed.value),
        severity: strV(parsed.severity),
        source: strV(parsed.source),
        tags: Array.isArray(parsed.tags) ? parsed.tags.map(String) : [],
      };
      if (x.value) items.push(x);
    } catch {
      // skip malformed
    }
  });
  return items;
}

function readWatchlistSignals(outputRoot: string): WatchlistSignal[] {
  const watchPath = path.join(outputRoot, "source", "watchlist.jsonld");
  if (!fs.existsSync(watchPath)) return [];

  const body = fs.readFileSync(watchPath, "utf-8");
  const v = JSON.parse(body) as Record<string, unknown>;
  const raw = (v.signals ?? []) as Record<string, unknown>[];
  const out: WatchlistSignal[] = [];

  for (const m of raw) {
    const ws: WatchlistSignal = {
      entityType: strV(m.entityType).trim(),
      value: strV(m.value).trim(),
      category: strV(m.category).trim(),
      source: strV(m.source).trim(),
      confidence: numV(m.confidence, 0.65),
      severity: Math.trunc(numV(m.severity, 3)),
      probability: numV(m.probability, 0.1),
      jurisdiction: strV(m.jurisdiction).trim(),
    };
    if (!ws.value) continue;
    if (!ws.source) ws.source = "yabai/watchlist";
    if (!ws.category) ws.category = "FraudSignal";
    out.push(ws);
  }
  return out;
}

function readLegalSignals(resourcesRoot: string): Evidence[] {
  const legalDir = path.join(resourcesRoot, "legal");
  if (!fs.existsSync(legalDir)) return [];

  const out: Evidence[] = [];
  walkJsonld(legalDir, (filePath) => {
    if (filePath.includes("global-legal-data-sources")) return;
    if (!looksLikeSanctionOrCriminal(filePath)) return;

    const eid = hashID("evidence", filePath);
    out.push({
      id: YABAI_BASE_ID + "/evidence/" + eid,
      evidenceID: eid,
      entityID: "global-legal-watch",
      category: "CriminalEvidence",
      source: "resources/legal",
      sourceReliability: "B",
      occurredAt: new Date().toISOString(),
      confidence: 0.55,
      severity: 2,
      probability: 0.20,
      jurisdiction: "",
      summary: "Legal dataset contains criminal/sanction-related material",
    });
  });
  return out;
}

// ── Apply functions ──

function applyCrawlPage(entities: Map<string, Entity>, evidences: Evidence[], p: CrawlPage, now: string): void {
  let u: URL;
  try {
    u = new URL(p.url);
  } catch {
    return;
  }
  if (!u.host) return;

  const host = u.host.toLowerCase();
  const eKey = "site:" + host;
  const e = ensureEntity(entities, eKey, "WebSite", host);
  e.websites.add(p.url);
  if (p.name) e.aliases.add(p.name);

  const mailMatches = [p.url, p.name].join(" ").toLowerCase().match(EMAIL_RE);
  if (mailMatches) {
    for (const m of mailMatches) {
      const me = ensureEntity(entities, "email:" + m, "ContactPoint", m);
      me.contacts.add(m);
      const ev = newEvidence(me.entityID, "FraudSignal", "resources/crawl", "C", now, 0.45, 2, 0.35, "Email discovered in crawled content");
      evidences.push(ev);
      me.evidenceIDs.push(ev.evidenceID);
    }
  }

  const penalty = crawlPenalty(p);
  if (penalty) {
    const ev = newEvidence(e.entityID, penalty.category, "resources/crawl", "B", now, penalty.confidence, penalty.severity, penalty.probability, summaryForCrawl(p, penalty.category));
    evidences.push(ev);
    e.evidenceIDs.push(ev.evidenceID);
  }
}

function applyTIIndicator(entities: Map<string, Entity>, evidences: Evidence[], i: TIIndicator, now: string): void {
  const value = i.value.trim().toLowerCase();
  if (!value) return;

  let etype = "Thing";
  let key = "indicator:" + value;
  if (value.includes("@")) {
    etype = "ContactPoint";
    key = "email:" + value;
  } else if (value.includes("/") || value.startsWith("http")) {
    etype = "WebSite";
    key = "url:" + value;
  } else if (value.includes(".")) {
    etype = "WebSite";
    key = "domain:" + value;
  }

  const e = ensureEntity(entities, key, etype, value);
  if (etype === "ContactPoint") e.contacts.add(value);
  if (etype === "WebSite") e.websites.add(value);

  const tagsLower = (i.tags || []).join(",").toLowerCase();
  let cat = "FraudSignal";
  if (tagsLower.includes("aml")) cat = "AMLPattern";
  if (tagsLower.includes("sanction")) cat = "SanctionHit";
  if (tagsLower.includes("crime")) cat = "CriminalEvidence";

  let conf = 0.65;
  let sev = 3;
  let prob = 0.15;
  switch (i.severity.toLowerCase()) {
    case "critical":
      conf = 0.9; sev = 5; prob = 0.02; break;
    case "high":
      conf = 0.82; sev = 4; prob = 0.06; break;
    case "low":
      conf = 0.45; sev = 1; prob = 0.40; break;
  }

  let summary = "TI indicator linked from resources";
  if (i.type || i.source) {
    summary = `TI indicator type=${i.type} source=${i.source}`;
  }
  const ev = newEvidence(e.entityID, cat, "resources/ti", "A", now, conf, sev, prob, summary);
  evidences.push(ev);
  e.evidenceIDs.push(ev.evidenceID);
}

function applyWatchlistSignal(entities: Map<string, Entity>, evidences: Evidence[], ws: WatchlistSignal, now: string): void {
  const value = ws.value.trim().toLowerCase();
  if (!value) return;

  let etype = ws.entityType.trim();
  let key = "watch:" + value;
  if (etype) {
    key = etype.toLowerCase() + ":" + value;
  } else if (value.includes("@")) {
    etype = "ContactPoint";
    key = "email:" + value;
  } else if (value.includes("/") || value.startsWith("http")) {
    etype = "WebSite";
    key = "url:" + value;
  } else {
    etype = "Thing";
  }

  const e = ensureEntity(entities, key, etype, value);
  if (etype === "ContactPoint") e.contacts.add(value);
  if (etype === "WebSite") e.websites.add(value);

  const ev = newEvidence(e.entityID, ws.category, ws.source, "A", now, ws.confidence, ws.severity, ws.probability, "Watchlist signal");
  ev.jurisdiction = ws.jurisdiction;
  evidences.push(ev);
  e.evidenceIDs.push(ev.evidenceID);
}

// ── Scoring ──

function scoreAll(entities: Map<string, Entity>, evidences: Evidence[], now: string): Map<string, RiskScore> {
  const group = new Map<string, Evidence[]>();
  for (const ev of evidences) {
    if (!ev.entityID) continue;
    const arr = group.get(ev.entityID) ?? [];
    arr.push(ev);
    group.set(ev.entityID, arr);
  }

  const out = new Map<string, RiskScore>();
  for (const e of entities.values()) {
    const evs = group.get(e.entityID) ?? [];
    if (evs.length === 0) {
      out.set(e.entityID, {
        entityID: e.entityID,
        wellBecomingScore: 72,
        penaltyScore: 5,
        yabaiRiskScore: 32,
        infoRisk: 0,
        scoredAt: now,
      });
      continue;
    }

    let penaltyRaw = 0;
    let infoRisk = 0;
    for (const ev of evs) {
      const sevWeight = ev.severity / 5.0;
      penaltyRaw += ev.severity * ev.confidence;
      const prob = clamp(ev.probability, 0.0001, 0.9999);
      infoRisk += -Math.log2(prob) * ev.confidence * sevWeight;
    }

    const penaltyScore = clamp(penaltyRaw * 7.5, 0, 100);
    const well = clamp(90.0 - penaltyScore * 0.55 - Math.min(25, infoRisk * 0.8), 0, 100);
    const yabai = clamp(100.0 - well + penaltyScore * 0.8, 0, 100);

    out.set(e.entityID, {
      entityID: e.entityID,
      wellBecomingScore: round1(well),
      penaltyScore: round1(penaltyScore),
      yabaiRiskScore: round1(yabai),
      infoRisk: round2(infoRisk),
      scoredAt: now,
    });
  }
  return out;
}

// ── Output Writer ──

function writeOutput(
  outputRoot: string,
  entities: Map<string, Entity>,
  evidences: Evidence[],
  riskByEntity: Map<string, RiskScore>,
  resourceRoot: string,
  now: string,
  topRisk: string[],
): void {
  const entityDir = path.join(outputRoot, "entity");
  const evidenceDir = path.join(outputRoot, "evidence");
  const riskDir = path.join(outputRoot, "risk");

  fs.mkdirSync(entityDir, { recursive: true });
  fs.mkdirSync(evidenceDir, { recursive: true });
  fs.mkdirSync(riskDir, { recursive: true });

  clearJsonld(entityDir);
  clearJsonld(evidenceDir);
  clearJsonld(riskDir);

  const entityList = [...entities.values()].sort((a, b) => a.entityID.localeCompare(b.entityID));
  for (const e of entityList) {
    writeJSON(path.join(entityDir, e.entityID + ".jsonld"), {
      "@context": YABAI_CONTEXT,
      "@type": e.type,
      "@id": e.id,
      entityId: e.entityID,
      canonicalName: e.canonicalName,
      aliases: sortedSet(e.aliases),
      contacts: sortedSet(e.contacts),
      websites: sortedSet(e.websites),
    });
  }

  const sortedEvidences = [...evidences].sort((a, b) => a.evidenceID.localeCompare(b.evidenceID));
  for (const ev of sortedEvidences) {
    const doc: Record<string, unknown> = {
      "@context": YABAI_CONTEXT,
      "@type": "etzhayyim:YabaiEvidence",
      "@id": ev.id,
      evidenceId: ev.evidenceID,
      entityId: ev.entityID,
      category: ev.category,
      source: ev.source,
      sourceReliability: ev.sourceReliability,
      occurredAt: ev.occurredAt,
      confidence: round2(ev.confidence),
      severity: ev.severity,
      probability: round4(ev.probability),
    };
    if (ev.jurisdiction) doc.jurisdiction = ev.jurisdiction;
    if (ev.summary) doc.summary = ev.summary;
    writeJSON(path.join(evidenceDir, ev.evidenceID + ".jsonld"), doc);
  }

  const riskIDs = [...riskByEntity.keys()].sort();
  for (const id of riskIDs) {
    const rs = riskByEntity.get(id)!;
    writeJSON(path.join(riskDir, id + ".jsonld"), {
      "@context": YABAI_CONTEXT,
      "@type": "etzhayyim:YabaiRiskScore",
      "@id": YABAI_BASE_ID + "/risk/" + id,
      entityId: rs.entityID,
      wellBecomingScore: rs.wellBecomingScore,
      penaltyScore: rs.penaltyScore,
      yabaiRiskScore: rs.yabaiRiskScore,
      infoRisk: rs.infoRisk,
      scoredAt: rs.scoredAt,
    });
  }

  writeJSON(path.join(outputRoot, "index.jsonld"), {
    "@context": YABAI_CONTEXT,
    "@type": "Dataset",
    "@id": YABAI_BASE_ID + "/index",
    generatedAt: now,
    resourceRoot,
    entityCount: entities.size,
    evidenceCount: evidences.length,
    riskCount: riskByEntity.size,
    topRisk,
  });
}

// ── Helpers ──

function ensureEntity(m: Map<string, Entity>, key: string, entityType: string, canonical: string): Entity {
  const existing = m.get(key);
  if (existing) {
    if (canonical) existing.aliases.add(canonical);
    return existing;
  }
  const entityID = shortID(key);
  const e: Entity = {
    id: YABAI_BASE_ID + "/entity/" + entityID,
    entityID,
    type: entityType,
    canonicalName: canonical,
    aliases: new Set(canonical ? [canonical] : []),
    contacts: new Set(),
    websites: new Set(),
    evidenceIDs: [],
  };
  m.set(key, e);
  return e;
}

function newEvidence(
  entityID: string,
  category: string,
  source: string,
  reliability: string,
  occurredAt: string,
  confidence: number,
  severity: number,
  probability: number,
  summary: string,
): Evidence {
  const seed = [entityID, category, source, occurredAt, summary].join("|");
  const eid = hashID("evidence", seed);
  return {
    id: YABAI_BASE_ID + "/evidence/" + eid,
    evidenceID: eid,
    entityID,
    category,
    source,
    sourceReliability: reliability,
    occurredAt,
    confidence: clamp(confidence, 0, 1),
    severity: Math.trunc(clamp(severity, 1, 5)),
    probability: clamp(probability, 0.0001, 0.9999),
    jurisdiction: "",
    summary,
  };
}

function crawlPenalty(p: CrawlPage): { category: string; confidence: number; severity: number; probability: number } | null {
  const joined = [p.url, p.name].join(" ").toLowerCase();
  if (joined.includes("phishing") || joined.includes("fraud") || joined.includes("scam")) {
    return { category: "FraudSignal", confidence: 0.72, severity: 4, probability: 0.08 };
  }
  if (joined.includes("aml") || joined.includes("money laundering")) {
    return { category: "AMLPattern", confidence: 0.66, severity: 4, probability: 0.10 };
  }
  if (p.httpStatus >= 400) {
    return { category: "FraudSignal", confidence: 0.42, severity: 2, probability: 0.35 };
  }
  return null;
}

function summaryForCrawl(p: CrawlPage, category: string): string {
  if (p.name) {
    return `crawl page ${p.identifier} (${p.name}) matched ${category}`;
  }
  return `crawl page ${p.identifier} matched ${category}`;
}

function looksLikeSanctionOrCriminal(filePath: string): boolean {
  const p = filePath.toLowerCase();
  const keywords = ["sanction", "crime", "criminal", "terror", "fraud", "money-laundering", "aml", "\u53cd\u793e", "\u72af\u7f6a"];
  return keywords.some((k) => p.includes(k));
}

function sortedTopRisk(scores: Map<string, RiskScore>, limit: number): string[] {
  const rows = [...scores.values()];
  rows.sort((a, b) => {
    if (a.yabaiRiskScore !== b.yabaiRiskScore) return b.yabaiRiskScore - a.yabaiRiskScore;
    return a.entityID.localeCompare(b.entityID);
  });
  return rows.slice(0, limit).map((r) => `${r.entityID}:${r.yabaiRiskScore.toFixed(1)}`);
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

function hashID(prefix: string, raw: string): string {
  const h = crypto.createHash("sha1").update(prefix + ":" + raw).digest("hex");
  return prefix + "-" + h.substring(0, 16);
}

function shortID(raw: string): string {
  const h = crypto.createHash("sha1").update(raw).digest("hex");
  return "ent-" + h.substring(0, 12);
}

function sortedSet(s: Set<string>): string[] {
  return [...s].sort();
}

function walkJsonld(dir: string, callback: (filePath: string) => void): void {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkJsonld(fullPath, callback);
    } else if (entry.name.endsWith(".jsonld")) {
      callback(fullPath);
    }
  }
}

function clearJsonld(dir: string): void {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory() && entry.name.endsWith(".jsonld")) {
      fs.unlinkSync(path.join(dir, entry.name));
    }
  }
}

function writeJSON(filePath: string, v: unknown): void {
  fs.writeFileSync(filePath, JSON.stringify(v, null, 2) + "\n", "utf-8");
}

function strV(v: unknown): string {
  return typeof v === "string" ? v.trim() : "";
}

function numV(v: unknown, d: number): number {
  if (typeof v === "number") return v;
  return d;
}

function clamp(v: number, min: number, max: number): number {
  if (v < min) return min;
  if (v > max) return max;
  return v;
}

function round1(v: number): number { return Math.round(v * 10) / 10; }
function round2(v: number): number { return Math.round(v * 100) / 100; }
function round4(v: number): number { return Math.round(v * 10000) / 10000; }

main();
