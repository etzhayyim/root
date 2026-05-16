import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * sbom.gftd.ai — bump registerArtifact.bpmn to version 2 to trigger
 * F5 watcher redeploy. Phase C adds the Task_VulnMatch step between
 * Persist and Audit.
 *
 * Pattern mirrors `legal-entity BPMN v2` (deps.toml entry
 * "legal-entity BPMN v2 (2026-05-01)") — same vertex_id, version
 * bumped, xml refreshed; F5 watcher detects the version change and
 * redeploys to Zeebe within 30s.
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const sourcePath = "00-contracts/bpmn/ai/gftd/sbom/registerArtifact.bpmn";
const processVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/sbom-register-artifact-v1";
const bindingVertexId =
  "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/sbom-registerArtifact-v1";
const updatedAt = "2026-05-06T11:01:00Z";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readContract(sourcePath);
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    UPDATE vertex_bpmn_process_def
       SET xml = ${xml},
           xml_byte_size = CAST(${size} AS integer),
           version = 2,
           created_at = ${updatedAt}
     WHERE vertex_id = ${processVertexId}
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
       SET bpmn_version = 2,
           created_at = ${updatedAt}
     WHERE vertex_id = ${bindingVertexId}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Reverting to v1 requires the original Phase B BPMN; not auto-recoverable.
  // No-op down — re-apply the prior seed migration manually if needed.
  void db;
}
