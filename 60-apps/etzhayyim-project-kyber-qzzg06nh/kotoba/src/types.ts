/**
 * kyber-qzzg06nh kotoba — knowledge-graph record types.
 *
 * Per ADR-2606011400 + ADR-0025 (Kyber APQC/BPMN Projector). kyber-qzzg06nh is a
 * process/governance knowledge-graph actor: entities + events (FK→entity) +
 * reports (optional FK→entity). Registry on AT PDS records (replaces RW).
 * ADR-2605172000 kotoba.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean — AT records are public by design; no
 * PII custody (generic name/kind/category/status), no settlement, no liability.
 * PII MUST NOT be written to these public records.
 *
 * Identity hierarchy:
 *   did:web:kyber-qzzg06nh.etzhayyim.com                     — controller
 *   did:web:kyber-qzzg06nh.etzhayyim.com:entity:{entityId}   — a graph entity
 *   did:web:kyber-qzzg06nh.etzhayyim.com:event:{eventId}     — an event
 *   did:web:kyber-qzzg06nh.etzhayyim.com:report:{reportId}   — a report
 */

export const KYBER_DID_PREFIX = "did:web:kyber-qzzg06nh.etzhayyim.com:" as const;

export const ENTITY_COLLECTION = "com.etzhayyim.apps.kyber_qzzg06nh.kyber_qzzg06nh_entity";
export const EVENT_COLLECTION = "com.etzhayyim.apps.kyber_qzzg06nh.kyber_qzzg06nh_event";
export const REPORT_COLLECTION = "com.etzhayyim.apps.kyber_qzzg06nh.kyber_qzzg06nh_report";

// ─── Entity ─────────────────────────────────────────────────────────

export type EntityStatus = "active" | "archived";

export interface EntityRecord {
  did: string;
  entityId: string;
  name: string;
  kind: string;
  category?: string;
  status: EntityStatus;
  createdAt: string;
}
export interface EntityView extends EntityRecord {
  entityUri: string;
}
export interface DefineEntityInput {
  entityId: string;
  name: string;
  kind: string;
  category?: string;
}
export interface DefineEntityOutput {
  status: "defined" | "alreadyExists" | "rejected";
  entityUri?: string;
  did?: string;
  entityId?: string;
  error?: string;
}
export interface GetEntityInput {
  entityId: string;
}
export interface GetEntityOutput {
  entity?: EntityView;
  error?: string;
}
export interface ListEntitiesInput {
  kind?: string;
  category?: string;
  status?: EntityStatus;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListEntitiesOutput {
  items: EntityView[];
  cursor?: string;
  total: number;
}
export interface ArchiveEntityInput {
  entityId: string;
}
export interface ArchiveEntityOutput {
  status: "archived" | "notFound" | "rejected";
  entityId?: string;
  error?: string;
}

// ─── Event ──────────────────────────────────────────────────────────

export interface EventRecord {
  did: string;
  eventId: string;
  entityId: string;
  eventType: string;
  occurredAt: string;
  summary?: string;
  createdAt: string;
}
export interface EventView extends EventRecord {
  eventUri: string;
}
export interface RecordEventInput {
  eventId: string;
  entityId: string;
  eventType: string;
  occurredAt: string;
  summary?: string;
}
export interface RecordEventOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "entityNotFound";
  eventUri?: string;
  did?: string;
  eventId?: string;
  error?: string;
}
export interface ListEventsInput {
  entityId?: string;
  eventType?: string;
  since?: string;
  limit?: number;
  cursor?: string;
}
export interface ListEventsOutput {
  items: EventView[];
  cursor?: string;
  total: number;
}

// ─── Report ─────────────────────────────────────────────────────────

export type ReportStatus = "draft" | "published";

export interface ReportRecord {
  did: string;
  reportId: string;
  entityId?: string;
  reportType: string;
  title: string;
  summary?: string;
  status: ReportStatus;
  createdAt: string;
}
export interface ReportView extends ReportRecord {
  reportUri: string;
}
export interface SubmitReportInput {
  reportId: string;
  reportType: string;
  title: string;
  entityId?: string;
  summary?: string;
}
export interface SubmitReportOutput {
  status: "submitted" | "alreadyExists" | "rejected" | "entityNotFound";
  reportUri?: string;
  did?: string;
  reportId?: string;
  error?: string;
}
export interface PublishReportInput {
  reportId: string;
}
export interface PublishReportOutput {
  status: "published" | "notFound" | "rejected";
  reportId?: string;
  newStatus?: ReportStatus;
  error?: string;
}
export interface ListReportsInput {
  entityId?: string;
  reportType?: string;
  status?: ReportStatus;
  limit?: number;
  cursor?: string;
}
export interface ListReportsOutput {
  items: ReportView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  entityCount?: number;
  eventCount?: number;
  reportCount?: number;
  entitiesByKind?: Record<string, number>;
  reportsByStatus?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Helpers ────────────────────────────────────────────────────────

export function entityDidFor(id: string): string {
  return `${KYBER_DID_PREFIX}entity:${id.toLowerCase()}`;
}
export function entityRkey(id: string): string {
  return `entity-${id.toLowerCase()}`;
}
export function eventDidFor(id: string): string {
  return `${KYBER_DID_PREFIX}event:${id.toLowerCase()}`;
}
export function eventRkey(id: string): string {
  return `event-${id.toLowerCase()}`;
}
export function reportDidFor(id: string): string {
  return `${KYBER_DID_PREFIX}report:${id.toLowerCase()}`;
}
export function reportRkey(id: string): string {
  return `report-${id.toLowerCase()}`;
}
