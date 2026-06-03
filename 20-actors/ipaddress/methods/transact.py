#!/usr/bin/env python3
"""ipaddress — kotoba Datomic transact bridge (ADR-2605301400 §T2 save-path).

Pushes the kotoba-native IP/ASN graph into a running kotoba node's Datom log via:

    POST /xrpc/com.etzhayyim.apps.kotoba.datomic.transact   {graph, tx_edn}

Two transactions: (1) the schema from ip-network-ontology.kotoba.edn :attributes,
(2) the merged entity graph (data/ip-network.merged.kotoba.edn). The merged file is
already a vector of entity maps with :db.unique/identity keys, so it IS valid
datomic map-form tx-data — this just frames + posts it.

Live writes require an operator credential in KOTOBA_SESSION_POP or KOTOBA_TOKEN
(no platform-held key, ADR-2605231525). KOTOBA_SESSION_POP is verified via
com.etzhayyim.pds.session.verify first. Without a credential it is a DRY RUN that
prints the tx_edn summary. Mirrors tadori/kotoba/deploy.sh.

stdlib only. Usage:
    python3 methods/transact.py                 # dry-run (prints schema + data tx summary)
    KOTOBA_SESSION_POP=… python3 methods/transact.py --verify-readback   # live
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ip_edn import load_edn, to_edn  # noqa: E402

ACTOR = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ACTOR.parent.parent / "00-contracts" / "schemas" / "ip-network-ontology.kotoba.edn"
NSID_SESSION_VERIFY = "com.etzhayyim.pds.session.verify"
NSID_TRANSACT = "com.etzhayyim.apps.kotoba.datomic.transact"


def _post(url, body, token=None):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (own kotoba node)
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return exc.code, {"error": "non-json"}


def main(argv):
    url = os.environ.get("KOTOBA_URL", "http://127.0.0.1:8077")
    graph = os.environ.get("IPADDRESS_GRAPH", "etzhayyim/ipaddress/ip-network")
    merged = ACTOR / "data" / "ip-network.merged.kotoba.edn"
    if not merged.exists():
        merged = ACTOR / "data" / "seed-ip-network.kotoba.edn"

    onto = load_edn(SCHEMA)
    schema_attrs = onto.get(":attributes", []) if isinstance(onto, dict) else []
    schema_tx = to_edn(schema_attrs, [";; ip-network schema install"])
    data_rows = [r for r in load_edn(merged) if isinstance(r, dict)]
    data_tx = to_edn(data_rows, [";; ip-network entity graph"])

    token = os.environ.get("KOTOBA_SESSION_POP") or os.environ.get("KOTOBA_TOKEN")
    live = bool(token) and "--dry-run" not in argv

    print(f"ipaddress.transact: graph={graph}")
    print(f"  schema tx: {len(schema_attrs)} attrs ({len(schema_tx.encode()):,} bytes)")
    print(f"  data   tx: {len(data_rows)} entities ({len(data_tx.encode()):,} bytes)")

    if not live:
        print("  DRY RUN — no writes. Set KOTOBA_SESSION_POP or KOTOBA_TOKEN to transact "
              "into a running kotoba node (datomic.transact).")
        return 0

    if os.environ.get("KOTOBA_SESSION_POP"):
        st, info = _post(f"{url}/xrpc/{NSID_SESSION_VERIFY}", {"token": os.environ["KOTOBA_SESSION_POP"]})
        if st != 200 or not info.get("valid"):
            print(f"!! session PoP rejected: {info}", file=sys.stderr)
            return 1
        print(f"  session valid for {info.get('did', '?')}")

    for name, tx_edn in (("schema", schema_tx), ("data", data_tx)):
        st, body = _post(f"{url}/xrpc/{NSID_TRANSACT}", {"graph": graph, "tx_edn": tx_edn}, token)
        if st != 200:
            print(f"!! transact {name} failed: {st} {body}", file=sys.stderr)
            return 1
        print(f"  ok {name} tx_cid={body.get('tx_cid', '?')} datom_count={body.get('datom_count', '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
