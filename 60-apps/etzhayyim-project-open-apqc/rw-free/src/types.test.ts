/**
 * Pure-helper tests — APQC L1 code regex + ordinal extraction.
 *
 * Locks down: only the 13 v7.4 L1 codes ("1.0" .. "13.0") validate;
 * anything else is rejected. l1Ordinal returns a usable sort key.
 */

import { describe, expect, it } from "vitest";

import { isValidL1Code, l1Ordinal } from "./types.js";

describe("isValidL1Code", () => {
  it.each([
    "1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "7.0",
    "8.0", "9.0", "10.0", "11.0", "12.0", "13.0",
  ])("accepts L1 code %s", (c) => {
    expect(isValidL1Code(c)).toBe(true);
  });

  it.each([
    "0.0",      // 0 is not an L1
    "14.0",     // v7.4 stops at 13
    "100.0",
    "1",        // missing .0 suffix
    "1.0.0",    // L3-shaped
    "1.1",      // L2-shaped
    "a.0",
    "1.A",
    "",
    " 1.0",
    "1.0 ",
  ])("rejects %s", (c) => {
    expect(isValidL1Code(c)).toBe(false);
  });
});

describe("l1Ordinal", () => {
  it.each([
    ["1.0", 1],
    ["7.0", 7],
    ["13.0", 13],
  ])("returns numeric ordinal for %s", (code, expected) => {
    expect(l1Ordinal(code)).toBe(expected);
  });

  it("returns NaN for invalid codes (preserves sort safety)", () => {
    expect(Number.isNaN(l1Ordinal("14.0"))).toBe(true);
    expect(Number.isNaN(l1Ordinal("1.1"))).toBe(true);
    expect(Number.isNaN(l1Ordinal("foo"))).toBe(true);
  });
});
