#!/usr/bin/env python3
"""unit_refactor — stage 0: 関数単位分解 → 単位変換 → 決定的組立。

仮説 (plan.edn :ladder stage 0): 小入出力なら gemma4 は通る (pilot 33-44%) が
実ファイルは通らない (batch100 1-4%)。なら top-level 単位に分割して
得意なサイズに押し込み、ns/declare/連結はコードで決定的にやる。

  Python ast → units: [module-docstring] [imports(まとめて文脈として渡すのみ)]
                      [定数群] [class] [function] ...
  各単位 → fleet gemma4 で個別変換 (単位 lint: bracket/syntax のみ;
           unresolved-symbol は組立後の file lint で判定)
  組立   → (ns …) ヘッダ + (declare 全 defn 名) + 単位訳を原順で連結
  最終ゲート → clj-kondo full (通常レベル) — ここを通った時だけ .clj を書く

Usage:
  python3 unit_refactor.py FILE.py [FILE.py...]      # Python のみ (TS は stage 0 対象外)
  git ls-files '**/*.py' | python3 unit_refactor.py - --model gemma4:e4b-it-qat

結果ログ: unit-refactor-results.jsonl / SFT: fleet-refactor-sft.jsonl (単位粒度)
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fleet_refactor import (  # noqa: E402
    NODES, balance_repair, extract_clojure, ns_from_path,
)

MODEL = "gemma4:e4b-it-qat"
PER_NODE_CONCURRENCY = 2
REQUEST_TIMEOUT_S = 300
UNIT_ATTEMPTS = 2
RESULTS_LOG = Path("unit-refactor-results.jsonl")
SFT_LOG = Path("fleet-refactor-sft.jsonl")
_sft_lock = threading.Lock()

UNIT_SYSTEM = """You translate ONE Python top-level unit (a function, class, or constants) to Clojure.

Rules:
- Output EXACTLY ONE ```clojure code block, nothing else.
- Output ONLY the form(s) for this unit — NO (ns …) header, NO requires.
- Function names → kebab-case. A class becomes plain functions over an immutable map
  (Class.method(self, x) → (defn class-name-method [this x] …) where this is a map).
- Use fully-qualified clojure.string/… clojure.set/… clojure.edn/… (no aliases).
- Sibling functions from the same file may be called by their kebab-case names.
- Stdlib-only. Never invent symbols. Every ( [ { must close.
- If untranslatable (FFI/platform), emit (defn name [& _] (throw (ex-info "TODO: port" {:from "<name>"}))).

Example:

```python
def screen_kind(kind, allowed):
    k = kind if kind.startswith(":") else f":{kind}"
    if k not in allowed:
        raise ValueError(f"bad kind {kind!r}")
    return k
```

```clojure
(defn screen-kind [kind allowed]
  (let [k (if (clojure.string/starts-with? kind ":") kind (str ":" kind))]
    (when-not (contains? (set allowed) k)
      (throw (ex-info (str "bad kind " (pr-str kind)) {:kind kind})))
    k))
