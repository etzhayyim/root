import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424163100_seed_open_road_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-road/defineRoad.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-road/reportIncident.bpmn"),
  "utf-8",
);

describe("Seed open-road BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-road-define-road-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_road_define_road"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-road/defineRoad.bpmn"');
    expect(migrationSource).toContain("open-road-report-incident-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_road_report_incident"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-road/reportIncident.bpmn"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openRoad.defineRoad"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openRoad.reportIncident"');
  });
  it("uses open-road-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-road"');
    expect(migrationSource).toContain("did:web:open-road.etzhayyim.com");
  });
  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_road_define_road"');
    expect(bpmn2).toContain('id="open_road_report_incident"');
  });
});
