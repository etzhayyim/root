import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424130100_seed_open_airplane_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-airplane/scheduleFlight.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-airplane/reportIncident.bpmn"),
  "utf-8",
);

describe("Seed open-airplane BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-airplane-schedule-flight-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_airplane_schedule_flight"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-airplane/scheduleFlight.bpmn"');
    expect(migrationSource).toContain("open-airplane-report-incident-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_airplane_report_incident"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-airplane/reportIncident.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openAirplane.scheduleFlight"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openAirplane.reportIncident"');
  });

  it("uses open-airplane-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-airplane"');
    expect(migrationSource).toContain("did:web:open-airplane.etzhayyim.com:ops");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_airplane_schedule_flight"');
    expect(bpmn2).toContain('id="open_airplane_report_incident"');
  });
});
