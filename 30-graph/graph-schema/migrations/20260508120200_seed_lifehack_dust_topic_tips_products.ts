import type { Kysely } from "kysely";
import { sql } from "kysely";
import { createHash } from "node:crypto";

/**
 * lifehack.etzhayyim.com Phase 1 seed data — dust prevention.
 *
 * 5 topics + 12 tips + 10 commercial products + edges, hand-curated
 * from the design conversation (CLAUDE → user, 2026-05-08).  All
 * commercial products carry an Amazon search keyword (the root rule
 * forbids guessing Amazon URLs); diy_tsukuru cross-reference fields
 * stay null in Phase 1 — they get back-filled when tsukuru.etzhayyim.com
 * publishes the matching CAD model + factory DID.
 *
 * Authority policy (matches schema cap rules):
 *   - secondary  → effectiveness ≤ 80 (physics-grounded tips)
 *   - llm-synth  → effectiveness ≤ 60 (gear-specific recommendations)
 *
 * Re-runs are idempotent (content-hashed PKs + INSERT WHERE NOT EXISTS).
 */

const OWNER_DID = "did:web:lifehack.etzhayyim.com";
const ACTOR_TAG = "sys.lifehack.seed.phase1";
const CREATED_AT = "2026-05-08T12:00:00Z";
const NSID_TOPIC = "app.etzhayyim.apps.lifehack.topic";
const NSID_TIP = "app.etzhayyim.apps.lifehack.tip";
const NSID_PRODUCT = "app.etzhayyim.apps.lifehack.product";
const NSID_EDGE_TS = "app.etzhayyim.apps.lifehack.tipSolvesTopic";
const NSID_EDGE_TP = "app.etzhayyim.apps.lifehack.tipRecommendsProduct";

function hash12(s: string): string {
  return createHash("sha1").update(s).digest("hex").slice(0, 12);
}

function topicVid(topicId: string): string {
  return `at://${OWNER_DID}/${NSID_TOPIC}/${topicId}`;
}
function tipVid(tipId: string): string {
  return `at://${OWNER_DID}/${NSID_TIP}/${tipId}`;
}
function productVid(productId: string): string {
  return `at://${OWNER_DID}/${NSID_PRODUCT}/${productId}`;
}

type Topic = {
  topicId: string;
  category: string;
  titleJa: string;
  titleEn: string;
  summaryJa: string;
  parentTopicId?: string;
};

type Tip = {
  topicId: string;
  bodyJa: string;
  bodyEn?: string;
  effectiveness: number;
  costMin: number;
  costMax: number;
  difficulty: "easy" | "medium" | "hard";
  sourceAuthority: "primary" | "secondary" | "llm-synth";
  evidence: string;
};

type Product = {
  productId: string;
  name: string;
  brand: string;
  category: string;
  sourceType: "commercial" | "diy_tsukuru";
  priceMin: number;
  priceMax: number;
  amazonKeyword: string;
  pseCertified?: boolean;
  notesJa?: string;
};

const topics: Topic[] = [
  { topicId: "dust-on-desk", category: "dust",
    titleJa: "机周りのホコリ対策",
    titleEn: "Dust prevention on the desk",
    summaryJa: "卓上・電子機器周辺のホコリ蓄積を抑える基本セット。"
  },
  { topicId: "static-electricity-control", category: "humidity",
    titleJa: "静電気の抑制",
    titleEn: "Static electricity control",
    summaryJa: "湿度コントロールと帯電防止でホコリ吸着を1/3に。",
    parentTopicId: "dust-on-desk" },
  { topicId: "air-cleanliness", category: "cleaning",
    titleJa: "室内の空気清浄度",
    titleEn: "Indoor air cleanliness",
    summaryJa: "供給源を断つことでホコリ付着を体感1/3まで下げる。",
    parentTopicId: "dust-on-desk" },
  { topicId: "cable-management", category: "cable",
    titleJa: "配線・ケーブルのホコリ対策",
    titleEn: "Cable dust avoidance",
    summaryJa: "配線量を減らす・浮かすことで掃除工数を10倍下げる。",
    parentTopicId: "dust-on-desk" },
  { topicId: "routine-cleaning", category: "cleaning",
    titleJa: "毎日のホコリ掃除ルーチン",
    titleEn: "Daily dust-cleaning routine",
    summaryJa: "毎日30秒の習慣で蓄積を防ぐ。" },
];

