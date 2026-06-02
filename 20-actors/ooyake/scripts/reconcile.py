#!/usr/bin/env python3
"""reconcile.py — OFFLINE demonstrator of ooyake's R1 `reconcile` cell.

Per ADR-2606021600 §5. The production reconcile cell FETCHES external authorities
(Wikidata / 行政機関コード / GeoNames) over the network — that path is G4 + Council
+ operator gated. THIS script demonstrates the promotion MECHANISM deterministically
and offline, against the bundled `authority-reference.edn` (which stands in for what
the cell would fetch).

Promotion rule (G5): a seed `:gov.unit` is promoted
    :representative / :unverified-seed  →  :authoritative / :maintainer-verified
ONLY when an authority record exists for its unit-id AND both :gov.unit/wikidata
and :gov.unit/official-url AGREE. Disagreement keeps the unit unverified and is
reported as a conflict (never silently promoted). Units with no authority record
stay :representative (honest coverage — not counted as verified).

Usage:
    python3 reconcile.py                 # print report to stdout
    python3 reconcile.py --json out.json # also write a machine report

NO network. NO writes to the seed (promotion is reported, not applied — applying is
an operator-gated step). Pure, repeatable, audit-friendly.
"""
import sys, json, os

# ── minimal EDN reader (maps / vectors / strings / keywords / numbers / comments)
def parse_edn(src):
    i = 0
    n = len(src)
    def skip():
        nonlocal i
        while i < n:
            c = src[i]
            if c in " \t\r\n,":
                i += 1; continue
            if c == ";":
                while i < n and src[i] != "\n":
                    i += 1
                continue
            break
    def read():
        nonlocal i
        skip()
        c = src[i]
        if c == '"':
            return read_str()
        if c == "{":
            return read_map()
        if c == "[":
            return read_vec()
        return read_atom()
    def read_str():
        nonlocal i
        i += 1
        out = []
        while i < n:
            c = src[i]; i += 1
            if c == "\\":
                e = src[i]; i += 1
                out.append({"n": "\n", "t": "\t", "r": "\r"}.get(e, e))
            elif c == '"':
                return "".join(out)
            else:
                out.append(c)
        raise ValueError("unterminated string")
    def read_vec():
        nonlocal i
        i += 1
        arr = []
        while True:
            skip()
            if src[i] == "]":
                i += 1; return arr
            arr.append(read())
    def read_map():
        nonlocal i
        i += 1
        d = {}
        while True:
            skip()
            if src[i] == "}":
                i += 1; return d
            k = read(); v = read()
            d[k] = v
    def read_atom():
        nonlocal i
        start = i
        while i < n and src[i] not in " \t\r\n,;{}[]\"":
            i += 1
        tok = src[start:i]
        if tok == "true": return True
        if tok == "false": return False
        if tok == "nil": return None
        if tok.startswith(":"): return tok          # keyword kept as string ":foo/bar"
        try:
            return int(tok)
        except ValueError:
            try: return float(tok)
            except ValueError: return tok
    skip()
    return read()

HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(HERE, "..", "registry")
SEED_FILES = [
    os.path.join(REG, "gov-units.seed.edn"),
    os.path.join(REG, "gov-units.jp-central.seed.edn"),
]
AUTH_FILE = os.path.join(REG, "authority-reference.edn")

def load_units():
    units = {}
    for f in SEED_FILES:
        doc = parse_edn(open(f, encoding="utf-8").read())
        for u in doc.get(":units", []):
            uid = u.get(":gov.unit/id")
            if uid:
                units[uid] = u
    return units

def load_authority():
    doc = parse_edn(open(AUTH_FILE, encoding="utf-8").read())
    return {r[":unit"]: r for r in doc.get(":authority-records", [])}

def main():
    units = load_units()
    auth = load_authority()
    promoted, conflicts, no_authority = [], [], []
    for uid, u in sorted(units.items()):
        rec = auth.get(uid)
        if rec is None:
            no_authority.append(uid); continue
        wd_ok = u.get(":gov.unit/wikidata") == rec.get(":wikidata")
        url_ok = u.get(":gov.unit/official-url") == rec.get(":official-url")
        if wd_ok and url_ok:
            promoted.append(uid)
        else:
            conflicts.append({
                "unit": uid,
                "wikidata_match": wd_ok, "official_url_match": url_ok,
                "seed_wikidata": u.get(":gov.unit/wikidata"), "auth_wikidata": rec.get(":wikidata"),
                "seed_url": u.get(":gov.unit/official-url"), "auth_url": rec.get(":official-url"),
            })

    total = len(units)
    report = {
        "total_units": total,
        "authority_records": len(auth),
        "promoted_to_authoritative": sorted(promoted),
        "conflicts_kept_unverified": conflicts,
        "no_authority_record_kept_representative": sorted(no_authority),
        "coverage": {
            "authoritative_after": len(promoted),
            "representative_after": total - len(promoted),
            "authoritative_pct": round(100.0 * len(promoted) / total, 1) if total else 0.0,
        },
    }

    print("ooyake reconcile (offline demo, ADR-2606021600 §5)")
    print(f"  units in seed         : {total}")
    print(f"  authority records     : {len(auth)}")
    print(f"  → PROMOTED authoritative : {len(promoted)}  {sorted(promoted)}")
    print(f"  → conflicts (unverified) : {len(conflicts)}")
    for c in conflicts:
        print(f"      ! {c['unit']}  wikidata_match={c['wikidata_match']} url_match={c['official_url_match']}")
    print(f"  → no authority (stays representative): {len(no_authority)}")
    print(f"  coverage: {report['coverage']['authoritative_pct']}% authoritative "
          f"({len(promoted)}/{total})  [rest honestly :representative, G5]")

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  wrote {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
