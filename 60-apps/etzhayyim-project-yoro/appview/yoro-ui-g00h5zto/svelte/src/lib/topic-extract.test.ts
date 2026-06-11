/**
 * Unit tests for topic-extract.ts (P3).
 *
 * Invariants:
 *   - Facet-declared hashtag takes precedence over inline / embed / link.
 *   - Inline `#tag` fallback only fires when facets are absent.
 *   - Embed kind maps to stable buckets (image/video/quote/url).
 *   - External URI domain is registrable-domain-normalized.
 *   - vertex_joucho column mapping is 1:1 and clamped to [0,100].
 */
import { describe, expect, it } from "vitest";
import { extractTopic, jouchoRowToState } from "../../../src/appview/topic-extract";

describe("extractTopic", () => {
  it("returns null for missing input", () => {
    expect(extractTopic(null)).toBeNull();
    expect(extractTopic(undefined)).toBeNull();
    expect(extractTopic({})).toBeNull();
  });

  it("picks the first facet hashtag", () => {
    const rec = {
      text: "hello #world",
      facets: [{
        features: [
          { $type: "app.bsky.richtext.facet#tag", tag: "Handotai" },
          { $type: "app.bsky.richtext.facet#link", uri: "https://example.com" },
        ],
      }],
    };
    expect(extractTopic(rec)).toBe("tag:handotai");
  });

  it("falls back to inline hashtag when facets are missing", () => {
    expect(extractTopic({ text: "新作 #半導体 について" })).toBe("tag:半導体");
    expect(extractTopic({ text: "intro #AI_Agent end" })).toBe("tag:ai_agent");
  });

  it("facet takes precedence over inline hashtag", () => {
    const rec = {
      text: "see #inline",
      facets: [{
        features: [{ $type: "app.bsky.richtext.facet#tag", tag: "facet-wins" }],
      }],
    };
    expect(extractTopic(rec)).toBe("tag:facet-wins");
  });

  it("maps embed kinds to stable buckets", () => {
    expect(extractTopic({ text: "", embed: { type: "images" } })).toBe("embed:image");
    expect(extractTopic({ text: "", embed: { type: "video" } })).toBe("embed:video");
    expect(extractTopic({ text: "", embed: { type: "record" } })).toBe("embed:quote");
  });

  it("extracts registrable domain from external embed", () => {
    expect(extractTopic({
      text: "", embed: { type: "external", external: { uri: "https://www.example.com/path" } },
    })).toBe("url:example.com");
    expect(extractTopic({
      text: "", embed: { type: "external", external: { uri: "https://news.example.co.jp/a/b" } },
    })).toBe("url:example.co.jp");
  });

  it("falls back to link facet domain when no hashtag / embed", () => {
    const rec = {
      text: "check this",
      facets: [{
        features: [{ $type: "app.bsky.richtext.facet#link", uri: "https://docs.example.org/foo" }],
      }],
    };
    expect(extractTopic(rec)).toBe("url:example.org");
  });

  it("returns null for plain text with no hashtags / embeds / links", () => {
    expect(extractTopic({ text: "今日もよろしく" })).toBeNull();
  });

  it("ignores malformed URIs gracefully", () => {
    expect(extractTopic({ text: "", embed: { type: "external", external: { uri: "not-a-url" } } })).toBeNull();
  });
});

describe("jouchoRowToState", () => {
  it("maps joy/calm/stress/gratitude/focus onto plan axis names", () => {
    const s = jouchoRowToState({
      joy: 80, calm: 60, stress: 30, gratitude: 70, focus: 55,
    });
    expect(s).not.toBeNull();
    if (!s) throw new Error("expected non-null");
    expect(s.vitality).toBe(80);
    expect(s.serenity).toBe(60);
    expect(s.connection).toBe(70);
    expect(s.growth).toBe(55);
    expect(s.stressIdx).toBe(30);
    // resilience = (calm + (100-stress)) / 2 = (60 + 70) / 2 = 65
    expect(s.resilience).toBe(65);
  });

  it("clamps out-of-range values to [0,100]", () => {
    const s = jouchoRowToState({ joy: 150, calm: -20, stress: 200, gratitude: 50, focus: 50 });
    if (!s) throw new Error("expected non-null");
    expect(s.vitality).toBe(100);
    expect(s.serenity).toBe(0);
    expect(s.stressIdx).toBe(100);
  });

  it("returns null for null/undefined row", () => {
    expect(jouchoRowToState(null)).toBeNull();
    expect(jouchoRowToState(undefined)).toBeNull();
  });

  it("treats missing columns as 0", () => {
    const s = jouchoRowToState({ joy: 50 });
    if (!s) throw new Error("expected non-null");
    expect(s.vitality).toBe(50);
    expect(s.serenity).toBe(0);
    expect(s.stressIdx).toBe(0);
  });

  it("accepts bigint values (pg wire type for BIGINT columns)", () => {
    const s = jouchoRowToState({ joy: 42n as unknown as bigint, calm: 30n as unknown as bigint, stress: 10n as unknown as bigint });
    if (!s) throw new Error("expected non-null");
    expect(s.vitality).toBe(42);
    expect(s.serenity).toBe(30);
    expect(s.stressIdx).toBe(10);
  });
});
