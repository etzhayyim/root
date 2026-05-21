// lead-sources/hn.ts — Hacker News Algolia scraper.
//
// Source:  https://hn.algolia.com/api/v1/search
// Tags:    `story` only (skip comments — too low SNR)
// Window:  last 7 days by default
// Queries: graph DB / supabase / neo4j / hasura / dgraph / arangodb / firebase migration
//
// For each story:
//   - Take story.url (if present)
//   - Skip if hostname is an aggregator (HN, Reddit, GitHub topic listings, …)
//   - Use hostname (e.g. "company.com") as both `domain` and `company`
//   - signal = "HN: <title>"
//   - source_url = "https://news.ycombinator.com/item?id={objectID}"
//   - fit_score: heuristic per query keyword match
//
// All ingest goes through handleLeadIngest which dedupes by vertex_id.
// Scraper running every 6h is safe — repeated runs over the same window
// are no-ops for already-known domains.

import type { LeadIngest } from "../leads";

const HN_ALGOLIA = "https://hn.algolia.com/api/v1/search";

interface HnHit {
  title: string | null;
  url: string | null;
  author: string;
  story_text: string | null;
  points: number | null;
  num_comments: number | null;
  created_at_i: number;
  objectID: string;
  _tags?: string[];
}

interface HnSearchResp {
  hits: HnHit[];
  nbHits: number;
}

// Keyword bundles per signal strength. Higher = better fit for yatabase.
const QUERIES: Array<{ q: string; fit: number; tag: string }> = [
  { q: "graph database",  fit: 75, tag: "graph-db" },
  { q: "neo4j",           fit: 70, tag: "neo4j" },
  { q: "supabase",        fit: 65, tag: "supabase" },
  { q: "hasura",          fit: 65, tag: "hasura" },
  { q: "dgraph",          fit: 70, tag: "dgraph" },
  { q: "arangodb",        fit: 70, tag: "arangodb" },
  { q: "firebase migrate",fit: 60, tag: "firebase-migrate" },
];

// Hostname suffixes we never use as a lead — too generic / aggregator.
const SKIP_HOSTS = new Set([
  "news.ycombinator.com",
  "ycombinator.com",
  "ycombinator.org",
  "reddit.com",
  "twitter.com",
  "x.com",
  "youtube.com",
  "youtu.be",
  "medium.com",
  "github.com",     // skip generic; user-specific paths are not company signals
  "gitlab.com",
  "bitbucket.org",
  "stackoverflow.com",
  "wikipedia.org",
  "linkedin.com",
  "facebook.com",
  "amazon.com",
  "google.com",
  "microsoft.com",
  "openai.com",
  "anthropic.com",
  "huggingface.co",
  "arxiv.org",
  "dev.to",
  "substack.com",
  "wordpress.com",
  "blogspot.com",
  "notion.so",
]);

// Truncate hostname to its registrable domain. "blog.example.com" → "example.com".
// Keeps known multi-label suffixes (.co.uk, .co.jp, .com.br, .ne.jp, …).
const TWO_LABEL_TLD = new Set([
  "co.uk", "co.jp", "co.kr", "co.in", "co.nz", "com.au", "com.br",
  "com.cn", "com.mx", "com.tr", "com.tw", "ne.jp", "or.jp", "ac.jp",
  "ac.uk", "gov.uk", "gov.au",
]);

function registrableDomain(hostname: string): string {
  const h = hostname.toLowerCase().replace(/^\./, "");
  const parts = h.split(".");
  if (parts.length <= 2) return h;
  const lastTwo = parts.slice(-2).join(".");
  const lastThree = parts.slice(-3).join(".");
  // strip "co.uk" etc. → keep last 3 labels
  for (const seg of TWO_LABEL_TLD) {
    if (h.endsWith(`.${seg}`)) {
      return parts.slice(-3).join(".");
    }
  }
  return lastTwo;
}

function shouldSkip(hostname: string): boolean {
  if (SKIP_HOSTS.has(hostname)) return true;
  // Skip subdomains of skip list (e.g., "user.github.io" → blog hosting).
  for (const skip of SKIP_HOSTS) {
    if (hostname.endsWith(`.${skip}`)) return true;
  }
  // Skip github user pages and gist-style.
  if (hostname.endsWith(".github.io")) return true;
  return false;
}

