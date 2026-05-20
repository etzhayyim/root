/**
 * kiyo rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). kiyo = 紀要 = research archive.
 * Per ADR-2604300000 kiyo: paper_id = `kiyo:{YYYY}:{TID}`.
 *
 * Identity hierarchy (per kiyo CLAUDE.md):
 *   did:web:kiyo.etzhayyim.com                            — controller
 *   did:web:kiyo.etzhayyim.com:paper:{paperId-slug}       — Paper
 *   did:web:kiyo.etzhayyim.com:review:{paperId}-{seq}     — Review
 *   did:web:kiyo.etzhayyim.com:endorsement:{paperId}-{endorser-slug}
 *   did:web:kiyo.etzhayyim.com:citation:{src}-{dst}       — Citation edge
 *
 * Paper PDFs/contents are content-addressed on IPFS (`ipfs.etzhayyim.com`);
 * the Paper record stores the CIDv1 only — Phase 3 mst-projector adds
 * IPFS pin index for availability tracking.
 */

export const KIYO_DID_PREFIX = "did:web:kiyo.etzhayyim.com:" as const;

export type PaperStatus =
  | "submitted"
  | "under-review"
  | "accepted"
  | "withdrawn"
  | "rejected"
  | "published";

// ─── Paper tier (slice 1) ───────────────────────────────────────────

export interface PaperRecord {
  did: string;
  /** `kiyo:{YYYY}:{TID}` natural identifier (e.g. kiyo:2026:lzxy1a). */
  paperId: string;
  title: string;
  titleLocal?: string;
  authorDids: string[];
  abstract?: string;
  abstractLocal?: string;
  language?: string;
  ipfsCid?: string;
  status: PaperStatus;
  submittedAt: string;
  publishedAt?: string;
  withdrawnAt?: string;
  withdrawalReason?: string;
  /** Previous revision paperId (chain). */
  prevRevisionPaperId?: string;
  tags?: string[];
  field?: string;
  doi?: string;
  createdAt: string;
}

export interface PaperView extends PaperRecord {
  paperUri: string;
}

export interface SubmitPaperInput {
  paperId: string;
  title: string;
  titleLocal?: string;
  authorDids: string[];
  abstract?: string;
  abstractLocal?: string;
  language?: string;
  ipfsCid?: string;
  tags?: string[];
  field?: string;
  doi?: string;
}

export interface SubmitPaperOutput {
  status: "registered" | "alreadyExists" | "rejected";
  paperUri?: string;
  did?: string;
  paperId?: string;
  error?: string;
}

export interface GetPaperInput {
  paperId?: string;
}

export interface GetPaperOutput {
  paper?: PaperView;
  error?: string;
}

export interface ListPapersInput {
  status?: PaperStatus;
  field?: string;
  language?: string;
  limit?: number;
  cursor?: string;
}

export interface ListPapersOutput {
  items: PaperView[];
  cursor?: string;
  total: number;
}

export interface ListByAuthorInput {
  authorDid: string;
  status?: PaperStatus;
  limit?: number;
  cursor?: string;
}

export type ListByAuthorOutput = ListPapersOutput;

export interface WithdrawPaperInput {
  paperId: string;
  reason: string;
}

export interface WithdrawPaperOutput {
  status: "withdrawn" | "rejected";
  paperUri?: string;
  paperId?: string;
  error?: string;
}

export interface SubmitRevisionInput {
  newPaperId: string;
  prevPaperId: string;
  title: string;
  titleLocal?: string;
  authorDids: string[];
  abstract?: string;
  abstractLocal?: string;
  language?: string;
  ipfsCid?: string;
  tags?: string[];
  field?: string;
  doi?: string;
}

export interface SubmitRevisionOutput {
  status: "registered" | "alreadyExists" | "rejected" | "prevNotFound";
  newPaperUri?: string;
  newPaperId?: string;
  prevPaperId?: string;
  error?: string;
}

// ─── Slug helpers ───────────────────────────────────────────────────

export function paperSlug(paperId: string): string {
  return paperId.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function paperDid(paperId: string): string {
  return `${KIYO_DID_PREFIX}paper:${paperSlug(paperId)}`;
}

export function paperRkey(paperId: string): string {
  return `paper-${paperSlug(paperId)}`;
}
