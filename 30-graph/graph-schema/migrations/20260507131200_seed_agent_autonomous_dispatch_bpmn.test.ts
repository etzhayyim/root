import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260507131200_seed_agent_autonomous_dispatch_bpmn.ts"),
  "utf-8",
);
const autonomousDispatch = readFileSync(
  resolve(
    __dirname,
    "../../../00-contracts/bpmn/ai/gftd/agent/realWorldAutonomousDispatch.bpmn",
  ),
  "utf-8",
);

describe("Seed agent autonomous dispatch BPMN migration", () => {
  it("seeds the autonomous real-world dispatch process", () => {
    expect(migrationSource).toContain("agent-realworld-autonomous-dispatch-v1");
    expect(migrationSource).toContain(
      'bpmnProcessId: "agent_realworld_autonomous_dispatch"',
    );
    expect(migrationSource).toContain(
      'nsid: "ai.gftd.apps.agent.planRealWorldDispatch"',
    );
    expect(migrationSource).toContain(
      'sourcePath: "00-contracts/bpmn/ai/gftd/agent/realWorldAutonomousDispatch.bpmn"',
    );
    expect(migrationSource).toContain(
      '"vertex_agent_realworld_effect,vertex_agent_observation,vertex_agent_dispatch_ledger"',
    );
  });

  it("dispatches only through supported autonomous email path in this phase", () => {
    expect(autonomousDispatch).toContain('id="agent_realworld_autonomous_dispatch"');
    expect(autonomousDispatch).toContain('type="agent.classifyRealWorldEffect"');
    expect(autonomousDispatch).toContain('type="agent.planRealWorldDispatch"');
    expect(autonomousDispatch).toContain('type="agent.buildDispatchReceiptObservation"');
    expect(autonomousDispatch).toContain('type="agent.recordDispatchReceipt"');
    expect(autonomousDispatch).toContain('type="mailer.sendEmail"');
    expect(autonomousDispatch).toContain("vertex_agent_observation");
    expect(autonomousDispatch).toContain("vertex_agent_dispatch_ledger");
    expect(autonomousDispatch).toContain("dispatchLedgerInserted = 1");
    expect(autonomousDispatch).toContain("effectReceiptUpdated");
    expect(autonomousDispatch).toContain("autonomousAuthorityRef");
    expect(autonomousDispatch).toContain("policyRef");
    expect(autonomousDispatch).toContain("payloadHash");
    expect(autonomousDispatch).not.toContain('type="fax.send"');
    expect(autonomousDispatch).not.toContain(
      'type="insatsu.printMailJob.createPrintMailJob"',
    );
    expect(autonomousDispatch).not.toContain("robotics.command.dispatch");
  });
});
