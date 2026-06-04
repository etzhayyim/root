import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed vertex_bpmn_process_def for media-gamers chart analysis BPMNs.
 *
 *   chartFetch.bpmn    — R/P7D timer-start; fetchAndPersist + analyze + post.
 *   chartAnalyze.bpmn  — none-start (XRPC com.etzhayyim.apps.media_gamers.analyzeChart).
 *
 * F5 watcher deploys each to Zeebe within 30s of insert.
 * ADR-0056 (BPMN-as-actor), INSERT 2 rows convention.
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..", "..");
const readBpmn = (file: string) =>
  readFileSync(
    path.resolve(repoRoot, "00-contracts/bpmn/com/etzhayyim/media-gamers", file),
    "utf8",
  );

const CREATED_AT = "2026-04-30T16:00:00Z";
const OWNER_DID = "did:web:bpmn.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.media-gamers-chart";

const FETCH_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-fetch-v1";
const ANALYZE_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-analyze-v1";
const ANALYZE_BINDING_VERTEX_ID =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-media-gamers-analyzeChart-v1";
const ANALYZE_NSID = "com.etzhayyim.apps.media_gamers.analyzeChart";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── chartFetch.bpmn (timer R/P7D) ──────────────────────────────────────
  const fetchXml = readBpmn("chartFetch.bpmn");
  const fetchSize = Buffer.byteLength(fetchXml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${FETCH_VERTEX_ID}, ${OWNER_DID}, ${"media_gamers_chart_fetch"}, 1,
           ${fetchXml}, CAST(${fetchSize} AS integer),
           ${"00-contracts/bpmn/com/etzhayyim/media-gamers/chartFetch.bpmn"},
           ${"active"}, ${CREATED_AT}, 1,
           ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${FETCH_VERTEX_ID}
    )
  `.execute(db);

  // ── chartAnalyze.bpmn (XRPC-triggered, none-start) ─────────────────────
  const analyzeXml = readBpmn("chartAnalyze.bpmn");
  const analyzeSize = Buffer.byteLength(analyzeXml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${ANALYZE_VERTEX_ID}, ${OWNER_DID}, ${"media_gamers_chart_analyze"}, 1,
           ${analyzeXml}, CAST(${analyzeSize} AS integer),
           ${"00-contracts/bpmn/com/etzhayyim/media-gamers/chartAnalyze.bpmn"},
           ${"active"}, ${CREATED_AT}, 1,
           ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${ANALYZE_VERTEX_ID}
    )
  `.execute(db);

  // ── lexicon binding for chartAnalyze (XRPC → BPMN) ────────────────────
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${ANALYZE_BINDING_VERTEX_ID}, ${OWNER_DID},
           ${ANALYZE_NSID}, ${"media_gamers_chart_analyze"},
           1, CAST(${180_000} AS integer), NULL,
           ${"active"}, ${CREATED_AT}, 1,
           ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${ANALYZE_BINDING_VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${ANALYZE_BINDING_VERTEX_ID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${ANALYZE_VERTEX_ID}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${FETCH_VERTEX_ID}`.execute(db);
}
