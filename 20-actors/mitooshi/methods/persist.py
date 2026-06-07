#!/usr/bin/env python3
"""mitooshi 見通し — append-only chokepoint-intel persistence (R0, offline).

ADR-2606051800. `bridge.py` turns ONE watari/watatsuna snapshot into `:series` + `:obs`
datoms. This module PERSISTS successive snapshots into a single durable, **append-only**
kotoba-EDN trail — the as-of observation history mitooshi actually forecasts (非終末論: a
later snapshot never overwrites an earlier one; the trail only grows).

Why this exists (intel 永続化): the canonical state home is the kotoba Datom log
(ADR-2605312345). Live ingestion into a running kotoba server is **G10-gated** (Council Lv6+
+ operator). Until that gate is opened, the charter-clean way to persist intel is an
append-only kotoba-EDN artifact in-repo — a materialisation of the exact Datoms a live
ingest would append, byte-for-byte replayable. This module writes that artifact.

Invariants preserved:
  * append-only — `append_obs` NEVER removes or mutates an existing `:obs`; a re-run is
    idempotent (dedup by `:obs/id`), and a new snapshot at a new `:obs/observed-at` is
    additive. There is no overwrite path (非終末論 — no final-state datom).
  * DERIVED / :representative — every persisted record stays `:series/sourcing
    :representative` and carries its `:obs/source-actor`; the trail header says "DERIVED,
    do NOT re-ingest as authoritative" (G11 sourcing-honesty, G4 public-broadcast).
  * no live ingest — this writes a FILE. Pushing the trail into a live kotoba server is
    `--live`, which REFUSES without the G10 operator gate (mirrors watari/yadori).

stdlib only. Usage:
    python3 persist.py --watari ../data/bridge/watari-sample.edn \
                       --watatsuna ../data/bridge/watatsuna-sample.edn \
                       --at 1 --trail ../data/persisted/chokepoint-trail.kotoba.edn
"""
from __future__ import annotations

import os
import pathlib
import sys

try:
    from analyze import load_edn
    from bridge import bridge
except ImportError:  # package-style import
    from mitooshi.methods.analyze import load_edn  # type: ignore
    from mitooshi.methods.bridge import bridge  # type: ignore


def load_trail(path: pathlib.Path) -> tuple[dict[str, dict], list[dict]]:
    """Read an existing trail file → ({series_id: series}, [obs...]). Missing file = empty."""
    if not path.exists():
        return {}, []
    series: dict[str, dict] = {}
    obs: list[dict] = []
    for rec in load_edn(path):
        if ":series/id" in rec:
            series[rec[":series/id"]] = rec
        elif ":obs/id" in rec:
            obs.append(rec)
    return series, obs


def append_obs(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], int, int]:
    """Append-only merge. Returns (merged, n_added, n_duplicate).

    A duplicate is an `:obs/id` already present — it is NOT re-added and NOT mutated
    (idempotent re-run). Existing obs are never removed (非終末論). Order is stable:
    existing first, then newly-added in input order.
    """
    seen = {o[":obs/id"] for o in existing}
    merged = list(existing)
    added = dup = 0
    for o in incoming:
        oid = o[":obs/id"]
        if oid in seen:
            dup += 1
            continue
        seen.add(oid)
        merged.append(o)
        added += 1
    return merged, added, dup


def merge_series(existing: dict[str, dict], incoming: dict[str, dict]) -> dict[str, dict]:
    """Union of series definitions keyed by :series/id (a series is its identity; first
    definition wins — its metadata is stable across snapshots)."""
    out = dict(existing)
    for sid, s in incoming.items():
        out.setdefault(sid, s)
    return out


