import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424161100_seed_open_lei_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-lei/registerLegalEntity.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-lei/recordOwnership.bpmn"),
  "utf-8",
);
const bpmn3 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-lei/collectGleifGlobalLei.bpmn"),
  "utf-8",
);

describe("Seed open-lei BPMN actors migration", () => {
  it("seeds process definitions", () => {
    expect(migrationSource).toContain("open-lei-register-legal-entity-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_lei_register_legal_entity"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-lei/registerLegalEntity.bpmn"');
    expect(migrationSource).toContain("open-lei-record-ownership-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_lei_record_ownership"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-lei/recordOwnership.bpmn"');
    expect(migrationSource).toContain("open-lei-collect-gleif-global-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_lei_collect_gleif_global_lei"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-lei/collectGleifGlobalLei.bpmn"');
  });
  it("seeds lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openLei.registerLegalEntity"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openLei.recordOwnership"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openLei.collectGleifGlobal"');
  });
  it("uses open-lei-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-lei"');
    expect(migrationSource).toContain("did:web:open-lei.etzhayyim.com");
  });
  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2, bpmn3]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
    expect(bpmn1 + bpmn2).toContain('type="generic.db.insert"');
    expect(bpmn3).toContain('type="openLei.gleif.manifest.plan"');
  });
  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_lei_register_legal_entity"');
    expect(bpmn2).toContain('id="open_lei_record_ownership"');
    expect(bpmn3).toContain('id="open_lei_collect_gleif_global_lei"');
  });
});
