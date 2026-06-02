/**
 * news rw-free — source + article registries + coverage.
 * AT PDS records (no RW). Articles FK→source. Public news-aggregation open-data;
 * quality-eval + translation LLM compute stays gftd.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ARTICLE_COLLECTION,
  SOURCE_COLLECTION,
  SOURCE_STATUSES,
  SOURCE_TYPES,
  articleDidFor,
  articleRkey,
  isLang,
  isQualityScore,
  sourceDidFor,
  sourceRkey,
  type ArticleRecord,
  type ArticleView,
  type CoverageInput,
  type CoverageOutput,
  type GetArticleInput,
  type GetArticleOutput,
  type IngestArticleInput,
  type IngestArticleOutput,
  type ListArticlesInput,
  type ListArticlesOutput,
  type ListSourcesInput,
  type ListSourcesOutput,
  type RegisterSourceInput,
  type RegisterSourceOutput,
  type SetSourceStatusInput,
  type SetSourceStatusOutput,
  type SourceRecord,
  type SourceView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

// ─── Source ─────────────────────────────────────────────────────────

export async function registerSource(e: Etzhayyim, input: RegisterSourceInput): Promise<RegisterSourceOutput> {
  if (!input.sourceId || !input.sourceName || !input.sourceUrl) return { status: "rejected", error: "missingRequiredFields" };
  if (!isLang(input.lang)) return { status: "rejected", error: "invalidLang" };
  if (!SOURCE_TYPES.has(input.sourceType)) return { status: "rejected", error: "invalidSourceType" };
  if (input.status && !SOURCE_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  const rkey = sourceRkey(input.sourceId);
  const existing = await e.read<SourceRecord>({ collection: SOURCE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", sourceUri: existing.records[0].uri, did: existing.records[0].value.did, sourceId: input.sourceId };
  }
  const did = sourceDidFor(input.sourceId);
  const record: SourceRecord = {
    did,
    sourceId: input.sourceId,
    sourceName: input.sourceName,
    sourceUrl: input.sourceUrl,
    feedUrl: input.feedUrl,
    lang: input.lang,
    sourceType: input.sourceType,
    status: input.status ?? "active",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: SOURCE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", sourceUri: receipt.uri, did, sourceId: input.sourceId };
}

export async function setSourceStatus(e: Etzhayyim, input: SetSourceStatusInput): Promise<SetSourceStatusOutput> {
  if (!input.sourceId || !SOURCE_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  const rkey = sourceRkey(input.sourceId);
  const resp = await e.read<SourceRecord>({ collection: SOURCE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const source = resp.records[0]?.value;
  if (!source) return { status: "notFound", error: "sourceNotFound" };
  await e.write({ collection: SOURCE_COLLECTION, record: { ...source, status: input.status } as unknown as Record<string, unknown>, rkey });
  return { status: "updated", sourceId: input.sourceId, newStatus: input.status };
}

export async function listSources(e: Etzhayyim, input: ListSourcesInput = {}): Promise<ListSourcesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SourceRecord>({ collection: SOURCE_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: SourceView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.status && v.status !== input.status) return false;
      if (input.lang && v.lang !== input.lang) return false;
      if (input.sourceType && v.sourceType !== input.sourceType) return false;
      if (q && !v.sourceName.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, sourceUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Article ────────────────────────────────────────────────────────

export async function ingestArticle(e: Etzhayyim, input: IngestArticleInput): Promise<IngestArticleOutput> {
  if (!input.articleId || !input.sourceId || !input.title || !input.url) return { status: "rejected", error: "missingRequiredFields" };
  if (!isLang(input.lang)) return { status: "rejected", error: "invalidLang" };
  if (input.qualityScore != null && !isQualityScore(input.qualityScore)) return { status: "rejected", error: "qualityScoreMustBe0to100Int" };
  if (!(await exists(e, SOURCE_COLLECTION, sourceRkey(input.sourceId)))) {
    return { status: "sourceNotFound", error: `sourceNotFound:${input.sourceId}` };
  }
  const rkey = articleRkey(input.articleId);
  const existing = await e.read<ArticleRecord>({ collection: ARTICLE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", articleUri: existing.records[0].uri, did: existing.records[0].value.did, articleId: input.articleId };
  }
  const did = articleDidFor(input.articleId);
  const record: ArticleRecord = {
    did,
    articleId: input.articleId,
    sourceId: input.sourceId,
    title: input.title,
    summary: input.summary,
    lang: input.lang,
    url: input.url,
    category: input.category,
    tags: input.tags,
    qualityScore: input.qualityScore,
    translatedTitle: input.translatedTitle,
    translatedLang: input.translatedLang,
    publishedAt: input.publishedAt,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ARTICLE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "ingested", articleUri: receipt.uri, did, articleId: input.articleId };
}

export async function getArticle(e: Etzhayyim, input: GetArticleInput): Promise<GetArticleOutput> {
  if (!input.articleId) return { error: "invalidArticleId" };
  const resp = await e.read<ArticleRecord>({ collection: ARTICLE_COLLECTION, rkey: articleRkey(input.articleId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { article: { ...r.value, articleUri: r.uri } };
}

export async function listArticles(e: Etzhayyim, input: ListArticlesInput = {}): Promise<ListArticlesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ArticleRecord>({ collection: ARTICLE_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: ArticleView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.sourceId && v.sourceId !== input.sourceId) return false;
      if (input.lang && v.lang !== input.lang) return false;
      if (input.category && v.category !== input.category) return false;
      if (input.tag && !(v.tags ?? []).includes(input.tag)) return false;
      if (input.minQuality != null && (v.qualityScore ?? 0) < input.minQuality) return false;
      if (q) {
        const hay = [v.title, v.summary ?? ""].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .map((r) => ({ ...r.value, articleUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const sourcesByStatus: Record<string, number> = {};
  const articlesByLang: Record<string, number> = {};
  const sourceCount = await scanAll<SourceRecord>(e, SOURCE_COLLECTION, maxScan, (v) => {
    sourcesByStatus[v.status] = (sourcesByStatus[v.status] ?? 0) + 1;
  });
  const articleCount = await scanAll<ArticleRecord>(e, ARTICLE_COLLECTION, maxScan, (v) => {
    articlesByLang[v.lang] = (articlesByLang[v.lang] ?? 0) + 1;
  });
  return {
    sourceCount,
    articleCount,
    sourcesByStatus,
    articlesByLang,
    truncated: sourceCount >= maxScan || articleCount >= maxScan,
  };
}