const tips: Tip[] = [
  // dust-on-desk
  { topicId: "dust-on-desk",
    bodyJa: "静電ハンディモップ（クイックル系）でキーボードや配線の隙間を片手30秒で拭く。マイクロファイバーが静電気でホコリを吸着し舞い上げない。",
    effectiveness: 55, costMin: 500, costMax: 1000, difficulty: "easy",
    sourceAuthority: "llm-synth",
    evidence: "市販ハンディモップの一般的仕様。静電吸着で再付着を抑制。"},
  { topicId: "dust-on-desk",
    bodyJa: "シリコンゲル・クリーニングパテをキーボードや通気口に押し付けて剥がすと、隙間のホコリごと除去できる。繰り返し使え、汚れたら捨てるだけ。",
    effectiveness: 50, costMin: 500, costMax: 800, difficulty: "easy",
    sourceAuthority: "llm-synth",
    evidence: "シリコン粘着クリーナーの一般用途。" },
  { topicId: "dust-on-desk",
    bodyJa: "充電式ミニ卓上クリーナーを引き出しに常備し、ボタン1つで吸引する。消しゴムカス・パンくず・ホコリを一気に取り除き蓄積を防ぐ。",
    effectiveness: 50, costMin: 2000, costMax: 4000, difficulty: "easy",
    sourceAuthority: "llm-synth",
    evidence: "USB卓上クリーナー製品群の一般仕様。" },

  // static-electricity-control
  { topicId: "static-electricity-control",
    bodyJa: "室内湿度を40-60%に保つだけで静電気電圧が数千V→数百V以下に激減し、卓上ホコリ付着が体感1/3になる。冬場対策の最優先事項。",
    effectiveness: 80, costMin: 5000, costMax: 30000, difficulty: "easy",
    sourceAuthority: "secondary",
    evidence: "湿度と静電気電圧の関係は静電気学会・各種ESD実験で広く確認。湿度50%以上で表面導通が回復する。" },
  { topicId: "static-electricity-control",
    bodyJa: "帯電防止スプレーを月1回、機器表面とデスクに薄く塗布する。表面の微量水分膜が電荷を逃がし、ホコリが寄ってこない。画面・基板に直接かけずクロス経由で。",
    effectiveness: 65, costMin: 500, costMax: 1500, difficulty: "easy",
    sourceAuthority: "secondary",
    evidence: "界面活性剤系の帯電防止剤は表面抵抗を下げる原理。製品ラベルの一般指示。" },
  { topicId: "static-electricity-control",
    bodyJa: "卓上イオナイザーは半径50cmの帯電をほぼゼロにする専門機器。半導体工場仕様の卓上型1-2万円帯。オーディオ・カメラ・PC周辺に有効。",
    effectiveness: 60, costMin: 10000, costMax: 30000, difficulty: "medium",
    sourceAuthority: "llm-synth",
    evidence: "産業用イオナイザーの民生機。除電原理は確立技術だが家庭用ではオーバースペック。" },

  // air-cleanliness
  { topicId: "air-cleanliness",
    bodyJa: "HEPA空気清浄機を24時間静音運転で机の近くに置く。ホコリ供給源を断つと付着量が体感1/3。強運転は気流でホコリを舞わせて逆効果なので静音モード固定。",
    effectiveness: 70, costMin: 20000, costMax: 50000, difficulty: "easy",
    sourceAuthority: "secondary",
    evidence: "HEPA H13フィルタは0.3μm粒子を99.97%以上除去（IEST規格）。長時間連続運転で室内浮遊量が低下。" },
  { topicId: "air-cleanliness",
    bodyJa: "エアダスター + マイクロファイバークロスの2刀流。吹き出した瞬間に舞ったホコリをクロスがキャッチ→再付着しない。年1-2回の本格清掃向け。",
    effectiveness: 55, costMin: 500, costMax: 1500, difficulty: "easy",
    sourceAuthority: "llm-synth",
    evidence: "エアダスター単独使用は再付着の原因。クロスとセットで運用するのがベスト。" },

  // cable-management
  { topicId: "cable-management",
    bodyJa: "ケーブルトレー・配線ボックスで床から浮かす。ケーブルが多い=表面積×複雑形状=ホコリの巣なので、本数を減らす方が拭く回数を10倍下げる。",
    effectiveness: 70, costMin: 1500, costMax: 4000, difficulty: "medium",
    sourceAuthority: "secondary",
    evidence: "整理整頓と清掃工数の相関は5S・Lean生産方式で確立。" },
  { topicId: "cable-management",
    bodyJa: "机の上に物を置かない=拭ける面積が増える。ミニマル配置は『掃除しない設計』として最強。月1掃除頻度を週1相当の効果に押し上げる。",
    effectiveness: 60, costMin: 0, costMax: 0, difficulty: "easy",
    sourceAuthority: "secondary",
    evidence: "5S整理整頓の延長。物理的障害物の削減が清掃時間を線形に下げる。" },

  // routine-cleaning
  { topicId: "routine-cleaning",
    bodyJa: "ハンディモップ・マイクロファイバー・小型ブロワーの3点セットを引き出しに常備。朝のコーヒー待ち30秒だけ拭く。蓄積させると2倍の時間がかかる。",
    effectiveness: 75, costMin: 1500, costMax: 3000, difficulty: "easy",
    sourceAuthority: "secondary",
    evidence: "予防保全（preventive maintenance）の原則。少額頻繁の清掃は累積コストを最小化する。" },
  { topicId: "routine-cleaning",
    bodyJa: "黒い機器は目立つだけで実際のホコリ付着量は色と無関係。色を変えるよりも素材選び（ガラス天板・メラミン化粧板）で帯電しにくい面に切替えるほうが効く。",
    effectiveness: 50, costMin: 0, costMax: 0, difficulty: "easy",
    sourceAuthority: "secondary",
    evidence: "プラスチック表面抵抗 vs ガラス表面抵抗の比較。帯電しやすさは素材依存。" },
];

