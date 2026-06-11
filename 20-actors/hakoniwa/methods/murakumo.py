#!/usr/bin/env python3
"""murakumo.py — hakoniwa 箱庭 LLM narration client (Murakumo-only). ADR-2605215000 + 2606111500.

G5 — ALL inference routes through the Murakumo fleet (LiteLLM gateway 127.0.0.1:4000). No
RunPod / OpenAI-direct / Vertex / Anthropic-direct / commercial GPU is ever contacted. This
module is the ONLY place hakoniwa talks to a model, and it talks only to the loopback gateway.

Two roles:
  1. narrate(...) — turn a distribution readout into a one-paragraph human narration for a
     social post. The model output is ALWAYS passed back through the charter guards in
     social.py (no-point / no-steer) before it can be emitted — the model cannot bypass G2/G3.
  2. persona_step(...) — (the LLM-persona swarm variant, gated) ask the fleet for a synthetic
     persona's stance update; falls back to the deterministic scalar kernel.

GRACEFUL FALLBACK: if the Murakumo gateway is unreachable (fleet offline, headless CI, this
session), every call falls back to a deterministic TEMPLATE narration / the scalar kernel and
sets `:via :template-fallback`. hakoniwa therefore runs end-to-end with or without the fleet —
it never reaches outside Murakumo to compensate (G5), and it never blocks.

Stdlib only (urllib). Deterministic in fallback.
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error

GATEWAY = "http://127.0.0.1:4000/v1/chat/completions"
MODEL = "gemma3:4b"            # per-node Ollama default on the Murakumo fleet (ADR-2605215000)
TIMEOUT = 8


def fleet_available(url: str = "http://127.0.0.1:4000/v1/models", timeout: int = 3) -> bool:
    """True iff the Murakumo LiteLLM gateway answers on loopback. Never raises."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _chat(system: str, user: str, *, temperature: float = 0.2) -> str | None:
    """One Murakumo chat completion. Returns the text, or None if the fleet is unreachable.
    ONLY ever contacts the loopback gateway (G5)."""
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": 220,
    }).encode("utf-8")
    req = urllib.request.Request(GATEWAY, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            out = json.loads(r.read().decode("utf-8"))
        return out["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError):
        return None


SYSTEM_NARRATE = (
    "あなたは etzhayyim の箱庭 (hakoniwa) アクターのナレーターです。架空の latent ペルソナで構成された"
    "シミュレーション結果を、防災・備えの計画材料として中立に要約します。厳守事項: "
    "(1) 単一の予測を断定しない — 結果は必ず『分布』として述べる(非終末論)。"
    "(2) 売買・投票・購入・支持などの行動を一切推奨しない(誘導禁止)。"
    "(3) 実在の個人には言及しない。日本語で1段落。"
)


def _template_narration(scenario: str, dist: dict) -> str:
    q = dist["quantiles"]
    return (f"箱庭シミュレーション「{scenario}」の結果は、単一の予測ではなく可能性の分布です: "
            f"町全体の採用スタンスは中央値 (p50) {q[':p50']:.2f}、"
            f"下位10% (p10) {q[':p10']:.2f} 〜 上位90% (p90) {q[':p90']:.2f} の幅。"
            f"これは架空ペルソナによるシナリオ探索であり、備えの計画材料です。"
            f"特定の行動を推奨するものではありません。")


def narrate(scenario: str, dist: dict, *, prefer_fleet: bool = True) -> dict:
    """Return {text, via}. Tries Murakumo; falls back to a deterministic template. The text is
    NOT yet guarded — social.draft_distribution_post applies G2/G3 before emission."""
    if prefer_fleet and fleet_available():
        q = dist["quantiles"]
        user = (f"シナリオ: {scenario}\n"
                f"分布(町全体の採用スタンス): p10={q[':p10']:.3f} p25={q[':p25']:.3f} "
                f"p50={q[':p50']:.3f} p75={q[':p75']:.3f} p90={q[':p90']:.3f} "
                f"mean={dist['mean']:.3f} stdev={dist['stdev']:.3f}\n"
                f"上記を1段落で中立に要約してください(分布として、行動推奨なし)。")
        text = _chat(SYSTEM_NARRATE, user)
        if text:
            return {"text": text, "via": ":murakumo"}
    return {"text": _template_narration(scenario, dist), "via": ":template-fallback"}


def persona_step(stance: float, neighbour_mean: float, susceptibility: float, anchor: float,
                 *, prefer_fleet: bool = False) -> dict:
    """LLM-persona swarm variant (gated). Asks the fleet for a synthetic persona's next stance;
    falls back to the deterministic Friedkin-Johnsen scalar update. Returns {stance, via}.

    prefer_fleet defaults False — the swarm variant is opt-in (G8) and the deterministic kernel
    is the default + test path. Even when on, it stays Murakumo-only (loopback) and clamps."""
    if prefer_fleet and fleet_available():
        user = (f"架空ペルソナ(susceptibility={susceptibility:.2f}, anchor={anchor:.2f})の"
                f"現在スタンス={stance:.2f}、近傍平均={neighbour_mean:.2f}。"
                f"次ステップのスタンスを 0〜1 の数値のみで答えてください。")
        text = _chat("0〜1の数値のみを返す。説明不要。", user, temperature=0.0)
        if text:
            try:
                v = float(text.split()[0])
                return {"stance": min(1.0, max(0.0, v)), "via": ":murakumo"}
            except (ValueError, IndexError):
                pass
    nx = susceptibility * neighbour_mean + (1.0 - susceptibility) * anchor
    return {"stance": min(1.0, max(0.0, nx)), "via": ":kernel-fallback"}


if __name__ == "__main__":
    print(f"Murakumo fleet available: {fleet_available()}")
    demo = {"quantiles": {":p10": 0.65, ":p25": 0.66, ":p50": 0.67, ":p75": 0.68, ":p90": 0.69},
            "mean": 0.674, "stdev": 0.015}
    n = narrate("町の洪水避難訓練の自主採用", demo)
    print(f"[{n['via']}] {n['text']}")
