// browser/types.ts — kami manifest shape for the `browser-only` mode.
//
// A browser-only kami has NO public API and no local binary. The agent
// drives a web UI directly (clicks, form fills, scrapes). Concrete L2/L3
// implementations are deferred — Phase 3 of ADR-2605211900 ships only
// the contract (this file) + L1 lexicon emission so callers can declare
// the surface even before a driver lands.

export interface BrowserKamiManifest {
  kami: {
    id: string; // e.g. "browser:internal-portal"
    base_url: string; // e.g. "https://portal.example.com"
    description?: string;
    auth_hint?: "session-cookie" | "sso" | "none" | "manual";
  };
  ops: BrowserOp[];
}

export interface BrowserOp {
  name: string;
  summary?: string;
  description?: string;
  // Ordered DOM interaction steps. The L3 driver (Phase 3 follow-up
  // implementation) replays this sequence in a headless browser /
  // mcp__claude-in-chrome session.
  steps: BrowserStep[];
  // Output extraction — what to read off the page once steps finish.
  extract?: BrowserExtract[];
}

export type BrowserStep =
  | { kind: "goto"; url_template: string }
  | { kind: "wait_for"; selector: string; timeout_ms?: number }
  | { kind: "fill"; selector: string; value_input_key: string }
  | { kind: "click"; selector: string }
  | { kind: "select"; selector: string; value_input_key: string }
  | { kind: "sleep_ms"; ms: number }
  | { kind: "scroll_to"; selector: string };

export interface BrowserExtract {
  output_key: string; // top-level key in the output object
  selector: string;
  attribute?: string; // default: textContent
  multiple?: boolean; // if true, returns string[]
}

export function validateBrowserManifest(m: unknown): BrowserKamiManifest {
  if (!m || typeof m !== "object") throw new Error("manifest must be an object");
  const km = m as BrowserKamiManifest;
  if (!km.kami || typeof km.kami !== "object") throw new Error("manifest.kami missing");
  if (!km.kami.id || !km.kami.id.startsWith("browser:")) {
    throw new Error(`manifest.kami.id must start with 'browser:' (got: ${km.kami.id ?? "<missing>"})`);
  }
  if (!km.kami.base_url || !/^https?:\/\//.test(km.kami.base_url)) {
    throw new Error("manifest.kami.base_url missing or not http(s)");
  }
  if (!Array.isArray(km.ops) || km.ops.length === 0) {
    throw new Error("manifest.ops must be a non-empty array");
  }
  for (const op of km.ops) {
    if (!op.name) throw new Error("op.name missing");
    if (!Array.isArray(op.steps) || op.steps.length === 0) {
      throw new Error(`op.steps missing or empty on op ${op.name}`);
    }
  }
  return km;
}
