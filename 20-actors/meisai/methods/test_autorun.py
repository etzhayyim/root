#!/usr/bin/env python3
"""test_autorun.py — meisai autonomous intake heartbeat + kotoba Datom-log invariants.
ADR-2606122400. Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence contract:

  - one content-addressed tx per NEW intake, appended to a verifiable commit-DAG;
  - dedup by intake content CID: a second cycle over the same intakes appends NOTHING
    (resume-safe), and tamper is detected by verify_chain;
  - G3 local-only: the loop touches only the paths it is given (no network modules imported).
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autorun  # noqa: E402
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


EDN_A = """{:source :sumitclub :statement/month "2026-05" :statement/total-jpy 46540
 :statement/rows [{:date "2026-05-02" :merchant "AMAZON.CO.JP" :amount_jpy 3980}
                  {:date "2026-05-15" :merchant "JR東日本" :amount_jpy 42560}]}
"""
EDN_B = """{:source :sumitclub :statement/month "2026-04" :statement/total-jpy 1200
 :statement/rows [{:date "2026-04-03" :merchant "SUICA" :amount_jpy 1200}]}
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        intake = pathlib.Path(td) / "intake"
        intake.mkdir()
        log = pathlib.Path(td) / "meisai.datoms.kotoba.edn"
        (intake / "2026-05.edn").write_text(EDN_A, encoding="utf-8")
        (intake / "2026-04.edn").write_text(EDN_B, encoding="utf-8")

        r1 = autorun.run_cycle(1, intake, log)
        check("first cycle ingests both intakes", len(r1["appended"]) == 2, str(r1))
        check("chain verifies", kotoba.verify_chain(log)["ok"])
        check("txs link (commit-DAG)",
              kotoba.read_log(log)[1][":tx/prev"] == kotoba.read_log(log)[0][":tx/cid"])

        r2 = autorun.run_cycle(2, intake, log)
        check("second cycle appends nothing (dedup by intake CID)",
              len(r2["appended"]) == 0 and r2["skipped"] == 2, str(r2))
        check("log length still 2", len(kotoba.read_log(log)) == 2)

        (intake / "2026-06.edn").write_text(
            EDN_A.replace("2026-05", "2026-06"), encoding="utf-8")
        r3 = autorun.run_cycle(3, intake, log)
        check("new intake → exactly one new tx", len(r3["appended"]) == 1, str(r3))
        check("chain still verifies", kotoba.verify_chain(log)["ok"])

        head_before = kotoba.head_cid(log)
        r4 = autorun.run_cycle(4, intake, log)
        check("resume-safe: idle cycle leaves head unchanged",
              kotoba.head_cid(log) == head_before and not r4["appended"])

        # tamper-detect: flip one amount in the persisted log
        tampered = log.read_text(encoding="utf-8").replace("42560", "1")
        log.write_text(tampered, encoding="utf-8")
        check("tamper is detected", kotoba.verify_chain(log)["ok"] is False)

        # G3: no network machinery may be imported anywhere in the method-pack
        here = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
        forbidden = ("import urllib", "import http", "import socket",
                     "import requests", "from urllib", "from http", "from socket")
        offenders = [f.name for f in here.glob("*.py") if not f.name.startswith("test_")
                     and any(tok in f.read_text(encoding="utf-8") for tok in forbidden)]
        check("method-pack imports are local-only (G3)", not offenders, str(offenders))

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
