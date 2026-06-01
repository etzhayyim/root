#!/usr/bin/env python3
"""Fetch real advisories from api.osv.dev → OSV JSON (feeds osv_to_kotoba.py).

Read-only query against the public OSV database (https://osv.dev). Emits the
raw `{"vulns":[…]}` response, which `osv_to_kotoba.py` converts to kotoba
CveEntry. This is the live, real-data form of the sbom lexicon's `cveIngestOsv`.

Note: OSV indexes SOFTWARE packages (npm/PyPI/Maven/Go/…). The giemon HARDWARE
purls (`pkg:generic/*`) won't match OSV — hardware advisories need a different
feed (e.g. ICS-CERT). Use this for a robot's SOFTWARE stack (RPi OS / ROS2 /
Python deps), which IS OSV-matchable.

Usage:
  python3 osv_fetch.py --purl pkg:pypi/django --out out.osv.json
  python3 osv_fetch.py --ecosystem Maven --name org.apache.logging.log4j:log4j-core \\
      --version 2.14.0 --out out.osv.json
"""
import argparse
import json
import sys
import urllib.request

API = "https://api.osv.dev/v1/query"


def query(body: dict) -> dict:
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--purl")
    ap.add_argument("--ecosystem")
    ap.add_argument("--name")
    ap.add_argument("--version")
    ap.add_argument("--out", default="-")
    a = ap.parse_args()

    if a.purl:
        body = {"package": {"purl": a.purl}}
    elif a.ecosystem and a.name:
        body = {"package": {"ecosystem": a.ecosystem, "name": a.name}}
        if a.version:
            body["version"] = a.version
    else:
        sys.exit("provide --purl OR (--ecosystem AND --name)")

    resp = query(body)
    n = len(resp.get("vulns", []))
    out = json.dumps(resp, ensure_ascii=False) + "\n"
    if a.out == "-":
        sys.stdout.write(out)
    else:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out)
    sys.stderr.write(f"osv.dev: {n} advisories for {body['package']} → {a.out}\n")


if __name__ == "__main__":
    main()
