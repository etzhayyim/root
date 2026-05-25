import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260424132100_seed_open_network_bpmn_actors.ts"),
  "utf-8",
);
const bpmn1 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-network/defineLink.bpmn"),
  "utf-8",
);
const bpmn2 = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/open-network/requestChange.bpmn"),
  "utf-8",
);

describe("Seed open-network BPMN actors migration", () => {
  it("seeds both process definitions", () => {
    expect(migrationSource).toContain("open-network-define-link-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_network_define_link"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-network/defineLink.bpmn"');
    expect(migrationSource).toContain("open-network-request-change-v1");
    expect(migrationSource).toContain('bpmnProcessId: "open_network_request_change"');
    expect(migrationSource).toContain('sourcePath: "00-contracts/bpmn/ai/gftd/open-network/requestChange.bpmn"');
  });

  it("seeds both lexicon bindings", () => {
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openNetwork.defineLink"');
    expect(migrationSource).toContain('nsid: "app.etzhayyim.apps.openNetwork.requestChange"');
  });

  it("uses open-network-specific actor_id + owner_did", () => {
    expect(migrationSource).toContain('"sys.bpmn.seed.open-network"');
    expect(migrationSource).toContain("did:web:open-network.etzhayyim.com:core");
  });

  it("BPMN processes target the Zeebe generic.* primitive set", () => {
    for (const xml of [bpmn1, bpmn2]) {
      expect(xml).toContain('xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"');
      expect(xml).toContain('type="generic.db.insert"');
      expect(xml).toContain('type="generic.audit.emit"');
    }
  });

  it("BPMN processIds match the seed rows (dispatcher lookup key)", () => {
    expect(bpmn1).toContain('id="open_network_define_link"');
    expect(bpmn2).toContain('id="open_network_request_change"');
  });
});
