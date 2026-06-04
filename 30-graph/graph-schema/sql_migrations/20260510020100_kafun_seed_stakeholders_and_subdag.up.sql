-- Seed real Japanese stakeholders + extend the topo DAG with the
-- satellite→canopy→parcel→landowner→outreach sub-chain.
--
-- Stakeholder seed (~30 行): central ministries, national associations,
-- key research institutions, sample prefecture-level forest cooperative
-- federations, major private forestry corps, patient/medical groups.
-- Specific contact_email left blank — to be populated when public listings
-- are imported (NOT scraped from web; only published email addresses).
--
-- Sub-DAG extension (5 nodes): L0-1a..L0-1d satellite imagery pipeline +
-- L1-0 stakeholder outreach. L1-1 (無花粉苗木) and L3-1 (主伐再造林) become
-- soft-dependent on L1-0 since execution requires landowner agreements.

-- ─────────────────────────────────────────────────────────────────────────
-- Central ministries
-- ─────────────────────────────────────────────────────────────────────────
INSERT INTO vertex_kafun_stakeholder (vertex_id, _seq, sensitivity_ord, kind, name, name_en, jurisdiction_iso, role_in_dag, website, created_at) VALUES
('did:web:n97ik10n.etzhayyim.com/stakeholder/maff-rinya',           0, 0, 'ministry',           '林野庁',                          'Forestry Agency',                                 'JP', 'capacity:L1-1,execution:L3-1', 'https://www.rinya.maff.go.jp', '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/maff-rinmoku-ikushu',  0, 0, 'central_agency',     '林木育種センター (FFPRI)',         'Forest Tree Breeding Center',                     'JP', 'capacity:L0-4,L1-1',           'https://www.ffpri.affrc.go.jp/research/dept/ftbc/',           '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/moe',                  0, 0, 'ministry',           '環境省',                          'Ministry of the Environment',                     'JP', 'evidence:L0-2',                 'https://www.env.go.jp',           '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/mhlw',                 0, 0, 'ministry',           '厚生労働省',                       'Ministry of Health, Labour and Welfare',          'JP', 'funding:L2-3,evidence:L0-3',   'https://www.mhlw.go.jp',          '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/mext',                 0, 0, 'ministry',           '文部科学省',                       'Ministry of Education, Culture, Sports, Science and Technology', 'JP', 'evidence:L0-3,capacity:L1-3', 'https://www.mext.go.jp', '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/mlit',                 0, 0, 'ministry',           '国土交通省',                       'Ministry of Land, Infrastructure, Transport and Tourism', 'JP', 'evidence:L0-1', 'https://www.mlit.go.jp', '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/cao',                  0, 0, 'central_agency',     '内閣府',                          'Cabinet Office (花粉症対策実行計画)',              'JP', 'funding:L2-1',                 'https://www.cao.go.jp',           '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/maff-affrc',           0, 0, 'research_institute', '森林総合研究所 (FFPRI)',           'Forestry and Forest Products Research Institute', 'JP', 'evidence:L0-1,L0-4',           'https://www.ffpri.affrc.go.jp',   '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/jica-forestry',        0, 0, 'research_institute', '国際協力機構 林業セクター',         'JICA Forestry Sector',                            'JP', 'capacity:L1-2',                 'https://www.jica.go.jp',          '2026-05-10T00:00:00Z'),

-- ─────────────────────────────────────────────────────────────────────────
-- Industry associations / national federations
-- ─────────────────────────────────────────────────────────────────────────
('did:web:n97ik10n.etzhayyim.com/stakeholder/zenmori',              0, 0, 'forest_coop_fed',    '全国森林組合連合会',               'National Federation of Forest Owners Coop. Assoc.','JP', 'capacity:L1-2,execution:L3-1','https://www.zenmori.org',          '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/jfa',                  0, 0, 'industry_assoc',     '日本林業協会',                     'Japan Forestry Association',                       'JP', 'capacity:L1-5',                 'https://www.j-fa.or.jp',          '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/jclt',                 0, 0, 'industry_assoc',     '日本CLT協会',                      'Japan CLT Association',                            'JP', 'capacity:L1-5',                 'https://clta.jp',                 '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/jws',                  0, 0, 'industry_assoc',     '日本木材総合情報センター',           'Japan Wood-Products Information Center',           'JP', 'capacity:L1-5',                 'https://www.jawic.or.jp',         '2026-05-10T00:00:00Z'),

