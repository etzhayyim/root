"""weave.py — 系図 (keizu) relation-graph build + aggregate concentration. ADR-2606066000.

THE HEART of the actor and the G1/G2/G3/G4 anchor. Given the seed graph it:

  1. VALIDATES every node / relation / money flow against the closed structural vocab
     (mirror of the ontology :db/allowed + lexicon :enum/:const). A private-person node,
     a verdict relation kind, a bribe money kind, or an unsourced/under-sourced tie is a
     ValueError — not a silent drop. This is the third home of the invariants.
  2. WEAVES the validated records into an in-memory relation graph.
  3. Computes AGGREGATE, EDGE-PRIMARY concentration metrics (G4) — there is NO per-node
     power/influence score anywhere:
       - committee cross-organ concentration  (a committee drawing seats from many organs)
       - cross-committee co-membership          (one public seat sitting on >1 committee)
       - per-payee money concentration (HHI)    (award/subsidy/donation share by payee)
       - revolving-door chains                   (organ → committee-seat movement)

All findings are an accountability MAP (G5), never a target-list, and NON-adjudicating (G2):
the metrics describe ties and shares, never assert wrongdoing.

Stdlib only. Deterministic.
"""

from __future__ import annotations

from typing import Any

# ── closed vocab (mirror of the ontology :db/allowed) ───────────────────────────
NODE_SCOPES = ("public-office", "public-org", "public-committee", "public-role")
REL_KINDS = (
    "committee-membership", "appointment", "advisory-role", "co-membership",
    "revolving-door", "funding-tie", "statement-attribution", "procurement-award",
)
MONEY_KINDS = ("procurement-award", "subsidy", "grant", "political-donation", "budget-outlay")
SOURCING = ("representative", "authoritative")

# Tokens that would turn a factual map into an adjudication — must never appear as a kind.
VERDICT_TOKENS = ("corruption", "bribe", "kickback", "collusion", "guilt", "crime",
                  "fraud", "illegal", "slush", "不正", "違法", "汚職", "賄賂")

# G9 / G1 no-doxxing — a node is a PUBLIC seat/organ, so a personal-contact or sensitive-PII
# field on it is unrepresentable (any such datum lives encrypted off-graph, ADR-2605181100).
PII_FORBIDDEN_NODE_ATTRS = frozenset({
    "email", "phone", "tel", "mobile", "fax", "address", "home", "residence",
    "dob", "birthdate", "birthday", "ssn", "mynumber", "my-number", "passport",
    "personal-name", "private-name", "face", "photo", "headshot", "gender",
    "religion", "ethnicity", "health", "private",
})


def _kw(v: Any) -> str:
    """Normalize an edn keyword/string to a bare lowercase token (':rel/kind' → 'kind')."""
    s = str(v or "").lstrip(":")
    return s.split("/")[-1].lower()


