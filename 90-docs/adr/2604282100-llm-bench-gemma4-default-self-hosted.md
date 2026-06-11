---
id: adr-2604282100
title: LLM self-host benchmark — Gemma4-31B を既定の self-hosted 推論モデルに採用
status: active
doc_type: adr
topic: inference
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - self-hosted LLM model selection
  - RunPod inference compute layout
  - 70-tools/scripts/bench/llm-compare
related:
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-0050
supersedes: []
superseded_by: []
---

# Context

Murakumo mac mini fleet (Ollama + LiteLLM) は gemma4:e2b / e4b (Edge 2B/4B) を常時稼働させているが、
32B クラスの高品質モデルを必要とするタスク（BPMN 生成・長文文書作成・多言語翻訳）での品質が不十分。
RTX 6000 Ada (48GB VRAM) で動く self-hosted 32B モデルの品質比較が必要だった。

RunPod EU-SE-1 に RTX A6000 48GB Secure Cloud pod (`ptn9xaa58xhhxp`, $0.49/hr) を一時的に立て、
以下の 4 モデルをベンチマーク実施（2026-04-28）。

| モデル | 量子化 | VRAM | バックエンド |
|---|---|---|---|
| Qwen3-32B | AWQ 4-bit | ~18 GB | vLLM |
| Gemma4-31B-IT | compressed-tensors 4-bit | ~18 GB | vLLM |
| DeepSeek-R1-Distill-Qwen-32B | AWQ 4-bit | ~18 GB | vLLM |
| Llama 4 Scout 17B-16E | GGUF IQ3_XS | ~45 GB | llama.cpp |

速度ベンチ（5 prompts: reasoning/code/JP-summary/instruction/creative）と
品質ベンチ（6 prompts: QA推論/TypeScript/BPMN/翻訳/長文処理/文書作成）を実施。
Claude Sonnet 4.6（本会話自体）を gold standard として比較。

# Decision

**Gemma4-31B-IT (compressed-tensors 4-bit) を self-hosted 32B 推論モデルの既定として採用する。**

vLLM 0.19.1 + torch 2.6.0+cu124 + flashinfer cu124 の組み合わせで RTX A6000 / RTX 6000 Ada 上で安定動作確認済み。
量子化形式は `compressed-tensors`（config 自動検出）— `--quantization awq_marlin` を渡さないこと。

コンピュート: `comfyui-etzhayyim-6000ada` pod (RTX 6000 Ada, 48GB, $0.77/hr, `r127r1ab2arjg8`) に
vLLM を co-locate する（ComfyUI と VRAM 分離、合計 ~36GB 以内）。

ベンチマークスクリプト: `70-tools/scripts/bench/llm-compare/` (serve.sh / compare.py / quality_compare.py)
— `--model` 省略時のデフォルトは `gemma4-31b`。

# Consequences

**速度（RTX A6000 上、temperature=0, max_tokens=512）**

| タスク | Gemma4-31B | Qwen3-32B | DeepSeek-R1-32B |
|---|---|---|---|
| QA/推論 | 15.8s | 32.7s | 2.3s (誤回答) |
| コーディング | 35.8s | 32.5s | 32.6s |
| BPMN生成 | 36.1s | 32.5s | 32.6s (誤回答) |
| 翻訳 JP→EN | 27.8s | 28.6s | 27.4s (誤回答) |
| 長文処理 | 16.9s | 32.9s | 32.7s (誤回答) |
| 文書作成 | 36.0s | 32.5s | 21.7s (崩壊) |

**品質評価**

- **Gemma4-31B**: 全 6 タスクで正確・実用的。翻訳は 3 スタイルを自動提示するなど要求超過。
- **Qwen3-32B**: 全タスクで安定。Gemma4 とほぼ同等品質。`<think>` トークンで速度がやや劣る。
- **DeepSeek-R1-32B**: 日本語プロンプトをほぼ全て誤認識。AWQ 量子化モデルの日本語対応が壊滅的。英語タスクのみ有効。
- **Llama 4 Scout**: VRAM が 45GB 必要でベンチ未完（llama.cpp ビルドは完了済み `/workspace/llama.cpp`）。

**インフラ変更（2026-04-28 確定）**
- `llm-bench` pod `ptn9xaa58xhhxp` → terminate 済み（$353/月削減）
- Network Volume `3zgavabooi` (llm-bench-models, EU-SE-1, 200 GB) → **2026-05-07 削除** (ADR-2605010000 が co-locate plan を supersede し US-KS-2 で `p9riuzhrvf` 新規作成、EU-SE-1 volume は region mismatch で mount 不可、−$14/月)
- `comfyui-etzhayyim-6000ada` (`r127r1ab2arjg8`) → RUNNING 継続、vLLM co-locate 先

**CUDA 互換性メモ（運用上重要）**

RTX A6000 / 6000 Ada の host driver は CUDA 12.8 (version 12080)。
PyPI の `vllm==0.20.0` は `libcudart.so.13`（CUDA 13.0）にリンクされており動作不可。
`vllm==0.19.1` が `libcudart.so.12` でリンクされた最終版（2026-04-28 時点）。
セットアップ手順は `/workspace/setup_vllm.sh` に保存済み:

```bash
pip install vllm==0.19.1
pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124 --force-reinstall
pip install flashinfer-python -i https://flashinfer.ai/whl/cu124/torch2.6/ --no-deps --force-reinstall
pip install "transformers>=5"
```

**API エンドポイント**（6000ada co-locate 後は pod ID が変わる）

```
現状 (llm-bench, 終了済み):
  https://ptn9xaa58xhhxp-8000.proxy.runpod.net/v1

今後 (6000ada):
  https://r127r1ab2arjg8-8000.proxy.runpod.net/v1  (vLLM 起動後)
```

LiteLLM 設定:
```yaml
model_list:
  - model_name: gemma4-31b
    litellm_params:
      model: openai/gemma4-31b
      api_base: https://{pod_id}-8000.proxy.runpod.net/v1
      api_key: dummy
```

# Alternatives Considered

- **Qwen3-32B**: 品質はほぼ同等だが思考トークンで遅い。将来的な多言語強化版が出れば再評価。
- **Ollama + llama.cpp on mac mini**: mac mini fleet は E2B/E4B 専用に維持。32B は VRAM 不足。
- **DeepSeek-R1-32B**: 日本語用途には不適。英語 reasoning-heavy タスク専用なら有効。

# References

- ベンチスクリプト: `70-tools/scripts/bench/llm-compare/`
- vLLM CUDA 互換: `setup_vllm.sh` on Network Volume `3zgavabooi`
- ComfyUI co-locate: ADR-0050, `50-infra/runpod/comfyui-l40s/`
- Murakumo fleet: `60-apps/etzhayyim-project-murakumo/`
