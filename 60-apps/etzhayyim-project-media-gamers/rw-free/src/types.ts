/**
 * media-gamers rw-free — public game catalog: publisher + developer + gameTitle
 * + chart entry.
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 (3-axis OR-test).
 *
 * SPLIT (this app is (c) mixed — a game-information intelligence media):
 *   PUBLIC (THIS PACKAGE) — game titles + publishers + developers + sales/
 *   popularity charts. Public game-database open-data (IGDB / MobyGames style,
 *   external authority = public game DBs + charts). No PII (games/publishers/
 *   developers are public entities), no settlement, no liability.
 *     → migrated to etzhayyim front (AT PDS records, replaces RW).
 *
 *   COMPUTE (STAYS etzhayyim, NOT in this package) — `generateGuide` / `autopilot`
 *   LLM guide generation (LangGraph) is compute; published guides federate as
 *   first-party AT records via the feed. Consumed via consent-capability.
 *
 * AT-Lexicon: no float. Chart ranks are integers.
 *
 * Identity hierarchy:
 *   did:web:media-gamers.etzhayyim.com                       — controller
 *   did:web:media-gamers.etzhayyim.com:pub:{publisherId}     — a publisher
 *   did:web:media-gamers.etzhayyim.com:dev:{developerId}     — a developer
 *   did:web:media-gamers.etzhayyim.com:title:{titleId}       — a game title
 *   did:web:media-gamers.etzhayyim.com:chart:{entryId}       — a chart entry
 */

export const MG_DID_PREFIX = "did:web:media-gamers.etzhayyim.com:" as const;

export const PUBLISHER_COLLECTION = "com.etzhayyim.apps.mediaGamers.publisher";
export const DEVELOPER_COLLECTION = "com.etzhayyim.apps.mediaGamers.developer";
export const GAME_TITLE_COLLECTION = "com.etzhayyim.apps.mediaGamers.gameTitle";
export const CHART_ENTRY_COLLECTION = "com.etzhayyim.apps.mediaGamers.chartEntry";

// ─── Publisher ──────────────────────────────────────────────────────

export interface PublisherRecord {
  did: string;
  publisherId: string;
  name: string;
  country?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface PublisherView extends PublisherRecord {
  publisherUri: string;
}
export interface RegisterPublisherInput {
  publisherId: string;
  name: string;
  country?: string;
  sourceUrl?: string;
}
export interface RegisterPublisherOutput {
  status: "registered" | "alreadyExists" | "rejected";
  publisherUri?: string;
  did?: string;
  publisherId?: string;
  error?: string;
}
export interface ListPublishersInput {
  country?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPublishersOutput {
  items: PublisherView[];
  cursor?: string;
  total: number;
}

// ─── Developer ──────────────────────────────────────────────────────

export interface DeveloperRecord {
  did: string;
  developerId: string;
  name: string;
  country?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface DeveloperView extends DeveloperRecord {
  developerUri: string;
}
export interface RegisterDeveloperInput {
  developerId: string;
  name: string;
  country?: string;
  sourceUrl?: string;
}
export interface RegisterDeveloperOutput {
  status: "registered" | "alreadyExists" | "rejected";
  developerUri?: string;
  did?: string;
  developerId?: string;
  error?: string;
}
export interface ListDevelopersInput {
  country?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListDevelopersOutput {
  items: DeveloperView[];
  cursor?: string;
  total: number;
}

// ─── Game title ─────────────────────────────────────────────────────

export interface GameTitleRecord {
  did: string;
  titleId: string;
  name: string;
  slug: string;
  /** FK → publisher (optional). */
  publisherId?: string;
  /** FK → developer (optional). */
  developerId?: string;
  platforms?: string[];
  genre?: string;
  releaseDate?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface GameTitleView extends GameTitleRecord {
  titleUri: string;
}
export interface RegisterGameTitleInput {
  titleId: string;
  name: string;
  slug: string;
  publisherId?: string;
  developerId?: string;
  platforms?: string[];
  genre?: string;
  releaseDate?: string;
  sourceUrl?: string;
}
export interface RegisterGameTitleOutput {
  status: "registered" | "alreadyExists" | "rejected" | "publisherNotFound" | "developerNotFound";
  titleUri?: string;
  did?: string;
  titleId?: string;
  error?: string;
}
export interface GetGameTitleInput {
  titleId: string;
}
export interface GetGameTitleOutput {
  title?: GameTitleView;
  error?: string;
}
export interface ListGameTitlesInput {
  publisherId?: string;
  developerId?: string;
  genre?: string;
  platform?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListGameTitlesOutput {
  items: GameTitleView[];
  cursor?: string;
  total: number;
}

// ─── Chart entry (FK→gameTitle) ─────────────────────────────────────

export interface ChartEntryRecord {
  did: string;
  entryId: string;
  chartName: string;
  /** FK → gameTitle. */
  titleId: string;
  rank: number;
  region?: string;
  period?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface ChartEntryView extends ChartEntryRecord {
  entryUri: string;
}
export interface RecordChartEntryInput {
  entryId: string;
  chartName: string;
  titleId: string;
  rank: number;
  region?: string;
  period?: string;
  sourceUrl?: string;
}
export interface RecordChartEntryOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "titleNotFound";
  entryUri?: string;
  did?: string;
  entryId?: string;
  error?: string;
}
export interface ListChartEntriesInput {
  chartName?: string;
  titleId?: string;
  region?: string;
  period?: string;
  limit?: number;
  cursor?: string;
}
export interface ListChartEntriesOutput {
  items: ChartEntryView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  publisherCount?: number;
  developerCount?: number;
  gameTitleCount?: number;
  chartEntryCount?: number;
  titlesByGenre?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}

export function publisherDidFor(id: string): string {
  return `${MG_DID_PREFIX}pub:${id.toLowerCase()}`;
}
export function publisherRkey(id: string): string {
  return `pub-${id.toLowerCase()}`;
}
export function developerDidFor(id: string): string {
  return `${MG_DID_PREFIX}dev:${id.toLowerCase()}`;
}
export function developerRkey(id: string): string {
  return `dev-${id.toLowerCase()}`;
}
export function titleDidFor(id: string): string {
  return `${MG_DID_PREFIX}title:${id.toLowerCase()}`;
}
export function titleRkey(id: string): string {
  return `title-${id.toLowerCase()}`;
}
export function entryDidFor(id: string): string {
  return `${MG_DID_PREFIX}chart:${id.toLowerCase()}`;
}
export function entryRkey(id: string): string {
  return `chart-${id.toLowerCase()}`;
}
