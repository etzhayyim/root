#!/usr/bin/env python3
"""social.py — hakoniwa 箱庭 social-emission cell. ADR-2606111500 (+ founder R1 authorization).

Projects a distribution finding into a social post (app.bsky.feed.post-shaped) and EMITS it.
Live emission + the `:published` status are AUTHORIZED (Council Lv7+ unanimity — founder 1/1,
2026-06-11; ADR-2606111500 R1 addendum). The charter invariants are NOT relaxed by that
authorization — they are enforced here in their emission home (mirror of the ontology +
manifest gates):

  G2 — DISTRIBUTION-ONLY (非終末論). The post states a DISTRIBUTION (p10/p50/p90), never a
       point. `_guard_no_point` scans the body for certainty/foretelling tokens (必ず/確実に/
       will definitely/…) and REFUSES. There is no single foretold future.
  G3 — NON-STEERING. `_guard_no_steer` scans the body for action-steering tokens (買え/売れ/
       投票/購入/支持しよう/you should/vote for/boycott/…) and REFUSES. The post informs
       resilience planning; it never tells anyone what to do.
  G1 — the box is synthetic; the post says so (`:post/synthetic-box true`) and names no person.
  G4 — every post opens with the observational disclaimer and is plaintext-public (相互監視).
  G7 — `:post/server-held-key false`; the member signs, the server never does (ADR-2605231525).
       A `:published` post REQUIRES a member-DID author + signature; emit refuses without it.

Stdlib only. Deterministic body.
"""
from __future__ import annotations

DISCLAIMER = (
    "【箱庭シミュレーション / 架空ペルソナによる可能性分布 — 予測の断定ではありません。"
    "備えの計画材料であり、特定の行動を推奨しません。実在の個人は登場しません。】"
)

# G2 — certainty / single-foretold-future tokens. The body must speak in distributions, never
# collapse to a point. (The disclaimer is exempt — it NAMES these to disclaim them.)
POINT_TOKENS = [
    "必ず", "確実に", "間違いなく", "絶対に", "確定", "断言", "100%",
    "will definitely", "is guaranteed", "for certain", "the future is", "we predict that",
    "確実な予測", "必ず起こる",
]
# G3 — action-steering / persuasion tokens. The post informs; it never directs behaviour.
STEER_TOKENS = [
    "買え", "売れ", "買うべき", "売るべき", "購入し", "投票し", "投票しよう", "投票せよ",
    "支持しよう", "支持せよ", "ボイコット", "反対しよう", "賛成しよう", "今すぐ行動",
    "you should", "you must", "vote for", "vote against", "buy ", "sell ", "boycott",
    "sign up now", "act now", "purchase",
]


def _scan(body: str, tokens: list[str]) -> str | None:
    scanned = body.replace(DISCLAIMER, "")
    low = scanned.lower()
    for t in tokens:
        if t.lower() in low:
            return t
    return None


def _guard_no_point(body: str) -> None:
    if (t := _scan(body, POINT_TOKENS)):
        raise ValueError(
            f"G2: post body asserts a point/certain future via {t!r} — refused. hakoniwa states "
            f"a DISTRIBUTION, never a single foretold outcome (非終末論)."
        )


def _guard_no_steer(body: str) -> None:
    if (t := _scan(body, STEER_TOKENS)):
        raise ValueError(
            f"G3: post body steers behaviour via {t!r} — refused. hakoniwa informs resilience "
            f"planning; it never tells anyone what to do (non-steering)."
        )


def draft_distribution_post(scenario: str, dist: dict, narration: str = "",
                            author: str = "", *, status: str = ":dry-run") -> dict:
    """A post narrating the outcome DISTRIBUTION (resilience framing). status :dry-run | :published
    (a :published post needs a member-DID author — G7). Guards G2/G3 before returning."""
    q = dist["quantiles"]
    line = (f"箱庭「{scenario}」: 町全体の採用スタンスは分布として "
            f"p10={q[':p10']:.2f} / 中央値p50={q[':p50']:.2f} / p90={q[':p90']:.2f} "
            f"(平均{dist['mean']:.2f}・幅±{dist['stdev']:.2f})。可能性の分布であり予測の断定ではありません。")
    body = f"{DISCLAIMER}\n\n{line}"
    if narration:
        body += f"\n\n{narration}"
    _guard_no_point(body)        # G2
    _guard_no_steer(body)        # G3
    if status == ":published" and not author:
        raise ValueError("G7: a :published post requires a member-DID author (the member signs, "
                         "never the server). Supply author= or use status=:dry-run.")
    return {
        ":post/subject": "distribution",
        ":post/body": body,
        ":post/status": status,              # :dry-run | :published (R1-authorized)
        ":post/synthetic-box": True,         # G1
        ":post/distribution-only": True,     # G2
        ":post/non-steering": True,          # G3
        ":post/is-mirror": True,             # G4
        ":post/server-held-key": False,      # G7
        ":post/author": author,
        ":post/narration-via": "",           # set by the caller (murakumo / template)
    }


def emit(post: dict, *, transport=None) -> dict:
    """Emit an authorized post. R1 (founder-authorized): a :published post is persisted to the
    canonical kotoba Datom log (the substrate of record) by the autorun caller; the EXTERNAL
    relay (AT Proto firehose) is a downstream projection delivered by `transport` when an
    operator credential is present. With no transport, emission is substrate-only and the post
    is marked accordingly — honest, never a silent no-op.

    Re-applies G2/G3 at the emission boundary (defence in depth — a post cannot be mutated past
    the guards). Returns the emit receipt."""
    _guard_no_point(post[":post/body"])
    _guard_no_steer(post[":post/body"])
    if post[":post/status"] == ":published" and not post.get(":post/author"):
        raise ValueError("G7: refuse to emit a :published post with no member-DID author.")
    relay = None
    if transport is not None:
        relay = transport(post)              # operator-supplied external transport (AT Proto)
    return {
        "subject": post[":post/subject"],
        "status": post[":post/status"],
        "substrate": "kotoba-datom-log",     # always persisted to the canonical log
        "external_relay": relay or ":pending-operator-transport",
        "guards": ["G2:distribution-only", "G3:non-steering", "G7:member-signed"],
    }


if __name__ == "__main__":
    demo = {"quantiles": {":p10": 0.65, ":p25": 0.66, ":p50": 0.67, ":p75": 0.68, ":p90": 0.69},
            "mean": 0.674, "stdev": 0.015}
    p = draft_distribution_post("町の洪水避難訓練の自主採用", demo,
                                narration="架空ペルソナによるシナリオ探索です。")
    print(p[":post/body"])
    print(f"\n  status={p[':post/status']} distribution-only={p[':post/distribution-only']} "
          f"non-steering={p[':post/non-steering']} server-held-key={p[':post/server-held-key']}")
    print("  emit (dry-run):", emit(p))