const products: Product[] = [
  { productId: "handy-mop-quickle",
    name: "静電ハンディモップ（クイックル系）",
    brand: "花王 / アズマ", category: "dust-mop", sourceType: "commercial",
    priceMin: 500, priceMax: 1200, amazonKeyword: "クイックル ハンディ モップ",
    notesJa: "使い捨てヘッドで衛生的、機器に最も安全。" },
  { productId: "silicone-cleaning-putty",
    name: "シリコンゲル・クリーニングパテ",
    brand: "汎用", category: "cleaning-putty", sourceType: "commercial",
    priceMin: 500, priceMax: 1000, amazonKeyword: "シリコン クリーナー パテ キーボード",
    notesJa: "繰り返し使える、隙間のホコリに最強。" },
  { productId: "desktop-vacuum-usb",
    name: "充電式ミニ卓上掃除機",
    brand: "汎用", category: "vacuum", sourceType: "commercial",
    priceMin: 2000, priceMax: 4000, amazonKeyword: "卓上 ミニ 掃除機 USB",
    pseCertified: true,
    notesJa: "USB充電、ノズル切替でキーボード隙間も対応。" },
  { productId: "antistatic-spray-elecom",
    name: "帯電防止スプレー",
    brand: "エレコム / サンワサプライ", category: "antistatic-spray", sourceType: "commercial",
    priceMin: 600, priceMax: 1200, amazonKeyword: "エレコム 帯電防止 スプレー",
    notesJa: "クロスに吹いてから拭く。月1ルーチン化推奨。" },
  { productId: "humidifier-room",
    name: "加湿器（家庭用、室内湿度50%維持）",
    brand: "汎用 (シャープ / アイリスオーヤマ等)", category: "humidifier", sourceType: "commercial",
    priceMin: 5000, priceMax: 30000, amazonKeyword: "加湿器 6畳 ハイブリッド",
    pseCertified: true,
    notesJa: "湿度計を併用して50%維持。冬場の静電気対策の本命。" },
  { productId: "ionizer-desktop-hozan",
    name: "卓上イオナイザー（HOZAN相当）",
    brand: "HOZAN / SIMCO / ベッセル", category: "ionizer", sourceType: "commercial",
    priceMin: 10000, priceMax: 30000, amazonKeyword: "卓上 イオナイザー HOZAN",
    pseCertified: true,
    notesJa: "イオンバランス±35V以下を選定基準に。卓上ホコリ対策にはオーバースペック気味だが手軽。" },
  { productId: "air-purifier-hepa",
    name: "HEPA空気清浄機（6-8畳用）",
    brand: "シャープ / ダイキン / パナソニック", category: "air-purifier", sourceType: "commercial",
    priceMin: 20000, priceMax: 50000, amazonKeyword: "空気清浄機 HEPA 8畳 静音",
    pseCertified: true,
    notesJa: "24時間静音モード固定。机側に吸込口を向ける配置が効く。" },
  { productId: "air-duster-can",
    name: "エアダスター（缶タイプ）",
    brand: "サンワサプライ / エレコム", category: "air-duster", sourceType: "commercial",
    priceMin: 600, priceMax: 1500, amazonKeyword: "エアダスター 缶 PC キーボード",
    notesJa: "可燃性ガス使用品が多いため換気必須。" },
  { productId: "cable-tray",
    name: "ケーブルトレー / 配線ボックス",
    brand: "サンワサプライ / IKEA SIGNUM", category: "cable-tray", sourceType: "commercial",
    priceMin: 1500, priceMax: 4000, amazonKeyword: "ケーブルトレー デスク 下",
    notesJa: "床から浮かせて配線を集約、掃除工数を10倍下げる。" },
  { productId: "microfiber-cloth",
    name: "マイクロファイバークロス",
    brand: "汎用", category: "cloth", sourceType: "commercial",
    priceMin: 300, priceMax: 1500, amazonKeyword: "マイクロファイバー クロス 業務用",
    notesJa: "10枚セットで常備。エアダスターと併用。" },
];

