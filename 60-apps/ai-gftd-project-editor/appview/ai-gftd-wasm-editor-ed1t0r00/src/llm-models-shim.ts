import { MURAKUMO_DEFAULT_MODEL, resolveModelId as resolveSharedModelId } from "@gftd/llm-models";

// Local shim for @gftd/llm-models until the package is published.
// Keep the same surface but delegate to the repo-wide model registry.
export function resolveModelId(modelHint?: string, useCase?: string): string {
  return resolveSharedModelId(modelHint, useCase) || MURAKUMO_DEFAULT_MODEL;
}