# ── validation (G1/G2/G3) ───────────────────────────────────────────────────────
def validate_node(n: dict) -> None:
    scope = _kw(n.get(":node/scope", ""))
    if scope not in NODE_SCOPES:
        raise ValueError(
            f"G1: node scope {scope!r} not in {NODE_SCOPES} — a private person is unrepresentable "
            f"(keizu maps public seats/organs, never individuals)"
        )
    if "power-score" in n or ":node/power-score" in n or ":node/influence" in n or ":node/rank" in n:
        raise ValueError("G4: a per-node power/influence/rank score is unrepresentable (edge-primary)")
    for key in n:
        if _kw(key) in PII_FORBIDDEN_NODE_ATTRS:
            raise ValueError(
                f"G9/G1 no-doxxing: node field {key!r} is personal/sensitive PII — unrepresentable "
                f"on a public seat (any such datum lives encrypted off-graph, ADR-2605181100)"
            )
    if _kw(n.get(":node/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every node must declare :node/sourcing")


def validate_rel(r: dict) -> None:
    kind = _kw(r.get(":rel/kind", ""))
    if kind in VERDICT_TOKENS:
        raise ValueError(f"G2: relation kind {kind!r} is a verdict — unrepresentable (non-adjudicating)")
    if kind not in REL_KINDS:
        raise ValueError(f"G2: relation kind {kind!r} not in the factual closed vocab {REL_KINDS}")
    if r.get(":rel/non-adjudicating-notice") is not True:
        raise ValueError("G2: :rel/non-adjudicating-notice must be true")
    srcs = r.get(":rel/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 2:
        raise ValueError(f"G3: relation {r.get(':rel/id')!r} needs ≥2 public-source citations")
    if _kw(r.get(":rel/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every relation must declare :rel/sourcing")


def validate_statement(s: dict) -> None:
    """A public statement (発言) attributed to a public role. Must have a speaker + ≥1 public
    source (G3) + declared sourcing (G11). Non-adjudicating: a statement is recorded verbatim
    by topic, never characterized as true/false (ake/danjo own truth-rating)."""
    if not str(s.get(":statement/speaker", "")).strip():
        raise ValueError(f"statement {s.get(':statement/id')!r} needs a :statement/speaker")
    srcs = s.get(":statement/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 1:
        raise ValueError(f"G3: statement {s.get(':statement/id')!r} needs ≥1 public source")
    if _kw(s.get(":statement/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every statement must declare :statement/sourcing")


def validate_money(m: dict) -> None:
    kind = _kw(m.get(":money/kind", ""))
    if kind in VERDICT_TOKENS:
        raise ValueError(f"G2: money kind {kind!r} is a verdict — unrepresentable")
    if kind not in MONEY_KINDS:
        raise ValueError(f"G2: money kind {kind!r} not in the disclosed-flow vocab {MONEY_KINDS}")
    srcs = m.get(":money/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 2:
        raise ValueError(f"G3: money flow {m.get(':money/id')!r} needs ≥2 public-source citations")
    if _kw(m.get(":money/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every money flow must declare :money/sourcing")


# ── weave ───────────────────────────────────────────────────────────────────────
def weave(graph: dict) -> dict:
    """Validate + index the seed graph into an in-memory relation graph. Raises on a gate."""
    nodes = {n[":node/id"]: n for n in graph.get(":nodes", [])}
    for n in nodes.values():
        validate_node(n)
    committees = {c[":committee/id"]: c for c in graph.get(":committees", [])}
    rels = list(graph.get(":rels", []))
    for r in rels:
        validate_rel(r)
    money = list(graph.get(":money", []))
    for m in money:
        validate_money(m)
    statements = list(graph.get(":statements", []))
    for s in statements:
        validate_statement(s)
    return {
        "nodes": nodes,
        "committees": committees,
        "rels": rels,
        "money": money,
        "statements": statements,
    }


# ── aggregate, edge-primary concentration metrics (G4) ───────────────────────────
def committee_cross_organ(g: dict) -> list[dict]:
    """Per committee: how many DISTINCT organs its seats are drawn from (concentration of
    convening organ vs. diversity of member origins). Aggregate, no per-person score."""
    out = []
    nodes = g["nodes"]
    for cid, c in g["committees"].items():
        organs = []
        for mid in c.get(":committee/members", []):
            organ = nodes.get(mid, {}).get(":node/organ", "(unknown)")
            organs.append(organ)
        distinct = sorted(set(organs))
        out.append({
            "committee": cid,
            "label": c.get(":committee/label", cid),
            "member_count": len(c.get(":committee/members", [])),
            "distinct_organs": len(distinct),
            "organs": distinct,
        })
    return sorted(out, key=lambda x: (-x["member_count"], x["committee"]))


def cross_committee_seats(g: dict) -> list[dict]:
    """Public seats that sit on >1 committee (committee co-membership) — surfaced from the
    EDGES (:committee-membership), never a stored attribute on the seat."""
    by_seat: dict[str, list[str]] = {}
    for r in g["rels"]:
        if _kw(r.get(":rel/kind")) == "committee-membership":
            by_seat.setdefault(r[":rel/source"], []).append(r[":rel/target"])
    out = []
    for seat, comms in by_seat.items():
        uniq = sorted(set(comms))
        if len(uniq) > 1:
            out.append({"seat": seat, "committee_count": len(uniq), "committees": uniq})
    return sorted(out, key=lambda x: (-x["committee_count"], x["seat"]))


def money_concentration(g: dict) -> dict:
    """Per-payee money share + Herfindahl-Hirschman Index (HHI) over the disclosed flows.
    HHI ∈ (0,1]; higher = more concentrated in fewer payees. Aggregate, factual."""
    by_payee: dict[str, float] = {}
    total = 0.0
    for m in g["money"]:
        amt = float(m.get(":money/amount", 0.0))
        by_payee[m[":money/payee"]] = by_payee.get(m[":money/payee"], 0.0) + amt
        total += amt
    shares = {p: (v / total if total else 0.0) for p, v in by_payee.items()}
    hhi = sum(s * s for s in shares.values())
    ranked = sorted(shares.items(), key=lambda kv: -kv[1])
    return {"total": total, "hhi": round(hhi, 4), "shares": ranked, "by_payee": by_payee}


def payer_concentration(g: dict) -> dict:
    """Per-PAYER money share + HHI (which public authority/donor disburses most concentratedly).
    The payer-side complement of money_concentration (payee-side). Aggregate, factual (G2/G4)."""
    by_payer: dict[str, float] = {}
    total = 0.0
    for m in g["money"]:
        amt = float(m.get(":money/amount", 0.0))
        by_payer[m[":money/payer"]] = by_payer.get(m[":money/payer"], 0.0) + amt
        total += amt
    shares = {p: (v / total if total else 0.0) for p, v in by_payer.items()}
    hhi = sum(s * s for s in shares.values())
    ranked = sorted(shares.items(), key=lambda kv: -kv[1])
    return {"total": total, "hhi": round(hhi, 4), "shares": ranked, "by_payer": by_payer}


def revolving_door_chains(g: dict) -> list[dict]:
    """Organ → committee-seat movements (:revolving-door edges)."""
    out = []
    nodes = g["nodes"]
    for r in g["rels"]:
        if _kw(r.get(":rel/kind")) == "revolving-door":
            out.append({
                "from": r[":rel/source"],
                "from_label": nodes.get(r[":rel/source"], {}).get(":node/label", r[":rel/source"]),
                "to": r[":rel/target"],
                "to_label": nodes.get(r[":rel/target"], {}).get(":node/label", r[":rel/target"]),
                "as_of": r.get(":rel/as-of"),
            })
    return sorted(out, key=lambda x: str(x["from"]))


def connector_seats(g: dict) -> list[dict]:
    """Cross-organ connectors: a public seat sitting on committees that span MORE THAN ONE
    convening organ. Derived on read from the :committee-membership edges + each committee's
    organ (edge-primary, G4; aggregate, G3). A connector bridging distinct organs is the
    structural pattern keizu surfaces — never a per-person influence score."""
    comm_organ = {cid: c.get(":committee/organ", "(unknown)") for cid, c in g["committees"].items()}
    by_seat: dict[str, list[str]] = {}
    for r in g["rels"]:
        if _kw(r.get(":rel/kind")) == "committee-membership":
            by_seat.setdefault(r[":rel/source"], []).append(r[":rel/target"])
    out = []
    for seat, comms in by_seat.items():
        uniq_comms = sorted(set(comms))
        organs = sorted({comm_organ.get(c, "(unknown)") for c in uniq_comms})
        if len(uniq_comms) > 1 and len(organs) > 1:
            out.append({"seat": seat, "committees": uniq_comms,
                        "organs_bridged": len(organs), "organs": organs})
    return sorted(out, key=lambda x: (-x["organs_bridged"], x["seat"]))


def active_as_of(g: dict, ts: int) -> dict:
    """G10 / 非終末論 — time-travel: which relations + committee compositions are active as of
    `ts` (as-of/term-from ≤ ts). The graph is append-only, so a query at an earlier ts simply
    sees fewer datoms; nothing is ever overwritten or deleted."""
    active_rels = [r for r in g["rels"] if int(r.get(":rel/as-of", 0)) <= ts]
    active_comms = [c for c in g["committees"].values() if int(c.get(":committee/term-from", 0)) <= ts]
    return {
        "ts": ts,
        "active_rels": len(active_rels),
        "total_rels": len(g["rels"]),
        "active_committees": len(active_comms),
        "total_committees": len(g["committees"]),
    }


def award_and_fund(g: dict) -> list[dict]:
    """FACTUAL co-occurrence (non-adjudicating, G2): public roles that BOTH received public
    money (procurement-award / subsidy / grant) AND made a political donation. A classic
    accountability-map pattern — surfaced as a co-occurrence of two disclosed flows, NEVER as
    an allegation. Aggregate, edge-primary; the substance lives on the money edges (G4)."""
    received: dict[str, list] = {}   # payee → [(payer, amount)]
    donated: dict[str, list] = {}    # payer → [(payee, amount)]
    for m in g["money"]:
        kind = _kw(m.get(":money/kind"))
        amt = float(m.get(":money/amount", 0.0))
        if kind in ("procurement-award", "subsidy", "grant", "budget-outlay"):
            received.setdefault(m[":money/payee"], []).append((m[":money/payer"], amt))
        if kind == "political-donation":
            donated.setdefault(m[":money/payer"], []).append((m[":money/payee"], amt))
    out = []
    for node in sorted(set(received) & set(donated)):
        out.append({
            "node": node,
            "received_from": sorted({p for p, _ in received[node]}),
            "received_total": round(sum(a for _, a in received[node]), 2),
            "donated_to": sorted({p for p, _ in donated[node]}),
            "donated_total": round(sum(a for _, a in donated[node]), 2),
        })
    return out


def check_integrity(g: dict) -> dict:
    """Referential integrity: every reference must resolve to an existing entity. Per-record
    validators check a record's OWN fields; this catches DANGLING refs across records (a typo'd
    node id, a committee member that doesn't exist). A data-quality diagnostic, not a charter gate.

    Id-space per field:
      :rel/source, :rel/target  → node ∪ committee ∪ statement (a tie may point at any entity)
      :money/payer, :money/payee → node
      :committee/members         → node
      :statement/speaker         → node
    """
    nodes = set(g["nodes"])
    committees = set(g["committees"])
    statements = {s.get(":statement/id") for s in g["statements"]}
    rel_space = nodes | committees | statements
    dangling = []

    def chk(ref, space, kind, owner, field):
        if ref and ref not in space:
            dangling.append({"kind": kind, "owner": owner, "field": field, "ref": ref})

    for r in g["rels"]:
        chk(r.get(":rel/source"), rel_space, "rel", r.get(":rel/id"), "source")
        chk(r.get(":rel/target"), rel_space, "rel", r.get(":rel/id"), "target")
    for m in g["money"]:
        chk(m.get(":money/payer"), nodes, "money", m.get(":money/id"), "payer")
        chk(m.get(":money/payee"), nodes, "money", m.get(":money/id"), "payee")
    for cid, c in g["committees"].items():
        for mid in c.get(":committee/members", []):
            chk(mid, nodes, "committee", cid, "member")
    for s in g["statements"]:
        chk(s.get(":statement/speaker"), nodes, "statement", s.get(":statement/id"), "speaker")

    return {"dangling_count": len(dangling), "dangling": dangling}


def assert_integrity(g: dict) -> None:
    """Strict mode — raise if any reference dangles (used by the ingest/bridge data-quality gate)."""
    rep = check_integrity(g)
    if rep["dangling_count"]:
        first = rep["dangling"][0]
        raise ValueError(
            f"integrity: {rep['dangling_count']} dangling ref(s); e.g. {first['kind']} "
            f"{first['owner']!r} {first['field']}→{first['ref']!r} (no such entity)"
        )


def statement_index(g: dict) -> dict:
    """発言 (statements) aggregate: per-speaker statement count + per-topic speaker set (who
    spoke on what, from public record). Non-adjudicating — a statement is indexed by topic,
    never rated true/false (ake/danjo own truth). Aggregate (G3)."""
    by_speaker: dict[str, int] = {}
    by_topic: dict[str, set] = {}
    for s in g["statements"]:
        sp = s.get(":statement/speaker", "?")
        by_speaker[sp] = by_speaker.get(sp, 0) + 1
        by_topic.setdefault(s.get(":statement/topic", "(untopiced)"), set()).add(sp)
    return {
        "count": len(g["statements"]),
        "by_speaker": sorted(by_speaker.items(), key=lambda kv: (-kv[1], kv[0])),
        "by_topic": sorted(({"topic": t, "speakers": sorted(sp)} for t, sp in by_topic.items()),
                           key=lambda x: x["topic"]),
    }


def concentration(g: dict) -> dict:
    """The full aggregate-first concentration report (G3/G4). All metrics are derived on
    read from edges/flows; nothing is a per-person score."""
    return {
        "node_count": len(g["nodes"]),
        "committee_count": len(g["committees"]),
        "rel_count": len(g["rels"]),
        "money_count": len(g["money"]),
        "statement_count": len(g["statements"]),
        "committee_cross_organ": committee_cross_organ(g),
        "cross_committee_seats": cross_committee_seats(g),
        "connector_seats": connector_seats(g),
        "money_concentration": money_concentration(g),
        "payer_concentration": payer_concentration(g),
        "revolving_door": revolving_door_chains(g),
        "award_and_fund": award_and_fund(g),
        "statement_index": statement_index(g),
        "integrity": check_integrity(g),
    }


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn")
    g = weave(seed)
    c = concentration(g)
    print("# 系図 (keizu) — aggregate concentration over the :representative seed\n")
    print(f"nodes={c['node_count']} committees={c['committee_count']} rels={c['rel_count']} "
          f"money={c['money_count']} statements={c['statement_count']}\n")
    print("## committee cross-organ concentration")
    for r in c["committee_cross_organ"]:
        print(f"- {r['label']}: {r['member_count']} seats from {r['distinct_organs']} organ(s) {r['organs']}")
    print("\n## cross-committee seats (co-membership)")
    for r in c["cross_committee_seats"]:
        print(f"- {r['seat']} sits on {r['committee_count']} committees: {r['committees']}")
    mc = c["money_concentration"]
    print(f"\n## money concentration — HHI={mc['hhi']} over total {mc['total']:.0f}")
    for payee, share in mc["shares"]:
        print(f"- {payee}: {share*100:.1f}%")
    print("\n## revolving-door chains")
    for r in c["revolving_door"]:
        print(f"- {r['from_label']} → {r['to_label']} (as-of {r['as_of']})")
