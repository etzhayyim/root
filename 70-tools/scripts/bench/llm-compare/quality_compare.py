#!/usr/bin/env python3
"""
Quality-focused LLM comparison: coding, BPMN, translation, doc creation, QA, long text.

Usage:
  python quality_compare.py --model qwen3-32b
  python quality_compare.py --model gemma4-31b
  python quality_compare.py --model deepseek-r1-32b
  python quality_compare.py --model claude-sonnet-4-6
  python quality_compare.py --report   # print formatted report
"""

import argparse
import json
import os
import time
import textwrap
from datetime import datetime
from pathlib import Path

import openai

RESULTS_FILE = Path(__file__).parent / "quality_results.jsonl"
MAX_TOKENS = 1024

PROMPTS = [
    {
        "id": "qa_logic",
        "category": "QA/推論",
        "prompt": (
            "以下の論理問題を解いてください。\n\n"
            "田中・鈴木・佐藤・山田・中村の5人が会議に参加しています。\n"
            "条件:\n"
            "1. 田中は鈴木より先に発言する\n"
            "2. 佐藤は山田の直後に発言する\n"
            "3. 中村は最初でも最後でもない\n"
            "4. 山田は田中より前に発言する\n"
            "5. 鈴木は最後に発言する\n\n"
            "発言順を全員分答え、各条件がどう満たされているか日本語で説明してください。"
        ),
    },
    {
        "id": "coding_ts",
        "category": "コーディング",
        "prompt": (
            "TypeScriptで以下の関数を実装してください。\n\n"
            "```\n"
            "function deepMerge<T extends object>(target: T, ...sources: Partial<T>[]): T\n"
            "```\n\n"
            "要件:\n"
            "- ネストされたオブジェクトを再帰的にマージ\n"
            "- 配列はconcatではなく上書き\n"
            "- nullやundefinedは無視\n"
            "- 循環参照を検出してエラーをthrow\n"
            "- 型安全にする\n\n"
            "実装と、エッジケースを含むテストケース(Jest形式)を書いてください。"
        ),
    },
    {
        "id": "bpmn_order",
        "category": "BPMN",
        "prompt": (
            "以下の受発注プロセスのBPMN 2.0 XML を生成してください。\n\n"
            "プロセス:\n"
            "1. 顧客が注文を送信\n"
            "2. 在庫確認（並行して与信チェックも実行）\n"
            "3. 在庫あり かつ 与信OK → 注文確定 → 請求書発行 → 発送準備 → 完了\n"
            "4. 在庫なし → 欠品メール送信 → 入荷待ちタスク → 在庫確認に戻る\n"
            "5. 与信NG → 却下メール送信 → 終了\n\n"
            "valid な BPMN 2.0 XML (namespace含む) を出力してください。"
        ),
    },
    {
        "id": "translation_jp_en",
        "category": "翻訳 (JP→EN)",
        "prompt": (
            "以下の日本語ビジネス文書を自然なビジネス英語に翻訳してください。\n\n"
            "---\n"
            "拝啓 時下ますますご清栄のこととお慶び申し上げます。\n\n"
            "このたびは弊社のAIソリューション導入提案書をお送りさせていただきます。"
            "貴社の製造ライン品質管理業務における課題解決に向け、"
            "画像認識AIと自然言語処理を組み合わせた独自のアプローチを提案いたします。\n\n"
            "本提案により、検査工程の自動化率を現状比30%向上させ、"
            "不良品検出精度を99.2%以上に引き上げることが可能と試算しております。"
            "初期投資回収期間は18ヶ月を見込んでおり、ROIは3年で240%を達成できる見通しです。\n\n"
            "ご多忙のところ誠に恐縮ではございますが、"
            "ご検討いただけますと幸甚に存じます。何卒よろしくお願い申し上げます。\n"
            "敬具\n"
            "---"
        ),
    },
    {
        "id": "long_text_summary",
        "category": "長文処理",
        "prompt": (
            "以下の技術文書を読み、(1)3行要約、(2)重要な技術的決定とその根拠、"
            "(3)潜在的なリスクと対策、の3セクションで分析してください。\n\n"
            "---\n"
            "システム移行計画書 v2.1\n\n"
            "現行システムはオンプレミスのOracle Database 11g上で動作する基幹業務システムであり、"
            "2025年末にサポート終了を迎える。移行先としてPostgreSQL 16 on AWS RDSを選定した。"
            "選定理由は(1)ライセンスコスト削減(年間約800万円)、(2)マネージドサービスによる運用負荷軽減、"
            "(3)Aurora PostgreSQLへの将来的な移行パスの確保である。\n\n"
            "移行方式はBig Bang方式を採用する。段階的移行も検討したが、"
            "Oracle固有のストアドプロシージャが200本以上あり、"
            "並行稼働期間中のデータ整合性確保が技術的に困難と判断した。"
            "移行ウィンドウは2025年8月13日(水)22:00〜8月14日(木)06:00の8時間を予定している。\n\n"
            "データ移行はpg_dumpおよびAWS Database Migration Serviceを組み合わせて使用する。"
            "本番移行前に4回のリハーサルを実施し、切り戻し手順も整備する。"
            "切り戻し判断タイムリミットは移行開始から5時間後(翌3:00)とし、"
            "それ以降は前進することとする。\n\n"
            "性能要件として、現行比でレスポンスタイムの劣化を10%以内に抑えることを目標とする。"
            "Oracleの分析関数やヒント句の代替実装、接続プーリングの最適化が課題として残っている。\n"
            "---"
        ),
    },
    {
        "id": "doc_creation",
        "category": "文書作成",
        "prompt": (
            "以下の要件に基づき、社内向けの技術標準ドキュメントを作成してください。\n\n"
            "テーマ: 社内AIエージェント開発ガイドライン\n"
            "対象読者: バックエンドエンジニア\n"
            "必須セクション:\n"
            "1. エージェント設計原則(3〜5項目)\n"
            "2. ツール定義の標準形式(コード例付き)\n"
            "3. エラーハンドリングポリシー\n"
            "4. セキュリティチェックリスト\n"
            "5. レビュー基準\n\n"
            "Markdownで、実際に使えるレベルの具体的な内容で書いてください。"
        ),
    },
]

