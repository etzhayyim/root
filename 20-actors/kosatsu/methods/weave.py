"""weave.py — 高札 (kosatsu) competing-claim build + divergence engine. ADR-2606072000.

THE HEART of the actor and the G1..G5 anchor. Given the seed designation graph it:

  1. VALIDATES every authority / subject / designation against the closed structural vocab
     (mirror of the ontology :db/allowed + lexicon :enum/:const). An etzhayyim-authored
     designation, a verdict measure (:criminal/:guilty/:terrorist), an asserter-less
     designation, a per-subject risk score, or an under-sourced/non-primary-sourced event is a
     ValueError — not a silent drop. This is the third home of the invariants.
  2. WEAVES the validated records into an in-memory competing-claim graph.
  3. Computes the AGGREGATE, EDGE-PRIMARY, POLITICALLY-NEUTRAL views — there is NO per-subject
     risk/guilt/threat score anywhere; "crime/sanction" is asserter-relative BY CONSTRUCTION:
       - status_as_of(subject, asserter, ts)  — listed/delisted from the event log (非終末論)
       - divergence(subject)                  — which asserters list / delist / are silent
       - divergence_class                     — :unanimous | :contested | :single-asserter
       - agreement_index                      — Σ contested / Σ designated subjects
       - co_designation                       — subjects sharing an asserter+program (network)

The OUTPUT is a MIRROR (G9) of who-designated-whom and WHERE-JURISDICTIONS-DISAGREE, routed to
compliance-awareness / due-process visibility / de-risking — NEVER a verdict and NEVER a
"who-to-freeze/attack" target-list. etzhayyim asserts nothing about any subject; it reports,
attributed, what each public authority itself posted.

Stdlib only. Deterministic.
"""

from __future__ import annotations

from typing import Any

# ── closed vocab (mirror of the ontology :db/allowed) ───────────────────────────
AUTHORITY_KINDS = ("state-treasury", "state-foreign-ministry", "financial-regulator",
                   "law-enforcement", "supranational", "international-body")
MEASURE_KINDS = ("asset-freeze", "financial-sanction", "transaction-ban", "travel-restriction",
                 "export-control", "sectoral-restriction", "list-inclusion",
                 "arrest-warrant", "wanted-notice")
DESIGNATION_STATUS = ("listed", "delisted")
SUBJECT_KINDS = ("designated-entity", "designated-org", "designated-person", "designated-vessel",
                 "designated-aircraft", "designated-wallet", "designated-domain")
SOURCING = ("representative", "authoritative")
DIVERGENCE_CLASSES = ("unanimous", "contested", "single-asserter")

# G1 — etzhayyim NEVER authors a designation. An asserter id/kind that resolves to ourselves is
# unrepresentable (mirror-not-adjudicator). These tokens may not appear as an asserter.
SELF_TOKENS = ("etzhayyim", "self", "our", "kosatsu", "amanomibashira", "天御柱")

# G2 — tokens that would turn an attributed mirror into OUR verdict — must never be a measure or
# a status. kosatsu mirrors an authority's INSTRUMENT (asset-freeze/…); it never labels a subject.
VERDICT_TOKENS = ("criminal", "guilty", "convicted", "terrorist", "enemy", "evil", "felon",
                  "perpetrator", "crime", "guilt", "threat", "犯罪者", "有罪", "テロリスト", "悪")

# G3 / Charter Rider §2(e) — a designation must cite the AUTHORITY'S OWN primary publication.
# A commercial sanctions-screening terminal is a PROHIBITED citation (anti-gatekeeping: cite the
# public record, never the paywalled compilation). Refused on EVERY path (seed / ingest / bridge).
SOURCE_DENY = ("worldcheck", "world-check", "refinitiv", "dow jones risk", "lexisnexis",
               "accuity", "factiva", "complyadvantage", "comply advantage", "sanctions.io",
               "opensanctions premium", "chainalysis", "elliptic", "trm labs", "bloomberg")

