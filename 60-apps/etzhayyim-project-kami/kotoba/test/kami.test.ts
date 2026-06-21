import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  createProject,
  getProject,
  listProjects,
  putDesign,
  getDesign,
  listDesigns,
  createWorld,
  listWorlds,
  coverage,
} from "../src/index.js";

const CID = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi";
const CID2 = "bafkreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku";
const OWNER = "did:web:kami.etzhayyim.com:guest:g1";

describe("kami kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:kami.etzhayyim.com" });
  });

  describe("engineering project + design (upsert across disciplines)", () => {
    it("creates project, puts/updates designs (FK→project, version bump), validates", async () => {
      expect((await createProject(e, { projectId: "P-1", name: "PCB Rev A", ownerDid: OWNER })).status).toBe("created");
      expect((await createProject(e, { projectId: "P-X", name: "x", ownerDid: "nope" })).status).toBe("rejected");
      const c = await putDesign(e, { designId: "D-1", projectId: "P-1", discipline: "eda-schematic", name: "main.sch", artifactCid: CID });
      expect(c.status).toBe("created");
      expect(c.version).toBe(1);
      const u = await putDesign(e, { designId: "D-1", projectId: "P-1", discipline: "eda-pcb", name: "main.pcb", artifactCid: CID2 });
      expect(u.status).toBe("updated");
      expect(u.version).toBe(2);
      expect((await getDesign(e, { designId: "D-1" })).design?.discipline).toBe("eda-pcb");
      expect((await putDesign(e, { designId: "D-X", projectId: "P-1", discipline: "warp-core" as any, name: "x" })).status).toBe("rejected");
      expect((await putDesign(e, { designId: "D-X", projectId: "GHOST", discipline: "cad-model", name: "x" })).status).toBe("projectNotFound");
      await putDesign(e, { designId: "D-2", projectId: "P-1", discipline: "cae-analysis", name: "fea.json" });
      expect((await listDesigns(e, { projectId: "P-1", discipline: "cae-analysis" })).total).toBe(1);
      expect((await listProjects(e, { ownerDid: OWNER })).total).toBe(1);
    });
  });

  describe("game worlds + coverage", () => {
    it("creates guest worlds (template), lists by template + search; validates", async () => {
      expect((await createWorld(e, { worldId: "W-1", name: "Sky Islands", creatorDid: OWNER, template: "minecraft", sceneCid: CID })).status).toBe("created");
      expect((await createWorld(e, { worldId: "W-2", name: "Battle Arena", creatorDid: OWNER, template: "fortnite", visibility: "private" })).status).toBe("created");
      expect((await createWorld(e, { worldId: "W-X", name: "x", creatorDid: OWNER, template: "doom" as any })).status).toBe("rejected");
      expect((await listWorlds(e, { template: "minecraft" })).total).toBe(1);
      expect((await listWorlds(e, { visibility: "public" })).total).toBe(1);
      expect((await listWorlds(e, { q: "arena" })).total).toBe(1);
    });
    it("coverage rolls up the three collections", async () => {
      await createProject(e, { projectId: "P-1", name: "P", ownerDid: OWNER });
      await putDesign(e, { designId: "D-1", projectId: "P-1", discipline: "rtl-module", name: "alu.v" });
      await createWorld(e, { worldId: "W-1", name: "W", creatorDid: OWNER, template: "blank" });
      const cov = await coverage(e);
      expect(cov.projectCount).toBe(1);
      expect(cov.designCount).toBe(1);
      expect(cov.worldCount).toBe(1);
      expect(cov.designsByDiscipline?.["rtl-module"]).toBe(1);
      expect(cov.worldsByTemplate?.blank).toBe(1);
    });
  });
});
