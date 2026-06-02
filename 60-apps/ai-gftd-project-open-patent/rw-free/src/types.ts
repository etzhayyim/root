/**
 * open-patent rw-free — patent open-data + open IP-generation record types.
 *
 * Per ADR-2606011400. open-patent ingests PUBLIC patent data (from
 * patent.etzhayyim.com + jurisdiction actors) and generates OPEN IP (invention
 * seeds + novelty reports, published as open prior-art). This package models:
 *   patent → citation (FK→patent)
 *   inventionSeed → noveltyReport (FK→inventionSeed)
 * Registry on AT PDS records (replaces vertex_open_patent_*). ADR-2605172000
 * RW-free.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean public/open data — published patents +
 * citation graph (public open-data) + open-generated invention seeds / novelty
 * reports (published openly, not confidential proprietary filings). No personal
 * PII (inventors are public on patents), no settlement, no fulfillment liability.
 *
 * AT-Lexicon: no float. Novelty score is per-mille (0..1000).
 *
 * Identity hierarchy:
 *   did:web:open-patent.etzhayyim.com                       — controller
 *   did:web:open-patent.etzhayyim.com:patent:{patentId}     — a patent
 *   did:web:open-patent.etzhayyim.com:cite:{citationId}     — a citation
 *   did:web:open-patent.etzhayyim.com:seed:{seedId}         — an invention seed
 *   did:web:open-patent.etzhayyim.com:novelty:{reportId}    — a novelty report
 */

export const OP_DID_PREFIX = "did:web:open-patent.etzhayyim.com:" as const;

export const PATENT_COLLECTION = "com.etzhayyim.apps.openPatent.patent";
export const CITATION_COLLECTION = "com.etzhayyim.apps.openPatent.citation";
export const SEED_COLLECTION = "com.etzhayyim.apps.openPatent.inventionSeed";
export const NOVELTY_COLLECTION = "com.etzhayyim.apps.openPatent.noveltyReport";

// ─── Patent ─────────────────────────────────────────────────────────

export type PatentStatus = "published" | "granted" | "expired";

