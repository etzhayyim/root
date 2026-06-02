import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424164100_seed_open_transit_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-transit/defineRoute.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-transit/reportDelay.bpmn"),
  "utf-8",
);

describe("Seed open-transit BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-transit-define-route-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_transit_define_route"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-transit/defineRoute.bpmn"');
    expect(migrationSource).toContain("open-transit-report-delay-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_transit_report_delay"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-transit/reportDelay.bpmn"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openTransit.defineRoute"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openTransit.reportDelay"');
  });
  it("uses open-transit-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-transit"');
    expect(migrationSource).toContain("did:web:open-transit.etzhayyim.com");
  });
  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_transit_define_route"');
    expect(bpmn2).toContain('id="open_transit_report_delay"');
  });
});
