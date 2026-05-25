import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424162100_seed_open_sanctions_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-sanctions/recordSanctionsEntry.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-sanctions/screenEntity.bpmn"),
  "utf-8",
);

describe("Seed open-sanctions BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-sanctions-record-entry-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_sanctions_record_entry"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-sanctions/recordSanctionsEntry.bpmn"');
    expect(migrationSource).toContain("open-sanctions-screen-entity-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_sanctions_screen_entity"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-sanctions/screenEntity.bpmn"');
  });
  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openSanctions.recordSanctionsEntry"');
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openSanctions.screenEntity"');
  });
  it("uses open-sanctions-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-sanctions"');
    expect(migrationSource).toContain("did:web:open-sanctions.etzhayyim.com");
  });
  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });
  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_sanctions_record_entry"');
    expect(bpmn2).toContain('id="open_sanctions_screen_entity"');
  });
});
