import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-0056 — yabai batch-3 BPMN pivots (coverage expansion).
 *
 * Seeds 3 BPMN process definitions + 3 NSID bindings so the
 * bpmn-dispatcher F5 watcher ships them to Zeebe and the per-actor
 * XRPC endpoints (`POST dispatcher.etzhayyim.com:8080/xrpc/ai.gftd.apps.yabai.*`)
 * go live within ~30 s of apply.
 *
 * 3 pivots driven by `70-tools/scripts/yabai/expand-coverage.mjs`:
 *
 *   crtshFuzzySearch      crt.sh CT log fuzzy search → sibling infra discovery
 *   reverseIpLookup       SecurityTrails-style reverse IP co-tenancy pivot
 *   enrichLegalEntity     GLEIF LEI lookup → vertex_legal_entity + ownership
 *
 * Pairs with `50-infra/cloudflare/workers/atproto/src/routing-table.ts`
 * NSID_EXACT_MATCH_TABLE entries added in d09a6faee6f — without this
 * migration those entries route to BPMN_URL but the dispatcher 404s.
 *
 * resultTimeoutMs values come from each file's <bpmn:documentation>
 * JSON blob (crtsh/reverseIp = 20s, enrichLegalEntity = 30s for GLEIF).
 */

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  resultTimeoutMs: number;
};

const OWNER_DID = "did:web:yabai.etzhayyim.com";
const createdAt = "2026-04-24T12:00:00Z";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readBpmn(fileName: string): string {
  return readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/ai/gftd/yabai", fileName),
    "utf8",
  );
}

const pivots: Array<{
  slug: string;
  bpmnProcessId: string;
  file: string;
  nsid: string;
  bindingSlug: string;
  resultTimeoutMs: number;
}> = [
  { slug: "yabai-crtsh-fuzzy-search-v1",    bpmnProcessId: "yabai_crtsh_fuzzy_search",    file: "crtshFuzzySearch.bpmn",    nsid: "ai.gftd.apps.yabai.crtshFuzzySearch",    bindingSlug: "yabai-crtshFuzzySearch-v1",    resultTimeoutMs: 20000 },
  { slug: "yabai-reverse-ip-lookup-v1",     bpmnProcessId: "yabai_reverse_ip_lookup",     file: "reverseIpLookup.bpmn",     nsid: "ai.gftd.apps.yabai.reverseIpLookup",     bindingSlug: "yabai-reverseIpLookup-v1",     resultTimeoutMs: 20000 },
  { slug: "yabai-enrich-legal-entity-v1",   bpmnProcessId: "yabai_enrich_legal_entity",   file: "enrichLegalEntity.bpmn",   nsid: "ai.gftd.apps.yabai.enrichLegalEntity",   bindingSlug: "yabai-enrichLegalEntity-v1",   resultTimeoutMs: 30000 },
];

const processSeeds: ProcessSeed[] = pivots.map((p) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${p.slug}`,
  bpmnProcessId: p.bpmnProcessId,
  sourcePath: `00-contracts/bpmn/ai/gftd/yabai/${p.file}`,
}));

const bindingSeeds: BindingSeed[] = pivots.map((p) => ({
  vertexId: `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${p.bindingSlug}`,
  nsid: p.nsid,
  bpmnProcessId: p.bpmnProcessId,
  resultTimeoutMs: p.resultTimeoutMs,
}));

export async function up(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not parse `ON CONFLICT` in raw SQL, so we check-
  // then-insert to get idempotent re-runs. (Same pattern documented in
  // `scripts/run-one-migration.mjs:33-42`.)
  for (let i = 0; i < pivots.length; i++) {
    const pivot = pivots[i];
    const seed = processSeeds[i];
    const xml = readBpmn(pivot.file);
    const existing = await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId} LIMIT 1
    `.execute(db);
    if (existing.rows.length > 0) continue;
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, bpmn_process_id, version, xml, status,
        owner_did, source_path, created_at
      ) VALUES (
        ${seed.vertexId}, ${pivot.bpmnProcessId}, 1, ${xml}, 'active',
        ${OWNER_DID}, ${seed.sourcePath}, ${createdAt}::timestamptz
      )
    `.execute(db);
  }

  for (const binding of bindingSeeds) {
    const existing = await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${binding.vertexId} LIMIT 1
    `.execute(db);
    if (existing.rows.length > 0) continue;
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, nsid, bpmn_process_id, status,
        owner_did, result_timeout_ms, created_at
      ) VALUES (
        ${binding.vertexId}, ${binding.nsid}, ${binding.bpmnProcessId}, 'active',
        ${OWNER_DID}, ${binding.resultTimeoutMs}, ${createdAt}::timestamptz
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const binding of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${binding.vertexId}`.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
}
