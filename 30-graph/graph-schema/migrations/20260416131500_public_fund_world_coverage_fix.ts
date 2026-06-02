import { Kysely, sql } from 'kysely';

/**
 * 2026-04-16
 * Fix public fund world coverage normalization.
 *
 * Problem:
 * - dim_world_domain.public_fund uses canonical host `public-fund`
 * - live app host is `pb.etzhayyim.com` → repo host fragment `pb`
 * - collection-level coverage defaulted public_fund to bootstrap, so real
 *   public fund records were invisible in mv_world_collection_coverage_live
 *
 * This patch:
 * 1. aliases `pb` → `public-fund`
 * 2. replaces bootstrap placeholder mapping for public_fund with explicit
 *    public-fund domain collections from the domain model
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM dim_app_host_alias
    WHERE alias_host = 'pb'
  `.execute(db);

  await sql`
    INSERT INTO dim_app_host_alias (alias_host, canonical_host)
    VALUES ('pb', 'public-fund')
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE domain = 'public_fund'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.fundProgram', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.fundCampaign', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.pledge', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.routedAllocation', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.eligibilityPolicy', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.application', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.decision', 150000, 'public funds', 'governance'),
      ('public_fund', 'public-fund', 'com.etzhayyim.apps.publicFund.disbursement', 150000, 'public funds', 'governance')
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM dim_world_domain_collection
    WHERE domain = 'public_fund'
      AND collection IN (
        'com.etzhayyim.apps.publicFund.fundProgram',
        'com.etzhayyim.apps.publicFund.fundCampaign',
        'com.etzhayyim.apps.publicFund.pledge',
        'com.etzhayyim.apps.publicFund.routedAllocation',
        'com.etzhayyim.apps.publicFund.eligibilityPolicy',
        'com.etzhayyim.apps.publicFund.application',
        'com.etzhayyim.apps.publicFund.decision',
        'com.etzhayyim.apps.publicFund.disbursement'
      )
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES ('public_fund', 'public-fund', 'com.etzhayyim.coverage.bootstrap', 150000, 'public funds', 'governance')
  `.execute(db);

  await sql`
    DELETE FROM dim_app_host_alias
    WHERE alias_host = 'pb' AND canonical_host = 'public-fund'
  `.execute(db);
}
