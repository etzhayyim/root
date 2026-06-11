/**
 * scap zod schema validation tests (coverage loop iteration 11).
 *
 * The SCAP security schemas (CVE / OVAL / scan-result / content / integration)
 * are the single source of truth for what counts as valid scan/vuln data, and
 * had zero tests. These verify the constraints actually accept valid records
 * and REJECT malformed ones (out-of-range scores, bad enums, negative counts,
 * empty required strings, non-URL references) + default/coercion behavior.
 */
import { describe, it, expect } from "vitest";
import {
  scapScanResultSchema,
  scapTestResultSchema,
  cveDataSchema,
  cveReferenceSchema,
  ovalDefinitionSchema,
  scapContentSchema,
  integrationSchema,
} from "../index";

// ── helpers ──────────────────────────────────────────────────────────────────
const ok = (schema: { safeParse: (v: unknown) => { success: boolean } }, v: unknown) =>
  schema.safeParse(v).success;

// ── CVE ──────────────────────────────────────────────────────────────────────

const validCve = {
  cveId: "CVE-2023-36025",
  description: "Windows SmartScreen bypass",
  publishedDate: "2023-11-14T00:00:00Z",
  lastModifiedDate: "2023-11-15T00:00:00Z",
  cvssScore: 8.8,
  severity: "high",
  cweIds: ["CWE-79"],
  references: [{ url: "https://nvd.nist.gov/vuln/detail/CVE-2023-36025", source: "nvd", tags: ["patch"] }],
  affectedProducts: [{ vendor: "microsoft", product: "windows", versions: ["10"] }],
};

describe("cveDataSchema", () => {
  it("accepts a valid CVE and coerces ISO dates + defaults status=published", () => {
    const r = cveDataSchema.parse(validCve);
    expect(r.publishedDate).toBeInstanceOf(Date);
    expect(r.status).toBe("published");
  });

  it("rejects an out-of-range cvssScore (>10) and a bad severity enum", () => {
    expect(ok(cveDataSchema, { ...validCve, cvssScore: 11 })).toBe(false);
    expect(ok(cveDataSchema, { ...validCve, cvssScore: -1 })).toBe(false);
    expect(ok(cveDataSchema, { ...validCve, severity: "spicy" })).toBe(false);
  });

  it("rejects empty required strings and a non-URL reference", () => {
    expect(ok(cveDataSchema, { ...validCve, cveId: "" })).toBe(false);
    expect(ok(cveReferenceSchema, { url: "not-a-url", source: "x", tags: [] })).toBe(false);
    expect(ok(cveReferenceSchema, { url: "https://x.test", source: "x", tags: [] })).toBe(true);
  });
});

// ── SCAP scan result + test result ──────────────────────────────────────────

describe("scapTestResultSchema", () => {
  const base = { ruleId: "xccdf_rule_1", result: "pass", score: 100, timestamp: "2026-06-12T00:00:00Z" };
  it("bounds score to 0..100 and enumerates result", () => {
    expect(ok(scapTestResultSchema, base)).toBe(true);
    expect(ok(scapTestResultSchema, { ...base, score: 101 })).toBe(false);
    expect(ok(scapTestResultSchema, { ...base, score: -1 })).toBe(false);
    expect(ok(scapTestResultSchema, { ...base, result: "maybe" })).toBe(false);
  });
});

