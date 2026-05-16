import type { Kysely } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await db.schema
    .createTable("vertex_lei_entity")
    .ifNotExists()
    .addColumn("vertex_id", "varchar", (c) => c.primaryKey().notNull())
    .addColumn("_seq", "bigint")
    .addColumn("created_date", "varchar")
    .addColumn("sensitivity_ord", "integer")
    .addColumn("owner_did", "varchar")
    .addColumn("lei", "varchar")
    .addColumn("legal_name", "varchar")
    .addColumn("legal_name_local", "varchar")
    .addColumn("legal_form_id", "varchar")
    .addColumn("jurisdiction", "varchar")
    .addColumn("entity_status", "varchar")
    .addColumn("entity_category", "varchar")
    .addColumn("registered_country", "varchar")
    .addColumn("hq_country", "varchar")
    .addColumn("parent_lei", "varchar")
    .addColumn("ultimate_parent_lei", "varchar")
    .addColumn("listed", "boolean")
    .addColumn("stock_exchange", "varchar")
    .addColumn("ticker", "varchar")
    .addColumn("isin", "varchar")
    .addColumn("registration_status", "varchar")
    .addColumn("initially_registered", "varchar")
    .addColumn("last_updated", "varchar")
    .addColumn("next_renewal", "varchar")
    .addColumn("managing_lou", "varchar")
    .addColumn("source", "varchar")
    .addColumn("ingested_at", "varchar")
    .addColumn("props", "varchar")
    .addColumn("actor_did", "varchar")
    .addColumn("org_did", "varchar")
    .addColumn("created_at", "varchar")
    .execute();

  await db.schema
    .createTable("edge_person_lei_entity")
    .ifNotExists()
    .addColumn("edge_id", "varchar", (c) => c.primaryKey().notNull())
    .addColumn("person_vertex_id", "varchar")
    .addColumn("lei_vertex_id", "varchar")
    .addColumn("role", "varchar")
    .addColumn("since", "varchar")
    .addColumn("until", "varchar")
    .addColumn("confidence", "double precision")
    .addColumn("source", "varchar")
    .addColumn("ingested_at", "varchar")
    .execute();
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await db.schema.dropTable("edge_person_lei_entity").ifExists().execute();
  await db.schema.dropTable("vertex_lei_entity").ifExists().execute();
}
