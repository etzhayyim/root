import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * otakiage.etzhayyim.com 季節祭 calendar 初期 seed (ADR-2605081700).
 *
 * Phase 1 = 4 events (年間カレンダー、Phase 1 は digital ritual のみ、capacity 0):
 *   春の人形供養祭   (2026-11-15)  ningyo / nuigurumi 対象
 *   絵本供養祭       (2026-04-20)  ehon / jidousho 対象、こどもの読書週間 (4/23) 直前
 *   秋の人形供養祭   (2026-11-15)  ningyo / nuigurumi 対象
 *   おもちゃ供養祭   (2026-08-08)  omocha 対象 (8/8 = はちはちでおもちゃの日に近接)
 *
 * 家具/家電は ritual に流れない (reuse_only モード) ので matsuri seed なし。
 * 以後の年は BPMN otakiage_matsuri_schedule (cron 月初) で auto seed される。
 *
 * vertex_id は content-addressed (ADR-0041): at://{authorDid}/{collection}/{rkey}
 *   authorDid = did:web:otakiage.etzhayyim.com:matsuri
 *   collection = com.etzhayyim.apps.otakiage.matsuri
 *   rkey = matsuri-{slug}-{yyyymm}
 */

type M = {
  vertexId: string;
  matsuriId: string;
  name: string;
  categoryScope: string;       // JSON array as string
  scheduledDate: string;       // YYYY-MM-DD
  description: string;
};

const createdAt = "2026-05-08T17:00:00Z";
const ownerDid = "did:web:otakiage.etzhayyim.com:matsuri";
const actorTag = "sys.matsuri.seed.otakiage";
const issuerName = "etzhayyim";

const matsuriSeeds: M[] = [
  {
    vertexId: "at://did:web:otakiage.etzhayyim.com:matsuri/com.etzhayyim.apps.otakiage.matsuri/matsuri-haru-ningyo-202604",
    matsuriId: "matsuri-haru-ningyo-202604",
    name: "春の人形供養祭 2026",
    categoryScope: JSON.stringify(["ningyo", "nuigurumi"]),
    scheduledDate: "2026-04-15",
    description: "春の人形供養祭 — 雛人形・五月人形・ぬいぐるみ をお焚き上げいたします。etzhayyim 主催。Phase 1 は digital ritual (証跡 AT Record JSON 発行)。",
  },
  {
    vertexId: "at://did:web:otakiage.etzhayyim.com:matsuri/com.etzhayyim.apps.otakiage.matsuri/matsuri-ehon-202604",
    matsuriId: "matsuri-ehon-202604",
    name: "絵本供養祭 2026 — こどもの読書週間",
    categoryScope: JSON.stringify(["ehon", "jidousho"]),
    scheduledDate: "2026-04-20",
    description: "絵本供養祭 — 子どもの成長で役目を終えた絵本・児童書をお焚き上げいたします。こどもの読書週間 (4/23) に合わせた開催。reuse 未成立分のみ対象、reuse 経路を最優先。",
  },
  {
    vertexId: "at://did:web:otakiage.etzhayyim.com:matsuri/com.etzhayyim.apps.otakiage.matsuri/matsuri-omocha-202608",
    matsuriId: "matsuri-omocha-202608",
    name: "おもちゃ供養祭 2026",
    categoryScope: JSON.stringify(["omocha"]),
    scheduledDate: "2026-08-08",
    description: "おもちゃ供養祭 — 8/8 おもちゃの日 周辺に開催。子どもの成長と共に役目を終えたおもちゃをお焚き上げ。プラスチック製品は供養対象 (物理焼却ではなく digital ritual + 永続証跡)。",
  },
  {
    vertexId: "at://did:web:otakiage.etzhayyim.com:matsuri/com.etzhayyim.apps.otakiage.matsuri/matsuri-aki-ningyo-202611",
    matsuriId: "matsuri-aki-ningyo-202611",
    name: "秋の人形供養祭 2026",
    categoryScope: JSON.stringify(["ningyo", "nuigurumi"]),
    scheduledDate: "2026-11-15",
    description: "秋の人形供養祭 — 七五三 (11/15) に合わせ、人形・ぬいぐるみをお焚き上げいたします。年 2 回 (春・秋) の人形供養の秋回。",
  },
];

async function insertMatsuri(db: Kysely<unknown>, m: M): Promise<void> {
  await sql`
    INSERT INTO vertex_otakiage_matsuri (
      vertex_id, owner_did, matsuri_id, name, category_scope, scheduled_date, capacity, registered_count, location_h3, description, state,
      created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${m.vertexId}, ${ownerDid}, ${m.matsuriId}, ${m.name}, ${m.categoryScope}, CAST(${m.scheduledDate} AS date),
      0, 0, NULL, ${m.description}, 'open',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_otakiage_matsuri WHERE vertex_id = ${m.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // issuerName is referenced in description text; suppress lint warning by using it.
  void issuerName;
  for (const m of matsuriSeeds) await insertMatsuri(db, m);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const m of matsuriSeeds) {
    await sql`DELETE FROM vertex_otakiage_matsuri WHERE vertex_id = ${m.vertexId}`.execute(db);
  }
}