describe("scapScanResultSchema", () => {
  const valid = {
    id: "scan-1", scanId: "s1", integrationId: "i1", targetId: "t1",
    targetType: "host", scapContentId: "c1",
    executedAt: "2026-06-12T00:00:00Z",
    results: [{ ruleId: "r1", result: "fail", score: 0, timestamp: "2026-06-12T00:00:00Z" }],
    summary: {
      totalRules: 1, passedRules: 0, failedRules: 1, errorRules: 0,
      unknownRules: 0, notApplicableRules: 0, compliancePercentage: 0,
    },
  };

  it("accepts a valid scan and defaults status=pending", () => {
    const r = scapScanResultSchema.parse(valid);
    expect(r.status).toBe("pending");
    expect(r.executedAt).toBeInstanceOf(Date);
  });

  it("rejects a bad targetType, negative summary counts, and >100 compliance", () => {
    expect(ok(scapScanResultSchema, { ...valid, targetType: "toaster" })).toBe(false);
    expect(ok(scapScanResultSchema, {
      ...valid, summary: { ...valid.summary, passedRules: -1 },
    })).toBe(false);
    expect(ok(scapScanResultSchema, {
      ...valid, summary: { ...valid.summary, compliancePercentage: 101 },
    })).toBe(false);
  });

  it("rejects a non-integer rule count", () => {
    expect(ok(scapScanResultSchema, {
      ...valid, summary: { ...valid.summary, totalRules: 1.5 },
    })).toBe(false);
  });
});

// ── OVAL ─────────────────────────────────────────────────────────────────────

describe("ovalDefinitionSchema", () => {
  const valid = {
    id: "oval:def:1", title: "Win10 vuln", description: "d", class: "vulnerability",
    affectedProducts: ["windows-10"],
    metadata: { title: "t", description: "d", affected: [{ family: "windows", platforms: ["10"] }] },
    criteria: { operator: "AND", criterion: [{ testRef: "oval:tst:1", comment: "c" }] },
  };
  it("accepts a valid definition; rejects a bad class + bad criteria operator", () => {
    expect(ok(ovalDefinitionSchema, valid)).toBe(true);
    expect(ok(ovalDefinitionSchema, { ...valid, class: "nonsense" })).toBe(false);
    expect(ok(ovalDefinitionSchema, {
      ...valid, criteria: { ...valid.criteria, operator: "XOR" },
    })).toBe(false);
    expect(ok(ovalDefinitionSchema, { ...valid, id: "" })).toBe(false);
  });
});

// ── SCAP content + integration ───────────────────────────────────────────────

describe("scapContentSchema", () => {
  const valid = {
    id: "c1", title: "USGCB Win10", description: "benchmark",
    type: "xccdf", version: "1.0", status: "active", source: "nist",
    publishedDate: "2022-08-01T00:00:00Z", lastUpdated: "2022-08-01T00:00:00Z",
    metadata: { publisher: "nist", platforms: ["windows"], tags: ["gov"], references: [] },
    content: { raw: "<xml/>", parsed: {}, checksum: "abc", size: 6 },
  };
  it("accepts valid content + defaults status=active; rejects bad type/status, empty title, non-URL ref, negative size", () => {
    const r = scapContentSchema.parse({ ...valid, status: undefined });
    expect(r.status).toBe("active");
    expect(ok(scapContentSchema, { ...valid, type: "yaml" })).toBe(false);
    expect(ok(scapContentSchema, { ...valid, status: "archived" })).toBe(false);
    expect(ok(scapContentSchema, { ...valid, title: "" })).toBe(false);
    expect(ok(scapContentSchema, {
      ...valid, metadata: { ...valid.metadata, references: [{ url: "bad", source: "s", tags: [] }] },
    })).toBe(false);
    expect(ok(scapContentSchema, {
      ...valid, content: { ...valid.content, size: -1 },
    })).toBe(false);
  });
});

describe("integrationSchema", () => {
  it("defaults status=active and rejects a bad type/status / empty id", () => {
    const r = integrationSchema.parse({ id: "i1", type: "aws", name: "scanner", config: {} });
    expect(r.status).toBe("active");
    expect(ok(integrationSchema, { id: "i1", type: "openscap", name: "n", config: {} })).toBe(false); // not in enum
    expect(ok(integrationSchema, { id: "i1", type: "aws", name: "n", status: "broken", config: {} })).toBe(false);
    expect(ok(integrationSchema, { id: "", type: "aws", name: "n", config: {} })).toBe(false);
  });
});
