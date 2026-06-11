"""Acceptance gate for baien graft 3D-augmented samples (ADR-2605202115 D4)."""

from __future__ import annotations


def _noun_stems(s: str) -> set[str]:
    return {w.lower().rstrip("s.,") for w in s.split() if len(w) > 3}


def _view_passes(src_caption: str, view_caption: str, jaccard_threshold: float = 0.10) -> tuple[bool, float]:
    src = _noun_stems(src_caption)
    view = _noun_stems(view_caption)
    intersection = src & view
    union = src | view
    jaccard = len(intersection) / max(len(union), 1)
    substr_match = any(n in view_caption.lower() for n in src if len(n) > 4)
    return (jaccard >= jaccard_threshold or substr_match), round(jaccard, 3)


def primary_gate(src_caption: str, view_captions: dict[str, str]) -> tuple[int, dict[str, dict]]:
    details: dict[str, dict] = {}
    matches = 0
    for view, cap in view_captions.items():
        ok, jacc = _view_passes(src_caption, cap)
        details[view] = {"jaccard": jacc, "pass": ok}
        if ok:
            matches += 1
    return matches, details


def sanity_gate(stats: dict) -> bool:
    if stats.get("vertex_count", 0) < 10_000 or stats.get("vertex_count", 0) > 1_500_000:
        return False
    if stats.get("face_count", 0) <= 1_000:
        return False
    bbox = stats.get("bbox_extents") or []
    if not bbox:
        return False
    smallest = max(min(bbox), 1e-6)
    if max(bbox) / smallest >= 10:
        return False
    return True
