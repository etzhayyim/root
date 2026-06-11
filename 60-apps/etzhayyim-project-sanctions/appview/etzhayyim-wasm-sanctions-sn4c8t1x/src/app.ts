import {
  asAgentTool,
  createWorkerExport,
  createKyselyDb,
  withCapabilityTags,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  nowISO,
  str,
  sql,
  nsid,
  genID,
} from "@etzhayyim/kotodama-host-sdk";

let appId = "";

type QueryRow = Record<string, unknown>;
type SanctionEntryRow = {
  entry_id: string | null;
  list_name: string | null;
  subject_name: string | null;
  subject_type: string | null;
  country: string | null;
  program: string | null;
  metadata_json: string | null;
  effective_at: string | null;
};
type ListUpdateRow = {
  update_id: string | null;
  list_name: string | null;
  list_version: string | null;
  change_count: number | string | bigint | null;
  fetched_at: string | null;
};

const SANCTION_ENTRY_TABLE = "vertex_sanctions_entry";
const LIST_UPDATE_TABLE = "vertex_sanctions_list_update";
const SANCTION_ENTRY_SELECT = [
  "entry_id",
  "list_name",
  "subject_name",
  "subject_type",
  "country",
  "program",
  "metadata_json",
  "effective_at",
] as const;
const LIST_UPDATE_SELECT = [
  "update_id",
  "list_name",
  "list_version",
  "change_count",
  "fetched_at",
] as const;

function getDb() {
  return createKyselyDb();
}

function escapeLike(value: string): string {
  return value.replace(/[\\%_]/g, "\\$&");
}

async function write(_sdk: HostSDK, collection: string, rec: Record<string, unknown>): Promise<void> {
  function camelToSnake(s: string): string { return s.replace(/[A-Z]/g, c => `_${c.toLowerCase()}`); }
  const tableMap: Record<string, string> = {
    match: "vertex_sanctions_match",
  };
  const table = tableMap[collection] ?? `vertex_sanctions_${camelToSnake(collection)}`;
  const ownerDid = `did:web:sn4c8t1x.etzhayyim.com`;
  const rkey = str(rec.matchId ?? rec.entryId ?? rec.updateId ?? "") || genID();
  const vertex_id = `at://${ownerDid}/com.etzhayyim.apps.sanctions.${collection}/${rkey}`;
  const snakeRec = Object.fromEntries(Object.entries(rec).map(([k, v]) => [camelToSnake(k), v]));
  await createKyselyDb().insertInto(table as any).values({ vertex_id, sensitivity_ord: 2, owner_did: ownerDid, actor_id: appId, ...snakeRec }).execute();
}

function post(sdk: HostSDK, text: string): void {
  const rec = { $type: "app.bsky.feed.post", text: text.slice(0, 300), createdAt: nowISO() };
  const pds = sdk.pds as unknown as {
    createRecord?: (collection: string, record: Record<string, unknown>) => unknown;
    dispatch?: (msg: { type: string; payload: unknown }) => unknown;
  };
  if (typeof pds.createRecord === "function") { pds.createRecord("app.bsky.feed.post", rec); return; }
  pds.dispatch?.({ type: "app.bsky.feed.post", payload: rec });
}

// --- Sanctions List Sources ---
// OFAC SDN:    https://www.treasury.gov/ofac/downloads/sdn.xml (XML) / sdnlist.txt (pipe-delimited)
// EU:          https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content (XML)
// UN:          https://scsanctions.un.org/resources/xml/en/consolidated.xml
// JP-MOF FEFTA: https://www.mof.go.jp/policy/international_policy/gaitame_kawase/gaitame/economic_sanctions/list.html

// --- Graph Schema ---
// SanctionEntry:  { entry_id, list_source, entity_name, entity_type, country, program, aliases_json, identifiers_json, updated_at }
// SanctionMatch:  { match_id, query_entity, matched_entry_id, score, match_type, screened_at }
// ListUpdate:     { update_id, list_source, version, entry_count, downloaded_at }

