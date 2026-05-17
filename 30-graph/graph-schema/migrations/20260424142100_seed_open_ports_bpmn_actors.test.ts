import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424142100_seed_open_ports_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-ports/scheduleVesselCall.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-ports/reportIncident.bpmn"),
  "utf-8",
);

describe("Seed open-ports BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-ports-schedule-vessel-call-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_ports_schedule_vessel_call"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-ports/scheduleVesselCall.bpmn"');
    expect(migrationSource).toContain("open-ports-report-incident-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_ports_report_incident"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-ports/reportIncident.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openPorts.scheduleVesselCall"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openPorts.reportIncident"');
  });

  it("uses open-ports-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-ports"');
    expect(migrationSource).toContain("did:web:open-ports.etzhayyim.com:ops");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_ports_schedule_vessel_call"');
    expect(bpmn2).toContain('id="open_ports_report_incident"');
  });
});
