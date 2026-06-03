/**
 * media-gamers rw-free — barrel.
 *
 * Per ADR-2606011400. Public game catalog (publisher + developer + gameTitle +
 * chart entry) on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   publisher  : registerPublisher / listPublishers
 *   developer  : registerDeveloper / listDevelopers
 *   gameTitle  : registerGameTitle (FK→publisher + FK→developer) / getGameTitle / listGameTitles
 *   chartEntry : recordChartEntry (FK→gameTitle, uint rank) / listChartEntries (rank-ordered)
 *   coverage
 *
 * (c) MIXED SPLIT: the public game-catalog open-data migrates. `generateGuide` /
 * `autopilot` LLM guide-generation (LangGraph) compute STAYS etzhayyim; published
 * guides federate as first-party AT records — NOT in this package.
 */

export * from "./types.js";
export {
  registerPublisher,
  listPublishers,
  registerDeveloper,
  listDevelopers,
  registerGameTitle,
  getGameTitle,
  listGameTitles,
  recordChartEntry,
  listChartEntries,
  coverage,
} from "./registry.js";