export interface HnScrapeOpts {
  windowHours?: number;     // default 168 (7d)
  perQueryHits?: number;    // default 30
  maxLeads?: number;        // overall ingest cap, default 25
  fetcher?: typeof fetch;   // injectable for tests
}

export interface HnScrapeReport {
  candidates: number;
  unique_domains: number;
  produced_leads: LeadIngest[];
  skipped_no_url: number;
  skipped_aggregator: number;
  skipped_dup_in_batch: number;
  errors: string[];
}

/**
 * Fetch HN Algolia, transform into LeadIngest candidates. Pure function
 * (no DB writes) — caller pipes results through handleLeadIngest which
 * applies the cross-run idempotency check.
 */
export async function fetchHnLeads(opts: HnScrapeOpts = {}): Promise<HnScrapeReport> {
  const fetcher = opts.fetcher ?? fetch;
  const windowHours = Math.max(1, Math.min(720, opts.windowHours ?? 168));
  const perQueryHits = Math.max(1, Math.min(100, opts.perQueryHits ?? 30));
  const maxLeads = Math.max(1, Math.min(100, opts.maxLeads ?? 25));

  const sinceUnix = Math.floor(Date.now() / 1000) - windowHours * 3600;

  const report: HnScrapeReport = {
    candidates: 0,
    unique_domains: 0,
    produced_leads: [],
    skipped_no_url: 0,
    skipped_aggregator: 0,
    skipped_dup_in_batch: 0,
    errors: [],
  };

  const seenDomains = new Set<string>();

  for (const { q, fit, tag } of QUERIES) {
    if (report.produced_leads.length >= maxLeads) break;
    const url = new URL(HN_ALGOLIA);
    url.searchParams.set("query", q);
    url.searchParams.set("tags", "story");
    url.searchParams.set("numericFilters", `created_at_i>${sinceUnix}`);
    url.searchParams.set("hitsPerPage", String(perQueryHits));

    let resp: Response;
    try {
      resp = await fetcher(url.toString(), {
        headers: { "user-agent": "yatabase-lead-scraper/0.1 (+https://yatabase.gftd.ai)" },
      });
    } catch (e) {
      report.errors.push(`${tag}: fetch threw — ${e instanceof Error ? e.message : "unknown"}`);
      continue;
    }
    if (!resp.ok) {
      report.errors.push(`${tag}: HTTP ${resp.status}`);
      continue;
    }
    let data: HnSearchResp;
    try {
      data = (await resp.json()) as HnSearchResp;
    } catch (e) {
      report.errors.push(`${tag}: bad JSON — ${e instanceof Error ? e.message : "?"}`);
      continue;
    }

    for (const hit of data.hits ?? []) {
      report.candidates++;
      if (!hit.url) {
        report.skipped_no_url++;
        continue;
      }
      let parsed: URL;
      try {
        parsed = new URL(hit.url);
      } catch {
        report.skipped_no_url++;
        continue;
      }
      if (shouldSkip(parsed.hostname)) {
        report.skipped_aggregator++;
        continue;
      }
      const domain = registrableDomain(parsed.hostname);
      if (!domain || seenDomains.has(domain)) {
        report.skipped_dup_in_batch++;
        continue;
      }
      seenDomains.add(domain);

      const title = (hit.title ?? "").slice(0, 240);
      const points = hit.points ?? 0;
      // small bump for highly-engaged threads
      const adjFit = Math.min(95, fit + Math.min(15, Math.floor(points / 30)));

      report.produced_leads.push({
        company: domain,                                     // best we have until enrichment
        domain,
        source: "hn-scraper",
        source_url: `https://news.ycombinator.com/item?id=${hit.objectID}`,
        signal: `HN [${tag}, ${points}pts]: ${title}`,
        tech_stack: [tag],
        fit_score: adjFit,
        reasoning: `Linked from HN search for "${q}". Hit ${title}`.slice(0, 2000),
        notes: `points=${points} comments=${hit.num_comments ?? 0} author=${hit.author}`,
      });

      if (report.produced_leads.length >= maxLeads) break;
    }
  }

  report.unique_domains = seenDomains.size;
  return report;
}
