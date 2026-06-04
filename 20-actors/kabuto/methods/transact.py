#!/usr/bin/env python3
"""kabuto 兜 — kotoba Datomic transact bridge (ADR-2606022000; mirrors ipaddress/yabai §T2/§T3).

Pushes the public-company supply-chain graph into a running kotoba node's Datom log via
POST /xrpc/com.etzhayyim.apps.kotoba.datomic.transact, emitting datomic list-form datoms
`[:db/add E A V]` (E = the entity's stable id; cardinality-many values fan out). The
company graph (data/companies.merged.kotoba.edn else the seed) is the source; schema is
installed from public-company-ontology.kotoba.edn (:db/doc dropped — kotoba EDN reader
rejects '|'). Data is BATCHED (the graph exceeds the 1 MiB tx_edn limit as one tx).

AUTH (ADR-2605231525, no platform-held key): a write needs EITHER an operator JWT
(KOTOBA_TOKEN, sub == operator_did) OR a CACAO authorising `datom:transact`. Without
either it is a DRY RUN that prints the tx summary.

CONSTITUTIONAL (kabuto G2/G4): public-record company facts only; a resilience +
transparency map, NEVER a target-list. kabuto does not adjudicate.

stdlib only. Usage:
    python3 methods/transact.py                       # dry-run
    python3 methods/transact.py --graph <CID>         # live (KOTOBA_TOKEN operator JWT)
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kabuto_edn import load_edn, edn_str  # noqa: E402

ACTOR = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ACTOR.parent.parent / "00-contracts" / "schemas" / "public-company-ontology.kotoba.edn"
NSID_TRANSACT = "com.etzhayyim.apps.kotoba.datomic.transact"
ID_KEYS = (":company/id", ":company.address/id", ":company.contact/id",
           ":supply.edge/id", ":company.process/id")
BATCH = 3500  # datoms per tx (keeps tx_edn well under the 1 MiB server cap)


def edn_val(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        return str(x)
    if isinstance(x, list):
        return "[" + " ".join(edn_val(i) for i in x) + "]"
    if isinstance(x, str):
        return x if x.startswith(":") else edn_str(x)
    return edn_str(str(x))


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
    return ["{" + " ".join(f"{k} {edn_val(v)}" for k, v in a.items() if k != ":db/doc") + "}"
            for a in attrs]


def _tx_edn(datoms):
    return "[\n " + "\n ".join(datoms) + "\n]"


def _post(url, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    tok = os.environ.get("KOTOBA_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (own kotoba node)
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
             else os.environ.get("KABUTO_GRAPH_CID"))
    cacao = (argv[argv.index("--cacao") + 1] if "--cacao" in argv
             else os.environ.get("KOTOBA_CACAO_B64"))
    merged = ACTOR / "data" / "companies.merged.kotoba.edn"
    if not merged.exists():
        merged = ACTOR / "data" / "seed-public-companies.kotoba.edn"

    schema = schema_datoms()
    data = rows_to_datoms(load_edn(merged))
    batches = [data[i:i + BATCH] for i in range(0, len(data), BATCH)] or [[]]
    print(f"kabuto.transact: graph={graph or '(unset)'}")
    print(f"  schema tx: {len(schema)} attrs  ·  data: {len(data)} datoms in {len(batches)} batch(es)")

    live = bool(graph) and (bool(cacao) or bool(os.environ.get("KOTOBA_TOKEN"))) and "--dry-run" not in argv
    if not live:
        print("  DRY RUN — provide --graph <CID> + KOTOBA_TOKEN operator JWT (or --cacao) to write.")
        return 0

    def send(name, datoms, fatal):
        body = {"graph": graph, "tx_edn": _tx_edn(datoms)}
        if cacao:
            body["cacao_b64"] = cacao
        st, resp = _post(f"{url}/xrpc/{NSID_TRANSACT}", body)
        if st != 200:
            msg = f"!! transact {name} → {st}: {str(resp)[:160]}"
            if fatal:
                print(msg, file=sys.stderr)
                return False
            print(msg + "  (best-effort; continuing)")
            return True
        print(f"  ok {name}: datom_count={resp.get('datom_count', '?')} tx_cid={str(resp.get('tx_cid','?'))[:20]}…")
        return True

    if not send("schema", schema, False):
        return 1
    total = 0
    for i, b in enumerate(batches, 1):
        if not send(f"data[{i}/{len(batches)}]", b, True):
            return 1
        total += len(b)
    print(f"  ✓ {total} company-graph datoms committed to {graph}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
