#!/usr/bin/env python3
"""ipaddress — kotoba Datomic transact bridge (ADR-2605301400 §T2 save-path).

Pushes the kotoba-native IP/ASN graph into a running kotoba node's Datom log via:

    POST /xrpc/com.etzhayyim.apps.kotoba.datomic.transact   {graph, tx_edn, cacao_b64?}

Emits datomic list-form datoms `[:db/add E A V]` (E = the entity's stable id string,
which the server hashes to a CID; cardinality-many values fan out). The merged graph
(data/ip-network.merged.kotoba.edn) is the source; schema is best-effort.

AUTH (ADR-2605231525, no platform-held key): a write needs EITHER an operator JWT
(KOTOBA_TOKEN, sub == operator_did) OR a CACAO authorising `datom:transact` on the
graph CID (--cacao / KOTOBA_CACAO_B64), minted by the operator via `kotoba cacao-sign`.
Without either it is a DRY RUN that prints the tx summary.

stdlib only. Usage:
    python3 methods/transact.py                                    # dry-run
    python3 methods/transact.py --graph <CID> --cacao <b64>        # live (operator CACAO)
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ip_edn import load_edn, edn_val, edn_str  # noqa: E402

ACTOR = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ACTOR.parent.parent / "00-contracts" / "schemas" / "ip-network-ontology.kotoba.edn"
NSID_TRANSACT = "com.etzhayyim.apps.kotoba.datomic.transact"
ID_KEYS = (":rir/id", ":asn/id", ":iprange/id", ":ip/id", ":net.announce/id",
           ":net.member/id", ":geo/id", ":rdns/id", ":whois/id")


def rows_to_datoms(rows):
    """Each entity map → [:db/add E A V] strings (E = its id; lists fan out)."""
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
    """Ontology :attributes (map-form datomic schema install)."""
    onto = load_edn(SCHEMA)
    attrs = onto.get(":attributes", []) if isinstance(onto, dict) else []
    rows = []
    for a in attrs:
        # drop :db/doc — its free-text (e.g. ":a | :b") carries '|' which the kotoba
        # EDN reader rejects; docs are not needed for the schema install.
        parts = " ".join(f"{k} {edn_val(v)}" for k, v in a.items() if k != ":db/doc")
        rows.append("{" + parts + "}")
    return rows


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
             else os.environ.get("IPADDRESS_GRAPH_CID"))
    cacao = (argv[argv.index("--cacao") + 1] if "--cacao" in argv
             else os.environ.get("KOTOBA_CACAO_B64"))
    merged = ACTOR / "data" / "ip-network.merged.kotoba.edn"
    if not merged.exists():
        merged = ACTOR / "data" / "seed-ip-network.kotoba.edn"

    schema = schema_datoms()
    data = rows_to_datoms(load_edn(merged))
    schema_tx = "[\n " + "\n ".join(schema) + "\n]"
    data_tx = "[\n " + "\n ".join(data) + "\n]"

    print(f"ipaddress.transact: graph={graph or '(unset)'}")
    print(f"  schema tx: {len(schema)} attrs ({len(schema_tx.encode()):,} bytes)")
    print(f"  data   tx: {len(data)} datoms ({len(data_tx.encode()):,} bytes)")

    live = bool(graph) and (bool(cacao) or bool(os.environ.get("KOTOBA_TOKEN"))) and "--dry-run" not in argv
    if not live:
        print("  DRY RUN — no writes. Provide --graph <CID> + --cacao <b64> (kotoba cacao-sign, "
              "capability datom:transact) or KOTOBA_TOKEN operator JWT to write.")
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
