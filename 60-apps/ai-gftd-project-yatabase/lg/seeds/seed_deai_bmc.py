"""One-shot seed: deai.gftd.ai Business Model Canvas + Lean hypotheses.

Usage (from lg/ directory):
    RW_URL=postgres://... python seeds/seed_deai_bmc.py

Re-running is safe: bmcAppendState always appends a new version (v+1),
and bmcAddHypothesis is a no-op if the slug PK already exists (PK
re-INSERT in RW = implicit upsert / ignore on conflict).
"""

from __future__ import annotations

import asyncio
import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from lg_yatabase.bmc import repository
from lg_yatabase.bmc.db import close_pool, execute, fetchval

ORG_DID = "did:web:deai.gftd.ai"
ACTOR_DID = "did:web:deai.gftd.ai"
AUTHORED_BY = "jun@gftd.group"

# ── BMC canvas (9 blocks + 5 Lean-Canvas extensions) ───────────────────
CANVAS: dict = {
    "key_partners": {
        "bullets": [
            "Hume AI — 表情・音声感情解析 API",
            "Niigata Univ. / Aarhus Univ. — 共同研究機関",
            "spirit-in-physics.com — 研究 SSoT・データ受信先",
            "etzhayyim — 運営法人 (alias: etzhayyim / 天御柱)",
            "Apple / Google — App Store 配信",
        ],
        "notes": "Hume AI が最大コスト変数。volume discount 交渉は DAU 5k 到達後。",
    },
    "key_activities": {
        "bullets": [
            "Jung 語連想実験 (100語→20語/セッション) のオンライン実施",
            "Hume AI 表情・音声スコアリングパイプライン",
            "Spirit Type 分類 (Hero/Sage/Lover/Caregiver) + 感情ベクトル計算",
            "テンセグリティ RBF カーネルマッチング (W_ij = exp(-||e_i-e_j||²/2σ²))",
            "研究データ品質管理・spirit-in-physics.com へのリアルタイム送信",
            "匿名コホート DID 管理 (PII 非保持)",
        ],
        "notes": None,
    },
    "key_resources": {
        "bullets": [
            "Spirit-in-Physics 理論 + 測定式 (Kawasaki et al. 2026) — 特許化候補",
            "Jung 語連想 × 生体計測データセット (累積・競合再現不可)",
            "AT Protocol / RisingWave / Capacitor インフラ",
            "Hume AI 処理パイプライン (WebM 後処理 + WS リアルタイム)",
            "Cohort DID 匿名化設計 — PII 非保持",
        ],
        "notes": None,
    },
    "value_props": {
        "bullets": [
            "魂の共鳴を熱力学で測る — スワイプ不要の深い出会い",
            "Jung 語連想実験参加が自己理解 + 研究貢献に直結",
            "Spirit Type 診断による自己発見 (Hero/Sage/Lover/Caregiver)",
            "感情テンセグリティ共鳴スコアによる科学的マッチング",
            "PII 非保持・Cohort DID 匿名性 — 安心してデータ提供できる",
        ],
        "notes": "研究参加フレーミングが参加意欲を高め、PII 不要設計が心理的抵抗を下げる。",
    },
    "customer_relationships": {
        "bullets": [
            "SPA + Capacitor アプリ (自動化、非対人)",
            "毎日の Spirit Check-in による習慣化",
            "マッチング通知 (E2E 暗号化 DM) による関係継続",
            "研究フィードバック (researcher.spirit-in-physics.com へのリンク)",
        ],
        "notes": None,
    },
    "channels": {
        "bullets": [
            "deai.gftd.ai Web SPA (Phase 1)",
            "iOS / Android Capacitor アプリ (Phase 2)",
            "Bluesky / X — 研究 PR・口コミ",
            "論文・学術カンファレンス (spirit-in-physics.com)",
            "大学・研究機関パートナーシップ (Phase 3)",
        ],
        "notes": None,
    },
    "customer_segments": {
        "bullets": [
            "一次: 20-35 歳・深い関係を求める日本人シングル (研究参加者)",
            "アーリーアダプター: 心理学・自己分析好き・研究貢献意識が高い層",
            "二次: 感情熱力学・行動科学研究者 (spirit-in-physics.com 経由)",
            "将来 B2B: HR・ウェルネス企業 (感情適性診断 API)",
        ],
        "notes": "研究参加インセンティブが出会い目的ユーザーの質を高める。",
    },
    "cost_structure": {
        "bullets": [
            "Hume AI API 従量課金 (推定 $0.10/セッション — 最大変動費)",
            "Cloudflare Workers / Vultr K8s (固定 + 従量)",
            "iOS/Android App Store 年会費 + 手数料 30%",
            "研究・論文制作・IRB/倫理審査コスト",
            "spirit-in-physics.com API 維持・連携開発",
        ],
        "notes": "WebM 後処理バッチ化で Hume API 単価を削減 (現在実装済み)。",
    },
    "revenue_streams": {
        "bullets": [
            "Freemium: 診断・基本マッチング無料",
            "Premium サブスク: 無制限マッチング + 詳細感情レポート (¥980/月 / ¥6,800/年)",
            "研究データ B2B ライセンス: 匿名コホートデータ販売",
            "感情適性診断 API: HR・ウェルネス SaaS (Phase 3)",
        ],
        "notes": "短期は Premium サブスク。中長期はデータ資産の B2B 展開。",
    },
    # ── Lean Canvas extensions ────────────────────────────────────────
    "problem": {
        "bullets": [
            "既存マッチングアプリは外見・プロフィールの表層マッチング → 高 separation entropy",
            "自分の深い感情パターン・心理傾向を客観把握する手段がない",
            "感情データ提供に対する心理的抵抗 (なぜデータを渡すのか不透明)",
        ],
        "notes": "代替: Tinder/Bumble/Pairs (スワイプ), 16Personalities (診断のみ)。",
    },
    "solution": {
        "bullets": [
            "Jung 語連想 20語 × Hume AI 感情解析 × Spirit-in-Physics 熱力学マッチング",
            "反応時間・表情・音声から深層感情ベクトルを測定",
            "テンセグリティ共鳴スコアで最適ペアを算出 — 研究参加が直接マッチングに繋がる",
        ],
        "notes": None,
    },
    "unique_value_prop": {
        "bullets": [
            "「魂の共鳴を、熱力学で測る」",
            "スワイプではなく科学実験に参加することで出会う",
            "研究データ提供 = 参加インセンティブ → 倫理的・透明なデータ収集",
        ],
        "notes": None,
    },
    "unfair_advantage": {
        "bullets": [
            "Kawasaki et al. 2026 論文 + Spirit Type 測定式 (特許化候補)",
            "蓄積する感情 × 反応時間データセット (競合が短期間で再現不可)",
            "AT Protocol / Cohort DID による匿名性設計 (PII 非保持)",
        ],
        "notes": None,
    },
    "key_metrics": {
        "bullets": [
            "実験完了率 (consent → 20語完走) > 70%",
            "7日リテンション率 > 30%",
            "平均マッチング共鳴スコア > 700/1000",
            "完了アセスメント数 (30日) > 500",
            "Premium 転換率 > 5% (Phase 2 以降)",
        ],
        "notes": "Phase 1 KPI: 完了率 + アセスメント数。Phase 2 以降: リテンション + Premium 転換。",
    },
}

