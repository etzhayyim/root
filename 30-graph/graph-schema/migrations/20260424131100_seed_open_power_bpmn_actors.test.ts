import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424131100_seed_open_power_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-power/defineFeeder.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-power/reportOutage.bpmn"),
  "utf-8",
);

describe("Seed open-power BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-power-define-feeder-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_power_define_feeder"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-power/defineFeeder.bpmn"');
    expect(migrationSource).toContain("open-power-report-outage-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_power_report_outage"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-power/reportOutage.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openPower.defineFeeder"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openPower.reportOutage"');
  });

  it("uses open-power-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-power"');
    expect(migrationSource).toContain("did:web:open-power.etzhayyim.com:grid");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_power_define_feeder"');
    expect(bpmn2).toContain('id="open_power_report_outage"');
  });
});
