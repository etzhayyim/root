import type { Kysely } from "kysely";
import { sql } from "kysely";

const cohortColumns = [
  "country", "region", "municipality", "age", "gender",
  "income_decile", "education_isced", "occupation_isco", "employment_status",
  "marital_status", "household_size", "housing_tenure", "urban_rural",
  "health_icd10", "disability_type", "migration_status",
  "ethnicity", "religion", "language_primary",
  "entity_did", "community_id",
  "vital_status", "birth_year", "death_year",
  "death_cause_icd10", "era",
] as const;

type CohortRow = {
  vertex_id: string;
  cohort_hash: string | null;
} & Record<(typeof cohortColumns)[number], string | null>;

function canonical(row: CohortRow): string {
  return cohortColumns.map((column) => String(row[column] ?? "")).join("|");
}

function cohortHashV1(input: string): string {
  let h = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  const mask = 0xffffffffffffffffn;
  for (let i = 0; i < input.length; i++) {
    h ^= BigInt(input.charCodeAt(i));
    h = (h * prime) & mask;
  }
  return `npch1_${h.toString(16).padStart(16, "0")}`;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  const rows = await sql<CohortRow>`
    SELECT vertex_id, cohort_hash,
           country, region, municipality, age, gender,
           income_decile, education_isced, occupation_isco, employment_status,
           marital_status, household_size, housing_tenure, urban_rural,
           health_icd10, disability_type, migration_status,
           ethnicity, religion, language_primary,
           entity_did, community_id,
           vital_status, birth_year, death_year,
           death_cause_icd10, era
      FROM vertex_natural_person_cohort_person
  `.execute(db);

  for (const row of rows.rows) {
    const nextHash = cohortHashV1(canonical(row));
    if (row.cohort_hash === nextHash) continue;
    await sql`
      UPDATE vertex_natural_person_cohort_person
         SET cohort_hash = ${nextHash}
       WHERE vertex_id = ${row.vertex_id}
    `.execute(db);
  }

  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Irreversible: previous hashes were collision-prone and not recoverable
  // for every row without preserving a side table.
}