DEFAULT_MODEL = "gemma4-31b"

MODEL_CONFIGS = {
    "qwen3-32b":       {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "gemma4-31b":      {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "deepseek-r1-32b": {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "claude-sonnet-4-6": {
        "base_url": "https://api.anthropic.com/v1",
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
    },
}

DIVIDER = "=" * 72


def run_prompt(client: openai.OpenAI, model_name: str, prompt: str) -> dict:
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=0.0,
        )
        elapsed = time.perf_counter() - t0
        content = resp.choices[0].message.content or ""
        usage = resp.usage
        return {
            "ok": True,
            "content": content,
            "elapsed_sec": round(elapsed, 3),
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "elapsed_sec": round(time.perf_counter() - t0, 3)}


def strip_think(text: str) -> str:
    """Remove <think>...</think> blocks for display."""
    import re
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def run_model(model_key: str) -> None:
    cfg = MODEL_CONFIGS.get(model_key)
    if not cfg:
        print(f"Unknown model: {model_key}. Available: {list(MODEL_CONFIGS)}")
        return

    if model_key == "claude-sonnet-4-6" and not cfg["api_key"]:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    print(f"\n{DIVIDER}")
    print(f"Model: {model_key}  |  {datetime.now().isoformat()}")
    print(DIVIDER)

    for p in PROMPTS:
        print(f"\n[{p['id']}] ({p['category']}) ", end="", flush=True)
        result = run_prompt(client, model_key, p["prompt"])

        if result["ok"]:
            tokens = result.get("completion_tokens") or "?"
            print(f"{result['elapsed_sec']}s  {tokens} tok")
            preview = strip_think(result["content"])[:400]
            print(textwrap.indent(preview + ("…" if len(strip_think(result["content"])) > 400 else ""), "  "))
        else:
            print(f"ERROR: {result['error']}")

        row = {
            "model": model_key,
            "prompt_id": p["id"],
            "category": p["category"],
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        with RESULTS_FILE.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_report() -> None:
    if not RESULTS_FILE.exists():
        print("No results yet.")
        return

    rows = [json.loads(l) for l in RESULTS_FILE.read_text().splitlines() if l.strip()]
    models = sorted({r["model"] for r in rows})
    prompts = [p["id"] for p in PROMPTS]

    # Timing table
    print(f"\n{DIVIDER}")
    print("TIMING (seconds)")
    print(DIVIDER)
    header = f"{'prompt':<25}" + "".join(f"{m:<22}" for m in models)
    print(header)
    print("-" * len(header))
    for pid in prompts:
        line = f"{pid:<25}"
        for m in models:
            match = [r for r in rows if r["model"] == m and r["prompt_id"] == pid]
            val = f"{match[-1]['elapsed_sec']}s" if match and match[-1]["ok"] else ("ERR" if match else "-")
            line += f"{val:<22}"
        print(line)

    # Full responses per prompt
    for p in PROMPTS:
        pid = p["id"]
        print(f"\n{'='*72}")
        print(f"PROMPT: [{pid}] {p['category']}")
        print(f"{'='*72}")
        for m in models:
            match = [r for r in rows if r["model"] == m and r["prompt_id"] == pid]
            if not match:
                continue
            r = match[-1]
            print(f"\n--- {m} ({r['elapsed_sec']}s) ---")
            if r["ok"]:
                print(strip_think(r["content"]))
            else:
                print(f"ERROR: {r.get('error')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model key to run (default: gemma4-31b)")
    parser.add_argument("--report", action="store_true", help="Print full quality report")
    args = parser.parse_args()

    if args.report:
        print_report()
    else:
        run_model(args.model)