# G5/G6/G9 no-doxxing — a subject is a PUBLIC designation target, so a private-life PII field on
# it is unrepresentable (only the authority-published identifier; anything else lives encrypted
# off-graph, ADR-2605181100).
PII_FORBIDDEN_SUBJECT_ATTRS = frozenset({
    "email", "phone", "tel", "mobile", "fax", "home", "residence", "dob", "birthdate",
    "birthday", "ssn", "mynumber", "my-number", "passport", "face", "photo", "headshot",
    "health", "religion", "ethnicity", "family", "relatives", "geolocation", "gps",
    "home-address", "private",
})


def _kw(v: Any) -> str:
    """Normalize an edn keyword/string to a bare lowercase token (':designation/measure' → 'measure')."""
    s = str(v or "").lstrip(":")
    return s.split("/")[-1].lower()


def source_denied(sources) -> str:
    """Return the first prohibited commercial screening terminal found in any source, or '' if clean."""
    blob = " ".join(str(s) for s in (sources or [])).lower()
    for d in SOURCE_DENY:
        if d in blob:
            return d
    return ""


# ── validation (G1/G2/G3/G5) ────────────────────────────────────────────────────
def validate_authority(a: dict) -> None:
    aid = str(a.get(":authority/id", "")).strip().lower()
    if not aid:
        raise ValueError("authority needs :authority/id")
    for tok in SELF_TOKENS:
        if tok in aid:
            raise ValueError(
                f"G1: authority {aid!r} resolves to etzhayyim — UNREPRESENTABLE. kosatsu mirrors "
                f"PUBLIC authorities; it never authors a designation (mirror-not-adjudicator)."
            )
    kind = _kw(a.get(":authority/kind", ""))
    if kind not in AUTHORITY_KINDS:
        raise ValueError(f"G1: authority kind {kind!r} not in {AUTHORITY_KINDS}")
    if not str(a.get(":authority/stance", "")).strip():
        raise ValueError(f"G6 stance-explicit: authority {aid!r} must declare its OWN :authority/stance")
    srcs = a.get(":authority/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 1:
        raise ValueError(f"G3: authority {aid!r} needs ≥1 primary-publication source")
    if (d := source_denied(srcs)):
        raise ValueError(f"Rider §2(e): source {d!r} is a commercial screening terminal — prohibited citation")
    if _kw(a.get(":authority/sourcing", "")) not in SOURCING:
        raise ValueError("G10: every authority must declare :authority/sourcing")


def validate_subject(s: dict) -> None:
    kind = _kw(s.get(":subject/kind", ""))
    if kind not in SUBJECT_KINDS:
        raise ValueError(f"G5: subject kind {kind!r} not in {SUBJECT_KINDS}")
    if "risk-score" in s or ":subject/risk-score" in s or ":subject/guilt" in s or ":subject/threat-level" in s:
        raise ValueError("G2/G7: a per-subject risk/guilt/threat score is unrepresentable (edge-primary; we never rate a subject)")
    for key in s:
        if _kw(key) in PII_FORBIDDEN_SUBJECT_ATTRS:
            raise ValueError(
                f"G5/G9 no-doxxing: subject field {key!r} is private-life PII — unrepresentable. A "
                f"subject carries only the authority-published identifier (private data lives "
                f"encrypted off-graph, ADR-2605181100)."
            )
    if _kw(s.get(":subject/sourcing", "")) not in SOURCING:
        raise ValueError("G10: every subject must declare :subject/sourcing")


def validate_designation(d: dict) -> None:
    if not str(d.get(":designation/asserter", "")).strip():
        raise ValueError(
            f"G2: designation {d.get(':designation/id')!r} has NO asserter — an asserter-less "
            f"'global truth' designation is unrepresentable. Every designation is attributed."
        )
    measure = _kw(d.get(":designation/measure", ""))
    if measure in VERDICT_TOKENS:
        raise ValueError(f"G2: measure {measure!r} is a verdict/label — unrepresentable (we mirror an instrument, never judge a subject)")
    if measure not in MEASURE_KINDS:
        raise ValueError(f"G3: measure {measure!r} not in the authority-instrument vocab {MEASURE_KINDS}")
    status = _kw(d.get(":designation/status", ""))
    if status in VERDICT_TOKENS or status in ("permanent", "final", "convicted"):
        raise ValueError(f"G4: status {status!r} is a final/verdict state — unrepresentable (非終末論)")
    if status not in DESIGNATION_STATUS:
        raise ValueError(f"G4: status {status!r} not in {DESIGNATION_STATUS}")
    if d.get(":designation/asserted-notice") is not True:
        raise ValueError("G1/G2: :designation/asserted-notice must be true (this is an ATTRIBUTED mirror, not our claim)")
    try:
        int(d.get(":designation/posted-at", 0))
    except (TypeError, ValueError):
        raise ValueError(f"designation {d.get(':designation/id')!r} :posted-at must be an integer date")
    if status == "delisted" and ":designation/lifted-at" not in d:
        raise ValueError(f"G4: a :delisted designation {d.get(':designation/id')!r} must carry :designation/lifted-at (the removal event date)")
    srcs = d.get(":designation/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 2:
        raise ValueError(f"G3: designation {d.get(':designation/id')!r} needs ≥2 PRIMARY-publication citations")
    if (dn := source_denied(srcs)):
        raise ValueError(f"Rider §2(e): source {dn!r} is a commercial screening terminal — prohibited citation")
    if _kw(d.get(":designation/sourcing", "")) not in SOURCING:
        raise ValueError("G10: every designation must declare :designation/sourcing")


# ── weave ───────────────────────────────────────────────────────────────────────
def weave(graph: dict) -> dict:
    """Validate + index the seed graph into an in-memory competing-claim graph. Raises on a gate."""
    authorities = {a[":authority/id"]: a for a in graph.get(":authorities", [])}
    for a in authorities.values():
        validate_authority(a)
    subjects = {s[":subject/id"]: s for s in graph.get(":subjects", [])}
    for s in subjects.values():
        validate_subject(s)
    designations = list(graph.get(":designations", []))
    for d in designations:
        validate_designation(d)
    return {"authorities": authorities, "subjects": subjects, "designations": designations}


# ── status as-of (the event log → current state) ─────────────────────────────────
def status_as_of(g: dict, subject: str, asserter: str, ts: int | None = None) -> str | None:
    """The (subject, asserter) status as of `ts` (default: latest) read from the append-only
    event log: the most recent designation event (posted-at ≤ ts, or lifted-at ≤ ts for a
    delisting) wins. Returns 'listed' | 'delisted' | None (asserter never designated subject).
    Nothing is ever overwritten — an earlier ts simply sees fewer events (G4/非終末論)."""
    events = []
    for d in g["designations"]:
        if d.get(":designation/subject") != subject or d.get(":designation/asserter") != asserter:
            continue
        st = _kw(d.get(":designation/status"))
        eff = int(d.get(":designation/lifted-at", d.get(":designation/posted-at", 0))) if st == "delisted" \
            else int(d.get(":designation/posted-at", 0))
        if ts is None or eff <= ts:
            events.append((eff, st))
    if not events:
        return None
    events.sort(key=lambda x: x[0])
    return events[-1][1]


def divergence(g: dict, subject: str, ts: int | None = None) -> dict:
    """The political-stance core (G2): for one subject, partition the TRACKED authorities into
    {listing, delisted, silent} as of `ts`. The divergence CLASS is computed only over the
    authorities that actually OPINED (listing ∪ delisted) — silence is NOT inferred as dissent
    (a fairer, more neutral reading: an authority that never designated the subject has taken no
    position, not a contrary one):

      - single-asserter : exactly one authority ever opined (only one jurisdiction took a stance)
      - contested       : opinions ACTIVELY CONFLICT — ≥1 authority currently lists it AND ≥1
                          authority delisted it (a real disagreement on current status)
      - unanimous       : ≥2 authorities opined and they AGREE (all currently listing, or all delisted)

    Separately, `coverage_split` flags the softer signal the user cares about — listed by some
    jurisdictions while OTHERS (silent) never designated it (e.g. one bloc sanctions, another does
    not). It is reported as a field, NOT folded into the class, so we never overstate disagreement.
    This is the computed, neutral FACT that 'what is sanctionable varies by political position'."""
    listing, delisted, silent = [], [], []
    for aid in g["authorities"]:
        st = status_as_of(g, subject, aid, ts)
        if st == "listed":
            listing.append(aid)
        elif st == "delisted":
            delisted.append(aid)
        else:
            silent.append(aid)
    n_opined = len(listing) + len(delisted)
    if n_opined <= 1:
        cls = "single-asserter"
    elif len(listing) > 0 and len(delisted) > 0:
        cls = "contested"
    else:
        cls = "unanimous"   # ≥2 opined and they agree (all listing or all delisted)
    return {
        "subject": subject,
        "listing": sorted(listing),
        "delisted": sorted(delisted),
        "silent": sorted(silent),
        "class": cls,
        "coverage_split": bool(listing and silent),
    }


def divergence_all(g: dict, ts: int | None = None) -> list[dict]:
    """divergence() over every designated subject, sorted contested-first (the interesting cases)."""
    order = {"contested": 0, "single-asserter": 1, "unanimous": 2}
    out = [divergence(g, sid, ts) for sid in _designated_subjects(g)]
    return sorted(out, key=lambda x: (order.get(x["class"], 9), x["subject"]))


def _designated_subjects(g: dict) -> list[str]:
    return sorted({d.get(":designation/subject") for d in g["designations"] if d.get(":designation/subject")})


def agreement_index(g: dict, ts: int | None = None) -> dict:
    """Aggregate: how contested is the whole board? contested / designated subjects ∈ [0,1].
    A HIGH index means jurisdictions disagree a lot (crime/sanction is highly stance-relative)."""
    divs = divergence_all(g, ts)
    n = len(divs)
    contested = sum(1 for d in divs if d["class"] == "contested")
    single = sum(1 for d in divs if d["class"] == "single-asserter")
    unanimous = sum(1 for d in divs if d["class"] == "unanimous")
    coverage_split = sum(1 for d in divs if d.get("coverage_split"))
    return {
        "designated_subjects": n,
        "contested": contested,
        "single_asserter": single,
        "unanimous": unanimous,
        "coverage_split": coverage_split,
        "contested_ratio": round(contested / n, 4) if n else 0.0,
    }


def delisting_timeline(g: dict) -> list[dict]:
    """G4/非終末論: every delisting EVENT as an as-of record (the original :listed datom is never
    deleted; this is the removal event in the append-only history)."""
    out = []
    for d in g["designations"]:
        if _kw(d.get(":designation/status")) == "delisted":
            out.append({
                "designation": d.get(":designation/id"),
                "asserter": d.get(":designation/asserter"),
                "subject": d.get(":designation/subject"),
                "posted_at": d.get(":designation/posted-at"),
                "lifted_at": d.get(":designation/lifted-at"),
                "program": d.get(":designation/program"),
            })
    return sorted(out, key=lambda x: (int(x["lifted_at"] or 0), str(x["designation"])))


def by_authority(g: dict, ts: int | None = None) -> list[dict]:
    """Per-asserter slice: how many subjects each authority CURRENTLY lists (as-of). Aggregate;
    the count is on the EDGES, never a per-authority 'power' score."""
    counts: dict[str, dict] = {}
    for aid, a in g["authorities"].items():
        listed = sum(1 for sid in _designated_subjects(g) if status_as_of(g, sid, aid, ts) == "listed")
        counts[aid] = {
            "authority": aid,
            "label": a.get(":authority/label", aid),
            "jurisdiction": a.get(":authority/jurisdiction", "?"),
            "listed_subjects": listed,
        }
    return sorted(counts.values(), key=lambda x: (-x["listed_subjects"], x["authority"]))


def co_designation(g: dict, ts: int | None = None) -> list[dict]:
    """Subjects that share an asserter+program (currently listed) — a co-designation edge that
    composes into a network (a sanctions PROGRAM links its subjects). Aggregate, edge-primary;
    a resilience/awareness map of program co-membership, NEVER a target cluster (G9)."""
    by_prog: dict[tuple, list[str]] = {}
    for d in g["designations"]:
        if status_as_of(g, d.get(":designation/subject"), d.get(":designation/asserter"), ts) != "listed":
            continue
        key = (d.get(":designation/asserter"), d.get(":designation/program"))
        by_prog.setdefault(key, []).append(d.get(":designation/subject"))
    out = []
    for (asserter, program), subs in by_prog.items():
        uniq = sorted(set(subs))
        if len(uniq) > 1:
            out.append({"asserter": asserter, "program": program, "subjects": uniq, "count": len(uniq)})
    return sorted(out, key=lambda x: (-x["count"], x["asserter"], str(x["program"])))


def check_integrity(g: dict) -> dict:
    """Referential integrity: every designation's asserter/subject must resolve. A data-quality
    diagnostic, not a charter gate."""
    authorities = set(g["authorities"])
    subjects = set(g["subjects"])
    dangling = []
    for d in g["designations"]:
        if d.get(":designation/asserter") not in authorities:
            dangling.append({"designation": d.get(":designation/id"), "field": "asserter", "ref": d.get(":designation/asserter")})
        if d.get(":designation/subject") not in subjects:
            dangling.append({"designation": d.get(":designation/id"), "field": "subject", "ref": d.get(":designation/subject")})
    return {"dangling_count": len(dangling), "dangling": dangling}


def assert_integrity(g: dict) -> None:
    rep = check_integrity(g)
    if rep["dangling_count"]:
        first = rep["dangling"][0]
        raise ValueError(
            f"integrity: {rep['dangling_count']} dangling ref(s); e.g. designation "
            f"{first['designation']!r} {first['field']}→{first['ref']!r} (no such entity)"
        )


def report(g: dict, ts: int | None = None) -> dict:
    """The full aggregate-first, politically-neutral competing-claim report (G2/G4/G9)."""
    return {
        "authority_count": len(g["authorities"]),
        "subject_count": len(g["subjects"]),
        "designation_count": len(g["designations"]),
        "agreement_index": agreement_index(g, ts),
        "divergence": divergence_all(g, ts),
        "by_authority": by_authority(g, ts),
        "delisting_timeline": delisting_timeline(g),
        "co_designation": co_designation(g, ts),
        "integrity": check_integrity(g),
    }


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn")
    g = weave(seed)
    r = report(g)
    print("# 高札 (kosatsu) — competing-claim report over the :representative seed\n")
    ai = r["agreement_index"]
    print(f"authorities={r['authority_count']} subjects={r['subject_count']} designations={r['designation_count']}")
    print(f"contested={ai['contested']} single-asserter={ai['single_asserter']} unanimous={ai['unanimous']} "
          f"contested_ratio={ai['contested_ratio']}\n")
    print("## divergence (where jurisdictions disagree — the political-stance signal)")
    for d in r["divergence"]:
        print(f"- {d['subject']} [{d['class']}]: listing={d['listing']} delisted={d['delisted']} silent={d['silent']}")
    print("\n## delisting timeline (as-of history, append-only)")
    for d in r["delisting_timeline"]:
        print(f"- {d['asserter']} delisted {d['subject']} on {d['lifted_at']} (listed {d['posted_at']})")
    print("\n## by authority (currently listed subjects)")
    for a in r["by_authority"]:
        print(f"- {a['label']} ({a['jurisdiction']}): {a['listed_subjects']} listed")
