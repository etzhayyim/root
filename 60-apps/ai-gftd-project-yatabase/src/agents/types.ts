// agents/types.ts — yatabase BaaS AI-actor team common shape (Project Actor Composition).
//
// Roster (path-based DIDs under did:web:yatabase.gftd.ai):
//   chikada (dev)    → did:web:yatabase.gftd.ai:actor:chikada
//   tanaka  (qa)     → did:web:yatabase.gftd.ai:actor:tanaka
//   nishino (sales)  → did:web:yatabase.gftd.ai:actor:nishino
//   sakamoto (cs)    → did:web:yatabase.gftd.ai:actor:sakamoto
//
// Each agent is a stateless run() function that:
//   1. reads bounded recent state (audit log / billing event / outbox) via Hyperdrive
//   2. decides 0-N actions based on its role
//   3. writes side-effects (outbox row, audit row, agent_run row)
//   4. returns a structured AgentRunReport
//
// Trigger paths:
//   POST /_agents/{name}/run   — admin-keyed manual fire
//   CF Cron (planned)         — hourly tick for all 4

export type AgentName = "chikada" | "tanaka" | "nishino" | "sakamoto";
export type AgentRole = "dev" | "qa" | "sales" | "cs";

export interface AgentDef {
  name: AgentName;
  role: AgentRole;
  did: string;
  displayName: string;
  description: string;
  run: (env: AgentEnv, input?: AgentInput) => Promise<AgentRunReport>;
}

export interface AgentEnv {
  HYPERDRIVE?: unknown;
  YATA_VERSION?: string;
  RESEND_API_KEY?: string;
  EMAIL_FROM?: string;
  YATA_AGENT_ADMIN_KEY?: string;
}

export interface AgentInput {
  reason?: string;
  dryRun?: boolean;
  maxActions?: number;
}

export interface AgentAction {
  kind: string;
  target?: string;
  summary: string;
  outboxId?: string;
  ticketId?: string;
}

export interface AgentRunReport {
  ok: boolean;
  agent: AgentName;
  role: AgentRole;
  did: string;
  runId: string;
  startedAt: string;
  durationMs: number;
  actionsCount: number;
  actions: AgentAction[];
  notes?: string;
  error?: string;
  dryRun?: boolean;
}

export const ADMIN_ORG_DID = "did:web:yatabase.gftd.ai";
