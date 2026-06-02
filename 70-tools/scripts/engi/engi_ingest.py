#!/usr/bin/env python3
"""engi ingest — atproto follow/deps → 縁(:en) kotoba EDN, floor-enforced.

ADR-2606011000 §D6/§D7.1 + ADR-2605310100 §4(2).

The first runnable piece of the Engi Knowledge Graph: turn the atproto follow-graph
(and dependency edges) — which already express しがらみ/呪い (=取) — into engi
vocabulary datoms (:organism/* :en/* :grasp/*) over the kotoba Datom log.

CONSTITUTIONAL FLOOR (enforced IN CODE, fail-closed):
  F1  `:owns` / `:owner` never appears in output (ADR-2606011000 §D2/§D6).
  F2  No non-member DID/handle ever appears in output — outbound third-party data
      for latent, non-ingressed organisms stays under the §4(2) gate. Latent
      organisms contribute to ANONYMOUS AGGREGATES only (ADR-2605310100 §4(2)).
  F3  Every emitted :en edge has BOTH endpoints claimed (covenant members) — their
      own follow-graph is covenant-visible (ADR-2605310100 §1–§2).
  F4  Every emitted :en edge carries :en/grasping-load and :en/source :atproto-follow.

This is proposed scaffold (ADR-2606011000 §D9): a reference transform + machine guard.
It does NOT run against production data and binds nothing until Council Lv7+ ratifies
§D1–§D4. The graph it produces grows CLAIMED-FIRST + AGGREGATE-FIRST by construction.

Run:   python3 engi_ingest.py        # prints a worked example
Test:  python3 test_engi_ingest.py   # or: pytest test_engi_ingest.py
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Forbidden tokens — the F1 floor. Ownership is never reified (ADR-2606011000 §D2).
# --------------------------------------------------------------------------- #
FORBIDDEN_KEYWORDS = (":owns", ":owner", ":owned-by", ":title-of", ":proprietor")


@dataclass
class Follow:
    """An atproto edge. `kind` ∈ {follows, depends-on}. ids are DIDs (did:plc/did:web)."""
    frm: str
    to: str
    kind: str = "follows"


# atproto collection ($type) → :en/kind. Only known graph collections are ingested;
# everything else is skipped (no silent mis-typing). com.etzhayyim.engi.dep is our
# own dependency-edge collection (deps express しがらみ just like follows).
ATPROTO_KIND = {
    "app.bsky.graph.follow": "follows",
    "com.etzhayyim.engi.dep": "depends-on",
}


def from_atproto_records(records: list[dict], member_dids: set[str]) -> list[Follow]:
    """Normalize MST feed-membrane / firehose records (ADR-2605231902) into Follow
    edges. Record shape (normalized): {"author_did": <did>, "record": {"$type": ...,
    "subject": <did>}}. The author is the grasping side (:en/from), the subject is the
    grasped side (:en/to). Unknown collections are skipped. The §4 floor is NOT applied
    here — it is enforced downstream in ingest()/validate_floor(), so reading the live
    firehose for everyone is safe: only member-member edges are ever emitted."""
    out: list[Follow] = []
    for r in records:
        rec = r.get("record") or {}
        kind = ATPROTO_KIND.get(str(rec.get("$type") or ""))
        if kind is None:
            continue
        frm = str(r.get("author_did") or r.get("repo") or "")
        to = str(rec.get("subject") or "")
        if frm and to:
            out.append(Follow(frm, to, kind))
    return out


@dataclass
class IngestResult:
    organisms: dict = field(default_factory=dict)  # did -> organism datom map
    edges: list = field(default_factory=list)       # list of :en datom maps
    grasp: dict = field(default_factory=dict)        # did -> :grasp datom map (members only)
    latent_aggregate: dict = field(default_factory=dict)  # anonymous global counters


# --------------------------------------------------------------------------- #
# grasping-load — the 取 measure on a single edge (ADR-2606011000 §D2).
# A follow A→B binds A's attention to B; the load reflects B's accumulated reach
# (in-degree concentration). Pure, deterministic, method-versioned.
# --------------------------------------------------------------------------- #
GRASP_METHOD_VERSION = "engi-grasp/v0.1.0-log1p-indegree"


def grasping_load(target_indegree: int) -> float:
    """しがらみ/呪い weight of one follow edge, given the target's in-degree."""
    return round(1.0 + math.log1p(max(0, target_indegree)), 3)


