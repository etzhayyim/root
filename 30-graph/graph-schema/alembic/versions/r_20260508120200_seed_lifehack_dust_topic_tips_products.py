"""Captured from Kysely migration 20260508120200_seed_lifehack_dust_topic_tips_products."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508120200_seed_lifehack_dust_topic_tips_products"
down_revision = 'r_20260508120100_seed_lifehack_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_lifehack_topic (\n'
         '        vertex_id, owner_did, sensitivity_ord, topic_id, category,\n'
         '        title_ja, title_en, summary_ja, summary_en, parent_topic_id,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, $6, $7, NULL, $8,\n'
         "             'active', $9, $10, $11, $12\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_topic WHERE vertex_id = $13)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/dust-on-desk',
                 'did:web:lifehack.etzhayyim.com',
                 'dust-on-desk',
                 'dust',
                 '机周りのホコリ対策',
                 'Dust prevention on the desk',
                 '卓上・電子機器周辺のホコリ蓄積を抑える基本セット。',
                 None,
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/dust-on-desk']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_topic (\n'
         '        vertex_id, owner_did, sensitivity_ord, topic_id, category,\n'
         '        title_ja, title_en, summary_ja, summary_en, parent_topic_id,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, $6, $7, NULL, $8,\n'
         "             'active', $9, $10, $11, $12\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_topic WHERE vertex_id = $13)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/static-electricity-control',
                 'did:web:lifehack.etzhayyim.com',
                 'static-electricity-control',
                 'humidity',
                 '静電気の抑制',
                 'Static electricity control',
                 '湿度コントロールと帯電防止でホコリ吸着を1/3に。',
                 'dust-on-desk',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/static-electricity-control']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_topic (\n'
         '        vertex_id, owner_did, sensitivity_ord, topic_id, category,\n'
         '        title_ja, title_en, summary_ja, summary_en, parent_topic_id,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, $6, $7, NULL, $8,\n'
         "             'active', $9, $10, $11, $12\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_topic WHERE vertex_id = $13)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/air-cleanliness',
                 'did:web:lifehack.etzhayyim.com',
                 'air-cleanliness',
                 'cleaning',
                 '室内の空気清浄度',
                 'Indoor air cleanliness',
                 '供給源を断つことでホコリ付着を体感1/3まで下げる。',
                 'dust-on-desk',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/air-cleanliness']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_topic (\n'
         '        vertex_id, owner_did, sensitivity_ord, topic_id, category,\n'
         '        title_ja, title_en, summary_ja, summary_en, parent_topic_id,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, $6, $7, NULL, $8,\n'
         "             'active', $9, $10, $11, $12\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_topic WHERE vertex_id = $13)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/cable-management',
                 'did:web:lifehack.etzhayyim.com',
                 'cable-management',
                 'cable',
                 '配線・ケーブルのホコリ対策',
                 'Cable dust avoidance',
                 '配線量を減らす・浮かすことで掃除工数を10倍下げる。',
                 'dust-on-desk',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/cable-management']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_topic (\n'
         '        vertex_id, owner_did, sensitivity_ord, topic_id, category,\n'
         '        title_ja, title_en, summary_ja, summary_en, parent_topic_id,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, $6, $7, NULL, $8,\n'
         "             'active', $9, $10, $11, $12\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_topic WHERE vertex_id = $13)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/routine-cleaning',
                 'did:web:lifehack.etzhayyim.com',
                 'routine-cleaning',
                 'cleaning',
                 '毎日のホコリ掃除ルーチン',
                 'Daily dust-cleaning routine',
                 '毎日30秒の習慣で蓄積を防ぐ。',
                 None,
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/routine-cleaning']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-b86cd290507a',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-b86cd290507a',
                 'dust-on-desk',
                 '静電ハンディモップ（クイックル系）でキーボードや配線の隙間を片手30秒で拭く。マイクロファイバーが静電気でホコリを吸着し舞い上げない。',
                 55,
                 500,
                 1000,
                 'easy',
                 'llm-synth',
                 '市販ハンディモップの一般的仕様。静電吸着で再付着を抑制。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-b86cd290507a']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-b86cd290507a-dust-on-desk',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-b86cd290507a',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/dust-on-desk',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-b86cd290507a-dust-on-desk']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-faeb28c530cd',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-faeb28c530cd',
                 'dust-on-desk',
                 'シリコンゲル・クリーニングパテをキーボードや通気口に押し付けて剥がすと、隙間のホコリごと除去できる。繰り返し使え、汚れたら捨てるだけ。',
                 50,
                 500,
                 800,
                 'easy',
                 'llm-synth',
                 'シリコン粘着クリーナーの一般用途。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-faeb28c530cd']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-faeb28c530cd-dust-on-desk',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-faeb28c530cd',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/dust-on-desk',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-faeb28c530cd-dust-on-desk']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-75bd800d5fe9',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-75bd800d5fe9',
                 'dust-on-desk',
                 '充電式ミニ卓上クリーナーを引き出しに常備し、ボタン1つで吸引する。消しゴムカス・パンくず・ホコリを一気に取り除き蓄積を防ぐ。',
                 50,
                 2000,
                 4000,
                 'easy',
                 'llm-synth',
                 'USB卓上クリーナー製品群の一般仕様。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-75bd800d5fe9']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-75bd800d5fe9-dust-on-desk',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-75bd800d5fe9',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/dust-on-desk',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-75bd800d5fe9-dust-on-desk']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-239e07b8e574',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-239e07b8e574',
                 'static-electricity-control',
                 '室内湿度を40-60%に保つだけで静電気電圧が数千V→数百V以下に激減し、卓上ホコリ付着が体感1/3になる。冬場対策の最優先事項。',
                 80,
                 5000,
                 30000,
                 'easy',
                 'secondary',
                 '湿度と静電気電圧の関係は静電気学会・各種ESD実験で広く確認。湿度50%以上で表面導通が回復する。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-239e07b8e574']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-239e07b8e574-static-electricity-control',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-239e07b8e574',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/static-electricity-control',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-239e07b8e574-static-electricity-control']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-10b8c9a7d3d1',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-10b8c9a7d3d1',
                 'static-electricity-control',
                 '帯電防止スプレーを月1回、機器表面とデスクに薄く塗布する。表面の微量水分膜が電荷を逃がし、ホコリが寄ってこない。画面・基板に直接かけずクロス経由で。',
                 65,
                 500,
                 1500,
                 'easy',
                 'secondary',
                 '界面活性剤系の帯電防止剤は表面抵抗を下げる原理。製品ラベルの一般指示。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-10b8c9a7d3d1']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-10b8c9a7d3d1-static-electricity-control',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-10b8c9a7d3d1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/static-electricity-control',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-10b8c9a7d3d1-static-electricity-control']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d22c29493612',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-d22c29493612',
                 'static-electricity-control',
                 '卓上イオナイザーは半径50cmの帯電をほぼゼロにする専門機器。半導体工場仕様の卓上型1-2万円帯。オーディオ・カメラ・PC周辺に有効。',
                 60,
                 10000,
                 30000,
                 'medium',
                 'llm-synth',
                 '産業用イオナイザーの民生機。除電原理は確立技術だが家庭用ではオーバースペック。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d22c29493612']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-d22c29493612-static-electricity-control',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d22c29493612',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/static-electricity-control',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-d22c29493612-static-electricity-control']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-51b072777188',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-51b072777188',
                 'air-cleanliness',
                 'HEPA空気清浄機を24時間静音運転で机の近くに置く。ホコリ供給源を断つと付着量が体感1/3。強運転は気流でホコリを舞わせて逆効果なので静音モード固定。',
                 70,
                 20000,
                 50000,
                 'easy',
                 'secondary',
                 'HEPA H13フィルタは0.3μm粒子を99.97%以上除去（IEST規格）。長時間連続運転で室内浮遊量が低下。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-51b072777188']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-51b072777188-air-cleanliness',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-51b072777188',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/air-cleanliness',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-51b072777188-air-cleanliness']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-8a322db257ca',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-8a322db257ca',
                 'air-cleanliness',
                 'エアダスター + マイクロファイバークロスの2刀流。吹き出した瞬間に舞ったホコリをクロスがキャッチ→再付着しない。年1-2回の本格清掃向け。',
                 55,
                 500,
                 1500,
                 'easy',
                 'llm-synth',
                 'エアダスター単独使用は再付着の原因。クロスとセットで運用するのがベスト。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-8a322db257ca']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-8a322db257ca-air-cleanliness',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-8a322db257ca',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/air-cleanliness',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-8a322db257ca-air-cleanliness']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-787a477eb7a2',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-787a477eb7a2',
                 'cable-management',
                 'ケーブルトレー・配線ボックスで床から浮かす。ケーブルが多い=表面積×複雑形状=ホコリの巣なので、本数を減らす方が拭く回数を10倍下げる。',
                 70,
                 1500,
                 4000,
                 'medium',
                 'secondary',
                 '整理整頓と清掃工数の相関は5S・Lean生産方式で確立。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-787a477eb7a2']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-787a477eb7a2-cable-management',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-787a477eb7a2',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/cable-management',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-787a477eb7a2-cable-management']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-6e39d1f51050',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-6e39d1f51050',
                 'cable-management',
                 '机の上に物を置かない=拭ける面積が増える。ミニマル配置は『掃除しない設計』として最強。月1掃除頻度を週1相当の効果に押し上げる。',
                 60,
                 0,
                 0,
                 'easy',
                 'secondary',
                 '5S整理整頓の延長。物理的障害物の削減が清掃時間を線形に下げる。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-6e39d1f51050']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-6e39d1f51050-cable-management',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-6e39d1f51050',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/cable-management',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-6e39d1f51050-cable-management']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d7466b0e5bc6',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-d7466b0e5bc6',
                 'routine-cleaning',
                 'ハンディモップ・マイクロファイバー・小型ブロワーの3点セットを引き出しに常備。朝のコーヒー待ち30秒だけ拭く。蓄積させると2倍の時間がかかる。',
                 75,
                 1500,
                 3000,
                 'easy',
                 'secondary',
                 '予防保全（preventive maintenance）の原則。少額頻繁の清掃は累積コストを最小化する。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d7466b0e5bc6']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-d7466b0e5bc6-routine-cleaning',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d7466b0e5bc6',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/routine-cleaning',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-d7466b0e5bc6-routine-cleaning']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_tip (\n'
         '        vertex_id, owner_did, sensitivity_ord, tip_id, topic_id,\n'
         '        body_ja, body_en, effectiveness_score, cost_jpy_min, cost_jpy_max,\n'
         '        difficulty, source_url, source_authority, evidence_summary, llm_model,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4,\n'
         '             $5, NULL, $6, $7, $8,\n'
         "             $9, NULL, $10, $11, 'curated',\n"
         "             'active', $12, $13, $14, $15\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_tip WHERE vertex_id = $16)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-6b26e49d4dd9',
                 'did:web:lifehack.etzhayyim.com',
                 'tip-6b26e49d4dd9',
                 'routine-cleaning',
                 '黒い機器は目立つだけで実際のホコリ付着量は色と無関係。色を変えるよりも素材選び（ガラス天板・メラミン化粧板）で帯電しにくい面に切替えるほうが効く。',
                 50,
                 0,
                 0,
                 'easy',
                 'secondary',
                 'プラスチック表面抵抗 vs ガラス表面抵抗の比較。帯電しやすさは素材依存。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-6b26e49d4dd9']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_solves_topic (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'solves',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_solves_topic WHERE edge_id = '
         '$9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-6b26e49d4dd9-routine-cleaning',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-6b26e49d4dd9',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.topic/routine-cleaning',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipSolvesTopic/tip-6b26e49d4dd9-routine-cleaning']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/handy-mop-quickle',
                 'did:web:lifehack.etzhayyim.com',
                 'handy-mop-quickle',
                 '静電ハンディモップ（クイックル系）',
                 '花王 / アズマ',
                 'dust-mop',
                 'commercial',
                 500,
                 1200,
                 'クイックル ハンディ モップ',
                 None,
                 '使い捨てヘッドで衛生的、機器に最も安全。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/handy-mop-quickle']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/silicone-cleaning-putty',
                 'did:web:lifehack.etzhayyim.com',
                 'silicone-cleaning-putty',
                 'シリコンゲル・クリーニングパテ',
                 '汎用',
                 'cleaning-putty',
                 'commercial',
                 500,
                 1000,
                 'シリコン クリーナー パテ キーボード',
                 None,
                 '繰り返し使える、隙間のホコリに最強。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/silicone-cleaning-putty']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/desktop-vacuum-usb',
                 'did:web:lifehack.etzhayyim.com',
                 'desktop-vacuum-usb',
                 '充電式ミニ卓上掃除機',
                 '汎用',
                 'vacuum',
                 'commercial',
                 2000,
                 4000,
                 '卓上 ミニ 掃除機 USB',
                 True,
                 'USB充電、ノズル切替でキーボード隙間も対応。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/desktop-vacuum-usb']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/antistatic-spray-elecom',
                 'did:web:lifehack.etzhayyim.com',
                 'antistatic-spray-elecom',
                 '帯電防止スプレー',
                 'エレコム / サンワサプライ',
                 'antistatic-spray',
                 'commercial',
                 600,
                 1200,
                 'エレコム 帯電防止 スプレー',
                 None,
                 'クロスに吹いてから拭く。月1ルーチン化推奨。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/antistatic-spray-elecom']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/humidifier-room',
                 'did:web:lifehack.etzhayyim.com',
                 'humidifier-room',
                 '加湿器（家庭用、室内湿度50%維持）',
                 '汎用 (シャープ / アイリスオーヤマ等)',
                 'humidifier',
                 'commercial',
                 5000,
                 30000,
                 '加湿器 6畳 ハイブリッド',
                 True,
                 '湿度計を併用して50%維持。冬場の静電気対策の本命。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/humidifier-room']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/ionizer-desktop-hozan',
                 'did:web:lifehack.etzhayyim.com',
                 'ionizer-desktop-hozan',
                 '卓上イオナイザー（HOZAN相当）',
                 'HOZAN / SIMCO / ベッセル',
                 'ionizer',
                 'commercial',
                 10000,
                 30000,
                 '卓上 イオナイザー HOZAN',
                 True,
                 'イオンバランス±35V以下を選定基準に。卓上ホコリ対策にはオーバースペック気味だが手軽。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/ionizer-desktop-hozan']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/air-purifier-hepa',
                 'did:web:lifehack.etzhayyim.com',
                 'air-purifier-hepa',
                 'HEPA空気清浄機（6-8畳用）',
                 'シャープ / ダイキン / パナソニック',
                 'air-purifier',
                 'commercial',
                 20000,
                 50000,
                 '空気清浄機 HEPA 8畳 静音',
                 True,
                 '24時間静音モード固定。机側に吸込口を向ける配置が効く。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/air-purifier-hepa']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/air-duster-can',
                 'did:web:lifehack.etzhayyim.com',
                 'air-duster-can',
                 'エアダスター（缶タイプ）',
                 'サンワサプライ / エレコム',
                 'air-duster',
                 'commercial',
                 600,
                 1500,
                 'エアダスター 缶 PC キーボード',
                 None,
                 '可燃性ガス使用品が多いため換気必須。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/air-duster-can']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/cable-tray',
                 'did:web:lifehack.etzhayyim.com',
                 'cable-tray',
                 'ケーブルトレー / 配線ボックス',
                 'サンワサプライ / IKEA SIGNUM',
                 'cable-tray',
                 'commercial',
                 1500,
                 4000,
                 'ケーブルトレー デスク 下',
                 None,
                 '床から浮かせて配線を集約、掃除工数を10倍下げる。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/cable-tray']},
 {'sql': '\n'
         '      INSERT INTO vertex_lifehack_product (\n'
         '        vertex_id, owner_did, sensitivity_ord, product_id, name, brand, category,\n'
         '        source_type, price_jpy_min, price_jpy_max, amazon_search_keyword, asin, '
         'pse_certified,\n'
         '        tsukuru_cad_model_did, tsukuru_factory_did, tsukuru_production_order_nsid,\n'
         '        estimated_make_cost_jpy, estimated_make_time_hours, notes_ja,\n'
         '        status, created_at, org_id, user_id, actor_id)\n'
         '      SELECT $1, $2, 0, $3, $4, $5, $6,\n'
         '             $7, $8, $9, $10, NULL,\n'
         '             $11,\n'
         '             NULL, NULL, NULL, NULL, NULL, $12,\n'
         "             'active', $13, $14, $15, $16\n"
         '      WHERE NOT EXISTS (SELECT 1 FROM vertex_lifehack_product WHERE vertex_id = $17)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/microfiber-cloth',
                 'did:web:lifehack.etzhayyim.com',
                 'microfiber-cloth',
                 'マイクロファイバークロス',
                 '汎用',
                 'cloth',
                 'commercial',
                 300,
                 1500,
                 'マイクロファイバー クロス 業務用',
                 None,
                 '10枚セットで常備。エアダスターと併用。',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/microfiber-cloth']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-b86cd290507a-handy-mop-quickle',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-b86cd290507a',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/handy-mop-quickle',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-b86cd290507a-handy-mop-quickle']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-faeb28c530cd-silicone-cleaning-putty',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-faeb28c530cd',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/silicone-cleaning-putty',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-faeb28c530cd-silicone-cleaning-putty']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-75bd800d5fe9-desktop-vacuum-usb',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-75bd800d5fe9',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/desktop-vacuum-usb',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-75bd800d5fe9-desktop-vacuum-usb']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-239e07b8e574-humidifier-room',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-239e07b8e574',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/humidifier-room',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-239e07b8e574-humidifier-room']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-10b8c9a7d3d1-antistatic-spray-elecom',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-10b8c9a7d3d1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/antistatic-spray-elecom',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-10b8c9a7d3d1-antistatic-spray-elecom']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-d22c29493612-ionizer-desktop-hozan',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d22c29493612',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/ionizer-desktop-hozan',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-d22c29493612-ionizer-desktop-hozan']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-51b072777188-air-purifier-hepa',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-51b072777188',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/air-purifier-hepa',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-51b072777188-air-purifier-hepa']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-8a322db257ca-air-duster-can',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-8a322db257ca',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/air-duster-can',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-8a322db257ca-air-duster-can']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-8a322db257ca-microfiber-cloth',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-8a322db257ca',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/microfiber-cloth',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-8a322db257ca-microfiber-cloth']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-787a477eb7a2-cable-tray',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-787a477eb7a2',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/cable-tray',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-787a477eb7a2-cable-tray']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-d7466b0e5bc6-handy-mop-quickle',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d7466b0e5bc6',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/handy-mop-quickle',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-d7466b0e5bc6-handy-mop-quickle']},
 {'sql': '\n'
         '      INSERT INTO edge_lifehack_tip_recommends_product (\n'
         '        edge_id, owner_did, sensitivity_ord, src_vid, dst_vid, role,\n'
         '        created_at, org_id, user_id, actor_id)\n'
         "      SELECT $1, $2, 0, $3, $4, 'recommends',\n"
         '             $5, $6, $7, $8\n'
         '      WHERE NOT EXISTS (SELECT 1 FROM edge_lifehack_tip_recommends_product WHERE edge_id '
         '= $9)\n'
         '    ',
  'parameters': ['at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-d7466b0e5bc6-microfiber-cloth',
                 'did:web:lifehack.etzhayyim.com',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tip/tip-d7466b0e5bc6',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.product/microfiber-cloth',
                 '2026-05-08T12:00:00Z',
                 'did:web:lifehack.etzhayyim.com',
                 'did:web:lifehack.etzhayyim.com',
                 'sys.lifehack.seed.phase1',
                 'at://did:web:lifehack.etzhayyim.com/app.etzhayyim.apps.lifehack.tipRecommendsProduct/tip-d7466b0e5bc6-microfiber-cloth']}]

DOWN = [{'sql': 'DELETE FROM edge_lifehack_tip_recommends_product WHERE actor_id = $1',
  'parameters': ['sys.lifehack.seed.phase1']},
 {'sql': 'DELETE FROM edge_lifehack_tip_solves_topic       WHERE actor_id = $1',
  'parameters': ['sys.lifehack.seed.phase1']},
 {'sql': 'DELETE FROM vertex_lifehack_product               WHERE actor_id = $1',
  'parameters': ['sys.lifehack.seed.phase1']},
 {'sql': 'DELETE FROM vertex_lifehack_tip                   WHERE actor_id = $1',
  'parameters': ['sys.lifehack.seed.phase1']},
 {'sql': 'DELETE FROM vertex_lifehack_topic                 WHERE actor_id = $1',
  'parameters': ['sys.lifehack.seed.phase1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
