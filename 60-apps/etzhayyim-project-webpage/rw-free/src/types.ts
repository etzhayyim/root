/**
 * webpage rw-free — web-page authoring & publishing document model (space → page).
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 (3-axis OR-test).
 *
 * AXIS NOTE: (a) content-editor product (the editor / pptx / xlsx document-tool
 * cluster). A page is the USER'S OWN authored content held in their OWN repo —
 * first-party content, so the AT PDS record IS the canonical store: no
 * third-party PII custody, no settlement, no fulfillment liability. Authoring
 * (create/update) and publishing (status flip + public directory) are
 * first-party CRUD; published pages form a public searchable directory.
 *
 * Contrast `webya` ((b)): that is a managed generation SaaS that HOSTS client
 * production sites at custom domains (Hyperdrive serving + domain provisioning =
 * fulfillment liability). webpage is self-serve content authoring — no hosting-
 * of-others, no custom domains, no settlement.
 *
 * AT-Lexicon: no float. View counts are integers.
 *
 * Identity hierarchy:
 *   did:web:webpage.etzhayyim.com                       — controller
 *   did:web:webpage.etzhayyim.com:space:{spaceId}       — a space (page group)
 *   did:web:webpage.etzhayyim.com:page:{pageId}         — a page
 */

export const WEBPAGE_DID_PREFIX = "did:web:webpage.etzhayyim.com:" as const;

export const SPACE_COLLECTION = "com.etzhayyim.apps.webpage.space";
export const PAGE_COLLECTION = "com.etzhayyim.apps.webpage.page";

// ─── Enums ──────────────────────────────────────────────────────────

export type PageStatus = "draft" | "published" | "archived";

export const PAGE_STATUSES: ReadonlySet<string> = new Set(["draft", "published", "archived"]);

// ─── Space (page group / site) ──────────────────────────────────────

export interface SpaceRecord {
  did: string;
  spaceId: string;
  name: string;
  description?: string;
  ownerDid?: string;
  createdAt: string;
}
export interface SpaceView extends SpaceRecord {
  spaceUri: string;
}
export interface RegisterSpaceInput {
  spaceId: string;
  name: string;
  description?: string;
  ownerDid?: string;
}
export interface RegisterSpaceOutput {
  status: "registered" | "alreadyExists" | "rejected";
  spaceUri?: string;
  did?: string;
  spaceId?: string;
  error?: string;
}
export interface ListSpacesInput {
  ownerDid?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListSpacesOutput {
  items: SpaceView[];
  cursor?: string;
  total: number;
}

// ─── Page ───────────────────────────────────────────────────────────

export interface PageRecord {
  did: string;
  pageId: string;
  /** FK → space. */
  spaceId: string;
  title: string;
  slug: string;
  body: string;
  status: PageStatus;
  tags?: string[];
  publishedAt?: string;
  createdAt: string;
  updatedAt: string;
}
export interface PageView extends PageRecord {
  pageUri: string;
}
export interface CreatePageInput {
  pageId: string;
  spaceId: string;
  title: string;
  slug: string;
  body: string;
  tags?: string[];
}
export interface CreatePageOutput {
  status: "created" | "alreadyExists" | "rejected" | "spaceNotFound";
  pageUri?: string;
  did?: string;
  pageId?: string;
  error?: string;
}
export interface UpdatePageInput {
  pageId: string;
  title?: string;
  body?: string;
  tags?: string[];
}
export interface UpdatePageOutput {
  status: "updated" | "rejected" | "notFound";
  pageId?: string;
  error?: string;
}
export interface SetPageStatusInput {
  pageId: string;
  status: PageStatus;
  publishedAt?: string;
}
export interface SetPageStatusOutput {
  status: "updated" | "rejected" | "notFound";
  pageId?: string;
  newStatus?: PageStatus;
  error?: string;
}
export interface GetPageInput {
  pageId: string;
}
export interface GetPageOutput {
  page?: PageView;
  error?: string;
}
export interface ListPagesInput {
  spaceId?: string;
  status?: PageStatus;
  tag?: string;
  /** App-layer substring search over title + body. */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPagesOutput {
  items: PageView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  spaceCount?: number;
  pageCount?: number;
  pagesByStatus?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isSlug(s: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(s);
}

export function spaceDidFor(id: string): string {
  return `${WEBPAGE_DID_PREFIX}space:${id.toLowerCase()}`;
}
export function spaceRkey(id: string): string {
  return `space-${id.toLowerCase()}`;
}
export function pageDidFor(id: string): string {
  return `${WEBPAGE_DID_PREFIX}page:${id.toLowerCase()}`;
}
export function pageRkey(id: string): string {
  return `page-${id.toLowerCase()}`;
}
