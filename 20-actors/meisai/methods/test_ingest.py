#!/usr/bin/env python3
"""test_ingest.py — meisai statement-EDN → EAVT invariants. ADR-2606122400.
Standalone-runnable (`python3 test_ingest.py`), stdlib only, hermetic.

Guards the ingestion contract:

  - the REAL fetch-leg EDN shape (computer-use-clj sumitclub_meisai save_statement output)
    parses and lands as :meisai.stmt/* + :meisai.row/* datoms;
  - determinism: same intake → byte-identical datoms (entity ids are content hashes);
  - **G2 (the defining gate)**: a credential-shaped key or a PAN-shaped value anywhere in the
    intake RAISES — a card number or secret is unrepresentable in the Datom log.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingest  # noqa: E402
import kotoba  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}  {detail}")


# the exact shape the Clojure fetch leg pprints (verified against a live run 2026-06-12)
INTAKE_EDN = """{:source :sumitclub,
 :source/url
 "https://www.sumitclub.jp/JPCRD/col/action/WA2020101Action/RWA2020105",
 :statement/month "2026-05",
 :statement/total-jpy 46540,
 :statement/rows
 [{:date "2026-05-02", :merchant "AMAZON.CO.JP", :amount_jpy 3980}
  {:date "2026-05-15", :merchant "JR東日本", :amount_jpy 42560}]}
"""


def test_parse_and_datoms() -> None:
    doc = kotoba.parse_edn(INTAKE_EDN)
    cid = ingest.intake_cid(INTAKE_EDN.encode("utf-8"))
    datoms = ingest.statement_datoms(doc, cid)
    stmt = [d for d in datoms if d[1] == "meisai-stmt:sumitclub:2026-05"]
    rows = [d for d in datoms if d[1].startswith("meisai-row:")]
    check("statement entity id derives from source+month", len(stmt) >= 4)
    check("every datom is :db/add (append-only)", all(d[0] == ":db/add" for d in datoms))
    check("intake CID persisted for provenance (G5)",
          any(d[2] == ":meisai.stmt/intake-cid" and d[3] == cid for d in stmt))
    check("total lands as int yen",
          any(d[2] == ":meisai.stmt/total-jpy" and d[3] == 46540 for d in stmt))
    check("2 rows × 5 attrs", len(rows) == 10)
    check("row links back to statement",
          all(d[3] == "meisai-stmt:sumitclub:2026-05"
              for d in rows if d[2] == ":meisai.row/stmt"))
    check("merchant survives UTF-8 (JR東日本)",
          any(d[2] == ":meisai.row/merchant" and d[3] == "JR東日本" for d in rows))


def test_determinism() -> None:
    doc = kotoba.parse_edn(INTAKE_EDN)
    cid = ingest.intake_cid(INTAKE_EDN.encode("utf-8"))
    check("same intake → identical datoms",
          ingest.statement_datoms(doc, cid) == ingest.statement_datoms(doc, cid))


def test_g2_credential_unrepresentable() -> None:
    doc = kotoba.parse_edn(INTAKE_EDN)
    poisoned = dict(doc)
    poisoned[":password"] = "hunter2"
    try:
        ingest.statement_datoms(poisoned, "bdead")
        check("credential-shaped key raises (G2)", False, "no raise")
    except ValueError as e:
        check("credential-shaped key raises (G2)", "G2" in str(e))

    pan = kotoba.parse_edn(INTAKE_EDN)
    pan[":statement/rows"] = [{":date": "2026-05-02",
                               ":merchant": "card 4111 1111 1111 1111 memo",
                               ":amount_jpy": 1}]
    try:
        ingest.statement_datoms(pan, "bdead")
        check("PAN-shaped value raises (G2)", False, "no raise")
    except ValueError as e:
        check("PAN-shaped value raises (G2)", "G2" in str(e))

    clean_long = kotoba.parse_edn(INTAKE_EDN)
    clean_long[":statement/rows"] = [{":date": "2026-05-02",
                                      ":merchant": "ORDER 123-4567890-12",
                                      ":amount_jpy": 1}]
    try:
        ingest.statement_datoms(clean_long, "bok")
        check("short digit runs (order numbers) pass", True)
    except ValueError:
        check("short digit runs (order numbers) pass", False, "false positive")


if __name__ == "__main__":
    test_parse_and_datoms()
    test_determinism()
    test_g2_credential_unrepresentable()
    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)
