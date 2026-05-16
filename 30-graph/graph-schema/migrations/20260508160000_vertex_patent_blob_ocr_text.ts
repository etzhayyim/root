import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Add ocr_text column to vertex_patent_blob so patent OCR text is
 * stored directly in RisingWave (in addition to B2 CID reference).
 * This enables v_training_text to UNION ALL patent OCR without an
 * external B2 fetch at query time.
 *
 * patent.blob.convert (patent.py) will be updated to populate this
 * column alongside the existing ocr_text_cid B2 upload.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_patent_blob
      ADD COLUMN IF NOT EXISTS ocr_text VARCHAR
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN — leave column in place.
}
