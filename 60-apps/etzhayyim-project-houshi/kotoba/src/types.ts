/**
 * houshi kotoba — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). houshi = 方子 (spore dispersal,
 * dormancy) — the fungal sporulation system of the bonsai actor ecosystem.
 * Handles spore lifecycle: storage, custody chains, and germination.
 *
 * 3-stage flow (each stage = one lexicon = one PDS record):
 *   storeSpore  → SporeRecord     (artifact blob in custody chain)
 *   listSpores  → SporeQuery      (enumerate spores by custodian/origin)
 *   germinate   → GerminateRecord (revive dormant spore → kobo agent)
 *
 * Identity hierarchy:
 *   did:web:houshi.etzhayyim.com                       — controller
 *   did:web:houshi.etzhayyim.com:spore:{sporeId}       — SporeRecord
 *   did:web:houshi.etzhayyim.com:germinate:{sporeId}   — GerminateRecord
 */

export const HOUSHI_DID_PREFIX = "did:web:houshi.etzhayyim.com:" as const;

// ─── Spore storage tier ─────────────────────────────────────────────────

export interface SporeRecord {
  did: string;
  sporeVertexId: string;
  originAgentDid: string;
  quorumN: number;
  custodyChain: string[];
  blobCbor: string;
  revivalKeyHint: string;
  germinatedAt?: string;
  createdAt: string;
}

export interface SporeView extends SporeRecord {
  sporeUri: string;
}

export interface StoreSporeInput {
  sporeVertexId: string;
  custodianDid: string;
  originAgentDid: string;
  quorumN: number;
  blobCbor: string;
  revivalKeyHint: string;
}

export interface StoreSporeOutput {
  status: "registered" | "alreadyExists" | "rejected";
  sporeUri?: string;
  sporeVertexId?: string;
  did?: string;
  error?: string;
}

// ─── Spore listing tier ────────────────────────────────────────────────

export interface SporeListInput {
  custodianDid?: string;
  originAgentDid?: string;
  includeGerminated?: boolean;
  offset?: number;
  limit?: number;
}

export interface SporeListItem {
  vertexId: string;
  originAgentDid: string;
  quorumN: number;
  custodyCount: number;
  germinatedAt?: string;
  createdAt: string;
}

export interface SporeListOutput {
  spores: SporeListItem[];
  total: number;
  offset: number;
  limit: number;
}

// ─── Germination tier ──────────────────────────────────────────────────

export interface GerminateRecord {
  did: string;
  sporeVertexId: string;
  newAgentDid: string;
  prionsRestored: number;
  germinatedAt: string;
  createdAt: string;
}

export interface GerminateInput {
  sporeVertexId: string;
  revivalKey: string;
  newAgentDid: string;
}

export interface GerminateOutput {
  status: "germinated" | "alreadyGerminated" | "rejected" | "sporeNotFound" | "invalidRevivalKey";
  agentVertexId?: string;
  agentDid?: string;
  prionsRestored?: number;
  germinatedAt?: string;
  error?: string;
}

// ─── Slug helpers ──────────────────────────────────────────────────────

export function idSlug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function sporeDid(sporeVertexId: string): string {
  return `${HOUSHI_DID_PREFIX}spore:${idSlug(sporeVertexId)}`;
}

export function sporeRkey(sporeVertexId: string): string {
  return `spore-${idSlug(sporeVertexId)}`;
}

export function germinateDid(sporeVertexId: string): string {
  return `${HOUSHI_DID_PREFIX}germinate:${idSlug(sporeVertexId)}`;
}

export function germinateRkey(sporeVertexId: string): string {
  return `germinate-${idSlug(sporeVertexId)}`;
}
