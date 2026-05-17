import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type FormSeed = {
  key: string;
  path: string;
  actorDid: string;
};

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../../..");

const seeds: FormSeed[] = [
  { key: "itr1-form-v1", path: "00-contracts/forms/ai/gftd/itr1/itr1-form-v1.json", actorDid: "did:web:ind-union.etzhayyim.com:cbdt:itr1" },
  { key: "itr1-self-review-v1", path: "00-contracts/forms/ai/gftd/itr1/itr1-self-review-v1.json", actorDid: "did:web:ind-union.etzhayyim.com:cbdt:itr1" },
  { key: "itr1-amend-v1", path: "00-contracts/forms/ai/gftd/itr1/itr1-amend-v1.json", actorDid: "did:web:ind-union.etzhayyim.com:cbdt:itr1" },
  { key: "gstr3b-form-v1", path: "00-contracts/forms/ai/gftd/gstr3b/gstr3b-form-v1.json", actorDid: "did:web:ind-union.etzhayyim.com:cbic:gstr3b" },
  { key: "gstr3b-review-v1", path: "00-contracts/forms/ai/gftd/gstr3b/gstr3b-review-v1.json", actorDid: "did:web:ind-union.etzhayyim.com:cbic:gstr3b" },
  { key: "gstr3b-amend-v1", path: "00-contracts/forms/ai/gftd/gstr3b/gstr3b-amend-v1.json", actorDid: "did:web:ind-union.etzhayyim.com:cbic:gstr3b" },
  { key: "epfo-ecr-form-v1", path: "00-contracts/forms/ai/gftd/epfo/ecr-form-v1.json", actorDid: "did:web:ind-payroll.etzhayyim.com:epfo" },
  { key: "epfo-review-v1", path: "00-contracts/forms/ai/gftd/epfo/review-v1.json", actorDid: "did:web:ind-payroll.etzhayyim.com:epfo" },
  { key: "epfo-amend-v1", path: "00-contracts/forms/ai/gftd/epfo/amend-v1.json", actorDid: "did:web:ind-payroll.etzhayyim.com:epfo" },
  { key: "esic-monthly-form-v1", path: "00-contracts/forms/ai/gftd/esic/monthly-form-v1.json", actorDid: "did:web:ind-payroll.etzhayyim.com:esic" },
  { key: "esic-review-v1", path: "00-contracts/forms/ai/gftd/esic/review-v1.json", actorDid: "did:web:ind-payroll.etzhayyim.com:esic" },
  { key: "esic-amend-v1", path: "00-contracts/forms/ai/gftd/esic/amend-v1.json", actorDid: "did:web:ind-payroll.etzhayyim.com:esic" },
];

function formRow(seed: FormSeed, seq: number) {
  const raw = readFileSync(resolve(repoRoot, seed.path), "utf8");
  const form = JSON.parse(raw) as {
    name?: string;
    title?: string;
    description?: string;
    schemaVersion?: number;
    components?: unknown[];
    variableMappings?: unknown;
  };
  return {
    vertexId: `at://${seed.actorDid}/ai.gftd.form.task/${seed.key}`,
    seq,
    ownerDid: seed.actorDid,
    rkey: seed.key,
    repo: seed.actorDid,
    did: seed.actorDid,
    formKey: seed.key,
    name: form.name || form.title || seed.key,
    displayName: form.name || form.title || seed.key,
    description: form.description || "",
    formType: "camunda",
    schemaVersion: Number(form.schemaVersion || 1),
    componentsJson: JSON.stringify(form.components || []),
    variableMappingsJson: JSON.stringify(form.variableMappings || {}),
  };
}

export async function up(db: Kysely<unknown>): Promise<void> {
  let seq = 20260427001000;
  for (const seed of seeds) {
    const row = formRow(seed, seq++);
    await sql`
      DELETE FROM vertex_form_task WHERE form_key = ${row.formKey}
    `.execute(db);
    await sql`
      INSERT INTO vertex_form_task (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        rkey, repo, did, form_key, name, display_name, description,
        form_type, schema_version, components_json, variable_mappings_json,
        status, updated_at
      ) VALUES (
        ${row.vertexId}, ${row.seq}, DATE '2026-04-27', 2, ${row.ownerDid},
        ${row.rkey}, ${row.repo}, ${row.did}, ${row.formKey}, ${row.name},
        ${row.displayName}, ${row.description}, ${row.formType},
        ${row.schemaVersion}, ${row.componentsJson}, ${row.variableMappingsJson},
        'active', '2026-04-27T00:10:00Z'
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_form_task WHERE form_key = ${seed.key}`.execute(db);
  }
}
