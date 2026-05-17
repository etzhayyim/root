import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424140100_seed_open_banking_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-banking/createAccount.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-banking/transfer.bpmn"),
  "utf-8",
);

describe("Seed open-banking BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-banking-create-account-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_banking_create_account"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-banking/createAccount.bpmn"');
    expect(migrationSource).toContain("open-banking-transfer-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_banking_transfer"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-banking/transfer.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openBanking.createAccount"');
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.openBanking.transfer"');
  });

  it("uses open-banking-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-banking"');
    expect(migrationSource).toContain("did:web:open-banking.etzhayyim.com:core");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_banking_create_account"');
    expect(bpmn2).toContain('id="open_banking_transfer"');
  });
});
