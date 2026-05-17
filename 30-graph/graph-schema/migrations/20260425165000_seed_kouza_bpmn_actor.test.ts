import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260425165000_seed_kouza_bpmn_actor.ts"),
  "utf-8",
);
const bpmn = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/kouza/syncDueConnections.bpmn"),
  "utf-8",
);

describe("Seed kouza BPMN actor migration", () => {
  it("seeds the resident sync process definition", () => {
    expect(migrationSource).toContain("kouza-sync-due-connections-v1");
    expect(migrationSource).toContain('bpmnProcessId: "kouza_sync_due_connections"');
    expect(migrationSource).toContain(
      'sourcePath: "00-contracts/bpmn/ai/gftd/kouza/syncDueConnections.bpmn"',
    );
  });

  it("seeds the MCP/lexicon binding", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.kouza.syncDueConnections"');
    expect(migrationSource).toContain("did:web:kouza.etzhayyim.com");
    expect(migrationSource).toContain("sys.bpmn.seed.kouza");
  });

  it("BPMN is a timer-start Zeebe resident process", () => {
    expect(bpmn).toContain('id="kouza_sync_due_connections"');
    expect(bpmn).toContain("<bpmn:timerEventDefinition");
    expect(bpmn).toContain("R/PT30M");
    expect(bpmn).toContain('type="ai.gftd.kouza.syncDueConnections"');
    expect(bpmn).toContain('type="generic.audit.emit"');
  });
});
