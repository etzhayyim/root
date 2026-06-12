#!/usr/bin/env python3
"""yabai — kotoba Datomic transact bridge (ADR-2605301400 §T3 save-path).

Pushes the kotoba-native CTI / passive-DNS graph into a running kotoba node's Datom
log via POST /xrpc/com.etzhayyim.apps.kotoba.datomic.transact, emitting datomic
list-form datoms `[:db/add E A V]` (E = entity id string; cardinality-many fans out).

G6/G10 (constitutional): every :access/* record MUST carry :cti.attr/encrypted true —
this bridge REFUSES to transact if any access record is plaintext (the analyze
self-audit invariant, enforced at write).

AUTH (ADR-2605231525, no platform-held key): a write needs EITHER an operator JWT
(KOTOBA_TOKEN, sub == operator_did) OR a CACAO authorising `datom:transact` on the
graph CID (--cacao / KOTOBA_CACAO_B64). Without either it is a DRY RUN.

stdlib only. Usage:
    python3 methods/transact.py                               # dry-run + encryption check
    python3 methods/transact.py --graph <CID>                 # live (KOTOBA_TOKEN operator JWT)
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yabai_edn import load_edn, edn_val, edn_str  # noqa: E402

ACTOR = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ACTOR.parent.parent / "00-contracts" / "schemas" / "passive-dns-cti-ontology.kotoba.edn"
NSID_TRANSACT = "com.etzhayyim.apps.kotoba.datomic.transact"
ID_KEYS = (
    ":domain/id", ":pdns/id", ":iphist/id", ":tlscert/id",
    ":indicator/id", ":access/id", ":btobs/id",
)


def rows_to_datoms(rows):
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        e = next((r[k] for k in ID_KEYS if k in r), None)
        if e is None:
            continue
        for k, v in r.items():
            if k in ID_KEYS:
                continue
            for item in (v if isinstance(v, list) else [v]):
                out.append(f"[:db/add {edn_str(e)} {k} {edn_val(item)}]")
    return out


def schema_datoms():
    onto = load_edn(SCHEMA)
    attrs = onto.get(":attributes", []) if isinstance(onto, dict) else []
    # drop :db/doc — its free-text carries '|' which the kotoba EDN reader rejects.
    return ["{" + " ".join(f"{k} {edn_val(v)}" for k, v in a.items() if k != ":db/doc") + "}"
            for a in attrs]


def check_encryption_invariant(rows) -> int:
    return sum(1 for r in rows if isinstance(r, dict) and ":access/id" in r
               and r.get(":cti.attr/encrypted") is not True)


def _post(url, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    tok = os.environ.get("KOTOBA_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (own kotoba node)
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body_txt = exc.read().decode("utf-8") or ""
        try:
            return exc.code, json.loads(body_txt)
        except json.JSONDecodeError:
            return exc.code, {"error": body_txt}


def main(argv):
    url = os.environ.get("KOTOBA_URL", "http://127.0.0.1:8077")
    graph = (argv[argv.index("--graph") + 1] if "--graph" in argv
             else os.environ.get("YABAI_GRAPH_CID"))
    cacao = (argv[argv.index("--cacao") + 1] if "--cacao" in argv
             else os.environ.get("KOTOBA_CACAO_B64"))
    merged = ACTOR / "data" / "passive-dns.merged.kotoba.edn"
    if not merged.exists():
        merged = ACTOR / "data" / "seed-passive-dns.kotoba.edn"

    rows = [r for r in load_edn(merged) if isinstance(r, dict)]
    violations = check_encryption_invariant(rows)
    if violations:
        print(f"!! REFUSED: {violations} access-audit record(s) lack :cti.attr/encrypted true "
              "(G6/G10). Encrypt accessor PII into a com.etzhayyim.encrypted.* envelope first.",
              file=sys.stderr)
        return 1
    print("  G6/G10 encryption invariant: PASS (all :access/* encrypted)")

    schema = schema_datoms()
    data = rows_to_datoms(rows)
    schema_tx = "[\n " + "\n ".join(schema) + "\n]"
    data_tx = "[\n " + "\n ".join(data) + "\n]"
    print(f"yabai.transact: graph={graph or '(unset)'}")
    print(f"  schema tx: {len(schema)} attrs ({len(schema_tx.encode()):,} bytes)")
    print(f"  data   tx: {len(data)} datoms ({len(data_tx.encode()):,} bytes)")

    live = bool(graph) and (bool(cacao) or bool(os.environ.get("KOTOBA_TOKEN"))) and "--dry-run" not in argv
    if not live:
        print("  DRY RUN — provide --graph <CID> + KOTOBA_TOKEN operator JWT (or --cacao) to write.")
        return 0

    for name, tx_edn, fatal in (("schema", schema_tx, False), ("data", data_tx, True)):
        body = {"graph": graph, "tx_edn": tx_edn}
        if cacao:
            body["cacao_b64"] = cacao
        st, resp = _post(f"{url}/xrpc/{NSID_TRANSACT}", body)
        if st != 200:
            msg = f"!! transact {name} → {st}: {resp}"
            if fatal:
                print(msg, file=sys.stderr)
                return 1
            print(msg + "  (schema best-effort; continuing)")
            continue
        print(f"  ok {name}: tx_cid={resp.get('tx_cid', '?')} datom_count={resp.get('datom_count', '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
