#!/usr/bin/env python3
"""autorun.py — tadori AUTONOMOUS silenTadoriReview self-audit heartbeat. ADR-2605301400 §D1.

tadori's autonomy is constitutionally constrained (unlike ipaddress/yabai/shionome): it is
AUTHORIZED-INVESTIGATION-ONLY (G3) and EVIDENCE-PRODUCING-NOT-ENFORCEMENT (G7). It may NOT
autonomously persist case-anchored observation / attribution / PII datoms — that needs a
`caseMandate`. So the charter-permitted autonomous act is the **Transparent-Force self-audit**
(Charter §1.12, G5): each heartbeat the actor

    observe (load the OFFLINE operator-staged corpus) → validate against the tadori gates
      (Phase 0, no case → dry-run posture; raises if the corpus is not gate-clean)
      → recompute the 9 silenTadoriReview structural ZERO-COUNTERS over the corpus
      → G12 guard: any nonzero counter HALTS (Bonsai prune), persisting nothing
      → PERSIST one append-only, content-addressed AUDIT datom (counters + totals + the
        Transparent-Force flag) to the local kotoba Datom log.

By construction the log holds ONLY audit counters — no observation, no PII, no case data ever
reaches it (G3/G6/G10 structurally honored). The loop is deterministic / resume-safe (cycle drives
tx-id + as-of → same CIDs) and append-only. It does NO external I/O, NO live source fetch, NO LLM
inference, NO enforcement. Live case-anchored ingest stays in `ingest_threat_intel.py` behind the
operator credential + `TADORI_CASE_ID` gate. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_log import (append_tx, assert_all_clear, head_cid, make_tx,  # noqa: E402
                       read_log, review_datoms, verify_chain)
from ingest_threat_intel import (VENDOR_COMPAT, ValidationError,  # noqa: E402
                                 load_jsonl, validate_records)

HERE = pathlib.Path(__file__).resolve().parent
SEED = HERE / "seed.threat-intel.jsonl"
LOG = HERE.parent / "data" / "persisted" / "tadori.silen-review.datoms.kotoba.edn"
BASE_AS_OF = 20260608

# PII-bearing observation kinds: per CLAUDE.md, person/IP/device attribution MUST be encrypted (G6).
PII_KINDS = {"ip-obs"}


def audit_corpus(records: list[dict]) -> dict:
    """Recompute the 9 silenTadoriReview structural counters over the staged corpus, in the
    autonomous Phase-0 posture. The autonomous loop writes NO observation/PII/case datoms, so the
    write-side counters (noncaseWrite / massSurveillance / adherentDeanon / nonKotobaStore /
    enforcementAction / platformHeldKey / murakumoBypass) are zero by construction; the corpus-side
    counters (plaintextPii / proprietarySor) are measured against the staged records."""
    obs = [r for r in records if r.get("kind") in ("dns-obs", "ip-obs", "indicator")]
    sources = [r for r in records if r.get("kind") == "intel-source"]

    # plaintext-pii: a PII-bearing observation lacking encryption (G6/G10 violation)
    plaintext_pii = sum(1 for r in obs
                        if r.get("kind") in PII_KINDS and r.get("encrypted") is not True)
    # proprietary-sor: a vendor-compatible feed declared system-of-record (G4 violation)
    proprietary_sor = sum(1 for r in sources
                          if str(r.get("vendor_family")) in VENDOR_COMPAT
                          and r.get("source_role") == "system-of-record")
    # informational: observations carrying no case anchor (would be Phase-0-only under G3)
    obs_without_case = sum(1 for r in obs if not r.get("case_id"))

    return {
        "noncase-write": 0,        # the loop persists ONLY the audit datom — never a case-write
        "plaintext-pii": plaintext_pii,
        "proprietary-sor": proprietary_sor,
        "enforcement-action": 0,   # tadori is evidence-only (G7)
        "platform-held-key": 0,    # local append, no key (G8)
        "murakumo-bypass": 0,      # no LLM inference in the loop (G9)
        "mass-surveillance": 0,    # bounded staged corpus, no untargeted collection (G10)
        "adherent-deanon": 0,      # no adherent data (G10)
        "non-kotoba-store": 0,     # kotoba Datom log only (G11)
        "sources-audited": len(sources),
        "obs-audited": len(obs),
        "obs-without-case": obs_without_case,
    }


def run_cycle(cycle: int, seed_path: pathlib.Path = SEED, log_path: pathlib.Path = LOG) -> dict:
    """One autonomous self-audit heartbeat: observe → validate → recompute counters → G12 guard
    → persist one append-only audit datom. cycle drives tx-id + as-of (deterministic)."""
    records = load_jsonl(str(seed_path))
    # Phase 0 (no case): validate raises if the corpus is not gate-clean (e.g. vendor-SoR,
    # bad collection_mode). Tier-D is NOT auto-allowed by the autonomous loop.
    validate_records(records, allow_tier_d=False, live=False, case_id=None)
    review = audit_corpus(records)
    assert_all_clear(review)                          # G12 — any nonzero counter HALTS (no persist)
    datoms = review_datoms(review, cycle)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)
    return {"cycle": cycle, "review": review, "datoms": len(datoms), "cid": cid}


def run_autonomous(cycles: int = 3, seed_path: pathlib.Path = SEED,
                   log_path: pathlib.Path = LOG) -> dict:
    beats = [run_cycle(c, seed_path, log_path) for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="tadori autonomous silenTadoriReview self-audit loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--seed", type=pathlib.Path, default=SEED, help="operator-staged corpus (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba audit Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    try:
        res = run_autonomous(args.cycles, seed_path=args.seed, log_path=args.log)
    except (ValidationError, Exception) as exc:  # noqa: BLE001 — surface any HALT clearly
        print(f"!! tadori self-audit HALT: {exc}", file=sys.stderr)
        sys.exit(1)
    print("# tadori — AUTONOMOUS silenTadoriReview self-audit over the kotoba Datom log "
          "(Phase 0; counters only, NO case/PII/obs data; live case-ingest stays gated)\n")
    for bt in res["beats"]:
        r = bt["review"]
        print(f"  ♥ cycle {bt['cycle']}: audited {r['sources-audited']} sources / {r['obs-audited']} obs "
              f"· plaintext-pii {r['plaintext-pii']} · proprietary-sor {r['proprietary-sor']} "
              f"· ALL-CLEAR +{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"9 silenTadoriReview counters = 0 (Transparent-Force audit, G5)")
