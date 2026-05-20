/**
 * otakiage rw-free — record types.
 *
 * Per ADR-2605081700 + ADR-2605203000 Option B (PDS XRPC).
 *
 * otakiage.etzhayyim.com = reuse + ritual platform. Single state machine
 * per item: reuse (local handover) → ritual (お焚き上げ ceremonial dispose).
 *
 * Item lifecycle (state machine):
 *
 *   submitted
 *     → reuse_open (TTL 30d, auto)
 *         ├→ handed_over (terminal, T1 social derive)
 *         └→ reuse_expired
 *               └→ ritual_pending (mode=reuse_then_ritual のみ)
 *                    └→ ritualized (terminal, certificate URI 発行)
 *
 * Identity hierarchy (per CLAUDE.md path-based DIDs):
 *   did:web:otakiage.etzhayyim.com                    — controller
 *   did:web:otakiage.etzhayyim.com:reuse              — handover broker
 *   did:web:otakiage.etzhayyim.com:ritual             — ceremony actor
 *   did:web:otakiage.etzhayyim.com:matsuri            — seasonal organizer
 *   did:web:otakiage.etzhayyim.com:item:{itemId-slug} — Item record
 *   did:web:otakiage.etzhayyim.com:certificate:{certId-slug} — Certificate
 *   did:web:otakiage.etzhayyim.com:matsuri:{matsuriId-slug}  — Matsuri event
 */

export const OTAKIAGE_DID_PREFIX = "did:web:otakiage.etzhayyim.com:" as const;

export type ItemMode = "reuse_only" | "ritual_only" | "reuse_then_ritual";

export type ItemStatus =
  | "submitted"
  | "reuse_open"
  | "handed_over"
  | "reuse_expired"
  | "ritual_pending"
  | "ritualized";

// ─── Item tier (slice 1) ────────────────────────────────────────────

export interface ItemRecord {
  did: string;
  itemId: string;
  ownerDid: string;
  title: string;
  description?: string;
  category?: string;
  mode: ItemMode;
  status: ItemStatus;
  submittedAt: string;
  /** When status transitioned to reuse_open (or null if mode=ritual_only). */
  reuseOpenAt?: string;
  reuseDeadlineAt?: string;
  handedOverAt?: string;
  handedOverToDid?: string;
  reuseExpiredAt?: string;
  ritualPendingAt?: string;
  ritualizedAt?: string;
  /** Issued upon ritualization (state=ritualized). */
  certificateUri?: string;
  locationHint?: string;
  imageCids?: string[];
  createdAt: string;
}

export interface ItemView extends ItemRecord {
  itemUri: string;
}

export interface SubmitItemInput {
  itemId: string;
  ownerDid: string;
  title: string;
  description?: string;
  category?: string;
  mode: ItemMode;
  locationHint?: string;
  imageCids?: string[];
  /** Override default 30-day reuse window. */
  reuseDeadlineAt?: string;
}

export interface SubmitItemOutput {
  status: "registered" | "alreadyExists" | "rejected";
  itemUri?: string;
  did?: string;
  itemId?: string;
  itemStatus?: ItemStatus;
  error?: string;
}

export interface GetItemInput {
  itemId?: string;
}

export interface GetItemOutput {
  item?: ItemView;
  error?: string;
}

export interface ListItemsInput {
  status?: ItemStatus;
  mode?: ItemMode;
  ownerDid?: string;
  category?: string;
  limit?: number;
  cursor?: string;
}

export interface ListItemsOutput {
  items: ItemView[];
  cursor?: string;
  total: number;
}

// ─── Slug helpers ───────────────────────────────────────────────────

export function idSlug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function itemDid(itemId: string): string {
  return `${OTAKIAGE_DID_PREFIX}item:${idSlug(itemId)}`;
}

export function itemRkey(itemId: string): string {
  return `item-${idSlug(itemId)}`;
}

/** Default 30-day reuse window from ADR-2605081700. */
export const REUSE_DEFAULT_TTL_MS = 30 * 24 * 3_600_000;