-- ─────────────────────────────────────────────────────────────────────────
-- Patient / medical groups
-- ─────────────────────────────────────────────────────────────────────────
('did:web:n97ik10n.etzhayyim.com/stakeholder/jsa-allergy',          0, 0, 'academic_society',   '日本アレルギー学会',                'Japanese Society of Allergology',                  'JP', 'capacity:L1-4,evidence:L0-3', 'https://www.jsaweb.jp',           '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/jibi',                 0, 0, 'academic_society',   '日本耳鼻咽喉科学会',                'Oto-Rhino-Laryngological Society of Japan',        'JP', 'capacity:L1-4',                 'https://www.jibika.or.jp',        '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/kafun-society',        0, 0, 'patient_group',      '日本花粉症協会',                   'Japan Hay Fever Association (Pollen)',             'JP', 'evidence:L0-3',                 NULL,                              '2026-05-10T00:00:00Z'),

-- ─────────────────────────────────────────────────────────────────────────
-- Major private forestry corporations
-- ─────────────────────────────────────────────────────────────────────────
('did:web:n97ik10n.etzhayyim.com/stakeholder/sumitomo-forestry',    0, 0, 'private_corp',       '住友林業',                         'Sumitomo Forestry',                                'JP', 'capacity:L1-1,L1-2,L1-5',     'https://sfc.jp',                   '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/oji-green',            0, 0, 'private_corp',       '王子グリーンリソース',              'Oji Green Resources',                              'JP', 'capacity:L1-2,L1-5',           'https://www.ojigreenresources.com','2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/mitsui-forest',        0, 0, 'private_corp',       '三井物産フォレスト',                'Mitsui Bussan Forest',                             'JP', 'capacity:L1-2,L1-5',           'https://www.mitsuibussan-forest.co.jp', '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/chugoku-mokuzai',      0, 0, 'private_corp',       '中国木材',                         'Chugoku Lumber',                                   'JP', 'capacity:L1-5',                 'https://www.chugokumokuzai.co.jp', '2026-05-10T00:00:00Z'),

-- ─────────────────────────────────────────────────────────────────────────
-- Sample prefecture-level cooperative federations (Tokyo/Kanto + Shizuoka, where sugi is dense)
-- ─────────────────────────────────────────────────────────────────────────
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-tokyo',     0, 0, 'forest_coop_fed',    '東京都森林組合連合会',               'Tokyo Pref. Forest Owners Coop. Federation',      'JP-13', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-kanagawa',  0, 0, 'forest_coop_fed',    '神奈川県森林組合連合会',             'Kanagawa Pref. Forest Owners Coop. Federation',   'JP-14', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-saitama',   0, 0, 'forest_coop_fed',    '埼玉県森林組合連合会',               'Saitama Pref. Forest Owners Coop. Federation',    'JP-11', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-chiba',     0, 0, 'forest_coop_fed',    '千葉県森林組合連合会',               'Chiba Pref. Forest Owners Coop. Federation',      'JP-12', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-shizuoka',  0, 0, 'forest_coop_fed',    '静岡県森林組合連合会',               'Shizuoka Pref. Forest Owners Coop. Federation',   'JP-22', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-yamanashi', 0, 0, 'forest_coop_fed',    '山梨県森林組合連合会',               'Yamanashi Pref. Forest Owners Coop. Federation',  'JP-19', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-tochigi',   0, 0, 'forest_coop_fed',    '栃木県森林組合連合会',               'Tochigi Pref. Forest Owners Coop. Federation',    'JP-09', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-gunma',     0, 0, 'forest_coop_fed',    '群馬県森林組合連合会',               'Gunma Pref. Forest Owners Coop. Federation',      'JP-10', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-ibaraki',   0, 0, 'forest_coop_fed',    '茨城県森林組合連合会',               'Ibaraki Pref. Forest Owners Coop. Federation',    'JP-08', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z'),
('did:web:n97ik10n.etzhayyim.com/stakeholder/forestcoop-nagano',    0, 0, 'forest_coop_fed',    '長野県森林組合連合会',               'Nagano Pref. Forest Owners Coop. Federation',     'JP-20', 'execution:L3-1,L1-2',         NULL, '2026-05-10T00:00:00Z');

