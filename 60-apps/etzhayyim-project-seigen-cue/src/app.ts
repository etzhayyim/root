/**
 * seigen-did-actor design stub.
 *
 * Runtime entry is `scripts/seigen/seigen-did-actor.mjs` (CLI + MCP stdio).
 * This file documents a typed shape for future worker/component integration.
 */

export interface SeigenValidateRequest {
  configPath: string;
  locale?: "ja" | "en";
  enforceCue?: boolean;
}

export interface SeigenPolicyExportRequest {
  policyId?: string;
  version?: string;
  sourceDate?: string;
  actorDid?: string;
  locale?: "ja" | "en";
}

export interface SeigenActorDesign {
  id: "seigen-did-actor";
  tools: ["seigen.validate", "seigen.policy.exportSql"];
  storage: {
    model: "sql";
    label: "SeigenPolicy";
  };
  policyLanguage: "cue";
}

export const SEIGEN_ACTOR_DESIGN: SeigenActorDesign = {
  id: "seigen-did-actor",
  tools: ["seigen.validate", "seigen.policy.exportSql"],
  storage: {
    model: "sql",
    label: "SeigenPolicy",
  },
  policyLanguage: "cue",
};
