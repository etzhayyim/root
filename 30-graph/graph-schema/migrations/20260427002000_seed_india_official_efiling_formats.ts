import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Descriptor = {
  formatKey: string;
  jurisdiction: string;
  actorDid: string;
  formatKind: string;
  officialSourceUrl: string;
  sourcePageUrl?: string;
  lastVerified: string;
  status: string;
  internalFormKeys?: string[];
  fieldMap?: unknown[];
  notes?: string[];
};

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../../..");

const descriptorPaths = [
  "00-contracts/formats/ai/gftd/ind/itr1/eri-submit-flow-v1.1.json",
  "00-contracts/formats/ai/gftd/ind/itr1/prefill-schema-v6.5.manifest.json",
  "00-contracts/formats/ai/gftd/ind/gstr3b/gsp-framework-v3.manifest.json",
  "00-contracts/formats/ai/gftd/ind/epfo/ecr-file-format.json",
  "00-contracts/formats/ai/gftd/ind/esic/monthly-contribution-format.manifest.json",
];

function loadDescriptor(path: string): Descriptor {
  return JSON.parse(readFileSync(resolve(repoRoot, path), "utf8")) as Descriptor;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ind_efiling_format (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      format_key             varchar NOT NULL,
      jurisdiction           varchar NOT NULL,
      actor_did              varchar NOT NULL,
      format_kind            varchar NOT NULL,
      status                 varchar NOT NULL,
      official_source_url    varchar NOT NULL,
      source_page_url        varchar,
      local_descriptor_path  varchar NOT NULL,
      internal_form_keys     varchar,
      field_map_json         varchar,
      descriptor_json        varchar NOT NULL,
      last_verified_at       varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  let seq = 20260427002000;
  for (const path of descriptorPaths) {
    const descriptor = loadDescriptor(path);
    const vertexId = `at://${descriptor.actorDid}/app.etzhayyim.apps.ind.efiling.format/${descriptor.formatKey}`;
    await sql`DELETE FROM vertex_ind_efiling_format WHERE format_key = ${descriptor.formatKey}`.execute(db);
    await sql`
      INSERT INTO vertex_ind_efiling_format (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        format_key, jurisdiction, actor_did, format_kind, status,
        official_source_url, source_page_url, local_descriptor_path,
        internal_form_keys, field_map_json, descriptor_json,
        last_verified_at, created_at, org_id, user_id, actor_id
      ) VALUES (
        ${vertexId}, ${seq++}, DATE '2026-04-27', 2, ${descriptor.actorDid},
        ${descriptor.formatKey}, ${descriptor.jurisdiction}, ${descriptor.actorDid},
        ${descriptor.formatKind}, ${descriptor.status}, ${descriptor.officialSourceUrl},
        ${descriptor.sourcePageUrl || ""}, ${path},
        ${(descriptor.internalFormKeys || []).join(",")},
        ${JSON.stringify(descriptor.fieldMap || [])},
        ${JSON.stringify(descriptor)},
        ${descriptor.lastVerified}, '2026-04-27T00:20:00Z',
        'ind', 'system', 'sys.ind.efiling.format'
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const path of descriptorPaths) {
    const descriptor = loadDescriptor(path);
    await sql`DELETE FROM vertex_ind_efiling_format WHERE format_key = ${descriptor.formatKey}`.execute(db);
  }
}
