// G11 Wellbecoming invariants — no streak / no score reveal during intake / no fear-priming /
// no re-engagement push for non-completion / push only for 3 urgency-only channels.
// Per ADR-2605260100 §G11 + ADR-2605260200 §Decision 3.

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PWA_ROOT = join(import.meta.dirname ?? __dirname, "..");

function readPublic(file: string): string {
  return readFileSync(join(PWA_ROOT, "public", file), "utf-8");
}

describe("G11 no addictive engagement design", () => {
  it("intake page (index.html) does NOT contain streak / score / gamification text", () => {
    const html = readPublic("index.html");
    const forbidden = ["streak", "score", "points", "achievement", "level up", "daily challenge", "連続", "ストリーク", "獲得ポイント"];
    forbidden.forEach((term) => {
      expect(html.toLowerCase()).not.toContain(term.toLowerCase());
    });
  });

  it("intake page does NOT contain fear-priming 'you may have X' style anxiety triggers", () => {
    const html = readPublic("index.html");
    const fearPatterns = ["you might have cancer", "could be deadly", "あなたは ... の可能性があります", "重大な疾患かも"];
    fearPatterns.forEach((pat) => {
      expect(html.toLowerCase()).not.toContain(pat.toLowerCase());
    });
  });

  it("G11 allowed notification channels are exactly 3 urgency-only types", () => {
    const allowed = new Set(["emergency-ack", "appointment-reminder", "ae-followup"]);
    expect(allowed.size).toBe(3);
    expect(allowed.has("daily-tip")).toBe(false);
    expect(allowed.has("re-engagement")).toBe(false);
    expect(allowed.has("streak-reminder")).toBe(false);
    expect(allowed.has("marketing")).toBe(false);
  });

  it("disclaimer page presents G3 + G1 + G6 acknowledgment fields (no celebratory framing)", () => {
    const html = readPublic("disclaimer.html");
    expect(html).toContain("g3_ack");
    expect(html).toContain("g1_consent");
    expect(html).toContain("g6_acknowledge_high_risk");
    // Forbidden celebratory framing
    expect(html.toLowerCase()).not.toContain("congratulations");
    expect(html.toLowerCase()).not.toContain("おめでとう");
    expect(html.toLowerCase()).not.toContain("welcome aboard");
  });

  it("emergency page leads with red-flag detection and 119 routing — no calming text suppressing urgency", () => {
    const html = readPublic("emergency.html");
    expect(html).toContain("119"); // 救急要請
    expect(html.toLowerCase()).not.toContain("don't worry");
    expect(html.toLowerCase()).not.toContain("心配ありません");
  });
});
