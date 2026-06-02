import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424141100_seed_open_gas_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-gas/definePipeSegment.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/open-gas/reportLeak.bpmn"),
  "utf-8",
);

describe("Seed open-gas BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-gas-define-pipe-segment-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_gas_define_pipe_segment"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-gas/definePipeSegment.bpmn"');
    expect(migrationSource).toContain("open-gas-report-leak-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_gas_report_leak"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/com/etzhayyim/open-gas/reportLeak.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openGas.definePipeSegment"');
    expect(migrationSource).toContain('nsid: "com.etzhayyim.apps.openGas.reportLeak"');
  });

  it("uses open-gas-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-gas"');
    expect(migrationSource).toContain("did:web:open-gas.etzhayyim.com:network");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_gas_define_pipe_segment"');
    expect(bpmn2).toContain('id="open_gas_report_leak"');
  });
});
