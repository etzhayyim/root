import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260507130000_seed_agent_active_inference_bpmn.ts"),
  "utf-8",
);
const activeInferenceTick = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/agent/activeInferenceTick.bpmn"),
  "utf-8",
);
const homeostasisWatch = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/agent/homeostasisWatch.bpmn"),
  "utf-8",
);
const realWorldEffectDispatch = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/ai/gftd/agent/realWorldEffectDispatch.bpmn"),
  "utf-8",
);

describe("Seed agent active inference BPMN migration", () => {
  it("seeds the three agent process definitions", () => {
    expect(migrationSource).toContain("agent-active-inference-tick-v1");
    expect(migrationSource).toContain('bpmnProcessId: "agent_active_inference_tick"');
    expect(migrationSource).toContain(
      'sourcePath: "00-contracts/bpmn/ai/gftd/agent/activeInferenceTick.bpmn"',
    );

    expect(migrationSource).toContain("agent-homeostasis-watch-v1");
    expect(migrationSource).toContain('bpmnProcessId: "agent_homeostasis_watch"');
    expect(migrationSource).toContain(
      'sourcePath: "00-contracts/bpmn/ai/gftd/agent/homeostasisWatch.bpmn"',
    );

    expect(migrationSource).toContain("agent-realworld-effect-dispatch-v1");
    expect(migrationSource).toContain('bpmnProcessId: "agent_realworld_effect_dispatch"');
    expect(migrationSource).toContain(
      'sourcePath: "00-contracts/bpmn/ai/gftd/agent/realWorldEffectDispatch.bpmn"',
    );
  });

  it("binds the expected agent NSIDs and write allowlists", () => {
    expect(migrationSource).toContain('nsid: "ai.gftd.apps.agent.activeInferenceTick"');
    expect(migrationSource).toContain('writeTableAllowlist: "vertex_agent_active_inference_tick"');

    expect(migrationSource).toContain('nsid: "ai.gftd.apps.agent.recordHomeostasis"');
    expect(migrationSource).toContain('writeTableAllowlist: "vertex_agent_homeostasis_snapshot"');

    expect(migrationSource).toContain(
      'nsid: "ai.gftd.apps.agent.classifyRealWorldEffect"',
    );
    expect(migrationSource).toContain('writeTableAllowlist: "vertex_agent_realworld_effect"');
  });

  it("BPMNs use only proposal/gate task types for Phase 1", () => {
    expect(activeInferenceTick).toContain('id="agent_active_inference_tick"');
    expect(activeInferenceTick).toContain('type="agent.evaluateExpectedFreeEnergy"');
    expect(activeInferenceTick).toContain('type="generic.db.insert"');
    expect(activeInferenceTick).toContain('type="generic.audit.emit"');
    expect(activeInferenceTick).toContain("vertex_agent_active_inference_tick");

    expect(homeostasisWatch).toContain('id="agent_homeostasis_watch"');
    expect(homeostasisWatch).toContain('type="agent.evaluateViability"');
    expect(homeostasisWatch).toContain("vertex_agent_homeostasis_snapshot");

    expect(realWorldEffectDispatch).toContain('id="agent_realworld_effect_dispatch"');
    expect(realWorldEffectDispatch).toContain('type="agent.classifyRealWorldEffect"');
    expect(realWorldEffectDispatch).toContain("vertex_agent_realworld_effect");
  });

  it("real-world effect BPMN does not dispatch channel sends in Phase 1", () => {
    expect(realWorldEffectDispatch).not.toContain("mailer.sendEmail");
    expect(realWorldEffectDispatch).not.toContain("fax.send");
    expect(realWorldEffectDispatch).not.toContain("generic.pds.dispatch");
    expect(realWorldEffectDispatch).not.toContain("robotics.command.dispatch");
  });
});
