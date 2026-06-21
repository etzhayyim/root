import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerAgency,
  getAgency,
  listAgencies,
  recordOfficial,
  listOfficials,
  registerMunicipality,
  listMunicipalities,
  coverage,
} from "../src/index.js";

describe("gov kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:gov.etzhayyim.com" });
  });

  describe("agency hierarchy + officials", () => {
    it("registers agencies (parent FK), officials (FK→agency), lists + validates", async () => {
      expect((await registerAgency(e, { agencyId: "MHLW", name: "厚生労働省", level: "national", cofogCode: "07" })).status).toBe("registered");
      expect((await registerAgency(e, { agencyId: "MHLW-PB", name: "保険局", level: "national", parentAgencyId: "MHLW" })).status).toBe("registered");
      expect((await registerAgency(e, { agencyId: "X", name: "x", level: "galactic" as any })).status).toBe("rejected");
      expect((await registerAgency(e, { agencyId: "Y", name: "y", level: "national", parentAgencyId: "GHOST" })).status).toBe("parentNotFound");
      expect((await getAgency(e, { agencyId: "MHLW" })).agency?.cofogCode).toBe("07");
      expect((await listAgencies(e, { parentAgencyId: "MHLW" })).total).toBe(1);
      expect((await listAgencies(e, { q: "厚生" })).total).toBe(1);
      expect((await recordOfficial(e, { officialId: "O-1", agencyId: "MHLW", name: "Yamada Taro", title: "大臣", term: "2024-2028" })).status).toBe("recorded");
      expect((await recordOfficial(e, { officialId: "O-X", agencyId: "GHOST", name: "x", title: "y" })).status).toBe("agencyNotFound");
      expect((await listOfficials(e, { agencyId: "MHLW", title: "大臣" })).total).toBe(1);
    });
  });

  describe("municipalities + coverage", () => {
    it("registers municipalities, validates JIS/population, lists by prefecture", async () => {
      expect((await registerMunicipality(e, { municipalityId: "M-1", name: "千代田区", prefecture: "東京都", jisCode: "13101", population: 66680 })).status).toBe("registered");
      expect((await registerMunicipality(e, { municipalityId: "M-2", name: "横浜市", prefecture: "神奈川県", population: 3770000 })).status).toBe("registered");
      expect((await registerMunicipality(e, { municipalityId: "M-X", name: "x", prefecture: "y", jisCode: "999" })).status).toBe("rejected");
      expect((await registerMunicipality(e, { municipalityId: "M-Y", name: "x", prefecture: "y", population: -1 })).status).toBe("rejected");
      expect((await listMunicipalities(e, { prefecture: "東京都" })).total).toBe(1);
    });
    it("coverage rolls up the three reference collections", async () => {
      await registerAgency(e, { agencyId: "MHLW", name: "厚労省", level: "national" });
      await recordOfficial(e, { officialId: "O-1", agencyId: "MHLW", name: "T", title: "大臣" });
      await registerMunicipality(e, { municipalityId: "M-1", name: "千代田区", prefecture: "東京都", population: 66680 });
      const cov = await coverage(e);
      expect(cov.agencyCount).toBe(1);
      expect(cov.officialCount).toBe(1);
      expect(cov.municipalityCount).toBe(1);
      expect(cov.agenciesByLevel?.national).toBe(1);
      expect(cov.totalPopulation).toBe(66680);
    });
  });
});
