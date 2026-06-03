import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerCourt,
  getCourt,
  listCourts,
  addJudge,
  listJudges,
  mapJurisdiction,
  listJurisdictionMaps,
  coverage,
} from "../src/index.js";

describe("saiban rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:saiban.etzhayyim.com" });
  });

  describe("court hierarchy", () => {
    it("registers courts (parent FK), validates jurisdiction/level, lists", async () => {
      expect((await registerCourt(e, { courtId: "JP-SC", name: "最高裁判所", jurisdiction: "jp", level: "supreme" })).status).toBe("registered");
      expect((await registerCourt(e, { courtId: "JP-TKO-DC", name: "東京地方裁判所", jurisdiction: "JP", level: "district", parentCourtId: "JP-SC" })).status).toBe("registered");
      expect((await registerCourt(e, { courtId: "X", name: "x", jurisdiction: "JPN", level: "district" })).status).toBe("rejected"); // jurisdiction
      expect((await registerCourt(e, { courtId: "Y", name: "y", jurisdiction: "JP", level: "galactic" as any })).status).toBe("rejected"); // level
      expect((await registerCourt(e, { courtId: "Z", name: "z", jurisdiction: "JP", level: "high", parentCourtId: "GHOST" })).status).toBe("parentNotFound");
      expect((await getCourt(e, { courtId: "JP-SC" })).court?.level).toBe("supreme");
      expect((await listCourts(e, { jurisdiction: "JP", level: "district" })).total).toBe(1);
      expect((await listCourts(e, { q: "東京" })).total).toBe(1);
    });
  });

  describe("judges + jurisdiction maps", () => {
    beforeEach(async () => {
      await registerCourt(e, { courtId: "JP-TKO-DC", name: "東京地方裁判所", jurisdiction: "JP", level: "district" });
    });
    it("adds judges (FK→court, public official), rejects missing court", async () => {
      expect((await addJudge(e, { judgeId: "J-1", courtId: "JP-TKO-DC", name: "山田太郎", title: "presiding-judge", appointedDate: "2022-04-01" })).status).toBe("added");
      expect((await addJudge(e, { judgeId: "J-X", courtId: "GHOST", name: "x", title: "judge" })).status).toBe("courtNotFound");
      expect((await addJudge(e, { judgeId: "J-Y", courtId: "JP-TKO-DC", name: "y", title: "emperor" as any })).status).toBe("rejected");
      expect((await listJudges(e, { courtId: "JP-TKO-DC", title: "presiding-judge" })).total).toBe(1);
    });
    it("maps jurisdiction (FK→court, matter type), rejects bad type", async () => {
      expect((await mapJurisdiction(e, { mappingId: "M-1", courtId: "JP-TKO-DC", scope: "東京都23区", matterType: "civil" })).status).toBe("mapped");
      expect((await mapJurisdiction(e, { mappingId: "M-X", courtId: "JP-TKO-DC", scope: "x", matterType: "alien" as any })).status).toBe("rejected");
      expect((await listJurisdictionMaps(e, { courtId: "JP-TKO-DC", matterType: "civil" })).total).toBe(1);
    });
    it("coverage rolls up the three collections", async () => {
      await addJudge(e, { judgeId: "J-1", courtId: "JP-TKO-DC", name: "T", title: "judge" });
      await mapJurisdiction(e, { mappingId: "M-1", courtId: "JP-TKO-DC", scope: "x", matterType: "criminal" });
      const cov = await coverage(e);
      expect(cov.courtCount).toBe(1);
      expect(cov.judgeCount).toBe(1);
      expect(cov.jurisdictionMapCount).toBe(1);
      expect(cov.courtsByJurisdiction?.JP).toBe(1);
      expect(cov.courtsByLevel?.district).toBe(1);
    });
  });
});
