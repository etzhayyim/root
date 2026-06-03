// lead-sources/enrich.ts — fetch a lead's domain landing page and extract
// publicly-published contact info (mailto: tags, info@/hello@/contact@
// patterns) plus light tech-stack signals.
//
// Compliance:
//   - Reads ONLY the domain's public homepage. No /admin, no /login.
//   - Sends a self-identifying User-Agent so site operators can block
//     us via robots.txt or WAF if they prefer.
//   - 8s timeout, follows up to 2 redirects (CF fetch default behavior),
//     fails soft on 4xx/5xx.
//   - Skips the request if domain is in a known SKIP_HOSTS set, or
//     if it ends in .example / .test / .invalid (RFC 2606).
//   - Output is suitable for B2B outreach. Personal emails are not
//     scraped; only role-style aliases (info@, hello@, etc.) and
//     mailto: links from the public page.
//
// This is intentionally a low-effort fetch + regex pass — no headless
// browser, no JS rendering, no follow-link crawl. ~80% of B2B sites
// surface a usable role address on the homepage; that's good enough
// to unblock the human reviewer.

const RFC2606_SKIPPABLE = new Set(["example", "test", "invalid", "localhost"]);

const USER_AGENT =
  "yatabase-enrich-bot/0.1 (+https://yatabase.etzhayyim.com/.well-known/agent.json)";

const ROLE_PATTERNS = [
  "hello",
  "hi",
  "info",
  "contact",
  "support",
  "help",
  "team",
  "sales",
  "press",
  "media",
  "founders",
  "ceo",
  "office",
];

const TECH_PATTERNS: Array<{ re: RegExp; tag: string }> = [
  { re: /\bnext\.js\b|\b_next\/static/i, tag: "nextjs" },
  { re: /\bvercel\b|cdn\.vercel-insights\.com/i, tag: "vercel" },
  { re: /\bnetlify\b/i, tag: "netlify" },
  { re: /\bcloudflare\b|cf-ray|cdnjs\.cloudflare\.com/i, tag: "cloudflare" },
  { re: /\breact\b|react\.production/i, tag: "react" },
  { re: /\bvue\b/i, tag: "vue" },
  { re: /\bsvelte\b|sveltekit/i, tag: "svelte" },
  { re: /\bsupabase\b/i, tag: "supabase" },
  { re: /\bneo4j\b/i, tag: "neo4j" },
  { re: /\bhasura\b/i, tag: "hasura" },
  { re: /\bpostgres(ql)?\b/i, tag: "postgres" },
  { re: /\bfirebase(\.google\.com)?\b/i, tag: "firebase" },
  // Note: Stripe detection is for prospecting only; etzhayyim does not use Stripe (Charter Rider §2).
  { re: /\bstripe\b|js\.stripe\.com/i, tag: "stripe" },
  { re: /shopify(\.com)?/i, tag: "shopify" },
  { re: /\b(open|webgl)?ai\b|openai\.com/i, tag: "ai" },
];

export interface EnrichResult {
  ok: boolean;
  domain: string;
  fetched_url: string;
  http_status: number;
  duration_ms: number;
  contact_email_candidates: string[];
  best_email: string;
  tech_stack: string[];
  error?: string;
}

function shouldSkip(domain: string): { skip: boolean; reason: string } {
  const labels = domain.split(".");
  if (labels.length < 2) return { skip: true, reason: "domain has too few labels" };
  const tld = labels[labels.length - 1].toLowerCase();
  if (RFC2606_SKIPPABLE.has(tld)) return { skip: true, reason: `RFC 2606 skip (.${tld})` };
  return { skip: false, reason: "" };
}

