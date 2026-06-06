"""ingest.py — 朱 (ake) genesis-revision bridge over the REAL actor-profile SSoT. ADR-2606052100.

The membrane's "view history" must start from *reality*, not an empty log: every actor profile that
exists today has a current committed value, and that value is the **genesis revision** on top of
which member edits (via the membrane) later append. This bridge reads the REAL repo SSoT
(`00-contracts/schemas/actor-profile-seed.kotoba.edn`) — exactly the file the DID-web Worker
publishes from — and seeds the append-only revision history with one genesis `:revision/*` per
actor profile field.

Honest scope: this is a READ over a committed repo file + an offline genesis-history build. It does
NOT ingest into the canonical kotoba Datom log (that write is G8 — Council Lv6+ + operator); a
`--live` mode that reads from kotoba is gated the same way. Genesis revisions are `:authoritative`
because they mirror the committed SSoT, and they are `:assert`s by the genesis operator — they are
not member edits and carry no vote.

Stdlib only. `as_of` is passed in (deterministic, no wall-clock).
"""

from __future__ import annotations

import pathlib

from _edn import load_edn
from revision import append_revision, current, history_of

_REPO = pathlib.Path(__file__).resolve().parents[3]
_PROFILE_SEED = _REPO / "00-contracts" / "schemas" / "actor-profile-seed.kotoba.edn"

GENESIS_BY = "did:web:etzhayyim.com:operator:genesis"
# the profile fields the membrane treats as editable (actor-profile target-kind)
GENESIS_FIELDS = (":actor/description", ":actor/display-name-ja", ":actor/display-name-en")
GENESIS_AS_OF_BASE = 1_000_000


def _genesis_edit(handle: str, attr: str, value: str) -> dict:
    return {
        ":edit/id": f"genesis:{handle}:{attr.split('/')[-1]}",
        ":edit/target-kind": ":actor-profile",
        ":edit/target-entity": handle,
        ":edit/target-attr": attr,
        ":edit/op": ":assert",
        ":edit/proposed-value": value,
        ":edit/author": GENESIS_BY,
        ":edit/author-kind": ":member",
        ":edit/provenance": "00-contracts/schemas/actor-profile-seed.kotoba.edn",
        ":edit/sourcing": ":authoritative",   # mirrors the committed SSoT
    }


def genesis_revisions(profile_seed_path: pathlib.Path = _PROFILE_SEED,
                      as_of_base: int = GENESIS_AS_OF_BASE) -> dict:
    """Build the genesis append-only revision history from the REAL actor-profile SSoT."""
    seed = load_edn(profile_seed_path)
    records = [r for r in seed.get(":seed", []) if isinstance(r, dict) and r.get(":actor/handle")]

    history: list[dict] = []
    as_of = as_of_base
    actors = []
    for rec in records:
        handle = rec[":actor/handle"]
        actors.append(handle)
        for attr in GENESIS_FIELDS:
            val = rec.get(attr)
            if not val:
                continue
            as_of += 1
            history = append_revision(history, _genesis_edit(handle, attr, str(val)), as_of)
    return {"history": history, "actors": actors, "records": len(records)}


def _report(res: dict) -> str:
    out = ["# 朱 (ake) — genesis revision history from the REAL actor-profile SSoT\n",
           f"Bootstrapped {len(res['history'])} genesis revisions across {res['records']} actor "
           f"profiles (read from `00-contracts/schemas/actor-profile-seed.kotoba.edn`).\n",
           "Member edits via the membrane append ON TOP of these (the log only grows). NO ingest "
           "into the canonical kotoba Datom log (G8).\n",
           "| actor | description revisions | current sourcing |",
           "|---|---|---|"]
    for h in res["actors"]:
        n = len(history_of(res["history"], h, "description"))
        cur = current(res["history"], h, "description")
        src = (cur or {}).get(":revision/sourcing", "—")
        out.append(f"| {h} | {n} | {src} |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    res = genesis_revisions()
    report = _report(res)
    out = pathlib.Path(__file__).resolve().parent / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "genesis-revisions.md").write_text(report, encoding="utf-8")
    print(report)
