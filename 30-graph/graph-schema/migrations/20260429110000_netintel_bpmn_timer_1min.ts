// Bump netintel BPMN timer from R/P1M (monthly) to R/PT1M (every 1 minute)
// for fine-grained processing during development/pilot.
//
// F5 watcher detects xml column change and redeploys all 5 processes to Zeebe.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const procs = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-dns-delta-v1",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/netintelDnsDelta.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-ip-enrich-delta-v1",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/ipEnrichDelta.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-whois-delta-v1",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/whoisDelta.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-scan-banner-delta-v1",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/scanBannerDelta.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/netintel-fingerprint-delta-v1",
    sourcePath: "00-contracts/bpmn/ai/gftd/ingest/fingerprintDelta.bpmn",
  },
] as const;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const proc of procs) {
    const xml = readFileSync(path.resolve(repoRoot, proc.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      UPDATE vertex_bpmn_process_def
      SET "xml"            = ${xml},
          "xml_byte_size"  = CAST(${size} AS integer),
          "version"        = 2,
          "source_path"    = ${proc.sourcePath}
      WHERE "vertex_id" = ${proc.vertexId}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Restore version counter only; original XML is in git at parent commit.
  for (const proc of procs) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET version = 1
      WHERE vertex_id = ${proc.vertexId}
    `.execute(db);
  }
}
