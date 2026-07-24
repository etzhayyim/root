#!/usr/bin/env node
/**
 * no-cookie — Block cookie usage on the etzhayyim.com religious-corp surface.
 *
 * Per CHARTER-RIDER.md §2(c) (no surveillance/trackers), ADR-2605172000
 * (kotoba substrate — identity = DID + WebAuthn, not cookies), and the
 * apex Worker cookie-strip policy in `50-infra/etzhayyim-did-web/src/worker.ts`,
 * etzhayyim.com is a cookie-free zone in both directions:
 *
 *   - The Worker strips outgoing `Cookie` request headers and incoming
 *     `Set-Cookie` response headers on every proxy hop.
 *   - The Worker sends `Permissions-Policy: interest-cohort=(), browsing-topics=()`
 *     and (on `/` + `/privacy`) `Clear-Site-Data: "cookies"` to wipe
 *     residual cookies from pre-cookie-free visitors.
 *
 * This pre-commit hook prevents the invariant from drifting by blocking:
 *
 *   1. `document.cookie = "…"` writes in TS/JS/Svelte sources.
 *   2. `setCookie(`, `cookies.set(`, `Set-Cookie:` writes (SvelteKit `cookies` API,
 *      raw response header construction, hono `c.header('Set-Cookie', …)`).
 *
 * Reads (`document.cookie` getter, `req.cookies.get(…)`, `getCookie(…)`)
 * are NOT blocked — code may need to detect & migrate legacy cookies.
 *
 * Use an inline `// no-cookie: allow <reason>` marker on the same or
 * preceding line to bypass with a documented reason (e.g. read-only
 * adapters that need to inspect inbound cookies before stripping them).
 *
 * Exempt paths: `node_modules`, build outputs, tests, vendored libs,
 * docs/ADRs, and the Worker itself (which is the policy enforcer and
 * legitimately discusses cookies in code comments).
 */

import { readFileSync, statSync } from "node:fs";

const args = process.argv.slice(2);
if (args.length === 0) process.exit(0);

const EXEMPT_PATH_PATTERNS = [
  /\/node_modules\//,
  /\/dist\//,
  /\/build\//,
  /\/\.svelte-kit\//,
  /\/\.next\//,
  /\/out\//,
  /\/coverage\//,
  /\/vendor\//,
  /-fork\//,
  /\/lib\/forge-std\//,
  // Tests are allowed to assert on cookie behavior.
  /\.test\.[mc]?[tj]sx?$/,
  /\.spec\.[mc]?[tj]sx?$/,
  /\/tests?\//,
  /\/fixtures?\//,
  // Docs / ADRs / READMEs cite cookies as a topic, not a write.
  /\.md$/,
  /\.mdx$/,
  // The Worker IS the cookie-strip policy enforcer; it talks about cookies
  // in code & comments by design.
  /^50-infra\/etzhayyim-did-web\//,
  // The lint script itself.
  /no-cookie\.mjs$/,
];

const ALLOW_MARKER = /\/\/\s*no-cookie:\s*allow\b/;

const WRITE_PATTERNS = [
  // document.cookie = …   (any whitespace around the =, optional plus-equals
  // for chained Set-Cookie strings).
  /\bdocument\s*\.\s*cookie\s*(=|\+=)/,
  // SvelteKit / hono / express style cookie setters
  /\b(?:cookies|ctx\.cookies|c\.cookies|res\.cookies|response\.cookies)\s*\.\s*set\s*\(/,
  // Bare helper imports/callsites: setCookie(name, value, opts)
  /\bsetCookie\s*\(/,
  // serialize-cookie / cookie.serialize
  /\bcookie\s*\.\s*serialize\s*\(/,
  // Raw Set-Cookie header construction
  /['"`]Set-Cookie['"`]\s*[,:]/i,
  /headers\s*\.\s*(?:set|append)\s*\(\s*['"`]set-cookie['"`]/i,
  // hono's c.header('Set-Cookie', …)
  /\bheader\s*\(\s*['"`]set-cookie['"`]/i,
];

function isExempt(file) {
  return EXEMPT_PATH_PATTERNS.some((re) => re.test(file));
}

function readFileSafe(file) {
  try {
    const st = statSync(file);
    if (!st.isFile()) return null;
    return readFileSync(file, "utf8");
  } catch {
    return null;
  }
}

let violations = 0;

for (const file of args) {
  if (isExempt(file)) continue;
  const src = readFileSafe(file);
  if (!src) continue;

  const lines = src.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const re of WRITE_PATTERNS) {
      if (!re.test(line)) continue;
      // Bypass via inline marker on this line or the line above.
      if (ALLOW_MARKER.test(line)) continue;
      if (i > 0 && ALLOW_MARKER.test(lines[i - 1])) continue;
      console.error(
        `✘ no-cookie: ${file}:${i + 1} — cookie write detected (CHARTER §2(c) + ADR-2605172000)`,
      );
      console.error(`    ${line.trim()}`);
      violations++;
      break;
    }
  }
}

if (violations > 0) {
  console.error("");
  console.error(
    "  etzhayyim.com is a cookie-free zone (CHARTER-RIDER.md §2(c) + ADR-2605172000).",
  );
  console.error(
    "  Use DID + WebAuthn passkeys for identity, localStorage / OPFS for client state.",
  );
  console.error(
    "  If this write is unavoidable (e.g. reading inbound legacy cookies for migration),",
  );
  console.error(
    "  add `// no-cookie: allow <reason>` on the line above to bypass.",
  );
  process.exit(1);
}

process.exit(0);
