// G14 substrate boundary — all health-data writes route through @etzhayyim/sdk proxy.
// The Worker MUST NOT call AT MST / IPFS / Base L2 / viem / noble-ciphers / libsignal directly.
// Per ADR-2605260100 §G14 + ADR-2605172000.

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PWA_ROOT = join(import.meta.dirname ?? __dirname, "..");

function readSrc(file: string): string {
  return readFileSync(join(PWA_ROOT, "src", file), "utf-8");
}

describe("G14 substrate boundary", () => {
  it("src/app.ts does NOT import @atproto/api directly", () => {
    const code = readSrc("app.ts");
    expect(code).not.toMatch(/@atproto\/api/);
  });

  it("src/app.ts does NOT import viem (direct L2 contract calls)", () => {
    const code = readSrc("app.ts");
    expect(code).not.toMatch(/\bviem\b/);
  });

  it("src/app.ts does NOT import @noble/ciphers (G2 envelopes go via sdk)", () => {
    const code = readSrc("app.ts");
    expect(code).not.toMatch(/@noble\/ciphers/);
  });

  it("src/app.ts does NOT import @signalapp/libsignal-client", () => {
    const code = readSrc("app.ts");
    expect(code).not.toMatch(/@signalapp\/libsignal-client/);
  });

  it("src/app.ts does NOT call kubo / IPFS HTTP API directly", () => {
    const code = readSrc("app.ts");
    expect(code).not.toMatch(/\/api\/v0\/(add|cat|pin)/);
    expect(code).not.toMatch(/127\.0\.0\.1:5001/);
  });

  it("src/app.ts routes substrate calls via proxyToSubstrate with x-mitate-actor-did", () => {
    const code = readSrc("app.ts");
    expect(code).toContain("proxyToSubstrate");
    expect(code).toContain("x-mitate-actor-did");
    expect(code).toContain("ETZHAYYIM_SDK_PROXY_URL");
  });

  it("Murakumo gateway is the only configured inference endpoint (G12 sibling check)", () => {
    const code = readSrc("app.ts");
    expect(code).toContain("MURAKUMO_LITELLM_GATEWAY_URL");
    // Forbidden direct vendor inference endpoints
    expect(code).not.toMatch(/api\.openai\.com/);
    expect(code).not.toMatch(/api\.anthropic\.com/);
    expect(code).not.toMatch(/runpod\.io/);
    expect(code).not.toMatch(/bedrock-runtime/);
    expect(code).not.toMatch(/aiplatform\.googleapis\.com/);
  });
});
