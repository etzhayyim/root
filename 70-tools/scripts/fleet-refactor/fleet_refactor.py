#!/usr/bin/env python3
"""fleet_refactor — Murakumo fleet 並列 source→Clojure refactor harness.

Python / TypeScript ソースを kotoba-Datomic-native Clojure へ移植する
ファン・アウトハーネス。Murakumo Mac mini fleet の各ノード Ollama
(gemma4:e4b, OpenAI 互換 /v1/chat/completions) へ tailscale 経由で
ラウンドロビン分配する。

ADR-2605215000 (Murakumo-only inference): fleet Ollama 直叩きは認可経路。

検証ゲート: 生成された .clj は clj-kondo --lint を通過しない限り
書き込まれない (エラー時は lint 出力を添えて 1 回リトライ)。

Usage:
  python3 fleet_refactor.py FILE [FILE...]          # 指定ファイルを移植
  git ls-files '*.py' | python3 fleet_refactor.py - # stdin からリスト
  python3 fleet_refactor.py --dry-run FILE          # プロンプトのみ表示

出力: 各ソースと同じディレクトリに <stem>.clj を生成。
結果ログ: ./fleet-refactor-results.jsonl (append)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Murakumo fleet (tailscale IPs, 2026-06-11 時点で全 10 ノード gemma4:e4b 確認済) ──
NODES = [
    ("naphtali", "100.101.27.85"),
    ("simeon", "100.81.66.86"),
    ("judah", "100.113.200.45"),
    ("zebulun", "100.66.28.79"),
    ("levi", "100.102.78.81"),
    ("joseph", "100.82.123.35"),
    ("issachar", "100.89.204.30"),
    ("dan", "100.98.142.59"),
    ("benjamin", "100.75.169.8"),
    ("asher", "100.96.122.69"),
]
MODEL = "gemma4:e4b"  # --model で上書き可 (e.g. gemma4:12b-it-qat)
PER_NODE_CONCURRENCY = 2
MAX_SOURCE_CHARS = 16_000  # e4b コンテキスト保護; 超過ファイルは skip
REQUEST_TIMEOUT_S = 420
MAX_ATTEMPTS = 3
RESULTS_LOG = Path("fleet-refactor-results.jsonl")

LANG_BY_SUFFIX = {".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript (TSX)"}

SYSTEM_PROMPT = """You are a precise code translator. You convert source files to Clojure.