# --------------------------------------------------------------------------- #
# ingest
# --------------------------------------------------------------------------- #
def ingest(follows: list[Follow], member_dids: set[str]) -> IngestResult:
    """Transform follow/deps edges into engi datoms under the floor.

    member_dids = the set of CLAIMED organisms (organism/claimed? true, standing
    :member) per the §D5 covenant gate. Everything else is latent / non-ingressed
    and is handled by F2 (aggregate-only, never named).
    """
    res = IngestResult()

    # in-degree over ALL edges (used to weight grasp); latent endpoints count toward
    # a member target's reach but are NEVER themselves named (F2).
    indegree: dict[str, int] = {}
    for f in follows:
        indegree[f.to] = indegree.get(f.to, 0) + 1

    res.latent_aggregate = {
        "latent-organism-count": 0,      # distinct non-members observed (anonymous)
        "latent-incident-edges": 0,      # edges touching ≥1 non-member (dropped from :en)
    }
    seen_latent: set[str] = set()

    def note_member_organism(did: str, kind: str = ":human") -> None:
        if did in res.organisms:
            return
        res.organisms[did] = {
            ":organism/id": f"org.{_opaque(did)}",
            ":organism/kind": kind,
            ":organism/did": did,            # safe: claimed member (F2 ok)
            ":organism/claimed?": True,
            ":organism/standing": ":member",
            ":organism/sourcing": ":representative",
        }

    for f in follows:
        both_member = f.frm in member_dids and f.to in member_dids
        if both_member:
            # F3 satisfied: emit organisms + a 縁 edge with grasping-load (F4).
            note_member_organism(f.frm)
            note_member_organism(f.to)
            load = grasping_load(indegree.get(f.to, 0))
            res.edges.append({
                ":en/id": f"en.{f.kind}.{_opaque(f.frm)}.{_opaque(f.to)}",
                ":en/kind": f":{f.kind}",
                ":en/from": res.organisms[f.frm][":organism/id"],
                ":en/to": res.organisms[f.to][":organism/id"],
                ":en/grasping-load": load,
                ":en/source": ":atproto-follow" if f.kind == "follows" else ":atproto-deps",
                ":en/sourcing": ":representative",
            })
        else:
            # F2: at least one endpoint is latent/non-ingressed → NO individuated
            # node or edge. Fold into anonymous aggregates only.
            res.latent_aggregate["latent-incident-edges"] += 1
            for did in (f.frm, f.to):
                if did not in member_dids and did not in seen_latent:
                    seen_latent.add(did)
                    res.latent_aggregate["latent-organism-count"] += 1

    # :grasp aggregate — members only; concentration = in-degree (reach/取 held).
    # The count MAY include anonymous latent followers, but never names them (F2).
    for did in member_dids:
        if did in indegree:
            conc = float(indegree[did])
            res.grasp[did] = {
                ":grasp/organism": res.organisms.get(did, {}).get(
                    ":organism/id", f"org.{_opaque(did)}"),
                ":grasp/load": round(
                    sum(e[":en/grasping-load"] for e in res.edges
                        if e[":en/to"] == res.organisms.get(did, {}).get(":organism/id")), 3),
                ":grasp/concentration": conc,
                ":grasp/method-version": GRASP_METHOD_VERSION,
                ":grasp/release-path": "[:tithe :commons-access]",
            }
            # ensure the member target has an organism node even if it never follows
            note_member_organism(did)

    return res


def _opaque(did: str) -> str:
    """Stable, readable suffix for an id. Members only (callers guard with F2)."""
    return re.sub(r"[^a-z0-9]+", "-", did.lower()).strip("-")