```"""

UNIT_USER = """File: {path}
Module doc: {doc}
Sibling names (kebab-case, callable): {siblings}

Translate this unit:

```python
{unit}
```"""


# ───────────────────────── split ─────────────────────────

def split_units(source: str) -> tuple[str, list[dict]]:
    """→ (module_doc, [{kind, name, code} …]) — top-level 単位 (原順)。"""
    tree = ast.parse(source)
    lines = source.splitlines()
    doc = ast.get_docstring(tree) or ""
    units, const_buf = [], []

    def flush_consts():
        if const_buf:
            units.append({"kind": "consts", "name": const_buf[0][0],
                          "code": "\n".join(c for _, c in const_buf)})
            const_buf.clear()

    for node in tree.body:
        seg = "\n".join(lines[node.lineno - 1:node.end_lineno])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            flush_consts()
            units.append({"kind": "def", "name": node.name, "code": seg})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            tgt = node.targets[0] if isinstance(node, ast.Assign) else node.target
            name = tgt.id if isinstance(tgt, ast.Name) else "consts"
            const_buf.append((name, seg))
        # import / if __main__ / 式文 は単位化しない (ns 組立とテキスト文脈で扱う)
    flush_consts()
    return doc, units


def kebab(name: str) -> str:
    name = name.strip("_")
    if name.isupper():  # ALL_CAPS 定数
        return name.lower().replace("_", "-")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name)  # camelCase 境界のみ
    return s.lower().replace("_", "-")


# ───────────────────────── fleet pool ─────────────────────────

class Pool:
    def __init__(self):
        self._sems = {n: threading.Semaphore(PER_NODE_CONCURRENCY) for n, _ in NODES}
        self._i, self._lock = 0, threading.Lock()

    def acquire(self):
        while True:
            with self._lock:
                order = NODES[self._i:] + NODES[:self._i]
                self._i = (self._i + 1) % len(NODES)
            for name, ip in order:
                if self._sems[name].acquire(blocking=False):
                    return name, ip
            time.sleep(0.3)

    def release(self, name):
        self._sems[name].release()


def chat(ip, messages):
    body = json.dumps({"model": MODEL, "messages": messages, "stream": False,
                       "think": False,
                       "options": {"temperature": 0.1, "num_ctx": 16384}}).encode()
    req = urllib.request.Request(f"http://{ip}:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as r:
        data = json.load(r)
    if "error" in data:
        raise OSError(f"ollama: {data['error']}")
    return data["message"]["content"]


# ───────────────────────── lint ─────────────────────────

UNIT_LINT_CONFIG = ('{:linters {:unresolved-symbol {:level :warning} '
                    ':unresolved-namespace {:level :warning} '
                    ':unresolved-var {:level :warning}}}')


def lint_text(code: str, config: str | None = None) -> tuple[bool, str]:
    # (ns scratch) と一致するよう scratch.clj 固定名で lint する
    # (ランダム temp 名だと namespace-name-mismatch で全滅する)
    m = re.match(r"\(ns ([\w.\-]+)", code)
    fname = ((m.group(1).rsplit(".", 1)[-1].replace("-", "_")) if m else "scratch") + ".clj"
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / fname
        path.write_text(code, encoding="utf-8")
        cmd = ["clj-kondo", "--lint", str(path), "--fail-level", "error"]
        if config:
            cmd += ["--config", config]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


# ───────────────────────── per-unit translate ─────────────────────────

def translate_unit(pool: Pool, src: Path, doc: str, siblings: list[str],
                   unit: dict) -> dict:
    msgs = [{"role": "system", "content": UNIT_SYSTEM},
            {"role": "user", "content": UNIT_USER.format(
                path=src, doc=(doc.splitlines() or [""])[0][:160],
                siblings=" ".join(siblings) or "(none)", unit=unit["code"])}]
    node, ip = pool.acquire()
    try:
        lint_out = "no block"
        for attempt in range(1, UNIT_ATTEMPTS + 1):
            try:
                reply = chat(ip, msgs)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                return {**unit, "status": "error", "reason": f"{node}: {e}"}
            code = extract_clojure(reply)
            if code is not None:
                # 単位ヘッダ混入の除去 (指示違反で (ns …) を書く個体がいる)
                code = re.sub(r"^\(ns [^)]+\)\s*", "", code.strip()) + "\n"
                ok, lint_out = lint_text(f"(ns scratch)\n{code}", UNIT_LINT_CONFIG)
                if not ok and ("matching" in lint_out or "bracket" in lint_out):
                    rep = balance_repair(code)
                    if rep is not None:
                        ok, lint_out = lint_text(f"(ns scratch)\n{rep}", UNIT_LINT_CONFIG)
                        if ok:
                            code = rep
                if ok:
                    return {**unit, "status": "ok", "clj": code, "attempt": attempt}
            msgs.append({"role": "assistant", "content": reply})
            msgs.append({"role": "user", "content":
                         f"Errors — re-output the corrected ```clojure block only:\n"
                         f"{lint_out[:1200]}"})
        return {**unit, "status": "fail", "reason": lint_out[:300]}
    finally:
        pool.release(node)


# ───────────────────────── per-file orchestration ─────────────────────────

