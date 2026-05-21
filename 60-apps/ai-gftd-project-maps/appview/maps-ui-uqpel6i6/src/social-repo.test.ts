import { describe, expect, it } from "vitest";

import { buildFollowEdgeRow, buildRepoRecordRow, buildStableRkey } from "./social-repo";

describe("social repo helpers", () => {
  it("builds deterministic repo record rows", () => {
    const row = buildRepoRecordRow(
      "did:web:maps.gftd.ai",
      "app.bsky.feed.post",
      "summary",
      { $type: "app.bsky.feed.post", text: "hello", createdAt: "2026-04-20T10:00:00.000Z" },
      0,
    );
    expect(row.uri).toBe("at://did:web:maps.gftd.ai/app.bsky.feed.post/summary");
    expect(row.ts_ms).toBe(Date.parse("2026-04-20T10:00:00.000Z"));
    expect(row.created_at).toBe("2026-04-20T10:00:00.000Z");
    expect(row.cid).toBe(row.repo_rev);
  });

  it("builds follow edges with stable ids", () => {
    const row = buildFollowEdgeRow(
      "did:web:maps.gftd.ai",
      "did:web:yoro.gftd.ai",
      "follow-yoro",
      "2026-04-20T10:00:00.000Z",
      0,
    );
    expect(row.edge_id).toBe("at://did:web:maps.gftd.ai/app.bsky.graph.follow/follow-yoro");
    expect(row.src_vid).toBe("did:web:maps.gftd.ai");
    expect(row.dst_vid).toBe("did:web:yoro.gftd.ai");
    expect(row.created_date).toBe("2026-04-20");
  });

  it("creates compact stable rkeys", () => {
    expect(buildStableRkey("sample", "Building: Tokyo Midtown Yaesu #1")).toMatch(/^sample-[a-z0-9-]+-[0-9a-f]{8}$/);
  });
});
