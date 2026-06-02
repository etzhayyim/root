#!/usr/bin/env python3
"""firehose_dryrun — members-only dry run over real mst-projector FirehoseEvent shape.

ADR-2606011000 §D7.1 + ADR-2605231902 (mst-projector) + ADR-2605310100 §4(2).

Mirrors the projector's real contract (`50-infra/mst-projector/src/firehose.ts`):

    FirehoseEvent { seq, did, collection, rkey, op, recordCid }   # NO body

The firehose carries only the record CID; the body is hydrated by a `recordFetcher`
callback via `com.atproto.repo.getRecord` (exactly as feed-discover.ts does for
feed.post / membrane.verdict). For a follow, the resolved body's `subject` is the
followed DID. This driver wires that pattern to `engi_ingest`:

    firehose events ──(filter graph collections, skip delete)──▶
      hydrate subject via fetcher ──▶ normalized records ──▶
        ei.from_atproto_records ──▶ ei.ingest(member floor) ──▶ ei.validate_floor

DRY RUN: no PDS connection, no production write. The fetcher is injected, so a real run
swaps in a getRecord call. The §4(2) floor still holds for everyone — only member↔member
edges are emitted; latent followers stay anonymous-aggregate.

Run:   python3 firehose_dryrun.py
Test:  via test_engi_pipeline.py (test_dryrun_*)
"""
from __future__ import annotations

from typing import Callable

import engi_ingest as ei

# Graph collections we ingest (everything else on the firehose is ignored).
GRAPH_COLLECTIONS = set(ei.ATPROTO_KIND.keys())  # follow + engi.dep


def events_to_records(
    events: list[dict],
    fetch_subject: Callable[[str, str], str | None],
) -> list[dict]:
    """Normalize FirehoseEvent dicts → engi record dicts, hydrating subject via fetcher.

    events: dicts with at least {"did", "collection", "rkey", "op"} (FirehoseEvent shape).
    fetch_subject(did, rkey) -> followed-DID | None  (the recordFetcher; real run = getRecord).
    """
    out: list[dict] = []
    for ev in events:
        if ev.get("collection") not in GRAPH_COLLECTIONS:
            continue
        if ev.get("op") == "delete":            # deletes don't create 縁; skip (no body)
            continue
        subject = fetch_subject(ev["did"], ev["rkey"])
        if not subject:                          # record-not-found / fetch-failed → skip
            continue
        out.append({
            "author_did": ev["did"],
            "record": {"$type": ev["collection"], "subject": subject},
        })
    return out


def dry_run(events: list[dict], member_dids: set[str],
            fetch_subject: Callable[[str, str], str | None]) -> dict:
    """Full members-only pipeline. Returns a report dict; raises if the floor is dirty."""
    records = events_to_records(events, fetch_subject)
    follows = ei.from_atproto_records(records, member_dids)
    res = ei.ingest(follows, member_dids)
    edn = ei.to_edn(res)
    violations = ei.validate_floor(edn, res, member_dids)
    if violations:                               # fail-closed (ADR-2605310100 §4 discipline)
        raise RuntimeError(f"FLOOR DIRTY — refusing to emit: {violations}")
    return {
        "events_in": len(events),
        "graph_records": len(records),
        "member_edges_emitted": len(res.edges),
        "member_organisms": len(res.organisms),
        "latent_anonymous": res.latent_aggregate,
        "floor": "CLEAN",
        "edn": edn,
    }


if __name__ == "__main__":
    import json

    # Fixture mirroring real projector output (one #commit → several follow ops).
    EVENTS = [
        {"seq": 1, "did": "did:plc:alice", "collection": "app.bsky.graph.follow",
         "rkey": "3k1", "op": "create", "recordCid": "bafy1"},
        {"seq": 2, "did": "did:plc:alice", "collection": "app.bsky.graph.follow",
         "rkey": "3k2", "op": "create", "recordCid": "bafy2"},
        {"seq": 3, "did": "did:plc:bob", "collection": "com.etzhayyim.engi.dep",
         "rkey": "3k3", "op": "create", "recordCid": "bafy3"},
        {"seq": 4, "did": "did:plc:alice", "collection": "app.bsky.feed.post",
         "rkey": "3k4", "op": "create", "recordCid": "bafy4"},   # not a graph edge → ignored
        {"seq": 5, "did": "did:plc:bob", "collection": "app.bsky.graph.follow",
         "rkey": "3k5", "op": "delete"},                          # delete → skipped
    ]
    # Stand-in recordFetcher (real run = com.atproto.repo.getRecord → record.subject).
    SUBJECTS = {
        ("did:plc:alice", "3k1"): "did:plc:bob",      # member → member  (emitted)
        ("did:plc:alice", "3k2"): "did:plc:carol",    # member → latent  (aggregate)
        ("did:plc:bob", "3k3"): "did:plc:alice",      # member → member  (emitted, dep)
    }
    members = {"did:plc:alice", "did:plc:bob"}

    report = dry_run(EVENTS, members, lambda did, rkey: SUBJECTS.get((did, rkey)))
    edn = report.pop("edn")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n;; --- emitted EDN ---\n" + edn)
