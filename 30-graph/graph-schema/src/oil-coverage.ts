import type { Kysely } from 'kysely';
import type { Database, MvOilCoverageLiveRow } from './database.js';

export type OilCoverageSegment =
  | 'upstream'
  | 'midstream'
  | 'refining'
  | 'trading'
  | 'shipping'
  | 'distribution';

export interface OilCoverageFilters {
  segment?: OilCoverageSegment;
  countryCode?: string;
  limit?: number;
}

export async function listOilCoverageLive(
  db: Kysely<Database>,
  filters: OilCoverageFilters = {},
): Promise<MvOilCoverageLiveRow[]> {
  let q = db
    .selectFrom('mv_oil_coverage_live')
    .selectAll()
    .orderBy('coverage_gap', 'desc')
    .orderBy('priority', 'asc')
    .orderBy('country_code', 'asc');

  if (filters.segment) q = q.where('segment', '=', filters.segment);
  if (filters.countryCode) q = q.where('country_code', '=', filters.countryCode);
  if (filters.limit && filters.limit > 0) q = q.limit(filters.limit);

  return q.execute();
}

export async function listOilCoverageGaps(
  db: Kysely<Database>,
  limit = 20,
): Promise<MvOilCoverageLiveRow[]> {
  return db
    .selectFrom('mv_oil_coverage_live')
    .selectAll()
    .where('coverage_gap', '>', 0)
    .orderBy('coverage_gap', 'desc')
    .orderBy('priority', 'asc')
    .limit(limit)
    .execute();
}

export async function getOilCoverageSummary(db: Kysely<Database>) {
  return db
    .selectFrom('mv_oil_coverage_live')
    .select(({ fn }) => [
      fn.count<string>('target_key').as('target_count'),
      fn.sum<number | bigint>('actual_count').as('actual_total'),
      fn.sum<number | bigint>('target_count').as('target_total'),
    ])
    .executeTakeFirst();
}
