import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(resolve(__dirname, "20260423180000_seed_datacenter_bpmn_actor.ts"), "utf-8");
const bpmnSource = readFileSync(resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/datacenter/operateFacility.bpmn"), "utf-8");

describe("Seed Datacenter BPMN Actor Migration", () => {
  it("seeds the datacenter BPMN process definition", () => {
    expect(migrationSource).toContain("datacenter-operate-facility-v1");
    expect(migrationSource).toContain('bpmnProcessId: "datacenter_operate_facility"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/datacenter/operateFacility.bpmn"');
    expect(migrationSource).toContain('ownerDid: "did:web:infra.etzhayyim.com:datacenter"');
    expect(migrationSource).toContain("datacenter-access-review-v1");
    expect(migrationSource).toContain("datacenter-reserve-capacity-v1");
    expect(migrationSource).toContain("datacenter-purge-access-pii-v1");
  });

  it("seeds the startOperation lexicon binding", () => {
    expect(migrationSource).toContain("datacenter-startOperation-v1");
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.datacenter.startOperation"');
    expect(migrationSource).toContain("resultTimeoutMs: 0");
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.datacenter.requestAccess"');
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.datacenter.reserveCapacity"');
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.datacenter.purgeAccessPii"');
  });

  it("uses datacenter-specific seed actor_id", () => {
    expect(migrationSource).toContain("sys.bpmn.seed.datacenter");
  });

  it("matches the BPMN process id in the XML contract", () => {
    expect(bpmnSource).toContain('id="datacenter_operate_facility"');
    expect(bpmnSource).toContain('name="データセンター運営"');
  });
});