# ── Hypotheses (Lean Build-Measure-Learn) ──────────────────────────────
HYPOTHESES = [
    {
        "slug": "deai-experiment-completion-rate",
        "block": "key_metrics",
        "statement": "語連想実験の完了率 (consent → 20語完走) が 70% 以上になる",
        "metric": "completion_rate",
        "metric_query": "sql:vertex_deai_session_completion_rate:30d",
        "threshold": 0.70,
        "baseline": 0.0,
        "deadline_iso": "2026-08-01T00:00:00Z",
        "min_sample": 50,
        "auto_apply_pivot": False,
    },
    {
        "slug": "deai-retention-7d",
        "block": "key_metrics",
        "statement": "7日リテンション率 (実験完了者の翌週チェックイン率) が 30% 以上になる",
        "metric": "retention_7d",
        "metric_query": "sql:vertex_deai_retention_7d",
        "threshold": 0.30,
        "baseline": 0.0,
        "deadline_iso": "2026-09-01T00:00:00Z",
        "min_sample": 100,
        "auto_apply_pivot": False,
    },
    {
        "slug": "deai-match-resonance-avg",
        "block": "value_props",
        "statement": "平均マッチング共鳴スコアが 700/1000 以上になる (テンセグリティ品質の検証)",
        "metric": "resonance_avg",
        "metric_query": "sql:vertex_deai_match_resonance_avg:30d",
        "threshold": 700.0,
        "baseline": 0.0,
        "deadline_iso": "2026-08-01T00:00:00Z",
        "min_sample": 30,
        "auto_apply_pivot": False,
    },
    {
        "slug": "deai-assessment-count-30d",
        "block": "customer_segments",
        "statement": "月間完了アセスメント数が 500 件を超える (市場規模検証)",
        "metric": "assessment_count",
        "metric_query": "sql:vertex_deai_assessment_count:30d",
        "threshold": 500.0,
        "baseline": 0.0,
        "deadline_iso": "2026-10-01T00:00:00Z",
        "min_sample": 1,
        "auto_apply_pivot": False,
    },
    {
        "slug": "deai-hume-data-quality",
        "block": "key_activities",
        "statement": "Hume 感情スコアの標準偏差が語ごとに < 300/1000 (計測ノイズ検証)",
        "metric": "hume_stddev_ratio",
        "metric_query": "sql:vertex_deai_assessment_count:7d",
        "threshold": 10.0,
        "baseline": 0.0,
        "deadline_iso": "2026-07-01T00:00:00Z",
        "min_sample": 20,
        "auto_apply_pivot": False,
    },
]


