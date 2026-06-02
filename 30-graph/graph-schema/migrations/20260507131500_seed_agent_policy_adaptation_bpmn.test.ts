import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const migrationSource = readFileSync(
  resolve(__dirname, "20260507131500_seed_agent_policy_adaptation_bpmn.ts"),
  "utf-8",
);
const policyAdaptation = readFileSync(
  resolve(__dirname, "../../../00-contracts/bpmn/com/etzhayyim/agent/policyAdaptation.bpmn"),
  "utf-8",
);

describe("Seed agent policy adaptation BPMN migration", () => {
  it("seeds the policy adaptation process and binding", () => {
    expect(migrationSource).toContain("agent-policy-adaptation-v1");
    expect(migrationSource).toContain("'agent_policy_adaptation'");
    expect(migrationSource).toContain("'com.etzhayyim.apps.agent.adaptPolicy'");
    expect(migrationSource).toContain(
      "'vertex_agent_policy_adaptation_proposal,vertex_agent_prior_preference'",
    );
  });

  it("records proposals before activating accepted preferences", () => {
    expect(policyAdaptation).toContain('id="agent_policy_adaptation"');
    expect(policyAdaptation).toContain('type="agent.adaptPolicy"');
    expect(policyAdaptation).toContain("vertex_agent_policy_adaptation_proposal");
    expect(policyAdaptation).toContain("vertex_agent_prior_preference");
    expect(policyAdaptation).toContain("mokutekiGatePass");
    expect(policyAdaptation).toContain("tripleWitnessPass");
    expect(policyAdaptation).toContain("policyAccepted = true");
    expect(policyAdaptation).not.toContain("mailer.sendEmail");
    expect(policyAdaptation).not.toContain("robotics.command.dispatch");
  });
});
