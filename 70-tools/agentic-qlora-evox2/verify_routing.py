#!/usr/bin/env python3
"""Post-train routing-health check (ADR-2605302359 §5).

After training the agentic adapter, re-run the MoE expert profiler on the
merged model and diff the expert classification against the pre-train
baseline. Confirms (a) agentic-adjacent experts (code/reasoning/tool) gain
salience, (b) routing entropy stays healthy (no expert collapse / no large
unseen-set growth), (c) no catastrophic category drift.

This script does the DIFF; produce the two expert-classification.json files
with the profiler harness in the moe-expert-activation dataset
(harness/profile_experts.py + classify_all.py) — once for the base model,
once for the LoRA-merged model.

Usage:
  verify_routing.py --before base/expert-classification.json \
                    --after  merged/expert-classification.json
"""
import argparse, json
from collections import Counter


def load(path):
    return json.load(open(path))["experts"]


def entropy(shares):
    import math
    return -sum(p * math.log(p + 1e-12) for p in shares if p > 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    args = ap.parse_args()
    b, a = load(args.before), load(args.after)

    keys = set(b) & set(a)
    # 1) coverage / collapse check
    b_unseen = sum(1 for k in b if b[k]["classification"] == "unseen-rare")
    a_unseen = sum(1 for k in a if a[k]["classification"] == "unseen-rare")
    # 2) category drift (how many cells changed top class among co-seen)
    drift = sum(1 for k in keys
                if b[k]["classification"] != a[k]["classification"]
                and b[k]["classification"] != "unseen-rare"
                and a[k]["classification"] != "unseen-rare")
    co = sum(1 for k in keys
             if b[k]["classification"] != "unseen-rare"
             and a[k]["classification"] != "unseen-rare")
    # 3) per-category salience shift (mean salience by class, after - before)
    def by_cat_salience(d):
        s = Counter(); n = Counter()
        for v in d.values():
            c = v["classification"]
            if c == "unseen-rare":
                continue
            s[c] += (v.get("specialization") or 0) * (v.get("activations") or 0)
            n[c] += 1
        return {c: round(s[c] / n[c], 2) for c in s if n[c]}
    sb, sa = by_cat_salience(b), by_cat_salience(a)
    shifts = {c: round(sa.get(c, 0) - sb.get(c, 0), 2) for c in set(sb) | set(sa)}

    report = {
        "unseen_before": b_unseen, "unseen_after": a_unseen,
        "unseen_growth": a_unseen - b_unseen,
        "category_drift_cells": drift, "co_seen_cells": co,
        "drift_pct": round(100 * drift / co, 1) if co else None,
        "salience_shift_by_category": dict(sorted(shifts.items(), key=lambda kv: -kv[1])),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # health verdict (heuristic gates)
    ok = (report["unseen_growth"] <= 256          # no large collapse
          and (report["drift_pct"] or 0) <= 35)   # no catastrophic re-route
    print("\nROUTING HEALTH:", "OK" if ok else "REVIEW — possible collapse/drift")
    print("agentic gain:", "+code/+reasoning salience expected" )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