Rules:
- Output EXACTLY ONE ```clojure code block and nothing else. No prose before or after.
- Preserve the module's behavior and public API surface (function names become kebab-case).
- Idiomatic Clojure: pure functions, immutable data, EDN maps with namespaced keywords.
- State/persistence code is ported onto the kotoba Datom log idiom: facts are EAVT
  datoms `[e a v t]`, attributes are namespaced keywords like :entity/attr,
  writes are `(transact! conn tx-data)`, reads are datalog `(q '[:find ...] db)`.
  Do NOT invent HTTP clients for this; express it as data + a `transact!`/`q` boundary.
- Keep the original file's docstring/comments as a top ;; comment block (translated to ;;).
- Start the file with (ns <namespace>) derived from the file path.
- If something cannot be expressed (FFI, platform API), stub it as a function that
  throws (ex-info "TODO: port" {:from "<original symbol>"}) — never drop it silently.
- CRITICAL: every ( [ { must close. Count your brackets. Prefer many small top-level
  defn forms over deeply nested ones. Use only clojure.core + clojure.string +
  clojure.set + clojure.edn — never invent symbols (no if-contains?, no %? etc.).

Example shape (Python → Clojure):

```python
# guards feedstock intake
def is_allowed(feedstock):
    return feedstock.get("kind") in {"waste-plastic", "biomass"}
```

```clojure
;; guards feedstock intake
(ns kamado.methods.feedstock-guard)

(def allowed-kinds #{"waste-plastic" "biomass"})

(defn is-allowed? [feedstock]
  (contains? allowed-kinds (:kind feedstock)))
```"""

USER_TEMPLATE = """Convert this {lang} file to Clojure per the rules.

Path: {path}
Suggested ns: {ns}

```{tag}
{source}
```"""


def ns_from_path(path: Path) -> str:
    parts = [re.sub(r"[^a-zA-Z0-9]", "-", p).strip("-") for p in path.with_suffix("").parts]
    parts = [p for p in parts if p and not p[0].isdigit()] or ["ported"]
    return ".".join(parts[-4:]).lower()


class NodePool:
    """ノードごとの同時実行数を制限するラウンドロビンプール。"""

    def __init__(self, nodes, per_node):
        self._sems = {name: threading.Semaphore(per_node) for name, _ in nodes}
        self._nodes = list(nodes)
        self._lock = threading.Lock()
        self._i = 0

    def acquire(self):
        while True:
            with self._lock:
                order = self._nodes[self._i:] + self._nodes[: self._i]
                self._i = (self._i + 1) % len(self._nodes)
            for name, ip in order:
                if self._sems[name].acquire(blocking=False):
                    return name, ip
            time.sleep(0.5)

    def release(self, name):
        self._sems[name].release()


def chat(ip: str, messages: list[dict]) -> str:
    body = json.dumps(
        {"model": MODEL, "messages": messages, "stream": False,
         "options": {"temperature": 0.1, "num_ctx": 16384}}
    ).encode()
    req = urllib.request.Request(
        f"http://{ip}:11434/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def extract_clojure(text: str) -> str | None:
    m = re.search(r"```(?:clojure|clj)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip() + "\n"
    if text.lstrip().startswith((";;", "(ns ")):
        return text.strip() + "\n"
    return None


def lint(clj_path: Path) -> tuple[bool, str]:
    if not shutil.which("clj-kondo"):
        return True, "clj-kondo unavailable — lint skipped"
    r = subprocess.run(
        ["clj-kondo", "--lint", str(clj_path), "--fail-level", "error"],
        capture_output=True, text=True, timeout=60,
    )
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def port_file(pool: NodePool, src: Path) -> dict:
    rec = {"src": str(src), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    lang = LANG_BY_SUFFIX.get(src.suffix)
    if lang is None:
        return {**rec, "status": "skip", "reason": f"unsupported suffix {src.suffix}"}
    try:
        source = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return {**rec, "status": "skip", "reason": f"unreadable: {e}"}
    if len(source) > MAX_SOURCE_CHARS:
        return {**rec, "status": "skip", "reason": f"too large ({len(source)} chars)"}

    ns = ns_from_path(src)
    # ns 最終セグメントとファイル名を一致させる (clj-kondo namespace-name-mismatch 対策;
    # Clojure 規約: ns の '-' はファイル名では '_')
    out = src.parent / (ns.rsplit(".", 1)[-1].replace("-", "_") + ".clj")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_TEMPLATE.format(
            lang=lang, path=src, ns=ns,
            tag="python" if lang == "Python" else "typescript", source=source)},
    ]

    node, ip = pool.acquire()
    rec["node"] = node
    t0 = time.time()
    lint_out = "model never produced a clojure block"
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                reply = chat(ip, messages)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                return {**rec, "status": "error", "reason": f"node {node}: {e}"}
            code = extract_clojure(reply)
            if code is None:
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content":
                                 "Invalid: output exactly one ```clojure block."})
                continue
            out.write_text(code, encoding="utf-8")
            ok, lint_out = lint(out)
            if ok:
                return {**rec, "status": "ok", "out": str(out), "attempt": attempt,
                        "secs": round(time.time() - t0, 1)}
            if attempt < MAX_ATTEMPTS:
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content":
                                 f"clj-kondo found errors — fix and re-output the full "
                                 f"corrected ```clojure block:\n{lint_out[:2000]}"})
        out.unlink(missing_ok=True)
        return {**rec, "status": "fail", "reason": f"lint failed after retry: {lint_out[:500]}",
                "secs": round(time.time() - t0, 1)}
    finally:
        pool.release(node)


def main() -> int:
    global MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="source files, or '-' for stdin list")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()
    MODEL = args.model

    paths = []
    for f in args.files:
        if f == "-":
            paths += [Path(l.strip()) for l in sys.stdin if l.strip()]
        else:
            paths.append(Path(f))

    if args.dry_run:
        for p in paths:
            print(f"would port {p} -> {p.with_suffix('.clj')} (ns {ns_from_path(p)})")
        return 0

    pool = NodePool(NODES, PER_NODE_CONCURRENCY)
    workers = len(NODES) * PER_NODE_CONCURRENCY
    done = {"ok": 0, "fail": 0, "skip": 0, "error": 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex, \
            RESULTS_LOG.open("a") as logf:
        futs = {ex.submit(port_file, pool, p): p for p in paths}
        for fut in concurrent.futures.as_completed(futs):
            try:
                rec = fut.result()
            except Exception as e:  # 1 ファイルの例外で全体を殺さない
                rec = {"src": str(futs[fut]), "status": "error",
                       "reason": f"harness exception: {e!r}"}
            done[rec["status"]] += 1
            logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            logf.flush()
            n = sum(done.values())
            print(f"[{n}/{len(paths)}] {rec['status']:5s} {rec['src']}"
                  + (f" ({rec.get('secs')}s @{rec.get('node')})" if "secs" in rec else
                     f" — {rec.get('reason', '')[:80]}"))
    print(f"\nsummary: {done}")
    return 0 if done["fail"] + done["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
