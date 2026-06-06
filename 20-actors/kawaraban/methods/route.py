#!/usr/bin/env python3
"""kawaraban 瓦版 — the MEDIUM: actor→面 routing + the actor-to-actor connection wire.

ADR-2606061900. Reads a kotoba-EDN news-medium graph (:news.outlet/* :news.section/*
:news.article/* :news.mention/* :news.wire/*) and exposes the connective core of the
news medium:

  1. classify(rows)            — bucket the flat datom vector into entity maps.
  2. validate(articles)        — enforce the structural gates (G1/G4/G9/G11) by REFUSAL:
                                 every article must be :mirror (outlet+url) OR :actor-event
                                 (source-actor+source-tid); :verdict/:truth-rating/:full-text/
                                 :speak-as may never appear. An illegal article RAISES — a
                                 representable charter violation is never silently accepted.
  3. wire_table(rows)          — actor did → 面 (the medium config; seed :news.wire/* rows,
                                 with the canonical ACTOR_WIRE constant as fallback).
  4. section_of(article, wires)— the 面 an article belongs to (explicit, else routed by wire).
  5. actor_links(articles, mentions)
                               — THE WIRE: for each article, the set of first-party actors it
                                 connects (mention targets of kind :actor); every co-mention is
                                 an actor-to-actor edge. Returns the adjacency that makes
                                 kawaraban a medium "connecting actor to actor".

CONSTITUTIONAL framing: an article is an OBSERVATION carried by a medium, never a verdict
(G1) and never spoken in anyone's name (G9). A mention edge is observational (role ∈
{subject source mentioned affected responding}), never an accusation (watari/watatsuna
resilience-not-target precedent). kawaraban authors no :original claim (G11) — it mirrors
real outlets and projects first-party actor events, and the article × mention × 面 graph is
the wire between actors.

stdlib only. Usage:
    python3 route.py [seed.edn]
"""
from __future__ import annotations
import sys
import re
import pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from watari/watatsuna
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':
        return True
    if t == 'false':
        return False
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t  # keep keywords as ":ns/name" strings
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            v = _parse(it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def load_edn(path: pathlib.Path):
    it = _tokens(path.read_text(encoding='utf-8'))
    return _parse(it)


# ── canonical actor → 面 (men) wire fallback. The seed :news.wire/* rows are the SSoT;
#    this constant is the last-resort default so a first-party actor always has a 面.
ACTOR_WIRE: dict[str, str] = {
    "did:web:etzhayyim.com:actor:danjo": "politics",
    "did:web:etzhayyim.com:actor:ooyake": "politics",
    "did:web:etzhayyim.com:actor:moushibumi": "politics",
    "did:web:etzhayyim.com:actor:kanae": "economy",
    "did:web:etzhayyim.com:actor:kanjo": "economy",
    "did:web:etzhayyim.com:actor:kabuto": "economy",
    "did:web:etzhayyim.com:actor:mitooshi": "international",
    "did:web:etzhayyim.com:actor:watari": "international",
    "did:web:etzhayyim.com:actor:watatsuna": "international",
    "did:web:etzhayyim.com:actor:kataribe": "culture",
    "did:web:etzhayyim.com:actor:sanae": "society",
    "did:web:etzhayyim.com:actor:mitsuho": "society",
    "did:web:etzhayyim.com:actor:noroshi": "science",
    "did:web:etzhayyim.com:actor:hotaru": "science",
}

# Forbidden article fields — if any appears truthy, a charter invariant is violated.
_FORBIDDEN = {
    ":news.article/verdict": "G1 (mirror-not-adjudicator)",
    ":news.article/truth-rating": "G1 (no fact-check score)",
    ":news.article/full-text": "G4 (copyright / link-out only)",
    ":news.article/personalized-for": "G3 (no per-reader feed)",
    ":news.article/speak-as": "G9 (mirror-not-impersonation)",
}
VALID_KINDS = (":mirror", ":actor-event")


def classify(rows):
    outlets, sections, articles, mentions, wires = {}, {}, [], [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ":news.outlet/id" in r:
            outlets[r[":news.outlet/id"]] = r
        elif ":news.section/id" in r:
            sections[r[":news.section/id"]] = r
        elif ":news.article/id" in r:
            articles.append(r)
        elif ":news.mention/id" in r:
            mentions.append(r)
        elif ":news.wire/id" in r:
            wires.append(r)
    return outlets, sections, articles, mentions, wires


def validate(articles) -> None:
    """Enforce G1/G3/G4/G9/G11 by refusal. Raises ValueError on the first violation."""
    for a in articles:
        aid = a.get(":news.article/id", "<?>")
        # G1/G3/G4/G9 — forbidden fields may never appear truthy.
        for field, gate in _FORBIDDEN.items():
            v = a.get(field)
            if v not in (None, False, 0):
                raise ValueError(f"{aid}: field {field} = {v!r} violates {gate}; unrepresentable")
        # G11 — every article is :mirror or :actor-event; :original is not a kind.
        kind = a.get(":news.article/kind")
        if kind not in VALID_KINDS:
            raise ValueError(
                f"{aid}: kind {kind!r} not in {VALID_KINDS} — kawaraban is a medium, not a source (G11)"
            )
        if kind == ":mirror":
            if not a.get(":news.article/outlet") or not a.get(":news.article/url"):
                raise ValueError(f"{aid}: :mirror article needs :outlet + :url (G4/G5 link-out)")
        else:  # :actor-event
            if not a.get(":news.article/source-actor") or not a.get(":news.article/source-tid"):
                raise ValueError(
                    f"{aid}: :actor-event needs :source-actor + :source-tid (G7/G11 provenance)"
                )
        # G4 — bounded excerpt.
        ex = a.get(":news.article/excerpt", "")
        if isinstance(ex, str) and len(ex) > 280:
            raise ValueError(f"{aid}: excerpt {len(ex)} chars > 280 (G4 fair-use bound)")


def wire_table(wires) -> dict[str, str]:
    """actor did → 面 (men keyword without the colon). Seed rows first, then ACTOR_WIRE."""
    table = dict((k, v) for k, v in ACTOR_WIRE.items())
    for w in wires:
        actor = w.get(":news.wire/actor")
        sec = w.get(":news.wire/section")  # section id ref, e.g. "sec.economy"
        if actor and sec:
            table[actor] = sec.split(".", 1)[-1] if isinstance(sec, str) else sec
    return table


def section_men(section_id: str, sections: dict) -> str:
    s = sections.get(section_id, {})
    men = s.get(":news.section/men", ":?")
    return men.lstrip(":") if isinstance(men, str) else str(men)


def actor_targets(article_id: str, mentions) -> list[str]:
    """First-party actor mention targets of one article (the wire endpoints)."""
    out = []
    for m in mentions:
        if m.get(":news.mention/article") == article_id and m.get(":news.mention/target-kind") == ":actor":
            out.append(m.get(":news.mention/target"))
    return out


def actor_links(articles, mentions):
    """THE WIRE. For every article, each pair of co-mentioned first-party actors is an
    actor-to-actor edge. Returns (edges, degree):
      edges  : {frozenset({a,b}): count of shared articles}
      degree : {actor: number of distinct actors it is wired to}
    This is the medium that connects actor to actor — the user's headline requirement.
    """
    edges: dict[frozenset, int] = defaultdict(int)
    neighbors: dict[str, set] = defaultdict(set)
    for a in articles:
        aid = a.get(":news.article/id")
        actors = sorted(set(actor_targets(aid, mentions)))
        for i in range(len(actors)):
            for j in range(i + 1, len(actors)):
                pair = frozenset({actors[i], actors[j]})
                edges[pair] += 1
                neighbors[actors[i]].add(actors[j])
                neighbors[actors[j]].add(actors[i])
    degree = {a: len(ns) for a, ns in neighbors.items()}
    return dict(edges), degree


def _short(did: str) -> str:
    return did.rsplit(":", 1)[-1] if did.startswith("did:") else did


def main(argv):
    seed = pathlib.Path(argv[1]) if len(argv) > 1 else (
        pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-news-graph.kotoba.edn"
    )
    rows = load_edn(seed)
    outlets, sections, articles, mentions, wires = classify(rows)
    validate(articles)
    table = wire_table(wires)
    edges, degree = actor_links(articles, mentions)

    print(f"kawaraban route — {len(outlets)} outlets · {len(sections)} 面 · "
          f"{len(articles)} articles · {len(mentions)} mentions · {len(wires)} wires")
    print("\nactor → 面 wire (medium config):")
    for actor, men in sorted(table.items()):
        if any(w.get(':news.wire/actor') == actor for w in wires):
            print(f"  {_short(actor):12s} → {men}")
    print("\nactor-to-actor wire (co-mention edges, the medium):")
    for pair, n in sorted(edges.items(), key=lambda kv: (-kv[1], sorted(kv[0]))):
        a, b = sorted(_short(x) for x in pair)
        print(f"  {a:12s} —{n}— {b}")
    print("\nmost-wired actors (degree):")
    for actor, d in sorted(degree.items(), key=lambda kv: (-kv[1], kv[0]))[:5]:
        print(f"  {_short(actor):12s} wired to {d} actor(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
