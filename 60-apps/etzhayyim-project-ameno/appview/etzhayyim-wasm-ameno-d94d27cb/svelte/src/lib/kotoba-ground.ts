/**
 * Re-export from @etzhayyim/ameno package.
 * @see 40-engine/llm/inference/ameno/src/kotoba-ground.ts
 *
 * kotoba-grounded conversation: grounds the browser gemma4-e4b chat on the
 * published gov-procedures kotoba records (/.well-known/gov-procedures.json).
 */
export {
  fetchGovProcedures,
  tokenize,
  retrieveProcedures,
  buildKotobaContext,
  groundedMessages,
  type KotobaProcedure,
  type RetrievedProcedure,
  type GroundChatMessage,
} from "@etzhayyim/ameno/kotoba-ground";