// tip → product associations (curated)
const tipProductLinks: Array<[string, string]> = [
  // dust-on-desk
  ["dust-on-desk-mop",      "handy-mop-quickle"],
  ["dust-on-desk-putty",    "silicone-cleaning-putty"],
  ["dust-on-desk-vacuum",   "desktop-vacuum-usb"],
  // static-electricity-control
  ["static-humidity",       "humidifier-room"],
  ["static-spray",          "antistatic-spray-elecom"],
  ["static-ionizer",        "ionizer-desktop-hozan"],
  // air-cleanliness
  ["air-purifier",          "air-purifier-hepa"],
  ["air-duster-cloth",      "air-duster-can"],
  ["air-duster-cloth",      "microfiber-cloth"],
  // cable-management
  ["cable-tray",            "cable-tray"],
  // routine-cleaning
  ["routine-3piece",        "handy-mop-quickle"],
  ["routine-3piece",        "microfiber-cloth"],
];

// stable, deterministic short slug per tip body so re-seeding is idempotent
const tipSlugByIndex: Record<number, string> = {
  0:  "dust-on-desk-mop",
  1:  "dust-on-desk-putty",
  2:  "dust-on-desk-vacuum",
  3:  "static-humidity",
  4:  "static-spray",
  5:  "static-ionizer",
  6:  "air-purifier",
  7:  "air-duster-cloth",
  8:  "cable-tray",
  9:  "routine-clean-design",
  10: "routine-3piece",
  11: "routine-color",
};