export default createWorkerExport((sdk: HostSDK) => {
  appId = sdk.app.nanoid ?? "sn4c8t1x";

  // ── Commands ──

  sdk.app.command(nsid("com.etzhayyim.apps.sanctions.screenEntity"),
    async (_ctx, params) => {
      const name = str(params?.name ?? "");
      const entityType = str(params?.entityType ?? "any");
      const country = str(params?.country ?? "");
      if (!name) return { error: "name is required" };

      const rows = await getDb()
        .selectFrom(SANCTION_ENTRY_TABLE as any)
        .select(SANCTION_ENTRY_SELECT as any)
        .where(sql<boolean>`upper(coalesce(subject_name, '')) like ${`${escapeLike(name.toUpperCase())}%`} escape '\\'`)
        .limit(20)
        .execute() as SanctionEntryRow[];

      const matches = rows.map((r) => {
        return {
          entryId: r.entry_id,
          entityName: r.subject_name,
          listSource: r.list_name,
          country: r.country,
          program: r.program,
        };
      });

      if (matches.length > 0) {
        for (const m of matches) {
          await write(sdk, "match", {
            matchId: `match-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            queryEntity: name,
            matchedEntryId: m.entryId,
            matchedName: m.entityName,
            listSource: m.listSource,
            score: 0.85,
            matchType: "contains",
            screenedAt: nowISO(),
          });
        }
      }

      return { query: name, entityType, country, matchCount: matches.length, matches };
    },
    asAgentTool("Screen entity against OFAC/EU/UN/JP-MOF sanctions lists"),
    withCapabilityTags("sanctions", "compliance", "aml"),
  );

  sdk.app.command(nsid("com.etzhayyim.sanctions.getEntry"),
    async (_ctx, params) => {
      const entryId = str(params?.entryId ?? "");
      if (!entryId) return { error: "entryId is required" };
      const rows = await getDb()
        .selectFrom(SANCTION_ENTRY_TABLE as any)
        .select(SANCTION_ENTRY_SELECT as any)
        .where(sql<boolean>`coalesce(entry_id, '') = ${entryId}`)
        .limit(1)
        .execute() as SanctionEntryRow[];
      if (!rows[0]) return { error: "not found" };
      return {
        entry_id: rows[0].entry_id,
        list_source: rows[0].list_name,
        entity_name: rows[0].subject_name,
        entity_type: rows[0].subject_type,
        country: rows[0].country,
        program: rows[0].program,
        aliases_json: rows[0].metadata_json,
        identifiers_json: rows[0].metadata_json,
        updated_at: rows[0].effective_at,
      } as QueryRow;
    },
    asAgentTool("Get sanctions list entry by ID"),
  );

  sdk.app.command(nsid("com.etzhayyim.sanctions.listUpdates"),
    async (_ctx, params) => {
      const limit = Number(params?.limit ?? 20);
      const rows = await getDb()
        .selectFrom(LIST_UPDATE_TABLE as any)
        .select(LIST_UPDATE_SELECT as any)
        .orderBy(sql`coalesce(fetched_at, '') desc`)
        .limit(limit)
        .execute() as ListUpdateRow[];
      const updates = rows.map((r) => ({
        update_id: r.update_id,
        list_source: r.list_name,
        version: r.list_version,
        entry_count: r.change_count,
        downloaded_at: r.fetched_at,
      })) as QueryRow[];
      return { updates, total: updates.length };
    },
    asAgentTool("List recent sanctions list updates"),
  );

  // ── Reactive Pipeline (Design E) ──

  sdk.app.onCommit(handleComAtprotoSyncSubscribeReposCommit);
});

async function handleComAtprotoSyncSubscribeReposCommit(
  commit: ComAtprotoSyncSubscribeReposCommit,
): Promise<void> {
  if (commit.action !== "create") return;

  // malak threat actor/org → auto-screen against sanctions
  if (
    commit.collection === "com.etzhayyim.apps.malak.threatActor" ||
    commit.collection === "com.etzhayyim.apps.malak.threatOrganization"
  ) {
    const rec = commit.record as Record<string, unknown> | undefined;
    const name = str(rec?.entity_name ?? rec?.name ?? "");
    if (name) {
      const rows = await getDb()
        .selectFrom(SANCTION_ENTRY_TABLE as any)
        .select(["entry_id"])
        .where(sql<boolean>`upper(coalesce(subject_name, '')) like ${`${escapeLike(name.toUpperCase())}%`} escape '\\'`)
        .limit(5)
        .execute();
      if (rows.length > 0) {
        // Auto-post sanctions match alert
        console.log(`[sanctions] Auto-screen match for "${name}": ${rows.length} hits`);
      }
    }
  }
}
