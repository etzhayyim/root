#!/usr/bin/env python3
"""utsushie 写し絵 — offline render-PLAN builder (R0, charter-gated).

ADR-2606161536 §D2. This module is **pure and offline**: it turns a kawaraban
`:article` into a deterministic *plan* for a short narrated video. It NEVER calls a
model and NEVER renders — `render()` raises at R0 because live render is G8-gated
(Council Lv6+ + operator) and must run Murakumo-fleet only (U5 = G6, ADR-2605215000).

The plan it emits is bounded by the same gates the lexicon makes structural
(`lex/video.edn`, U1–U6):

  U1 (G1) no verdict          — the plan carries no truth-rating; narration is attributive.
  U2 (G4) script ≤ excerpt    — narration is the headline + the article's ≤280-char excerpt;
                                the full body is never narrated.
  U3 (G9) anti-deepfake       — no named-person photoreal likeness, no voice clone.
  U4 (G2) no engagement-edit  — recency / 面-fit only; no dwell-driven hook.
  U5 (G6) Murakumo-only       — external-GPU render unrepresentable; render() R0-gated.
  U6 (G7) member-signed       — publish carries no server-held key.

Standalone-runnable; pure stdlib (no deps).
"""
from __future__ import annotations

EXCERPT_MAX = 280  # = kawaraban G4 bound (lex/video.edn :narrationScript maxLength)
ALLOWED_KINDS = ("mirror", "actor-event")  # G11: 'original' is not a member


class CharterRefusal(ValueError):
    """Raised when an input would force a representable charter violation (U1–U6)."""


def build_plan(article: dict, *, langs=None) -> dict:
    """Build a deterministic, charter-bounded video plan from a kawaraban :article.

    `article` is the mirror/actor-event record (headline + excerpt + url + outlet …).
    `langs` is the list of target narration languages (i18n supplies the scripts, D3).
    Returns a plan dict; raises CharterRefusal on any gate violation. Never renders.
    """
    kind = article.get("kind")
    if kind not in ALLOWED_KINDS:
        raise CharterRefusal(
            f"G11/U-kind: kind must be one of {ALLOWED_KINDS} (got {kind!r}); "
            "utsushie narrates a mirror/actor-event, it is never an :original source"
        )

    headline = (article.get("headline") or "").strip()
    if not headline:
        raise CharterRefusal("missing headline — nothing to narrate")

    excerpt = (article.get("excerpt") or "").strip()
    if len(excerpt) > EXCERPT_MAX:
        # U2 (= G4): a script longer than the bounded fair-use excerpt = full-text narration.
        raise CharterRefusal(
            f"U2/G4: narration source exceeds the {EXCERPT_MAX}-char fair-use bound "
            f"({len(excerpt)} chars) — the full body is never narrated"
        )

    # U3 (= G9) anti-deepfake: the article may not request a real-person depiction / voice.
    if article.get("depictsPerson") or article.get("depicts_person"):
        raise CharterRefusal("U3/G9 anti-deepfake: no photoreal likeness of a named real person")
    if article.get("voiceClone") or article.get("voice_clone"):
        raise CharterRefusal("U3/G9 anti-deepfake: no cloned voice of a named real person")

    if kind == "mirror" and not (article.get("url") or "").strip():
        raise CharterRefusal("G4: a 'mirror' video must carry a canonical link-out (url)")

    # Narration script: headline + bounded excerpt only (U2). Deterministic join.
    script = headline if not excerpt else f"{headline}。{excerpt}"
    script = script[:EXCERPT_MAX]

    langs = list(langs) if langs else [article.get("lang") or "ja"]

    return {
        "videoId": f"utsushie-{article.get('articleId', 'unknown')}",
        "sourceArticleId": article.get("articleId"),
        "kind": kind,
        "section": article.get("section"),
        "headline": headline,
        # narration is bounded; one script per target language (filled by i18n at D3)
        "narrationScript": script,
        "langs": langs,
        "linkUrl": article.get("url"),
        "outlet": article.get("outlet"),
        "blobMime": "video/mp4",
        # gate witnesses — all const-false in lex/video.edn; echoed so callers can audit
        "gates": {
            "verdict": False,
            "fullTextNarration": False,
            "depictsPerson": False,
            "voiceClone": False,
            "engagementOptimized": False,
            "externalGpuRender": False,
            "serverHeldKey": False,
        },
        "narrator": "synthetic-neutral",  # U3: never a named person's voice
    }


def render(plan: dict):
    """R0 guard — live video render is G8-gated and Murakumo-fleet only (U5 = G6)."""
    raise RuntimeError(
        "utsushie.render is R0-gated: live video render requires Council Lv6+ + operator "
        "(G8) and must run Murakumo-fleet only (U5 = G6, ADR-2605215000). "
        "Use build_plan() for offline planning."
    )


if __name__ == "__main__":  # tiny smoke
    p = build_plan(
        {"articleId": "a1", "kind": "mirror", "section": "国際", "headline": "見出し",
         "excerpt": "要約。", "url": "https://example.org/a", "outlet": "outlet.x"},
        langs=["ja", "en"],
    )
    print("plan ok:", p["videoId"], p["langs"], "narrator=", p["narrator"])
