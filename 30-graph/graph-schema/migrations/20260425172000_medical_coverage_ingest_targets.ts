import { Kysely, sql } from "kysely";

/**
 * Medical coverage ingest targets.
 *
 * The Kubernetes medical-coverage-ingester writes to vertex_repo_record using
 * these collections. mv_world_collection_coverage_live then reports progress
 * without any app-specific read path.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE (domain = 'gakujutsu_ronbun' AND collection = 'com.etzhayyim.apps.iryo.pubmedPaper')
       OR (domain = 'rinshou_shiken'   AND collection = 'com.etzhayyim.apps.iryo.rinshou')
       OR (domain = 'iryo_shisetsu'    AND collection = 'com.etzhayyim.apps.iryo.shisetsu')
       OR (domain = 'dsm_shikkan'      AND collection = 'com.etzhayyim.apps.iryo.dsmCategory')
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('gakujutsu_ronbun', 'iryo', 'com.etzhayyim.apps.iryo.pubmedPaper', 200000000, 'academic papers indexed by PubMed/Semantic Scholar/Crossref', 'healthcare'),
      ('rinshou_shiken',   'iryo', 'com.etzhayyim.apps.iryo.rinshou',        500000, 'registered clinical trials', 'healthcare'),
      ('iryo_shisetsu',    'iryo', 'com.etzhayyim.apps.iryo.shisetsu',      1000000, 'hospitals and clinics', 'healthcare'),
      ('dsm_shikkan',      'iryo', 'com.etzhayyim.apps.iryo.dsmCategory',        21, 'DSM public category-level taxonomy rows', 'healthcare')
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain
    WHERE domain = 'dsm_shikkan'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES ('dsm_shikkan', 'iryo', 21, 'DSM public category-level taxonomy rows', 'healthcare')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE (domain = 'gakujutsu_ronbun' AND collection = 'com.etzhayyim.apps.iryo.pubmedPaper')
       OR (domain = 'rinshou_shiken'   AND collection = 'com.etzhayyim.apps.iryo.rinshou')
       OR (domain = 'iryo_shisetsu'    AND collection = 'com.etzhayyim.apps.iryo.shisetsu')
       OR (domain = 'dsm_shikkan'      AND collection = 'com.etzhayyim.apps.iryo.dsmCategory')
  `.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'dsm_shikkan'`.execute(db);
}
