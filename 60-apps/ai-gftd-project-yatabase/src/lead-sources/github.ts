// lead-sources/github.ts — GitHub stargazers scraper.
//
// Strategy:
//   1. List the top N stargazers for each competitor repo (one HTTP call
//      per repo). Anyone who stars neo4j/supabase/hasura/dgraph/arangodb
//      is high-intent ICP for yatabase.
//   2. For each stargazer, fetch /users/{login} once. If their `blog`
//      field is a real domain, ingest that domain as a lead. Stargazers
//      who hide their blog are skipped (we don't want to email people
//      we don't have a public reachable surface for).
//
// Compliance:
//   - Read-only against public APIs. No issue creation, no follow.
//   - Self-identifying User-Agent so GitHub can rate-limit us.
//   - Conditional on `GITHUB_TOKEN` env: with it 5000/h budget, without
//     it 60/h. Default `maxUsers` is conservative enough to fit the
//     unauthed budget across 4 daily fires (30 users × 4 fires = 120
//     /day, well under 60 × 24 = 1440 unauthed/day).
//   - Rate limits + 4xx fail soft; we never throw past the helper.

import type { LeadIngest } from "../leads";

const REPOS = [
  { owner: "neo4j",     repo: "neo4j",          tag: "neo4j",     fit: 78 },
  { owner: "supabase",  repo: "supabase",       tag: "supabase",  fit: 72 },
  { owner: "hasura",    repo: "graphql-engine", tag: "hasura",    fit: 70 },
  { owner: "dgraph-io", repo: "dgraph",         tag: "dgraph",    fit: 76 },
  { owner: "ArangoDB",  repo: "arangodb",       tag: "arangodb",  fit: 74 },
];

const USER_AGENT =
  "yatabase-github-bot/0.1 (+https://yatabase.gftd.ai/.well-known/agent.json)";

const TWO_LABEL_TLD = new Set([
  "co.uk", "co.jp", "co.kr", "co.in", "co.nz", "com.au", "com.br",
  "com.cn", "com.mx", "com.tr", "com.tw", "ne.jp", "or.jp", "ac.jp",
  "ac.uk", "gov.uk", "gov.au",
]);

// Aggregator hosts to skip. If a stargazer's `blog` points at one of
// these we have no domain-of-interest to ingest.
const SKIP_HOSTS = new Set([
  "github.com", "github.io", "gitlab.com", "bitbucket.org",
  "twitter.com", "x.com", "linkedin.com", "facebook.com",
  "medium.com", "dev.to", "substack.com", "wordpress.com",
  "blogspot.com", "notion.so", "gitee.com", "bsky.app",
  "youtube.com", "youtu.be", "instagram.com", "reddit.com",
  "stackoverflow.com", "wikipedia.org",
]);

interface GhStargazer {
  login: string;
  id: number;
  html_url: string;
}
interface GhUser {
  login: string;
  blog?: string | null;
  company?: string | null;
  bio?: string | null;
  public_repos?: number;
  followers?: number;
}

function registrableDomain(hostname: string): string {
  const h = hostname.toLowerCase().replace(/^\./, "").replace(/^www\./, "");
  const parts = h.split(".");
  if (parts.length <= 2) return h;
  for (const seg of TWO_LABEL_TLD) {
    if (h.endsWith(`.${seg}`)) return parts.slice(-3).join(".");
  }
  return parts.slice(-2).join(".");
}

const VALID_DOMAIN = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/i;

function blogToDomain(blog: string | null | undefined): string | null {
  if (!blog) return null;
  const raw = blog.trim();
  if (!raw) return null;
  let url: URL;
  try {
    // Most users prefix with http/https; some omit. Add a default scheme.
    url = new URL(/^https?:/i.test(raw) ? raw : `https://${raw}`);
  } catch {
    return null;
  }
  const host = url.hostname.toLowerCase();
  if (SKIP_HOSTS.has(host)) return null;
  for (const skip of SKIP_HOSTS) {
    if (host.endsWith(`.${skip}`)) return null;
  }
  const dom = registrableDomain(host);
  if (!VALID_DOMAIN.test(dom)) return null;
  return dom;
}

export interface GithubScrapeOpts {
  perRepo?: number;            // stargazers fetched per repo (default 20)
  maxUsers?: number;           // overall cap on /users/{login} fetches (default 30)
  reposLimit?: number;         // how many of REPOS[] to scan this fire (default 2 — rotate across days)
  githubToken?: string;        // optional, env GITHUB_TOKEN
  fetcher?: typeof fetch;
}

export interface GithubScrapeReport {
  repos_scanned: string[];
  stargazers_seen: number;
  user_fetches: number;
  rate_limit_hits: number;
  produced_leads: LeadIngest[];
  skipped_no_blog: number;
  skipped_aggregator_blog: number;
  skipped_dup_in_batch: number;
  errors: string[];
}

/**
 * Pure function — fetches GitHub, transforms into LeadIngest candidates.
 * Caller passes results through handleLeadIngest which dedups by vertex_id.
 */