export interface PatentRecord {
  did: string;
  patentId: string;
  /** Publication number, e.g. "US10123456B2". */
  publicationNumber: string;
  title: string;
  /** ISO 3166-1 alpha-2 jurisdiction / patent office. */
  jurisdiction: string;
  kindCode?: string;
  filedDate?: string;
  grantedDate?: string;
  status: PatentStatus;
  sourceUrl: string;
  createdAt: string;
}
export interface PatentView extends PatentRecord {
  patentUri: string;
}
export interface IngestPatentInput {
  patentId: string;
  publicationNumber: string;
  title: string;
  jurisdiction: string;
  status: PatentStatus;
  sourceUrl: string;
  kindCode?: string;
  filedDate?: string;
  grantedDate?: string;
}
export interface IngestPatentOutput {
  status: "ingested" | "alreadyExists" | "rejected";
  patentUri?: string;
  did?: string;
  patentId?: string;
  error?: string;
}
export interface GetPatentInput {
  patentId: string;
}
export interface GetPatentOutput {
  patent?: PatentView;
  error?: string;
}
export interface ListPatentsInput {
  jurisdiction?: string;
  status?: PatentStatus;
  /** App-layer substring match over title (AT PDS has no text search). */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPatentsOutput {
  items: PatentView[];
  cursor?: string;
  total: number;
}

// ─── Citation ───────────────────────────────────────────────────────

export type CitationType = "applicant" | "examiner" | "other";

export interface CitationRecord {
  did: string;
  citationId: string;
  /** FK → patent patentId (the citing patent). */
  citingPatentId: string;
  /** Cited publication number (may be an external reference). */
  citedRef: string;
  citationType: CitationType;
  createdAt: string;
}
export interface CitationView extends CitationRecord {
  citationUri: string;
}
export interface AddCitationInput {
  citationId: string;
  citingPatentId: string;
  citedRef: string;
  citationType: CitationType;
}
export interface AddCitationOutput {
  status: "added" | "alreadyExists" | "rejected" | "patentNotFound";
  citationUri?: string;
  did?: string;
  citationId?: string;
  error?: string;
}
export interface ListCitationsInput {
  citingPatentId?: string;
  citedRef?: string;
  citationType?: CitationType;
  limit?: number;
  cursor?: string;
}
export interface ListCitationsOutput {
  items: CitationView[];
  cursor?: string;
  total: number;
}

// ─── Invention seed (open-generated IP) ─────────────────────────────

export type SeedStatus = "draft" | "published";

export interface SeedRecord {
  did: string;
  seedId: string;
  title: string;
  description: string;
  /** Publication numbers / patentIds this seed builds on. */
  basisRefs: string[];
  status: SeedStatus;
  createdAt: string;
}
export interface SeedView extends SeedRecord {
  seedUri: string;
}
export interface SynthesizeSeedInput {
  seedId: string;
  title: string;
  description: string;
  basisRefs?: string[];
}
export interface SynthesizeSeedOutput {
  status: "synthesized" | "alreadyExists" | "rejected";
  seedUri?: string;
  did?: string;
  seedId?: string;
  error?: string;
}
export interface PublishSeedInput {
  seedId: string;
}
export interface PublishSeedOutput {
  status: "published" | "notFound" | "rejected";
  seedId?: string;
  newStatus?: SeedStatus;
  error?: string;
}
export interface ListSeedsInput {
  status?: SeedStatus;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListSeedsOutput {
  items: SeedView[];
  cursor?: string;
  total: number;
}

// ─── Novelty report ─────────────────────────────────────────────────

export interface NoveltyRecord {
  did: string;
  reportId: string;
  /** FK → inventionSeed seedId. */
  seedId: string;
  /** Novelty score, per-mille (0..1000). */
  noveltyPermille: number;
  priorArtRefs: string[];
  summary?: string;
  createdAt: string;
}
export interface NoveltyView extends NoveltyRecord {
  reportUri: string;
}
export interface AddNoveltyReportInput {
  reportId: string;
  seedId: string;
  noveltyPermille: number;
  priorArtRefs?: string[];
  summary?: string;
}
export interface AddNoveltyReportOutput {
  status: "added" | "alreadyExists" | "rejected" | "seedNotFound";
  reportUri?: string;
  did?: string;
  reportId?: string;
  error?: string;
}
export interface ListNoveltyReportsInput {
  seedId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListNoveltyReportsOutput {
  items: NoveltyView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  patentCount?: number;
  citationCount?: number;
  seedCount?: number;
  noveltyCount?: number;
  patentsByJurisdiction?: Record<string, number>;
  seedsByStatus?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const PATENT_STATUSES: ReadonlySet<string> = new Set(["published", "granted", "expired"]);
export const CITATION_TYPES: ReadonlySet<string> = new Set(["applicant", "examiner", "other"]);

export function isJurisdiction(s: string): boolean {
  return /^[A-Z]{2}$/.test(s);
}
export function isPermille(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 1000;
}

export function patentDidFor(id: string): string {
  return `${OP_DID_PREFIX}patent:${id.toLowerCase()}`;
}
export function patentRkey(id: string): string {
  return `patent-${id.toLowerCase()}`;
}
export function citationDidFor(id: string): string {
  return `${OP_DID_PREFIX}cite:${id.toLowerCase()}`;
}
export function citationRkey(id: string): string {
  return `cite-${id.toLowerCase()}`;
}
export function seedDidFor(id: string): string {
  return `${OP_DID_PREFIX}seed:${id.toLowerCase()}`;
}
export function seedRkey(id: string): string {
  return `seed-${id.toLowerCase()}`;
}
export function noveltyDidFor(id: string): string {
  return `${OP_DID_PREFIX}novelty:${id.toLowerCase()}`;
}
export function noveltyRkey(id: string): string {
  return `novelty-${id.toLowerCase()}`;
}