async def main() -> None:
    print(f"[seed] org_did={ORG_DID}")

    # 1. Seed canvas
    canvas_json = json.dumps(CANVAS, ensure_ascii=False)
    result = await repository.append_state(
        canvas_json=canvas_json,
        rationale="deai.gftd.ai v1 初期 BMC — Spirit-in-Physics 研究 × マッチングアプリ (seed)",
        source="seed",
        actor_did=ACTOR_DID,
        org_did=ORG_DID,
        created_by=AUTHORED_BY,
    )
    print(f"[seed] canvas appended: vertex_id={result['vertex_id']} version={result['version']}")

    # 2. Seed hypotheses — direct INSERT to handle clusters where vertex_bmc_hypothesis
    # has a legacy NOT NULL `status` column (RisingWave ≥v2.7 cannot SET DEFAULT/DROP NOT NULL).
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    has_status_col = bool(await fetchval(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='vertex_bmc_hypothesis' AND column_name='status' LIMIT 1"
    ))
    has_updated_at = bool(await fetchval(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='vertex_bmc_hypothesis' AND column_name='updated_at' LIMIT 1"
    ))

    for hyp in HYPOTHESES:
        vid = f"bmc:hyp:{hyp['slug']}"
        try:
            if has_status_col:
                # Legacy schema has NOT NULL status + updated_at (no SET DEFAULT in RisingWave)
                extra_cols = ""
                extra_vals = ""
                if has_updated_at:
                    extra_cols = ", updated_at"
                    extra_vals = ", $16"
                await execute(
                    f"""
                    INSERT INTO vertex_bmc_hypothesis
                      (vertex_id, slug, block, statement, metric, metric_query,
                       threshold, baseline, deadline_iso, min_sample,
                       authored_by, auto_apply_pivot,
                       sensitivity_ord, owner_did, actor_did, org_did, at_did,
                       status, created_at{extra_cols})
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,1,$13,$13,$14,NULL,'pending',$15{extra_vals})
                    """,
                    vid, hyp["slug"], hyp["block"], hyp["statement"],
                    hyp["metric"], hyp["metric_query"],
                    hyp["threshold"], hyp["baseline"], hyp["deadline_iso"],
                    hyp["min_sample"], AUTHORED_BY,
                    1 if hyp["auto_apply_pivot"] else 0,
                    ACTOR_DID, ORG_DID, now,
                    *(([now] if has_updated_at else [])),
                )
            else:
                r = await repository.add_hypothesis(
                    slug=hyp["slug"], block=hyp["block"], statement=hyp["statement"],
                    metric=hyp["metric"], metric_query=hyp["metric_query"],
                    threshold=hyp["threshold"], baseline=hyp["baseline"],
                    deadline_iso=hyp["deadline_iso"], min_sample=hyp["min_sample"],
                    authored_by=AUTHORED_BY, auto_apply_pivot=hyp["auto_apply_pivot"],
                    actor_did=ACTOR_DID, org_did=ORG_DID,
                )
                vid = r["vertex_id"]
            print(f"[seed] hypothesis added: {hyp['slug']} → {vid}")
        except Exception as e:
            print(f"[seed] hypothesis skip (already exists?): {hyp['slug']} — {e}")

    await close_pool()
    print("[seed] done.")


if __name__ == "__main__":
    asyncio.run(main())