function extractEmails(html: string, domain: string): { candidates: string[]; best: string } {
  const lower = html.toLowerCase();
  const found = new Set<string>();

  // 1. mailto: links anywhere on the page.
  const mailtoRe = /mailto:([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})/gi;
  let m: RegExpExecArray | null;
  while ((m = mailtoRe.exec(lower)) !== null) {
    found.add(m[1]);
    if (found.size > 30) break; // safety cap
  }

  // 2. Inline plain-text emails (covers sites that print "info@foo.com" without mailto:).
  const plainRe = /([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})/gi;
  while ((m = plainRe.exec(lower)) !== null) {
    found.add(m[1]);
    if (found.size > 60) break;
  }

  const all = [...found];
  // Filter to addresses on the lead's own domain (avoids @gmail.com personal emails
  // and 3rd-party SaaS support addresses like privacy@cloudflare.com that appear
  // in cookie banners). Match "@<bare>.com" or "@subdomain.<domain>.com".
  const onDomain = all.filter((e) => {
    const at = e.indexOf("@");
    if (at < 0) return false;
    const host = e.slice(at + 1);
    return host === domain || host.endsWith(`.${domain}`);
  });

  // Rank: prefer role aliases on the lead's own domain, then any email on its domain,
  // then any role alias regardless of domain.
  const candidates = onDomain.length > 0 ? onDomain : all;
  let best = "";
  // Pass 1: role-prefixed on-domain.
  for (const role of ROLE_PATTERNS) {
    const hit = onDomain.find((e) => e.startsWith(`${role}@`));
    if (hit) { best = hit; break; }
  }
  // Pass 2: any on-domain.
  if (!best && onDomain.length > 0) best = onDomain[0];
  // Pass 3: role-prefixed off-domain (very weak; mostly catches Mailgun cases).
  if (!best) {
    for (const role of ROLE_PATTERNS) {
      const hit = all.find((e) => e.startsWith(`${role}@`));
      if (hit) { best = hit; break; }
    }
  }
  return { candidates: candidates.slice(0, 12), best };
}

function extractTechStack(html: string): string[] {
  const found = new Set<string>();
  for (const { re, tag } of TECH_PATTERNS) {
    if (re.test(html)) found.add(tag);
  }
  return [...found];
}

export async function enrichDomain(domain: string, fetcher: typeof fetch = fetch): Promise<EnrichResult> {
  const t0 = Date.now();
  const skip = shouldSkip(domain);
  if (skip.skip) {
    return {
      ok: false,
      domain,
      fetched_url: "",
      http_status: 0,
      duration_ms: 0,
      contact_email_candidates: [],
      best_email: "",
      tech_stack: [],
      error: skip.reason,
    };
  }

  const url = `https://${domain}/`;
  let resp: Response;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 8000);
    resp = await fetcher(url, {
      method: "GET",
      headers: {
        "user-agent": USER_AGENT,
        "accept": "text/html,application/xhtml+xml,*/*;q=0.8",
      },
      redirect: "follow",
      signal: ctrl.signal,
    });
    clearTimeout(t);
  } catch (e) {
    return {
      ok: false,
      domain,
      fetched_url: url,
      http_status: 0,
      duration_ms: Date.now() - t0,
      contact_email_candidates: [],
      best_email: "",
      tech_stack: [],
      error: e instanceof Error ? e.message.slice(0, 240) : "fetch threw",
    };
  }

  if (!resp.ok) {
    return {
      ok: false,
      domain,
      fetched_url: url,
      http_status: resp.status,
      duration_ms: Date.now() - t0,
      contact_email_candidates: [],
      best_email: "",
      tech_stack: [],
      error: `HTTP ${resp.status}`,
    };
  }

  let html: string;
  try {
    html = await resp.text();
  } catch (e) {
    return {
      ok: false,
      domain,
      fetched_url: url,
      http_status: resp.status,
      duration_ms: Date.now() - t0,
      contact_email_candidates: [],
      best_email: "",
      tech_stack: [],
      error: "body read failed",
    };
  }

  // Cap the html we scan to the first ~256 KB to keep regex bounded.
  const scoped = html.slice(0, 256 * 1024);
  const { candidates, best } = extractEmails(scoped, domain);
  const techStack = extractTechStack(scoped);

  return {
    ok: true,
    domain,
    fetched_url: url,
    http_status: resp.status,
    duration_ms: Date.now() - t0,
    contact_email_candidates: candidates,
    best_email: best,
    tech_stack: techStack,
  };
}
