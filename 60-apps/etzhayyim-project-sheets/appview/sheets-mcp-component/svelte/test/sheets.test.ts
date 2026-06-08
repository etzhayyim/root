import { describe, it, expect, vi } from "vitest";
import app from "../src/app.js";

global.fetch = vi.fn();

describe("sheets appview facade", () => {
  it("returns health check on /health", async () => {
    const req = new Request("https://sheets.etzhayyim.com/health");
    const res = await app.fetch(req, {});
    expect(res.status).toBe(200);
    const data = await res.json() as any;
    expect(data.ok).toBe(true);
    expect(data.actor).toBe("did:web:sheets.etzhayyim.com");
  });

  it("handles invalid json in POST gracefully", async () => {
    const req = new Request("https://sheets.etzhayyim.com/xrpc/com.etzhayyim.apps.sheets.test", {
      method: "POST",
      body: "{ bad json",
    });
    const res = await app.fetch(req, {});
    expect(res.status).toBe(400);
    const data = await res.json() as any;
    expect(data.error).toBe("InvalidJson");
  });

  it("proxies valid XRPC to dispatcher", async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify({ success: true })));
    const req = new Request("https://sheets.etzhayyim.com/xrpc/com.etzhayyim.apps.sheets.ping");
    const res = await app.fetch(req, {});
    expect(res.status).toBe(200);
    const data = await res.json() as any;
    expect(data.success).toBe(true);
  });

  it("returns 404 for unknown path without ASSETS", async () => {
    const req = new Request("https://sheets.etzhayyim.com/unknown");
    const res = await app.fetch(req, {});
    expect(res.status).toBe(404);
  });
});
