/**
 * Seed catalog completeness + converter shape. No SDK / network.
 */

import { describe, expect, it } from "vitest";

import {
  APQC_PCF_VERSION,
  APQC_PUBLISHED_AT_DEFAULT,
} from "./types.js";
import { PCF_V74_L1_CATEGORIES, toProcessCategory } from "./seed.js";

describe("PCF_V74_L1_CATEGORIES (catalog completeness)", () => {
  it("contains exactly 13 entries (v7.4 cardinality)", () => {
    expect(PCF_V74_L1_CATEGORIES).toHaveLength(13);
  });

  it("codes cover 1.0–13.0 with no gaps", () => {
    const codes = PCF_V74_L1_CATEGORIES.map((c) => c.code).sort(
      (a, b) =>
        Number(a.slice(0, a.indexOf("."))) - Number(b.slice(0, b.indexOf("."))),
    );
    const expected = Array.from({length: 13}, (_, i) => `${i + 1}.0`);
    expect(codes).toEqual(expected);
  });

  it("every entry has a non-empty English name", () => {
    for (const c of PCF_V74_L1_CATEGORIES) {
      expect(c.name.length).toBeGreaterThan(0);
      // No leading/trailing whitespace in the source list.
      expect(c.name).toBe(c.name.trim());
    }
  });

  it("anchor entries match the published v7.4 names verbatim", () => {
    // Spot-check three well-known entries against the public APQC
    // PCF v7.4 cross-industry framework. If APQC publishes v7.5 with
    // renamings, these tests need updating in the same PR as the
    // catalog bump.
    expect(PCF_V74_L1_CATEGORIES.find((c) => c.code === "1.0")?.name).toBe(
      "Develop Vision and Strategy",
    );
    expect(PCF_V74_L1_CATEGORIES.find((c) => c.code === "7.0")?.name).toBe(
      "Develop and Manage Human Capital",
    );
    expect(PCF_V74_L1_CATEGORIES.find((c) => c.code === "13.0")?.name).toBe(
      "Develop and Manage Business Capabilities",
    );
  });
});

describe("toProcessCategory", () => {
  it("converts a valid source entry, defaulting level/version/publishedAt", () => {
    const out = toProcessCategory({code: "7.0", name: "Develop and Manage Human Capital"});
    expect(out.code).toBe("7.0");
    expect(out.name).toBe("Develop and Manage Human Capital");
    expect(out.level).toBe(1);
    expect(out.version).toBe(APQC_PCF_VERSION);
    expect(out.publishedAt).toBe(APQC_PUBLISHED_AT_DEFAULT);
  });

  it("trims whitespace from name", () => {
    const out = toProcessCategory({code: "1.0", name: "  Develop Vision and Strategy  "});
    expect(out.name).toBe("Develop Vision and Strategy");
  });

  it("rejects invalid codes", () => {
    expect(() => toProcessCategory({code: "14.0", name: "Future"})).toThrow(
      /invalid APQC L1 code/,
    );
    expect(() => toProcessCategory({code: "1.1", name: "L2 child"})).toThrow(
      /invalid APQC L1 code/,
    );
  });

  it("rejects empty name", () => {
    expect(() => toProcessCategory({code: "1.0", name: "   "})).toThrow(/empty name/);
  });
});