def emit_trail_edn(series: dict[str, dict], obs: list[dict]) -> str:
    """Serialise the trail to append-only kotoba EDN. Obs sorted by (series, observed-at)
    so the as-of history of each chokepoint reads in order; the file is still append-only
    in MEANING (no obs dropped/mutated), the sort is presentation only."""
    span = sorted({o[":obs/observed-at"] for o in obs}) if obs else []
    L = [
        ";; chokepoint-trail.kotoba.edn — APPEND-ONLY as-of intel trail.",
        ";; Bridged from watari 渡り (transit-load) + watatsuna 綿津綱 (cable-load).",
        ";; DERIVED public :representative observations — do NOT re-ingest as authoritative.",
        ";; 非終末論: snapshots only ACCUMULATE; no obs is ever overwritten. ADR-2606051800.",
        f";; observed-at span: {span if span else '(empty)'}  |  series: {len(series)}  obs: {len(obs)}",
        ";; Live kotoba-server ingest of this trail is G10-gated (Council Lv6+ + operator).",
        "", "[",
    ]
    for s in sorted(series.values(), key=lambda x: x[":series/id"]):
        L.append(
            f' {{:series/id "{s[":series/id"]}" :series/kind {s.get(":series/kind", ":transit-load")} '
            f':series/unit "{s.get(":series/unit", "")}" :series/source-class :public-broadcast '
            f":series/sourcing :representative}}"
        )
    for o in sorted(obs, key=lambda x: (x[":obs/series"], x[":obs/observed-at"])):
        L.append(
            f' {{:obs/id "{o[":obs/id"]}" :obs/series "{o[":obs/series"]}" '
            f':obs/observed-at {o[":obs/observed-at"]} :obs/value {o[":obs/value"]} '
            f':obs/source-actor "{o.get(":obs/source-actor", "?")}"}}'
        )
    L.append("]")
    return "\n".join(L) + "\n"


def persist(trail_path: pathlib.Path, bridged: dict) -> dict:
    """Append a bridged snapshot to the durable trail file (creating it if absent).
    Returns stats {added, duplicate, total_obs, series}."""
    ex_series, ex_obs = load_trail(trail_path)
    merged_obs, added, dup = append_obs(ex_obs, bridged["obs"])
    merged_series = merge_series(ex_series, bridged["series"])
    trail_path.parent.mkdir(parents=True, exist_ok=True)
    trail_path.write_text(emit_trail_edn(merged_series, merged_obs))
    return {"added": added, "duplicate": dup, "total_obs": len(merged_obs),
            "series": len(merged_series)}


def main(argv: list[str]) -> int:
    if "--at" not in argv or "--trail" not in argv:
        sys.exit(__doc__)
    observed_at = int(argv[argv.index("--at") + 1])
    trail_path = pathlib.Path(argv[argv.index("--trail") + 1])

    by_actor: dict[str, list] = {}
    for actor, flag in (("watari", "--watari"), ("watatsuna", "--watatsuna")):
        if flag in argv:
            by_actor[actor] = load_edn(pathlib.Path(argv[argv.index(flag) + 1]))
    if not by_actor:
        sys.exit("persist: provide at least one of --watari <edn> / --watatsuna <edn>")

    if "--live" in argv:
        # G10: live ingest into a running kotoba server requires the operator gate.
        if os.environ.get("MITOOSHI_ALLOW_LIVE_INGEST") != "1":
            sys.exit("persist --live REFUSED (G10): live kotoba-server ingest needs Council "
                     "Lv6+ + operator (set MITOOSHI_ALLOW_LIVE_INGEST=1 after ratification). "
                     "Offline file persistence runs without --live.")
        sys.exit("persist --live: operator-gated kotoba ingest not implemented at R0 "
                 "(file-persistence only). Remove --live to write the durable trail.")

    bridged = bridge(by_actor, observed_at)
    stats = persist(trail_path, bridged)
    print(f"mitooshi persist @ ts={observed_at} → {trail_path}")
    print(f"  +{stats['added']} obs added, {stats['duplicate']} duplicate(s) skipped "
          f"(idempotent); trail now {stats['total_obs']} obs across {stats['series']} series")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
