/**
 * news rw-free — public news-aggregation catalog: source + article.
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 (3-axis OR-test).
 *
 * SPLIT (this app is (c) mixed — a news-media aggregation platform):
 *   PUBLIC (THIS PACKAGE) — RSS/news sources + ingested articles. Public
 *   news-media open-data (Google-News-style aggregation; external authority =
 *   the RSS publisher / source URL). No PII (public news), no settlement, no
 *   liability. → migrated to etzhayyim front (AT PDS records, replaces RW).
 *
 *   COMPUTE (STAYS etzhayyim, NOT in this package) — the wRPC reactive pipeline's
 *   quality-evaluation + translation (LLM) is compute; the resulting article
 *   records (with quality score + translation) are public catalog data,
 *   published ATPosts federate. Consumed via consent-capability.
 *
 * AT-Lexicon: no float. Quality score is an integer 0–100.
 *
 * Identity hierarchy:
 *   did:web:news.etzhayyim.com                          — controller
 *   did:web:news.etzhayyim.com:source:{sourceId}        — a news source
 *   did:web:news.etzhayyim.com:article:{articleId}      — an article
 */

export const NEWS_DID_PREFIX = "did:web:news.etzhayyim.com:" as const;

export const SOURCE_COLLECTION = "com.etzhayyim.apps.news.source";
export const ARTICLE_COLLECTION = "com.etzhayyim.apps.news.article";

// ─── Enums ──────────────────────────────────────────────────────────

export type SourceType = "rss" | "atom" | "api" | "at-feed" | "other";
export type SourceStatus = "active" | "paused" | "disabled";

export const SOURCE_TYPES: ReadonlySet<string> = new Set(["rss", "atom", "api", "at-feed", "other"]);
export const SOURCE_STATUSES: ReadonlySet<string> = new Set(["active", "paused", "disabled"]);

// ─── Source ─────────────────────────────────────────────────────────

export interface SourceRecord {
  did: string;
  sourceId: string;
  sourceName: string;
  sourceUrl: string;
  feedUrl?: string;
  /** ISO 639-1 source language. */
  lang: string;
  sourceType: SourceType;
  status: SourceStatus;
  createdAt: string;
}
export interface SourceView extends SourceRecord {
  sourceUri: string;
}
export interface RegisterSourceInput {
  sourceId: string;
  sourceName: string;
  sourceUrl: string;
  lang: string;
  sourceType: SourceType;
  feedUrl?: string;
  status?: SourceStatus;
}
export interface RegisterSourceOutput {
  status: "registered" | "alreadyExists" | "rejected";
  sourceUri?: string;
  did?: string;
  sourceId?: string;
  error?: string;
}
export interface SetSourceStatusInput {
  sourceId: string;
  status: SourceStatus;
}
export interface SetSourceStatusOutput {
  status: "updated" | "rejected" | "notFound";
  sourceId?: string;
  newStatus?: SourceStatus;
  error?: string;
}
export interface ListSourcesInput {
  status?: SourceStatus;
  lang?: string;
  sourceType?: SourceType;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListSourcesOutput {
  items: SourceView[];
  cursor?: string;
  total: number;
}

// ─── Article (FK→source) ────────────────────────────────────────────

export interface ArticleRecord {
  did: string;
  articleId: string;
  /** FK → source. */
  sourceId: string;
  title: string;
  summary?: string;
  /** ISO 639-1 original language. */
  lang: string;
  url: string;
  category?: string;
  tags?: string[];
  /** Pipeline quality score, integer 0–100. */
  qualityScore?: number;
  translatedTitle?: string;
  translatedLang?: string;
  publishedAt?: string;
  createdAt: string;
}
export interface ArticleView extends ArticleRecord {
  articleUri: string;
}
export interface IngestArticleInput {
  articleId: string;
  sourceId: string;
  title: string;
  lang: string;
  url: string;
  summary?: string;
  category?: string;
  tags?: string[];
  qualityScore?: number;
  translatedTitle?: string;
  translatedLang?: string;
  publishedAt?: string;
}
export interface IngestArticleOutput {
  status: "ingested" | "alreadyExists" | "rejected" | "sourceNotFound";
  articleUri?: string;
  did?: string;
  articleId?: string;
  error?: string;
}
export interface GetArticleInput {
  articleId: string;
}
export interface GetArticleOutput {
  article?: ArticleView;
  error?: string;
}
export interface ListArticlesInput {
  sourceId?: string;
  lang?: string;
  category?: string;
  tag?: string;
  /** App-layer substring search over title + summary. */
  q?: string;
  /** Minimum quality score. */
  minQuality?: number;
  limit?: number;
  cursor?: string;
}
export interface ListArticlesOutput {
  items: ArticleView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  sourceCount?: number;
  articleCount?: number;
  sourcesByStatus?: Record<string, number>;
  articlesByLang?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isLang(s: string): boolean {
  return /^[a-z]{2}$/.test(s);
}
export function isQualityScore(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 100;
}

export function sourceDidFor(id: string): string {
  return `${NEWS_DID_PREFIX}source:${id.toLowerCase()}`;
}
export function sourceRkey(id: string): string {
  return `source-${id.toLowerCase()}`;
}
export function articleDidFor(id: string): string {
  return `${NEWS_DID_PREFIX}article:${id.toLowerCase()}`;
}
export function articleRkey(id: string): string {
  return `article-${id.toLowerCase()}`;
}