export async function fetchGithubLeads(opts: GithubScrapeOpts = {}): Promise<GithubScrapeReport> {
  const fetcher = opts.fetcher ?? fetch;
  const perRepo = Math.max(1, Math.min(100, opts.perRepo ?? 20));
  const maxUsers = Math.max(1, Math.min(60, opts.maxUsers ?? 30));
  const reposLimit = Math.max(1, Math.min(REPOS.length, opts.reposLimit ?? 2));

  // Rotate which repos we hit each fire so we don't always re-scan the
  // same most-popular repo's stargazers (high turnover, but the top of
  // the list barely changes day-to-day). Use the day-of-year mod len.
  const dayOfYear = Math.floor((Date.now() - Date.UTC(new Date().getUTCFullYear(), 0, 0)) / 86400000);
  const start = dayOfYear % REPOS.length;
  const selectedRepos = [];
  for (let i = 0; i < reposLimit; i++) {
    selectedRepos.push(REPOS[(start + i) % REPOS.length]);
  }

  const headers: Record<string, string> = {
    "user-agent": USER_AGENT,
    "accept": "application/vnd.github+json",
    "x-github-api-version": "2022-11-28",
  };
  if (opts.githubToken) headers["authorization"] = `Bearer ${opts.githubToken}`;

  const report: GithubScrapeReport = {
    repos_scanned: selectedRepos.map((r) => `${r.owner}/${r.repo}`),
    stargazers_seen: 0,
    user_fetches: 0,
    rate_limit_hits: 0,
    produced_leads: [],
    skipped_no_blog: 0,
    skipped_aggregator_blog: 0,
    skipped_dup_in_batch: 0,
    errors: [],
  };

  const seenDomains = new Set<string>();
  let userBudget = maxUsers;

  for (const r of selectedRepos) {
    if (userBudget <= 0) break;
    const url = `https://api.github.com/repos/${r.owner}/${r.repo}/stargazers?per_page=${perRepo}`;
    let stargazers: GhStargazer[] = [];
    try {
      const resp = await fetcher(url, { headers });
      if (resp.status === 403 || resp.status === 429) {
        report.rate_limit_hits++;
        report.errors.push(`${r.owner}/${r.repo}: rate-limited (HTTP ${resp.status})`);
        continue;
      }
      if (!resp.ok) {
        report.errors.push(`${r.owner}/${r.repo}: HTTP ${resp.status}`);
        continue;
      }
      stargazers = (await resp.json()) as GhStargazer[];
    } catch (e) {
      report.errors.push(`${r.owner}/${r.repo}: ${e instanceof Error ? e.message.slice(0, 200) : "?"}`);
      continue;
    }
    report.stargazers_seen += stargazers.length;

    // Batch: take up to userBudget stargazers and fetch their /users/{login}
    // in parallel. This is the difference between 30s sequential timeouts
    // and ~1-2s wall clock — GitHub serves authed user lookups in ~200-500ms
    // each, but only when issued concurrently against the same TCP pool.
    const slice = stargazers.slice(0, Math.max(0, userBudget));
    userBudget -= slice.length;
    report.user_fetches += slice.length;

    const userFetches = slice.map(async (s) => {
      try {
        const ur = await fetcher(`https://api.github.com/users/${encodeURIComponent(s.login)}`, { headers });
        if (ur.status === 403 || ur.status === 429) {
          report.rate_limit_hits++;
          report.errors.push(`user ${s.login}: rate-limited`);
          return null;
        }
        if (!ur.ok) {
          report.errors.push(`user ${s.login}: HTTP ${ur.status}`);
          return null;
        }
        const user = (await ur.json()) as GhUser;
        return { s, user };
      } catch (e) {
        report.errors.push(`user ${s.login}: ${e instanceof Error ? e.message.slice(0, 160) : "?"}`);
        return null;
      }
    });
    const results = await Promise.all(userFetches);

    for (const item of results) {
      if (!item) continue;
      const { s, user } = item;
      const dom = blogToDomain(user.blog);
      if (!dom) {
        if (!user.blog) report.skipped_no_blog++;
        else report.skipped_aggregator_blog++;
        continue;
      }
      if (seenDomains.has(dom)) {
        report.skipped_dup_in_batch++;
        continue;
      }
      seenDomains.add(dom);

      // Conservative bump: established devs (followers > 100) get +5,
      // very high (>1000) get +10. Capped to 95.
      const followers = user.followers ?? 0;
      const followerBump = followers > 1000 ? 10 : followers > 100 ? 5 : 0;
      const adjFit = Math.min(95, r.fit + followerBump);

      const company = (user.company ?? "").trim().replace(/^@/, "").slice(0, 200) || dom;
      const bioSnippet = (user.bio ?? "").trim().slice(0, 240);
      const signal = [
        `GH stargazer of ${r.owner}/${r.repo}`,
        `@${s.login}`,
        followers ? `${followers} followers` : "",
        bioSnippet ? `"${bioSnippet}"` : "",
      ].filter(Boolean).join(" · ");

      report.produced_leads.push({
        company,
        domain: dom,
        source: "github-stargazers",
        source_url: `https://github.com/${s.login}`,
        signal: signal.slice(0, 1024),
        tech_stack: [r.tag],
        fit_score: adjFit,
        reasoning: `Stargazer of ${r.owner}/${r.repo}; blog=${user.blog ?? ""}; company=${user.company ?? ""}`.slice(0, 2000),
        notes: `gh_login=${s.login} followers=${followers} public_repos=${user.public_repos ?? 0}`,
      });
    }
  }

  return report;
}