def port_file(pool: Pool, ex: concurrent.futures.ThreadPoolExecutor,
              src: Path) -> dict:
    rec = {"src": str(src), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    t0 = time.time()
    try:
        source = src.read_text(encoding="utf-8")
        doc, units = split_units(source)
    except (OSError, UnicodeDecodeError, SyntaxError) as e:
        return {**rec, "status": "skip", "reason": str(e)[:120]}
    if not units:
        return {**rec, "status": "skip", "reason": "no top-level units"}

    siblings = [kebab(u["name"]) for u in units if u["kind"] == "def"]
    futs = [ex.submit(translate_unit, pool, src, doc, siblings, u) for u in units]
    results = [f.result() for f in futs]
    bad = [r for r in results if r["status"] != "ok"]
    rec.update(units=len(units), unit_ok=len(results) - len(bad),
               secs=round(time.time() - t0, 1))
    if bad:
        return {**rec, "status": "fail",
                "reason": f"{len(bad)} units failed: "
                          + "; ".join(f"{b['name']}({b.get('reason','')[:60]})" for b in bad[:3])}

    ns = ns_from_path(src)
    header = (f";; ported from {src} (unit_refactor stage 0)\n"
              + (f";; {(doc.splitlines() or [''])[0]}\n" if doc else "")
              + f"(ns {ns}\n  (:require [clojure.string] [clojure.set] [clojure.edn]))\n\n"
              + (f"(declare {' '.join(siblings)})\n\n" if siblings else ""))
    assembled = header + "\n".join(r["clj"] for r in results)

    ok, lint_out = lint_text(assembled)
    if not ok:
        return {**rec, "status": "fail", "reason": f"assembled lint: {lint_out[:300]}"}

    out = src.parent / (ns.rsplit(".", 1)[-1].replace("-", "_") + ".clj")
    out.write_text(assembled, encoding="utf-8")
    with _sft_lock, SFT_LOG.open("a") as f:
        for r in results:
            f.write(json.dumps(
                {"messages": [
                    {"role": "system", "content": UNIT_SYSTEM},
                    {"role": "user", "content": UNIT_USER.format(
                        path=src, doc=(doc.splitlines() or [""])[0][:160],
                        siblings=" ".join(siblings) or "(none)", unit=r["code"])},
                    {"role": "assistant", "content": f"```clojure\n{r['clj']}```"}],
                 "meta": {"src": str(src), "unit": r["name"], "teacher": MODEL,
                          "verified": "clj-kondo-unit+file"}},
                ensure_ascii=False) + "\n")
    return {**rec, "status": "ok", "out": str(out)}


def main() -> int:
    global MODEL, PER_NODE_CONCURRENCY
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--per-node", type=int, default=PER_NODE_CONCURRENCY)
    args = ap.parse_args()
    MODEL, PER_NODE_CONCURRENCY = args.model, args.per_node

    paths = []
    for f in args.files:
        if f == "-":
            paths += [Path(l.strip()) for l in sys.stdin if l.strip()]
        else:
            paths.append(Path(f))
    paths = [p for p in paths if p.suffix == ".py"]

    pool = Pool()
    done = {"ok": 0, "fail": 0, "skip": 0, "error": 0}
    # unit 並列はノード総スロット; file 並列はその半分で oversubscribe を防ぐ
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(NODES) * PER_NODE_CONCURRENCY) as unit_ex, \
         concurrent.futures.ThreadPoolExecutor(
            max_workers=max(2, len(NODES) * PER_NODE_CONCURRENCY // 2)) as file_ex, \
         RESULTS_LOG.open("a") as logf:
        futs = {file_ex.submit(port_file, pool, unit_ex, p): p for p in paths}
        for fut in concurrent.futures.as_completed(futs):
            try:
                r = fut.result()
            except Exception as e:
                r = {"src": str(futs[fut]), "status": "error",
                     "reason": f"harness: {e!r}"}
            done[r["status"]] += 1
            logf.write(json.dumps(r, ensure_ascii=False) + "\n")
            logf.flush()
            print(f"[{sum(done.values())}/{len(paths)}] {r['status']:5s} "
                  f"{r['src']} ({r.get('unit_ok','-')}/{r.get('units','-')} units, "
                  f"{r.get('secs','-')}s)"
                  + (f" — {r.get('reason','')[:90]}" if r["status"] != "ok" else ""),
                  flush=True)
    print(f"\nsummary: {done}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
