import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424121000_seed_open_water_bpmn_actors.ts"),
  "utf-8",
);
const bpmnDefineMain = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-water/defineMain.bpmn"),
  "utf-8",
);
const bpmnReportLeak = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-water/reportLeak.bpmn"),
  "utf-8",
);

describe("Seed open-water BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-water-define-main-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_water_define_main"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-water/defineMain.bpmn"');
    expect(migrationSource).toContain("open-water-report-leak-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_water_report_leak"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-water/reportLeak.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openWater.defineMain"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openWater.reportLeak"');
  });

  it("uses open-water-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-water"');
    expect(migrationSource).toContain('did:web:open-water.etzhayyim.com:network');
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmnDefineMain, bpmnReportLeak]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
    }
    expect(bpmnDefineMain).toContain('type="generic.db.insert"');
    expect(bpmnDefineMain).toContain('type="generic.audit.emit"');
    expect(bpmnReportLeak).toContain('type="generic.db.insert"');
    expect(bpmnReportLeak).toContain('type="generic.pds.dispatch"');
    expect(bpmnReportLeak).toContain('type="generic.audit.emit"');
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmnDefineMain).toContain('id="open_water_define_main"');
    expect(bpmnReportLeak).toContain('id="open_water_report_leak"');
  });
});
