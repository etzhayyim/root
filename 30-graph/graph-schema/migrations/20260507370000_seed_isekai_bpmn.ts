import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:isekai.etzhayyim.com";
const createdAt = "2026-05-07T00:35:00Z";
const actorId = "sys.bpmn.seed.isekai";

const snake = (proc: string) => proc.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const writeAllowlist = [
  "vertex_isekai_world_state",
  "vertex_isekai_chunk_data",
  "vertex_isekai_creature_roster",
  "vertex_isekai_inventory_item",
  "vertex_isekai_brainrot_event",
  "vertex_isekai_compliance_dep",
  "vertex_isekai_game_capture",
  "vertex_isekai_game_craft",
  "vertex_isekai_game_brainrot_encounter",
].join(",");
const writeProcs = new Set([
  "catchPokoa",
  "craftItem",
  "createWorld",
  "mineBlock",
  "placeBlock",
  "registerCompliance",
  "rollBrainrot",
  "startOhioRaid",
]);

const seeds: Seed[] = [
  "analyze",
  "browseWorlds",
  "cardHome",
  "catchPokoa",
  "craftItem",
  "createWorld",
  "fleeBattle",
  "getChunk",
  "getCompliance",
  "getInventory",
  "getLegendaries",
  "getPortalState",
  "getRoster",
  "getWorld",
  "healParty",
  "listRecipes",
  "listScenes",
  "mineBlock",
  "placeBlock",
  "registerCompliance",
  "rollBrainrot",
  "rollEncounter",
  "startBattle",
  "startOhioRaid",
  "teleportBiome",
  "useMove",
].map((proc) => ({
  proc,
  bpmnProcessId: `isekai_${snake(proc)}`,
  nsid: `com.etzhayyim.apps.isekai.${proc}`,
  resultTimeoutMs: 30000,
  writeTableAllowlist: writeProcs.has(proc) ? writeAllowlist : "",
}));

const bpmnPath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/isekai/${s.proc}.bpmn`;
const processVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/isekai-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/isekai-${slug(s.proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
        ${xml}, ${bpmnPath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}
      )
    `.execute(db);
    await sql`
      UPDATE vertex_bpmn_process_def
      SET xml_byte_size = ${size}
      WHERE vertex_id = ${processVid(s)} AND xml_byte_size IS NULL
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
        ${sql.raw(String(s.resultTimeoutMs))}, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
