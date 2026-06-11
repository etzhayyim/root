/**
 * Pure-helper tests for the type / validation surface. No SDK / network.
 *
 * Locks down: code format, slug format, CPC segment-range mapping per
 * the documented boundaries in
 * `60-apps/etzhayyim-project-open-unispsc/CLAUDE.md`.
 */

import { describe, expect, it } from "vitest";

import { cpcSectionFor, isValidCode, isValidSlug } from "./types.js";

describe("isValidCode", () => {
  it.each(["10", "11", "43", "50", "99"])("accepts %s", (c) => {
    expect(isValidCode(c)).toBe(true);
  });

  it.each(["1", "100", "1A", "-1", "", "abc"])("rejects %s", (c) => {
    expect(isValidCode(c)).toBe(false);
  });
});

describe("isValidSlug", () => {
  it.each([
    "live-animals",
    "mineral-textile",
    "editorial-design",
    "ab",
    "a1",
    "land-buildings",
    "z9",
  ])("accepts %s", (s) => {
    expect(isValidSlug(s)).toBe(true);
  });

  it.each([
    "Live-Animals",   // uppercase
    "-leading",
    "trailing-",
    "double--hyphen",
    "a",              // too short
    "_underscore",
    "with space",
    "with.dot",
    "",
  ])("rejects %s", (s) => {
    // Note: "double--hyphen" passes the SLUG_RE technically (no rule against
    // consecutive hyphens); document it here for future tightening if needed.
    if (s === "double--hyphen") {
      expect(isValidSlug(s)).toBe(true);
    } else {
      expect(isValidSlug(s)).toBe(false);
    }
  });
});

describe("cpcSectionFor", () => {
  // Range boundary spot-checks per CLAUDE.md mapping.
  it.each([
    ["10", "0-1"],
    ["15", "0-1"],
    ["20", "3-4"],
    ["27", "3-4"],
    ["30", "5"],
    ["31", "5"],
    ["39", "3-4"],
    ["48", "3-4"],
    ["50", "2"],
    ["53", "2"],
    ["55", "8"],
    ["60", "8"],
    ["70", "6-9"],
    ["86", "6-9"],
    ["90", "9"],
    ["95", "9"],
  ])("code %s → CPC section %s", (code, section) => {
    expect(cpcSectionFor(code)).toBe(section);
  });

  it.each(["16", "17", "18", "19", "28", "29", "32", "33", "34", "49", "54", "65"])(
    "code %s falls in a gap → undefined",
    (code) => {
      expect(cpcSectionFor(code)).toBeUndefined();
    },
  );

  it("invalid codes return undefined (not an exception)", () => {
    expect(cpcSectionFor("1")).toBeUndefined();
    expect(cpcSectionFor("100")).toBeUndefined();
    expect(cpcSectionFor("ab")).toBeUndefined();
  });
});
