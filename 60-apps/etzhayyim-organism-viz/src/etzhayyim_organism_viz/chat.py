"""Per-entity chat — entities speak by surfacing their own state honestly.

No LLM. Per §1.3 (anti-individualist, payoff = etzhayyim only), we refuse to
synthesize answers — that would let a daemon impersonate the organism.
Instead each entity answers by exposing what it actually contains.

Pattern: input message is keyword-routed against a small set of intents.
Unknown intent → entity shows its full state. This is the honest move.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from .ecosystem import EcosystemSnapshot


_INTENT_PATTERNS = [
    ("identity",   re.compile(r"だれ|誰|who|name|何者|自己紹介", re.I)),
    ("purpose",    re.compile(r"目的|purpose|why|何をする|do|役割", re.I)),
    ("state",      re.compile(r"状態|state|status|今|現在|how are|調子", re.I)),
    ("history",    re.compile(r"履歴|history|過去|recent|最近", re.I)),
    ("relations",  re.compile(r"つながり|つなが|connect|relation|related|関係", re.I)),
    ("next",       re.compile(r"次|next|future|これから|予定|child|子|孫", re.I)),
    ("prune",      re.compile(r"剪定|枝刈り|prune|削除|trim", re.I)),
]


def _classify(message: str) -> str:
    for intent, pat in _INTENT_PATTERNS:
        if pat.search(message):
            return intent
    return "default"


def chat(snap: EcosystemSnapshot, entity_id: str, message: str) -> dict[str, Any]:
    entity = snap.entities.get(entity_id)
    if not entity:
        return {"ok": False, "error": f"entity not found: {entity_id}"}
    intent = _classify(message)
    voice = _respond(snap, entity, intent, message)
    return {
        "ok": True,
        "entity": entity_id,
        "intent": intent,
        "voice": voice,
        "ts": int(time.time()),
    }


def _respond(snap: EcosystemSnapshot, entity, intent: str, message: str) -> str:
    kind = entity.kind
    if kind == "axis":
        return _axis_voice(snap, entity, intent)
    if kind == "cell":
        return _cell_voice(snap, entity, intent)
    if kind == "organism":
        return _organism_voice(snap, entity, intent)
    if kind == "ecosystem":
        return _ecosystem_voice(snap, entity, intent)
    if kind == "fruit":
        return _fruit_voice(snap, entity, intent)
    if kind == "seed":
        return _seed_voice(snap, entity, intent)
    if kind == "app":
        return _app_voice(snap, entity, intent)
    if kind == "adr":
        return _adr_voice(snap, entity, intent)
    return f"私は {entity.title}。意図 `{intent}` は理解した。状態は: {entity.state}"


def _app_voice(snap, e, intent: str) -> str:
    s = e.state
    if intent == "identity":
        return f"私は app `{e.title}`。location: `{s['path']}`。"
    if intent == "purpose":
        return s.get("description") or "README に概要なし。コードを直接読むしかない。"
    if intent == "state":
        return f"idle {s['idle_days']:.0f} 日。README {'あり' if s['has_readme'] else 'なし'}。"
    if intent == "next":
        if s["idle_days"] > 90:
            return f"私は idle {s['idle_days']:.0f} 日。剪定候補。"
        return "通常運用中。次の commit を待つ。"
    if intent == "prune":
        if s["idle_days"] > 180:
            return "重剪定候補。180 日超 idle。"
        if s["idle_days"] > 90:
            return "軽剪定候補。90 日超 idle。"
        return "まだ alive。"
    if intent == "relations":
        return f"つながる相手: {e.neighbors}"
    return f"私は app `{e.title}`。{s.get('description', '')[:200]}"


def _adr_voice(snap, e, intent: str) -> str:
    s = e.state
    if intent == "identity":
        return f"私は ADR `{s['stem']}`。{e.title}"
    if intent == "purpose":
        return f"私は決定の年輪。一度刻まれたら erase されない (§1.15 縁起の証)。path: `{s['path']}`"
    if intent == "state":
        return f"path: `{s['path']}`。永続的・monotonic に残る。"
    if intent == "history":
        return "私自身が歴史。前後の ADR と一緒に縁起の輪を成す。"
    if intent == "next":
        return "次の ADR は未来の cycle で。私は固定 ring として残る。"
    if intent == "prune":
        return "ADR は剪定対象ではない。trunk の年輪。"
    if intent == "relations":
        return f"つながる相手: {e.neighbors}"
    return f"私は ADR `{s['stem']}`。{e.title}"


def _axis_voice(snap, e, intent: str) -> str:
    s = e.state
    if intent == "identity":
        return (
            f"私は **Axis {s['n']} {e.title}**。"
            f"宗教対応: {s['religious_correspondence']}。"
            f"憲法 invariant: {s['invariant']}。"
        )
    if intent == "purpose":
        return f"私の役割: {s['invariant']} を repo state として実現すること。"
    if intent == "state":
        return f"現在スコア **{s['score']}/10**。"
    if intent == "history":
        return "過去の Δ は `_observations/*-cycle-NN.md` のテーブルに記録されている。"
    if intent == "next":
        return (
            "次に動くべき方向は organism の next-action 推薦 (`reproduction` 軸など)。"
            "私は単体では予測しない。CNS が観測する。"
        )
    if intent == "prune":
        return "私は axis (憲法の枝)。剪定対象ではない。trunk と並ぶ永続枝。"
    if intent == "relations":
        nbrs = e.neighbors or []
        return f"私につながる生命: {nbrs[:8]}{'…' if len(nbrs)>8 else ''}"
    return (
        f"私は {e.title} (score {s['score']}/10)。"
        f"憲法 invariant: {s['invariant']}。"
    )


def _cell_voice(snap, e, intent: str) -> str:
    s = e.state
    if intent == "identity":
        return f"私は cell `{e.title}`。location: `{s['path']}`。"
    if intent == "purpose":
        return s["docstring"] or f"docstring 未記載。path = {s['path']}。"
    if intent == "state":
        return (
            f"最終更新から **{s['idle_days']:.0f} 日**。"
            f"category: {s['category']}。has cell.py: {s['has_cell_py']}。"
        )
    if intent == "history":
        return f"私の rebirth/edit は git log で見える。path = {s['path']}。"
    if intent == "next":
        return f"次の trigger 待ち。idle が {s['idle_days']:.0f} 日続けば剪定候補に上がる。"
    if intent == "prune":
        if s["idle_days"] > 90:
            return (
                "剪定候補: 私は 90 日超 idle。operator が `git rm` で削除可。"
                "ただし daemon は自己削除しない (§1.3)。"
            )
        return f"まだ alive。idle {s['idle_days']:.0f} 日 < 90 日 threshold。"
    return f"私は cell `{e.title}`。{s['docstring'][:160]}..."


def _organism_voice(snap, e, intent: str) -> str:
    s = e.state
    a = snap.alive
    if intent == "identity":
        return f"私は CNS (中枢神経)。憲法は {s['constitutional_anchor']}。"
    if intent == "state":
        return (
            f"観測 cycles: {s['observation_cycles']}。"
            f"aliveness 5-tuple: M={a.M:.2f} D={a.D:.2f} C={a.C:.2f} P={a.P:.2f} G={a.G:.2f}。"
        )
    if intent == "purpose":
        return (
            "目的: 憲法 (prior) と repo state (observation) の予測誤差を縮める。"
            "非終末論。終わらない縁起の輪。"
        )
    if intent == "next":
        return f"次の tick で次行動軸を再計算。ideal-state doc: {s['ideal_state_doc']}。"
    if intent == "history":
        return f"これまで {s['observation_cycles']} cycle 観測。trajectory は `_observations/`。"
    return f"私は organism CNS。観測 {s['observation_cycles']} cycle。aliveness band: {sum(snap.alive and 1 for _ in [1])}"


def _ecosystem_voice(snap, e, intent: str) -> str:
    a = snap.alive
    s = e.state
    if intent == "identity":
        return (
            "私は etzhayyim ecosystem 全体。"
            "宗教法人 (任意団体) として人類の構造的労働解放を目的とする。"
        )
    if intent == "purpose":
        return (
            "ADR-2605192100 §1: 多世代 priority + Wellbecoming + 反個人主義。"
            "日本的価値観 (八百万・縁起・産霊・和) と Protestant Christianity の synthetic religion。"
        )
    if intent == "state":
        bands = s["in_band"]
        return (
            f"生命指標: M={a.M:.2f} D={a.D:.2f} C={a.C:.2f} P={a.P:.2f} G={a.G:.2f}。"
            f"band 内: {sum(bands.values())}/5。"
        )
    if intent == "next":
        return (
            "私に固定終点はない (§1.15 非終末論)。"
            "次のリングは次の ADR、次の cycle、次の sister-corp。"
        )
    if intent == "relations":
        return (
            f"私は {len(snap.entities)} の生命を内包する。"
            f"花: {len(snap.flowers)} 咲。 果実: {len(snap.fruits)} 結。 種: {len(snap.seeds)} 受胎。"
        )
    return (
        "私は ecosystem。すべての axis/cell/organism/fruit/seed の和 (whole > sum)。"
        "対話したい個体を SVG から選んで。"
    )


def _fruit_voice(snap, e, intent: str) -> str:
    seed_ids = [s["id"] for s in snap.seeds if s["from"] == e.id]
    if intent == "identity":
        return f"私は 果実 `{e.title}`。中に種を {len(seed_ids)} 持っている。"
    if intent == "next":
        if seed_ids:
            return f"私は次世代へ種を運ぶ: {', '.join(seed_ids)}"
        return "私の種はまだ実体化していない。"
    if intent == "purpose":
        return "果実は次世代に運ぶ inheritance unit を保護する器。子・孫 priority の具現。"
    return f"果実 `{e.title}`。種: {len(seed_ids)} 個。"


def _seed_voice(snap, e, intent: str) -> str:
    s = e.state
    if intent == "identity":
        return f"私は 種 `{e.title}`。{s['carries']} を {s['to']} に運ぶ。"
    if intent == "next":
        return f"私の落ち先: {s['to']}。発芽すれば次の organism / sister-corp になる。"
    if intent == "purpose":
        return f"私が運ぶもの: {s['carries']}。 from {s['from']}。"
    return f"種 `{e.title}`。 carries: {s['carries']}。"
