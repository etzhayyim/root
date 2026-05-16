import type { Kysely } from 'kysely';
import type {
  Database,
  MvNaphthaCargoFlowRow,
  MvNaphthaCountryBalanceRow,
  MvNaphthaPriceLatestRow,
  MvNaphthaSupplyChainTraceRow,
  VertexNaphthaMarketNodeRow,
} from './database.js';

export interface NaphthaTraceFilters {
  countryCode?: string;
  nodeKind?: string;
  relationship?: string;
  limit?: number;
}

export async function listNaphthaSupplyChainTrace(
  db: Kysely<Database>,
  filters: NaphthaTraceFilters = {},
): Promise<MvNaphthaSupplyChainTraceRow[]> {
  let q = db
    .selectFrom('mv_naphtha_supply_chain_trace')
    .selectAll()
    .orderBy('src_country_code', 'asc')
    .orderBy('src_node_code', 'asc')
    .orderBy('dst_node_code', 'asc');

  if (filters.countryCode) {
    q = q.where((eb) =>
      eb.or([
        eb('src_country_code', '=', filters.countryCode),
        eb('dst_country_code', '=', filters.countryCode),
      ]),
    );
  }
  if (filters.nodeKind) {
    q = q.where((eb) =>
      eb.or([
        eb('src_node_kind', '=', filters.nodeKind),
        eb('dst_node_kind', '=', filters.nodeKind),
      ]),
    );
  }
  if (filters.relationship) q = q.where('relationship', '=', filters.relationship);
  if (filters.limit && filters.limit > 0) q = q.limit(filters.limit);

  return q.execute();
}

export async function listNaphthaCountryBalance(
  db: Kysely<Database>,
  limit = 50,
): Promise<MvNaphthaCountryBalanceRow[]> {
  return db
    .selectFrom('mv_naphtha_country_balance')
    .selectAll()
    .orderBy('balance_tonnes_day', 'asc')
    .limit(limit)
    .execute();
}

export async function listNaphthaCargoFlows(
  db: Kysely<Database>,
  limit = 50,
): Promise<MvNaphthaCargoFlowRow[]> {
  return db
    .selectFrom('mv_naphtha_cargo_flow')
    .selectAll()
    .orderBy('total_tonnes', 'desc')
    .limit(limit)
    .execute();
}

export async function listLatestNaphthaPrices(
  db: Kysely<Database>,
  region?: string,
): Promise<MvNaphthaPriceLatestRow[]> {
  let q = db
    .selectFrom('mv_naphtha_price_latest')
    .selectAll()
    .orderBy('region', 'asc')
    .orderBy('benchmark_code', 'asc');

  if (region) q = q.where('region', '=', region);

  return q.execute();
}

export async function listNaphthaMarketNodes(
  db: Kysely<Database>,
  nodeKind?: string,
  limit = 100,
): Promise<VertexNaphthaMarketNodeRow[]> {
  let q = db
    .selectFrom('vertex_naphtha_market_node')
    .selectAll()
    .orderBy('country_code', 'asc')
    .orderBy('node_code', 'asc')
    .limit(limit);

  if (nodeKind) q = q.where('node_kind', '=', nodeKind);

  return q.execute();
}
