// referrer.ts — Signup referrer tracking for H1 funnel measurement (Sprint 1).
//
// KV schema (all under YATABASE_AUTH_CACHE):
//   referrer:v1:{orgDid}              → ReferrerRecord JSON (90-day TTL)
//   referrer_daily:v1:{src}:{date}    → count string     (60-day TTL)
//   referrer_convert:v1:{src}:{date}  → count string     (60-day TTL)
//
// Sources are normalised to a short slug (see normaliseSource).
// UTM params may be passed in the signup body; Referer header is the fallback.

export interface ReferrerRecord {
  orgDid: string;
  source: string;       // normalised slug, e.g. "cursor" | "github" | "direct"
  medium: string;       // utm_medium or "referral" / "direct"
  campaign: string;     // utm_campaign or ""
  rawReferer: string;   // original Referer header value
  signupDate: string;   // YYYY-MM-DD UTC
  convertedDate?: string;
  convertedPlan?: string;
}

export interface ReferrerEnv {
  YATABASE_AUTH_CACHE?: KVNamespace;
}

// Map of hostname fragment → source slug. Longest-match wins.
const SOURCE_MAP: Array<[string, string]> = [
  ["cursor.com",          "cursor"],
  ["cursor.sh",           "cursor"],
  ["claude.ai",           "claude-desktop"],
  ["anthropic.com",       "claude-desktop"],
  ["smithery.ai",         "smithery"],
  ["glama.ai",            "glama"],
  ["mcp.so",              "mcp-so"],
  ["pulsemcp.com",        "pulsemcp"],
  ["mcpservers.org",      "mcpservers"],
  ["mcp.etzhayyim.com",         "mcp-internal"],
  ["yatabase.etzhayyim.com",    "direct"],     // self-referral → direct
  ["github.com",          "github"],
  ["news.ycombinator.com","hackernews"],
  ["ycombinator.com",     "hackernews"],
  ["linkedin.com",        "linkedin"],
  ["twitter.com",         "twitter"],
  ["x.com",               "twitter"],
  ["reddit.com",          "reddit"],
  ["dev.to",              "devto"],
  ["producthunt.com",     "producthunt"],
  ["devhunt.org",         "devhunt"],
  ["google.com",          "google"],
  ["google.",             "google"],     // google.co.jp etc.
  ["bing.com",            "bing"],
  ["zenn.dev",            "zenn"],
  ["qiita.com",           "qiita"],
];

export function normaliseSource(
  utmSource: string,
  refererHeader: string,
): { source: string; medium: string } {
  if (utmSource) {
    const s = utmSource.toLowerCase().trim().slice(0, 64);
    return { source: s, medium: "utm" };
  }
  if (!refererHeader) return { source: "direct", medium: "direct" };
  let host = refererHeader.toLowerCase();
  try { host = new URL(refererHeader).hostname; } catch { /* keep raw */ }
  for (const [frag, slug] of SOURCE_MAP) {
    if (host.includes(frag)) return { source: slug, medium: "referral" };
  }
  // Unknown external domain — keep first two segments of hostname.
  const parts = host.replace(/^www\./, "").split(".");
  const slug = parts.slice(0, 2).join(".").slice(0, 32) || "unknown";
  return { source: slug, medium: "referral" };
}

const TTL_RECORD  = 90 * 24 * 3600;  // 90 days
const TTL_COUNTER = 60 * 24 * 3600;  // 60 days

async function kvIncr(kv: KVNamespace, key: string, ttl: number): Promise<void> {
  const raw = await kv.get(key);
  const n = raw ? parseInt(raw, 10) + 1 : 1;
  await kv.put(key, String(n), { expirationTtl: ttl });
}

export async function recordReferrer(
  env: ReferrerEnv,
  orgDid: string,
  utmSource: string,
  utmMedium: string,
  utmCampaign: string,
  refererHeader: string,
): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return;
  const { source, medium } = normaliseSource(utmSource, refererHeader);
  const today = new Date().toISOString().slice(0, 10);
  const record: ReferrerRecord = {
    orgDid,
    source,
    medium: utmMedium || medium,
    campaign: utmCampaign.slice(0, 64),
    rawReferer: refererHeader.slice(0, 256),
    signupDate: today,
  };
  await kv.put(`referrer:v1:${orgDid}`, JSON.stringify(record), { expirationTtl: TTL_RECORD });
  await kvIncr(kv, `referrer_daily:v1:${source}:${today}`, TTL_COUNTER);
}

export async function recordConversion(
  env: ReferrerEnv,
  orgDid: string,
  plan: string,
): Promise<void> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return;
  const raw = await kv.get(`referrer:v1:${orgDid}`);
  if (!raw) return;
  try {
    const rec = JSON.parse(raw) as ReferrerRecord;
    const today = new Date().toISOString().slice(0, 10);
    rec.convertedDate = today;
    rec.convertedPlan = plan;
    await kv.put(`referrer:v1:${orgDid}`, JSON.stringify(rec), { expirationTtl: TTL_RECORD });
    await kvIncr(kv, `referrer_convert:v1:${rec.source}:${today}`, TTL_COUNTER);
  } catch { /* ignore */ }
}

export interface ReferrerStats {
  windowDays: number;
  sources: Array<{
    source: string;
    signups: number;
    conversions: number;
    cvr: string;   // "12.5%"
  }>;
  total: { signups: number; conversions: number; cvr: string };
  generatedAt: string;
}

export async function getReferrerStats(
  env: ReferrerEnv,
  windowDays = 30,
): Promise<ReferrerStats> {
  const kv = env.YATABASE_AUTH_CACHE;
  const empty: ReferrerStats = {
    windowDays,
    sources: [],
    total: { signups: 0, conversions: 0, cvr: "0%" },
    generatedAt: new Date().toISOString(),
  };
  if (!kv) return empty;

  // Build date range.
  const dates: string[] = [];
  for (let i = 0; i < windowDays; i++) {
    const d = new Date(Date.now() - i * 24 * 3600 * 1000);
    dates.push(d.toISOString().slice(0, 10));
  }

  // Collect all source slugs that appear in the daily keys.
  // KV.list returns at most 1000 keys — enough for 30d × ~30 sources.
  const listed = await kv.list({ prefix: "referrer_daily:v1:" });
  const sources = new Set<string>();
  for (const key of listed.keys) {
    // key.name = "referrer_daily:v1:{source}:{date}"
    const parts = key.name.split(":");
    if (parts.length >= 4) sources.add(parts[2]);
  }

  const rows: ReferrerStats["sources"] = [];
  let totalSignups = 0;
  let totalConversions = 0;

  for (const source of sources) {
    let signups = 0;
    let conversions = 0;
    for (const date of dates) {
      const sv = await kv.get(`referrer_daily:v1:${source}:${date}`);
      const cv = await kv.get(`referrer_convert:v1:${source}:${date}`);
      signups    += sv ? parseInt(sv, 10) : 0;
      conversions += cv ? parseInt(cv, 10) : 0;
    }
    totalSignups    += signups;
    totalConversions += conversions;
    rows.push({
      source,
      signups,
      conversions,
      cvr: signups > 0 ? `${((conversions / signups) * 100).toFixed(1)}%` : "—",
    });
  }

  rows.sort((a, b) => b.signups - a.signups);

  return {
    windowDays,
    sources: rows,
    total: {
      signups: totalSignups,
      conversions: totalConversions,
      cvr: totalSignups > 0 ? `${((totalConversions / totalSignups) * 100).toFixed(1)}%` : "—",
    },
    generatedAt: new Date().toISOString(),
  };
}
