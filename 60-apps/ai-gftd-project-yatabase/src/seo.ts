// seo.ts — robots.txt + sitemap.xml for organic discovery.
//
// Search engines need an explicit allowlist of public surfaces and a
// disallowlist for the API + operator paths. Without robots.txt a crawler
// will hit /api/* / /_agents/* / /webhook/* and waste both its quota and
// our edge budget.

const PUBLIC_ROUTES = ["/", "/docs", "/status", "/team", "/studio", "/dashboard", "/privacy", "/terms", "/integrations", "/changelog", "/quickstart", "/comparison"];

export function robotsResponse(): Response {
  const lines = [
    `# yatabase.etzhayyim.com robots.txt`,
    `# Operator: etz hayim · Vendor: Gftd Japan株式会社 (T9007028460042)`,
    ``,
    `User-agent: *`,
    `Allow: /`,
    `Allow: /docs`,
    `Allow: /status`,
    `Allow: /team`,
    `Allow: /studio`,
    `Allow: /embed`,
    `Allow: /privacy`,
    `Allow: /terms`,
    `Allow: /openapi.json`,
    `Allow: /integrations`,
    `Allow: /changelog`,
    `Allow: /quickstart`,
    `Allow: /comparison`,
    `Allow: /dashboard`,
    `Allow: /.well-known/security.txt`,
    `Allow: /.well-known/`,
    `Allow: /health`,
    `Allow: /_app/meta`,
    ``,
    `# API and operator paths — index-blocked. These return data, not pages.`,
    `Disallow: /cypher`,
    `Disallow: /sparql`,
    `Disallow: /mcp`,
    `Disallow: /xrpc/`,
    `Disallow: /storage/`,
    `Disallow: /s3/`,
    `Disallow: /api/`,
    `Disallow: /auth/`,
    `Disallow: /webhook/`,
    `Disallow: /_agents/`,
    `Disallow: /_worker/`,
    ``,
    `# Yatabase scrapers identify themselves and respect this file.`,
    `User-agent: yatabase-enrich-bot`,
    `Disallow: /`,
    ``,
    `Sitemap: https://yatabase.etzhayyim.com/sitemap.xml`,
    ``,
  ];
  return new Response(lines.join("\n"), {
    status: 200,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "x-yatabase-surface": "robots",
      "cache-control": "public, max-age=3600, s-maxage=3600",
    },
  });
}

/**
 * RFC 9116 security.txt — published at /.well-known/security.txt.
 * Provides a stable contact for security researchers reporting vulns.
 * Expires field set 1 year out so security tooling stays happy; rotate
 * by re-deploying.
 */
export function securityTxtResponse(): Response {
  const expires = new Date(Date.now() + 365 * 86400 * 1000).toISOString();
  const lines = [
    `# yatabase.etzhayyim.com security.txt — RFC 9116`,
    `# Operator: etz hayim · Vendor: Gftd Japan株式会社 (T9007028460042)`,
    ``,
    `Contact: mailto:security@etzhayyim.com`,
    `Expires: ${expires}`,
    `Preferred-Languages: en, ja`,
    `Canonical: https://yatabase.etzhayyim.com/.well-known/security.txt`,
    `Policy: https://yatabase.etzhayyim.com/privacy`,
    `Acknowledgments: https://yatabase.etzhayyim.com/team`,
    ``,
    `# Scope: yatabase.etzhayyim.com (Cloudflare Worker magatama-y4t4b4se),`,
    `# tenant schemas yata_* on RisingWave Vultr LAX, the dispatched`,
    `# LangServer storage primitives in mitama-yata-pool.`,
    `#`,
    `# In scope:    auth bypass, tenant-isolation breach, RCE, billing`,
    `#              tampering, IDOR on /api/leads/{id}/*, key leakage.`,
    `# Out of scope: rate-limit bypass on free tier, social engineering`,
    `#              of operator, third-party (Stripe / Resend / B2 / CF)`,
    `#              services we don't run.`,
    `#`,
    `# Disclosure: please give 90 days before public disclosure.`,
    `# Bug bounty: not formal yet; significant reports at our discretion`,
    `# receive credit, free Enterprise tier, and (where allowed) cash.`,
    ``,
  ];
  return new Response(lines.join("\n"), {
    status: 200,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "x-yatabase-surface": "security-txt",
      "cache-control": "public, max-age=3600, s-maxage=3600",
    },
  });
}

export function sitemapResponse(): Response {
  // lastmod is the same for all routes — the marketing/docs surface
  // is a single deploy unit so a per-page granularity buys nothing.
  const today = new Date().toISOString().slice(0, 10);
  const urls = PUBLIC_ROUTES.map(
    (p) => `  <url>
    <loc>https://yatabase.etzhayyim.com${p === "/" ? "/" : p}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${p === "/" ? "daily" : "weekly"}</changefreq>
    <priority>${p === "/" ? "1.0" : p === "/docs" ? "0.9" : "0.7"}</priority>
  </url>`,
  ).join("\n");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
  return new Response(xml, {
    status: 200,
    headers: {
      "content-type": "application/xml; charset=utf-8",
      "x-yatabase-surface": "sitemap",
      "cache-control": "public, max-age=3600, s-maxage=3600",
    },
  });
}
