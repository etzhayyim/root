import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  createOrg,
  getOrg,
  listOrgs,
  createProject,
  setProjectStatus,
  listProjects,
  assignResource,
  listResources,
  getOrgMetrics,
  coverage,
} from "../src/index.js";

describe("ge kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:ge.etzhayyim.com" });
  });

  describe("org hierarchy", () => {
    it("creates, reads, lists by parent/region; rejects missing parent", async () => {
      expect((await createOrg(e, { orgId: "ORG-HQ", name: "HQ", region: "global" })).status).toBe("created");
      expect((await createOrg(e, { orgId: "ORG-APAC", name: "APAC", parentOrgId: "ORG-HQ", region: "apac" })).status).toBe("created");
      expect((await getOrg(e, { orgId: "ORG-APAC" })).org?.parentOrgId).toBe("ORG-HQ");
      expect((await createOrg(e, { orgId: "ORG-X", name: "x", parentOrgId: "GHOST" })).status).toBe("parentNotFound");
      expect((await listOrgs(e, { parentOrgId: "ORG-HQ" })).total).toBe(1);
      expect((await createOrg(e, { orgId: "ORG-HQ", name: "dup" })).status).toBe("alreadyExists");
    });
  });

  describe("projects + resources + metrics", () => {
    beforeEach(async () => {
      await createOrg(e, { orgId: "ORG-APAC", name: "APAC" });
    });
    it("creates project (FK→org), advances status with terminal guard", async () => {
      expect((await createProject(e, { projectId: "P-1", orgId: "ORG-APAC", name: "Launch JP" })).status).toBe("created");
      expect((await createProject(e, { projectId: "P-X", orgId: "GHOST", name: "x" })).status).toBe("orgNotFound");
      expect((await setProjectStatus(e, { projectId: "P-1", status: "active" })).newStatus).toBe("active");
      expect((await setProjectStatus(e, { projectId: "P-1", status: "completed" })).newStatus).toBe("completed");
      expect((await setProjectStatus(e, { projectId: "P-1", status: "active" })).status).toBe("rejected"); // terminal
      expect((await listProjects(e, { orgId: "ORG-APAC", status: "completed" })).total).toBe(1);
    });
    it("assigns resources (FK→project), rejects bad headcount; rolls up org metrics", async () => {
      await createProject(e, { projectId: "P-1", orgId: "ORG-APAC", name: "Launch JP" });
      await createProject(e, { projectId: "P-2", orgId: "ORG-APAC", name: "Launch KR" });
      expect((await assignResource(e, { assignmentId: "A-1", projectId: "P-1", role: "engineer", headcount: 5 })).status).toBe("assigned");
      expect((await assignResource(e, { assignmentId: "A-2", projectId: "P-1", role: "pm", headcount: 1 })).status).toBe("assigned");
      expect((await assignResource(e, { assignmentId: "A-3", projectId: "P-2", role: "engineer", headcount: 3 })).status).toBe("assigned");
      expect((await assignResource(e, { assignmentId: "A-X", projectId: "GHOST", role: "x", headcount: 1 })).status).toBe("projectNotFound");
      expect((await assignResource(e, { assignmentId: "A-Y", projectId: "P-1", role: "x", headcount: 0 })).status).toBe("rejected");
      expect((await listResources(e, { projectId: "P-1", role: "engineer" })).total).toBe(1);
      const m = await getOrgMetrics(e, { orgId: "ORG-APAC" });
      expect(m.projectCount).toBe(2);
      expect(m.totalHeadcount).toBe(9);
      expect(m.headcountByRole?.engineer).toBe(8);
      expect(m.headcountByRole?.pm).toBe(1);
    });
    it("coverage rolls up the three collections", async () => {
      await createProject(e, { projectId: "P-1", orgId: "ORG-APAC", name: "Launch JP" });
      await assignResource(e, { assignmentId: "A-1", projectId: "P-1", role: "engineer", headcount: 4 });
      const cov = await coverage(e);
      expect(cov.orgCount).toBe(1);
      expect(cov.projectCount).toBe(1);
      expect(cov.assignmentCount).toBe(1);
      expect(cov.totalHeadcount).toBe(4);
      expect(cov.projectsByStatus?.planned).toBe(1);
    });
  });
});