# --------------------------------------------------------------------------- #
# EDN serialization
# --------------------------------------------------------------------------- #
def to_edn(res: IngestResult) -> str:
    lines = [";; engi ingest output — ADR-2606011000 §D7.1 (proposed scaffold)",
             ";; claimed-first organisms + 縁 edges; latent remainder = anonymous aggregate.",
             "["]
    for did in sorted(res.organisms):
        lines.append("  " + _map_edn(res.organisms[did]))
    for e in res.edges:
        lines.append("  " + _map_edn(e))
    for did in sorted(res.grasp):
        lines.append("  " + _map_edn(res.grasp[did]))
    # anonymous latent aggregate (no identities)
    lines.append("  " + _map_edn({
        ":grasp/latent-organism-count": res.latent_aggregate["latent-organism-count"],
        ":grasp/latent-incident-edges": res.latent_aggregate["latent-incident-edges"],
        ":grasp/method-version": GRASP_METHOD_VERSION,
    }))
    lines.append("]")
    return "\n".join(lines)


def _map_edn(m: dict) -> str:
    parts = []
    for k, v in m.items():
        if isinstance(v, bool):
            parts.append(f"{k} {'true' if v else 'false'}")
        elif isinstance(v, str) and (v.startswith(":") or v.startswith("[")):
            parts.append(f"{k} {v}")          # keyword or vector literal
        elif isinstance(v, str):
            parts.append(f'{k} "{v}"')
        else:
            parts.append(f"{k} {v}")
    return "{" + " ".join(parts) + "}"


# --------------------------------------------------------------------------- #
# Floor guard (fail-closed) — the machine enforcement of §4(2) + §D2.
# --------------------------------------------------------------------------- #
def validate_floor(edn: str, res: IngestResult, member_dids: set[str]) -> list[str]:
    """Return a list of floor violations. Empty list = clean. Callers MUST fail
    closed if non-empty (mirrors transparency-floor-and-gate.mjs discipline)."""
    violations: list[str] = []

    # F1 — no ownership keyword anywhere in the output.
    for kw in FORBIDDEN_KEYWORDS:
        if kw in edn:
            violations.append(f"F1: forbidden ownership keyword {kw} present in output")

    # F2 — no non-member DID/handle in output. Scan the SERIALIZED TEXT (not just the
    # result object) so an injected/leaked identity is caught fail-closed.
    for did in set(re.findall(r"did:[a-z0-9]+:[A-Za-z0-9._:-]+", edn)):
        if did not in member_dids:
            violations.append(f"F2: non-member id {did} leaked into output")

    # F3 — every edge has both endpoints among emitted (member) organisms.
    member_org_ids = {o[":organism/id"] for o in res.organisms.values()}
    for e in res.edges:
        if e[":en/from"] not in member_org_ids or e[":en/to"] not in member_org_ids:
            violations.append(f"F3: edge {e[':en/id']} has a non-member endpoint")
        # F4 — load + source present.
        if ":en/grasping-load" not in e:
            violations.append(f"F4: edge {e[':en/id']} missing :en/grasping-load")
        if not e.get(":en/source", "").startswith(":atproto"):
            violations.append(f"F4: edge {e[':en/id']} missing :en/source")

    return violations


def _all_dids(res: IngestResult) -> set[str]:
    return {o[":organism/did"] for o in res.organisms.values() if ":organism/did" in o}


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    members = {"did:plc:alice", "did:plc:bob"}
    follows = [
        Follow("did:plc:alice", "did:plc:bob"),            # member → member  (emitted)
        Follow("did:plc:alice", "did:plc:carol"),          # member → latent  (aggregate)
        Follow("did:plc:carol", "did:plc:bob"),            # latent → member  (aggregate)
        Follow("did:plc:dave", "did:plc:bob"),             # latent → member  (aggregate)
        Follow("did:plc:bob", "did:plc:alice", "depends-on"),  # member → member (emitted)
    ]
    res = ingest(follows, members)
    edn = to_edn(res)
    print(edn)
    v = validate_floor(edn, res, members)
    print("\n;; floor:", "CLEAN" if not v else v)
