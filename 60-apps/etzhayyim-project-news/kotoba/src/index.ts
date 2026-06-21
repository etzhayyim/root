/**
 * news kotoba — barrel.
 *
 * Per ADR-2606011400. Public news-aggregation catalog (source + article) on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   source  : registerSource / setSourceStatus (active/paused/disabled) / listSources (name search)
 *   article : ingestArticle (FK→source, lang + quality validated) / getArticle / listArticles (title+summary search, minQuality)
 *   coverage
 *
 * (c) MIXED SPLIT: the public news catalog (sources + articles, external
 * authority = RSS publisher / source URL) migrates. The wRPC pipeline's
 * quality-evaluation + translation (LLM) compute STAYS etzhayyim; published ATPosts
 * federate — NOT in this package.
 */

export * from "./types.js";
export {
  registerSource,
  setSourceStatus,
  listSources,
  ingestArticle,
  getArticle,
  listArticles,
  coverage,
} from "./registry.js";
