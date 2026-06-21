/**
 * public-kafun-bokumetsu kotoba — pollen-eradication research record types.
 *
 * Per ADR-2606011400. 花粉撲滅Fund is an autonomous agent that researches +
 * proposes + acts to eradicate hay fever (cedar/cypress pollen). This package
 * models its public knowledge layer:
 *   research → action (FK→research, maps to capabilities)
 *   capability
 * Registry on AT PDS records (replaces RW). ADR-2605172000 kotoba.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean — public environmental/public-health
 * research data (no personal PII — it concerns pollen, not people). "Fund" is a
 * project name; no actual money handling (no settlement). No fulfillment
 * liability (advisory research/proposals).
 *
 * Identity hierarchy:
 *   did:web:kafun-bokumetsu.etzhayyim.com                      — controller
 *   did:web:kafun-bokumetsu.etzhayyim.com:research:{researchId} — a research item
 *   did:web:kafun-bokumetsu.etzhayyim.com:action:{actionId}     — a proposed action
 *   did:web:kafun-bokumetsu.etzhayyim.com:cap:{capabilityId}    — a capability
 */

export const KAFUN_DID_PREFIX = "did:web:kafun-bokumetsu.etzhayyim.com:" as const;

export const RESEARCH_COLLECTION = "com.etzhayyim.apps.kafunBokumetsu.research";
export const ACTION_COLLECTION = "com.etzhayyim.apps.kafunBokumetsu.action";
export const CAPABILITY_COLLECTION = "com.etzhayyim.apps.kafunBokumetsu.capability";

// ─── Research ───────────────────────────────────────────────────────

export type ResearchCategory = "pollen-source" | "dispersal" | "medical" | "policy" | "technology" | "other";
export type ResearchStatus = "open" | "concluded";

export interface ResearchRecord {
  did: string;
  researchId: string;
  category: ResearchCategory;
  title: string;
  summary?: string;
  status: ResearchStatus;
  createdAt: string;
}
export interface ResearchView extends ResearchRecord {
  researchUri: string;
}
export interface RecordResearchInput {
  researchId: string;
  category: ResearchCategory;
  title: string;
  summary?: string;
}
export interface RecordResearchOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  researchUri?: string;
  did?: string;
  researchId?: string;
  error?: string;
}
export interface GetResearchInput {
  researchId: string;
}
export interface GetResearchOutput {
  research?: ResearchView;
  error?: string;
}
export interface ConcludeResearchInput {
  researchId: string;
}
export interface ConcludeResearchOutput {
  status: "concluded" | "notFound" | "rejected";
  researchId?: string;
  error?: string;
}
export interface ListResearchInput {
  category?: ResearchCategory;
  status?: ResearchStatus;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListResearchOutput {
  items: ResearchView[];
  cursor?: string;
  total: number;
}

// ─── Capability ─────────────────────────────────────────────────────

export interface CapabilityRecord {
  did: string;
  capabilityId: string;
  name: string;
  description?: string;
  createdAt: string;
}
export interface CapabilityView extends CapabilityRecord {
  capabilityUri: string;
}
export interface DefineCapabilityInput {
  capabilityId: string;
  name: string;
  description?: string;
}
export interface DefineCapabilityOutput {
  status: "defined" | "alreadyExists" | "rejected";
  capabilityUri?: string;
  did?: string;
  capabilityId?: string;
  error?: string;
}
export interface ListCapabilitiesInput {
  limit?: number;
  cursor?: string;
}
export interface ListCapabilitiesOutput {
  items: CapabilityView[];
  cursor?: string;
  total: number;
}

// ─── Action ─────────────────────────────────────────────────────────

export type ActionStatus = "proposed" | "inProgress" | "done" | "cancelled";

export interface ActionRecord {
  did: string;
  actionId: string;
  title: string;
  description?: string;
  /** FK → research researchId (the motivating research), optional. */
  researchId?: string;
  /** Mapped capability ids (cap.mapAction). */
  capabilityRefs: string[];
  status: ActionStatus;
  createdAt: string;
}
export interface ActionView extends ActionRecord {
  actionUri: string;
}
export interface ProposeActionInput {
  actionId: string;
  title: string;
  description?: string;
  researchId?: string;
  capabilityRefs?: string[];
}
export interface ProposeActionOutput {
  status: "proposed" | "alreadyExists" | "rejected" | "researchNotFound";
  actionUri?: string;
  did?: string;
  actionId?: string;
  error?: string;
}
export interface SetActionStatusInput {
  actionId: string;
  status: ActionStatus;
}
export interface SetActionStatusOutput {
  status: "updated" | "notFound" | "rejected";
  actionId?: string;
  newStatus?: ActionStatus;
  error?: string;
}
export interface ListActionsInput {
  researchId?: string;
  status?: ActionStatus;
  capabilityRef?: string;
  limit?: number;
  cursor?: string;
}
export interface ListActionsOutput {
  items: ActionView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  researchCount?: number;
  actionCount?: number;
  capabilityCount?: number;
  researchByCategory?: Record<string, number>;
  actionsByStatus?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const CATEGORIES: ReadonlySet<string> = new Set(["pollen-source", "dispersal", "medical", "policy", "technology", "other"]);
export const ACTION_STATUSES: ReadonlySet<string> = new Set(["proposed", "inProgress", "done", "cancelled"]);

export function researchDidFor(id: string): string {
  return `${KAFUN_DID_PREFIX}research:${id.toLowerCase()}`;
}
export function researchRkey(id: string): string {
  return `research-${id.toLowerCase()}`;
}
export function actionDidFor(id: string): string {
  return `${KAFUN_DID_PREFIX}action:${id.toLowerCase()}`;
}
export function actionRkey(id: string): string {
  return `action-${id.toLowerCase()}`;
}
export function capabilityDidFor(id: string): string {
  return `${KAFUN_DID_PREFIX}cap:${id.toLowerCase()}`;
}
export function capabilityRkey(id: string): string {
  return `cap-${id.toLowerCase()}`;
}