function tipIdFor(t: Tip, slug: string): string {
  const seed = `tip|${t.topicId}|${slug}|${t.bodyJa.slice(0, 64)}`;
  return `tip-${hash12(seed)}`;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // Topics
  for (const t of topics) {
    const vid = topicVid(t.topicId);
    await sql`
      INSERT INTO vertex_lifehack_topic (
        vertex_id, owner_did, sensitivity_ord, topic_id, category,
        title_ja, title_en, summary_ja, summary_en, parent_topic_id,
        status, created_at, org_id, user_id, actor_id)
      SELECT ${vid}, ${OWNER_DID}, 0, ${t.topicId}, ${t.category},
             ${t.titleJa}, ${t.titleEn}, ${t.summaryJa}, NULL, ${t.parentTopicId ?? null},
             'active', ${CREATED_AT}, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_topic WHERE vertex_id = ${vid})
    `.execute(db);
  }

  // Tips + slug → tipId map
  const tipIdMap: Record<string, string> = {};
  for (let i = 0; i < tips.length; i++) {
    const t = tips[i];
    const slug = tipSlugByIndex[i] ?? `tip-${i}`;
    const tipId = tipIdFor(t, slug);
    tipIdMap[slug] = tipId;
    const vid = tipVid(tipId);
    await sql`
      INSERT INTO vertex_lifehack_tip (
        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,
        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,
        difficulty, source_url, source_authority, evidence_summary, llm_model,
        status, created_at, org_id, user_id, actor_id)
      SELECT ${vid}, ${OWNER_DID}, 0, ${tipId}, ${t.topicId},
             ${t.bodyJa}, NULL, CAST(${t.effectiveness} AS DOUBLE PRECISION), CAST(${t.costMin} AS DOUBLE PRECISION), CAST(${t.costMax} AS DOUBLE PRECISION),
             ${t.difficulty}, NULL, ${t.sourceAuthority}, ${t.evidence}, 'curated',
             'active', ${CREATED_AT}, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = ${vid})
    `.execute(db);

    // tip → topic edge (1:1)
    const edgeVid = `at://${OWNER_DID}/${NSID_EDGE_TS}/${tipId}-${t.topicId}`;
    await sql`
      INSERT INTO edge_lifehack_tip_solves_topic (
        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,
        created_at, org_id, user_id, actor_id)
      SELECT ${edgeVid}, ${OWNER_DID}, 0, ${vid}, ${topicVid(t.topicId)}, 'solves',
             ${CREATED_AT}, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = ${edgeVid})
    `.execute(db);
  }

  // Products
  for (const p of products) {
    const vid = productVid(p.productId);
    await sql`
      INSERT INTO vertex_lifehack_product (
        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,
        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, pse_certified,
        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,
        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,
        status, created_at, org_id, user_id, actor_id)
      SELECT ${vid}, ${OWNER_DID}, 0, ${p.productId}, ${p.name}, ${p.brand}, ${p.category},
             ${p.sourceType}, CAST(${p.priceMin} AS DOUBLE PRECISION), CAST(${p.priceMax} AS DOUBLE PRECISION), ${p.amazonKeyword}, NULL,
             CAST(${p.pseCertified ?? null} AS BOOLEAN),
             NULL, NULL, NULL, CAST(NULL AS DOUBLE PRECISION), CAST(NULL AS DOUBLE PRECISION), ${p.notesJa ?? null},
             'active', ${CREATED_AT}, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = ${vid})
    `.execute(db);
  }

  // tip → product edges
  for (const [tipSlug, productId] of tipProductLinks) {
    const tipId = tipIdMap[tipSlug];
    if (!tipId) continue;
    const tipVidLocal = tipVid(tipId);
    const productVidLocal = productVid(productId);
    const edgeVid = `at://${OWNER_DID}/${NSID_EDGE_TP}/${tipId}-${productId}`;
    await sql`
      INSERT INTO edge_lifehack_tip_recommends_product (
        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,
        created_at, org_id, user_id, actor_id)
      SELECT ${edgeVid}, ${OWNER_DID}, 0, ${tipVidLocal}, ${productVidLocal}, 'recommends',
             ${CREATED_AT}, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id = ${edgeVid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // delete edges first
  await sql`DELETE FROM edge_lifehack_tip_recommends_product WHERE actor_id = ${ACTOR_TAG}`.execute(db);
  await sql`DELETE FROM edge_lifehack_tip_solves_topic       WHERE actor_id = ${ACTOR_TAG}`.execute(db);
  await sql`DELETE FROM vertex_lifehack_product               WHERE actor_id = ${ACTOR_TAG}`.execute(db);
  await sql`DELETE FROM vertex_lifehack_tip                   WHERE actor_id = ${ACTOR_TAG}`.execute(db);
  await sql`DELETE FROM vertex_lifehack_topic                 WHERE actor_id = ${ACTOR_TAG}`.execute(db);
}
