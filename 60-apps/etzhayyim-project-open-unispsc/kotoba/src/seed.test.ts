/**
 * Pure-helper tests for the seed converter + CSV parser. No SDK / network.
 */

import { describe, expect, it } from "vitest";

import { csvRowToSegmentDef, parseCsv } from "./seed.js";

describe("csvRowToSegmentDef", () => {
  it("converts a valid row with CPC-section enrichment", () => {
    const out = csvRowToSegmentDef({
      code: "43",
      slug: "communications-devices",
      name: "Communications Devices and Accessories",
    });
    expect(out.code).toBe("43");
    expect(out.slug).toBe("communications-devices");
    expect(out.name).toBe("Communications Devices and Accessories");
    expect(out.publishedAt).toBe("2023-08-15T00:00:00Z");
    expect(out.cpcSection).toBe("3-4");
  });

  it("omits cpcSection for segments outside the documented ranges", () => {
    const out = csvRowToSegmentDef({code: "16", slug: "xx", name: "X"});
    // Codes 16-19 sit in the gap between agriculture (10-15) and
    // industrial (20-27); the mapping table does not cover them.
    expect(out.cpcSection).toBeUndefined();
  });

  it("trims whitespace from name", () => {
    const out = csvRowToSegmentDef({
      code: "10",
      slug: "live-animals",
      name: "  Live Animals and Livestock and Agricultural Products  ",
    });
    expect(out.name).toBe("Live Animals and Livestock and Agricultural Products");
  });

  it("rejects invalid code", () => {
    expect(() =>
      csvRowToSegmentDef({code: "1", slug: "xx", name: "X"}),
    ).toThrow(/invalid UNSPSC segment code/);
    expect(() =>
      csvRowToSegmentDef({code: "abc", slug: "xx", name: "X"}),
    ).toThrow(/invalid UNSPSC segment code/);
  });

  it("rejects invalid slug", () => {
    expect(() =>
      csvRowToSegmentDef({code: "10", slug: "Invalid Slug", name: "X"}),
    ).toThrow(/invalid slug/);
  });

  it("rejects empty name", () => {
    expect(() =>
      csvRowToSegmentDef({code: "10", slug: "xx", name: "   "}),
    ).toThrow(/empty name/);
  });
});

describe("parseCsv", () => {
  it("parses a 3-column CSV with header", () => {
    const csv = [
      "code,slug,name",
      "10,live-animals,Live Animals and Livestock and Agricultural Products",
      "43,communications-devices,Communications Devices and Accessories",
    ].join("\n");
    const out = parseCsv(csv);
    expect(out).toHaveLength(2);
    expect(out[0]).toEqual({
      code: "10",
      slug: "live-animals",
      name: "Live Animals and Livestock and Agricultural Products",
    });
    expect(out[1].code).toBe("43");
  });

  it("returns rows sorted by code (deterministic MST insertion order)", () => {
    const csv = [
      "code,slug,name",
      "43,communications-devices,Communications",
      "10,live-animals,Live",
      "85,healthcare-services,Healthcare",
    ].join("\n");
    const out = parseCsv(csv);
    expect(out.map((r) => r.code)).toEqual(["10", "43", "85"]);
  });

  it("preserves commas in the name field (greedy slice from name index onward)", () => {
    const csv = [
      "code,slug,name",
      "12,chemicals,Chemicals, including Bio Chemicals and Gas Materials",
    ].join("\n");
    const out = parseCsv(csv);
    expect(out[0].name).toBe(
      "Chemicals, including Bio Chemicals and Gas Materials",
    );
  });

  it("rejects a CSV missing required columns", () => {
    const csv = "code,name\n10,Live Animals";
    expect(() => parseCsv(csv)).toThrow(/missing required columns/);
  });

  it("returns empty array on empty input", () => {
    expect(parseCsv("")).toEqual([]);
    expect(parseCsv("   \n   \n")).toEqual([]);
  });

  it("skips blank lines", () => {
    const csv = [
      "code,slug,name",
      "",
      "10,live-animals,Live",
      "",
      "43,communications-devices,Comms",
    ].join("\n");
    expect(parseCsv(csv)).toHaveLength(2);
  });
});
