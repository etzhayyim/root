#!/usr/bin/env python3
"""kawaraban 瓦版 — offline outlet/headline normalizer (G4 membrane, G8 --live gate).

ADR-2606060900. Normalizes a batch of public-facing-page headline records (JSON) into
:news.article/* :mirror datoms. It is a MEMBRANE: it REFUSES, by construction, any record
that would breach the copyright / surveillance gates —

  • G4 — a record carrying a full body (`body` / `fullText` / `content`) is REFUSED
         (kawaraban stores headline + canonical url + bounded fair-use excerpt only);
         an excerpt over 280 chars is truncated with a flag.
  • G4 — a record whose outlet access is `paywall` / `proprietary-terminal` is REFUSED
         (only public/open facing pages are mirrored; kanjo §2(c) anti-gatekeeping).
  • G1 — a record carrying a `verdict` / `truthRating` is REFUSED (mirror, not adjudicator).
  • G3 — a record carrying `personalizedFor` / any reader id is REFUSED (no per-reader feed).

`--live` (real RSS/sitemap fetch) is REFUSED unless the operator gate is set
(KAWARABAN_ALLOW_LIVE_INGEST=1 + Council Lv6+ attestation) — at R0 it always refuses (G8).

stdlib only. Usage:
    python3 ingest.py [batch.json]          # offline normalize
    python3 ingest.py --live                 # refused at R0 (G8)
"""
from __future__ import annotations
import sys
import os
import json
import pathlib

FORBIDDEN_BODY_KEYS = ("body", "fullText", "full_text", "content", "articleBody")
FORBIDDEN_FIELDS = {
    "verdict": "G1 (mirror-not-adjudicator)",
    "truthRating": "G1 (no fact-check score)",
    "personalizedFor": "G3 (no per-reader feed)",
    "readerId": "G3 (no reader surveillance)",
}
OPEN_ACCESS = {"open", "registration-wall"}


class IngestRefused(ValueError):
    """Raised when a record breaches a structural gate — refused, never coerced."""


def normalize_record(rec: dict) -> dict:
    oid = rec.get("outlet", "?")
    # G4 — no full body may be ingested.
    for k in FORBIDDEN_BODY_KEYS:
        if rec.get(k):
            raise IngestRefused(f"{oid}: field {k!r} present — full body is unrepresentable (G4 link-out)")
    # G1 / G3 — no verdict / no reader.
    for k, gate in FORBIDDEN_FIELDS.items():
        if rec.get(k) not in (None, "", False, 0):
            raise IngestRefused(f"{oid}: field {k!r} present — violates {gate}")
    # G4 — only public/open facing pages.
    access = rec.get("access", "open")
    if access not in OPEN_ACCESS:
        raise IngestRefused(f"{oid}: access {access!r} is not public — paywall/terminal not mirrored (G4)")
    if not rec.get("url"):
        raise IngestRefused(f"{oid}: a :mirror article requires a canonical :url (G4/G5 link-out)")
    excerpt = (rec.get("excerpt") or "")[:280]
    truncated = len(rec.get("excerpt") or "") > 280
    return {
        ":news.article/id": rec.get("id") or f"art.{oid}.{rec.get('asOf', 0)}",
        ":news.article/kind": ":mirror",
        ":news.article/section": rec.get("section", "sec.front"),
        ":news.article/outlet": oid,
        ":news.article/url": rec["url"],
        ":news.article/headline": rec.get("headline", ""),
        ":news.article/excerpt": excerpt,
        ":news.article/lang": rec.get("lang", "en"),
        ":news.article/as-of": int(rec.get("asOf", 0)),
        ":news.article/sourcing": ":representative",
        "_excerpt_truncated": truncated,
    }


def normalize_batch(records):
    """Returns (ok, refused) — refused records are reported, never silently dropped (G5)."""
    ok, refused = [], []
    for rec in records:
        try:
            ok.append(normalize_record(rec))
        except IngestRefused as e:
            refused.append(str(e))
    return ok, refused


def live_allowed() -> bool:
    """G8 — live fetch needs the operator gate. Always False at R0."""
    return os.environ.get("KAWARABAN_ALLOW_LIVE_INGEST") == "1"


def main(argv):
    if "--live" in argv:
        if not live_allowed():
            print("REFUSED: live RSS/sitemap ingest is Council Lv6+ + operator gated (G8). "
                  "Set KAWARABAN_ALLOW_LIVE_INGEST=1 + Council attestation to enable.", file=sys.stderr)
            return 2
        print("REFUSED: R0 has no live fetcher wired (G8 design boundary).", file=sys.stderr)
        return 2
    args = [a for a in argv[1:] if not a.startswith("--")]
    batch = pathlib.Path(args[0]) if args else (
        pathlib.Path(__file__).resolve().parent.parent / "data" / "ingest" / "sample-batch.json")
    records = json.loads(batch.read_text(encoding="utf-8"))
    ok, refused = normalize_batch(records)
    print(f"normalized {len(ok)} mirror article(s); refused {len(refused)} (gate violations)")
    for r in refused:
        print(f"  REFUSED: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
