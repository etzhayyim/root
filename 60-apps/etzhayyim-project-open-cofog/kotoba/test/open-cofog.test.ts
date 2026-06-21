import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerEntry,
  getEntry,
  listEntries,
  coverage,
  cofogLevel,
  parentOf,
  ancestorsOf,
  isValidCofogCode,
} from "../src/index.js";

describe("open-cofog kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:open-cofog.etzhayyim.com" });
  });

  describe("hierarchy helpers", () => {
    it("validates COFOG codes (division 01-10)", () => {
      expect(isValidCofogCode("07")).toBe(true);
      expect(isValidCofogCode("073")).toBe(true);
      expect(isValidCofogCode("0731")).toBe(true);
      expect(isValidCofogCode("11")).toBe(false); // division > 10
      expect(isValidCofogCode("00")).toBe(false);
      expect(isValidCofogCode("07311")).toBe(false); // too long
      expect(isValidCofogCode("7")).toBe(false);
    });
    it("levels + parent + ancestors", () => {
      expect(cofogLevel("07")).toBe("division");
      expect(cofogLevel("073")).toBe("group");
      expect(cofogLevel("0731")).toBe("class");
      expect(parentOf("0731")).toBe("073");
      expect(parentOf("073")).toBe("07");
      expect(parentOf("07")).toBeNull();
      expect(ancestorsOf("0731")).toEqual(["07", "073"]);
    });
  });

  describe("registry", () => {
    it("registers + derives level/division/parent", async () => {
      const r = await registerEntry(e, { code: "0731", titleEn: "General hospital services" });
      expect(r.status).toBe("registered");
      const got = await getEntry(e, { code: "0731" });
      expect(got.entry?.level).toBe("class");
      expect(got.entry?.division).toBe("07");
      expect(got.entry?.parent).toBe("073");
    });
    it("rejects invalid code + is idempotent", async () => {
      expect((await registerEntry(e, { code: "11", titleEn: "x" })).status).toBe("rejected");
      await registerEntry(e, { code: "07", titleEn: "Health" });
      expect((await registerEntry(e, { code: "07", titleEn: "Health" })).status).toBe("alreadyExists");
    });
    it("lists by level/division + coverage aggregates", async () => {
      await registerEntry(e, { code: "07", titleEn: "Health" });
      await registerEntry(e, { code: "073", titleEn: "Hospital services" });
      await registerEntry(e, { code: "0731", titleEn: "General hospital services" });
      await registerEntry(e, { code: "10", titleEn: "Social protection" });
      expect((await listEntries(e, { level: "class" })).total).toBe(1);
      expect((await listEntries(e, { division: "07" })).total).toBe(3);
      const cov = await coverage(e);
      expect(cov.total).toBe(4);
      expect(cov.byLevel?.division).toBe(2);
      expect(cov.byDivision?.["07"]).toBe(3);
    });
  });
});
