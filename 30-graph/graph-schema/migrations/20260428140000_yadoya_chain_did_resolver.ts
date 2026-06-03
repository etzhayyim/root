import type { Kysely } from "kysely";
import { sql } from "kysely";

// yadoya Phase 8a — resolve chain_did on vertex_yadoya_hotel by matching the
// hotel name against the canonical chain roster from ADR-0028
// (60-apps/etzhayyim-project-hospitality/CLAUDE.md §Chain).
//
// We use case-insensitive substring match against the chain slug spelled out
// in the brand name. Properties without a recognizable brand keep
// chain_did = NULL — this is intentional (independent / boutique hotels).
//
// RisingWave note: single-statement UPDATE is supported (see
// 20260417150000_etzhayyim_did_recursive_tree.ts for prior art). FLUSH afterward
// so downstream MVs (e.g. mv_yadoya_catalog_coverage) observe the change.

type ChainMatch = { slug: string; pattern: string };

const CHAINS: ChainMatch[] = [
  { slug: "marriott",   pattern: "%marriott%" },
  { slug: "hilton",     pattern: "%hilton%" },
  { slug: "hyatt",      pattern: "%hyatt%" },
  { slug: "ihg",        pattern: "%intercontinental%" },
  { slug: "ihg",        pattern: "%holiday inn%" },
  { slug: "accor",      pattern: "%accor%" },
  { slug: "accor",      pattern: "%mercure%" },
  { slug: "accor",      pattern: "%novotel%" },
  { slug: "wyndham",    pattern: "%wyndham%" },
  { slug: "choice",     pattern: "%comfort inn%" },
  { slug: "hoshino",    pattern: "%hoshino%" },
  { slug: "hoshino",    pattern: "%星野%" },
  { slug: "prince",     pattern: "%prince hotel%" },
  { slug: "prince",     pattern: "%プリンス%" },
  { slug: "tokyu-stay", pattern: "%tokyu stay%" },
  { slug: "apa",        pattern: "%apa hotel%" },
  { slug: "apa",        pattern: "%アパホテル%" },
  { slug: "route-inn",  pattern: "%route inn%" },
  { slug: "route-inn",  pattern: "%ルートイン%" },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const { slug, pattern } of CHAINS) {
    const did = `did:web:hospitality.etzhayyim.com:actor:chain:${slug}`;
    await sql`
      UPDATE vertex_yadoya_hotel
      SET chain_did = ${did}
      WHERE chain_did IS NULL
        AND LOWER(name) LIKE ${pattern.toLowerCase()}
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Reset chain_did to NULL for slugs minted by this resolver. We
  // identify them by the prefix; surgically undoing per-pattern is
  // unnecessary because no other migration sets chain_did yet.
  await sql`
    UPDATE vertex_yadoya_hotel
    SET chain_did = NULL
    WHERE chain_did LIKE 'did:web:hospitality.etzhayyim.com:actor:chain:%'
  `.execute(db);
  await sql`FLUSH`.execute(db);
}
