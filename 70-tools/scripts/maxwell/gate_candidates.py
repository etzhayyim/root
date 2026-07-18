"""
Gate maxwell-candidates.jsonl: clj-kondo + Charter Rider → maxwell-sft-corpus.jsonl
"""
import json, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
CANDIDATES = ROOT / "90-docs/baien/maxwell-candidates.jsonl"
CORPUS = ROOT / "90-docs/baien/maxwell-sft-corpus.jsonl"
KONDO = pathlib.Path.home() / "bin/clj-kondo"
CR_SRC = ROOT / "70-tools/scripts/maxwell/retired-charter-rider"
sys.path.insert(0, str(CR_SRC))
from etzhayyim_organism.sensors.charter_rider import scan

SYSTEM = (
    "You are Maxwell, etzhayyim's Murakumo fleet model. "
    "Convert Python actor methods to idiomatic Clojure that follows the "
    "kotoba Datom log conventions (namespaced keywords, pure stdlib, EAVT). "
    "Output only the defn form — no ns declaration, no prose."
)
INSTRUCTION = "Convert this Python method to Clojure following kotoba Datom log idioms:\n\n```python\n{py_src}\n```\n\nOutput only the Clojure defn form."

existing = set()
if CORPUS.exists():
    with open(CORPUS) as f:
        for line in f:
            if line.strip():
                existing.add(json.loads(line)["id"])

passed = failed_lint = failed_scan = skipped = 0
with open(CANDIDATES) as inf, open(CORPUS, "a") as outf:
    for line in inf:
        if not line.strip(): continue
        c = json.loads(line)
        eid = f"{c['label']}/{c['fn_name']}"
        if eid in existing:
            skipped += 1
            continue
        clj = c["clj_src"].strip()
        # clj-kondo gate
        with tempfile.NamedTemporaryFile(suffix=".clj", mode="w", delete=False) as tf:
            tf.write(clj)
            tf_path = tf.name
        try:
            r = subprocess.run([str(KONDO), "--lint", tf_path], capture_output=True, text=True)
            _m = re.search(r"errors:\s*(\d+)", r.stdout)
            _errs = int(_m.group(1)) if _m else (0 if r.returncode == 0 else 99)
            if _errs > 0:  # warnings (e.g. unused-private-var on a standalone defn) are tolerated
                failed_lint += 1
                continue
        finally:
            pathlib.Path(tf_path).unlink(missing_ok=True)
        # Charter Rider
        sr = scan(c.get("py_src","") + "\n" + clj)
        if not sr.ok:
            failed_scan += 1
            continue
        ex = {
            "id": eid,
            "messages": [
                {"role": "system",  "content": SYSTEM},
                {"role": "user",    "content": INSTRUCTION.format(py_src=c["py_src"])},
                {"role": "model",   "content": clj},
            ],
            "meta": {"src_py": c["pyPath"], "fn": c["fn_name"], "scan": "ok", "generator": "opus"},
        }
        outf.write(json.dumps(ex, ensure_ascii=False) + "\n")
        passed += 1

print(f"passed={passed} failed_lint={failed_lint} failed_scan={failed_scan} skipped={skipped}")
print(f"corpus total: {sum(1 for _ in open(CORPUS) if _.strip())} pairs")