-- ─────────────────────────────────────────────────────────────────────────
-- Topo DAG extension: 5 sub-nodes
-- ─────────────────────────────────────────────────────────────────────────
INSERT INTO vertex_agent_topo_node (vertex_id, _seq, sensitivity_ord, app_did, node_id, layer, category, title, description, status, bottleneck_rank, kpi_weight, target_metric, target_value, target_unit, owner_actor_did, created_at) VALUES
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1a', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-1a', 0, 'evidence', '衛星画像取り込み',       'Sentinel-2 / ALOS / ASTER tile を B2 に取り込み',          'planned', 0, 0.6, 'satellite_tiles_ingested', 50000, 'tiles', 'did:web:n97ik10n.etzhayyim.com:actor:scout',     '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1b', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-1b', 0, 'evidence', 'スギ・ヒノキ canopy 検出',  'ML 検出器で sugi/hinoki canopy polygon を生成',            'planned', 0, 0.7, 'canopy_segments_detected', 1000000, 'segments', 'did:web:n97ik10n.etzhayyim.com:actor:scout',     '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1c', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-1c', 0, 'evidence', 'canopy → 地番 (parcel) 紐付け','MLIT 国土数値情報 + 法務省登記で parcel ↔ canopy resolve',   'planned', 0, 0.7, 'attributed_canopy_pct',     90, '%',        'did:web:n97ik10n.etzhayyim.com:actor:cadastral', '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1d', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L0-1d', 0, 'evidence', '地主 (landowner) 解決',     'parcel → 国/県/市町村/民有 に分解、民有はLEI/連絡先まで',   'planned', 0, 0.8, 'landowners_identified',     50000, 'owners', 'did:web:n97ik10n.etzhayyim.com:actor:cadastral', '2026-05-10T00:00:00Z'),
  ('at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-0', 0, 0, 'did:web:n97ik10n.etzhayyim.com', 'L1-0', 1, 'capacity', 'Stakeholder outreach',    '林野庁・連合会・大手林業 etc に envoy DID 経由で接触',         'planned', 0, 0.9, 'in_dialogue_count',         200, 'orgs',  'did:web:n97ik10n.etzhayyim.com:actor:envoy',     '2026-05-10T00:00:00Z');

-- Sub-DAG dependency edges:
--   L0-1a → (none)         leaf
--   L0-1b → L0-1a          (canopy detection needs imagery)
--   L0-1c → L0-1b          (parcel binding needs canopy polygons)
--   L0-1d → L0-1c          (landowner resolution needs parcel attribution)
--   L1-0  → L0-1d          (outreach can only target identified owners)
--   L1-1  → L1-0  soft     (nursery scaling is helped by outreach but not blocked)
--   L3-1  → L1-0  hard     (主伐再造林 cannot proceed without landowner agreements)
INSERT INTO edge_agent_topo_depends (edge_id, _seq, sensitivity_ord, src_vid, dst_vid, dep_kind, weight, created_at) VALUES
  ('L0-1b->L0-1a', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1b', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1a', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L0-1c->L0-1b', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1c', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1b', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L0-1d->L0-1c', 0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1d', 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1c', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L1-0->L0-1d',  0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-0',  'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L0-1d', 'hard', 1.0, '2026-05-10T00:00:00Z'),
  ('L1-1->L1-0',   0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-1',  'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-0',  'soft', 0.5, '2026-05-10T00:00:00Z'),
  ('L3-1->L1-0',   0, 0, 'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L3-1',  'at://did:web:n97ik10n.etzhayyim.com/com.etzhayyim.agent.topoNode/L1-0',  'hard', 1.0, '2026-05-10T00:00:00Z');

-- L0-1 (existing parent) becomes complete when all sub-nodes are done — represented by
-- adding it as the parent via concerns edges. (Not changing its status here; the agent
-- can mark it 'done' once all sub-nodes are 'done'.)
