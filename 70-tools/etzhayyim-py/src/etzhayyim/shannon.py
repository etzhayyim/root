"""shannon — Shannon redundancy scoring (Python port, ADR-2605151500).

Implements the 9 redundancy checks from the Go binary. Checks that require
Go AST or the haisen graph (code_clone_cross, collection_write_fan,
wit_type_duplication, rust_duplication) score 100 with a note; the remaining
5 are fully ported.

Subcommands: scan, violations, dsm, bayesnet, bottleneck, minimize
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import click

# ── data types ─────────────────────────────────────────────────────────────────

@dataclass
class ShannonItem:
    path: str
    kind: str
    redundancy: float  # 0.0–1.0
    duplicate_of: str = ""
    detail: str = ""

    def to_dict(self) -> dict:
        d: dict = {"path": self.path, "kind": self.kind, "redundancy": self.redundancy}
        if self.duplicate_of:
            d["duplicate_of"] = self.duplicate_of
        if self.detail:
            d["detail"] = self.detail
        return d


@dataclass
class ShannonCheck:
    name: str
    score: float = 100.0
    weight: float = 0.0
    violations: int = 0
    details: str = ""
    items: list[ShannonItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "violations": self.violations,
            "details": self.details,
            "items": [i.to_dict() for i in self.items],
        }


@dataclass
class ShannonReport:
    evaluated_at: str
    overall_score: float
    redundancy_rate: float
    checks: list[ShannonCheck]
    hotspots: list[ShannonItem]
    scoring_model: str

    def to_dict(self) -> dict:
        return {
            "evaluated_at": self.evaluated_at,
            "overall_score": self.overall_score,
            "redundancy_rate": self.redundancy_rate,
            "checks": [c.to_dict() for c in self.checks],
            "hotspots": [h.to_dict() for h in self.hotspots],
            "scoring_model": self.scoring_model,
        }


WEIGHTS: dict[str, float] = {
    "claude_md_duplication":  0.25,
    "code_clone_cross":       0.15,
    "collection_write_fan":   0.15,
    "wit_type_duplication":   0.10,
    "config_redundancy":      0.10,
    "dead_code_entropy":      0.10,
    "doc_code_drift":         0.10,
    "rust_duplication":       0.05,
    "stale_symbol_entropy":   0.10,
}

_SKIP_DIRS = {"node_modules", ".git", "target", ".cargo-target", "_svelte"}

# ── helpers ────────────────────────────────────────────────────────────────────

def _cap(score: float) -> float:
    return round(max(0.0, min(100.0, score)), 1)


def _find_git_root(start: Path) -> Path:
    p = start
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    return start


def _resolve_root(override: str | None) -> Path:
    if override:
        return Path(override).resolve()
    return _find_git_root(Path.cwd()).resolve()


def _walk(root: Path, suffixes: tuple[str, ...] | None = None, name: str | None = None):
    """Yield files under root, skipping common skip dirs."""
    for p in root.rglob("*"):
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue
        if name and p.name != name:
            continue
        if suffixes and p.suffix not in suffixes:
            continue
        yield p


def _norm_line(s: str) -> str:
    s = s.lower().strip()
    for ch in ("**", "*", "`"):
        s = s.replace(ch, "")
    return " ".join(s.split())


def _hash8(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _dedup(items: list[ShannonItem]) -> list[ShannonItem]:
    seen: set[str] = set()
    result: list[ShannonItem] = []
    for item in items:
        key = f"{item.path}|{item.kind}|{item.detail}"
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# ── check 1: CLAUDE.md inter-file duplication ──────────────────────────────────

def check_claude_md_duplication(ws: Path) -> ShannonCheck:
    chk = ShannonCheck(name="claude_md_duplication")

    files = [p for p in _walk(ws, name="CLAUDE.md")]
    if len(files) < 2:
        chk.score = 100.0
        chk.details = "fewer than 2 CLAUDE.md files"
        return chk

    docs: list[tuple[str, dict[str, str]]] = []  # (rel_path, {hash: line})
    for f in files:
        try:
            content = f.read_text(errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(ws))
        hashes: dict[str, str] = {}
        in_fm = False
        for line in content.splitlines():
            trimmed = line.strip()
            if trimmed == "---":
                in_fm = not in_fm
                continue
            if in_fm:
                continue
            if len(trimmed) < 20:
                continue
            if trimmed.startswith("#") and "—" not in trimmed and len(trimmed) < 60:
                continue
            if trimmed.startswith("|---") or trimmed.startswith("| ---"):
                continue
            norm = _norm_line(trimmed)
            if len(norm) < 15:
                continue
            h = _hash8(norm)
            if h not in hashes:
                hashes[h] = trimmed
        if hashes:
            docs.append((rel, hashes))

    # Build hash → doc indices index
    line_files: dict[str, list[int]] = {}
    for i, (_, hashes) in enumerate(docs):
        for h in hashes:
            line_files.setdefault(h, []).append(i)
        line_files = {k: list(dict.fromkeys(v)) for k, v in line_files.items()}

    total_unique = len(line_files)
    duplicated = 0
    root_idx = next((i for i, (p, _) in enumerate(docs) if p == "CLAUDE.md"), -1)
    items: list[ShannonItem] = []

    for h, indices in line_files.items():
        if len(indices) < 2:
            continue
        duplicated += 1
        for idx in indices:
            if idx == root_idx:
                continue
            dup_of = docs[[j for j in indices if j != idx][0]][0]
            orig = docs[idx][1].get(h, "")
            if len(orig) > 80:
                orig = orig[:80] + "..."
            items.append(ShannonItem(
                path=docs[idx][0],
                kind="claude_md_duplication",
                redundancy=1.0,
                duplicate_of=dup_of,
                detail=orig,
            ))

    chk.items = _dedup(items)
    chk.violations = duplicated
    chk.score = _cap(100 - (duplicated / total_unique * 100) if total_unique > 0 else 100)
    if duplicated > 0:
        chk.details = f"{duplicated}/{total_unique} lines duplicated across {len(docs)} CLAUDE.md files"
    return chk


# ── check 2,3,4,8: Go-AST/haisen-dependent (stub ─ Python port skips) ─────────

def _go_only_stub(name: str) -> ShannonCheck:
    chk = ShannonCheck(name=name)
    chk.score = 100.0
    chk.details = f"not available in Python port — use Go binary: etzhayyim shannon scan"
    return chk


# ── check 5: config redundancy (wrangler.jsonc) ────────────────────────────────

_DEPLOY_INJECTED = {
    "APP_TEMPLATE", "APP_SOURCE", "APP_VERSION",
    "APP_DEPLOY_SHA", "APP_DEPLOY_AT", "WASM_HASH",
}

def _strip_jsonc_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        if esc:
            out.append(ch)
            esc = False
            i += 1
            continue
        if in_str:
            if ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < len(text):
            if text[i + 1] == "/":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            if text[i + 1] == "*":
                i += 2
                while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def check_config_redundancy(ws: Path) -> ShannonCheck:
    chk = ShannonCheck(name="config_redundancy")
    entries: list[tuple[str, str, str]] = []  # (key, value, file)

    for f in _walk(ws):
        if f.name not in ("wrangler.jsonc", "wrangler.json"):
            continue
        try:
            text = f.read_text(errors="replace")
            cleaned = _strip_jsonc_comments(text)
            parsed = json.loads(cleaned)
        except (OSError, json.JSONDecodeError):
            continue
        rel = str(f.relative_to(ws))
        vars_ = parsed.get("vars", {})
        for k, v in vars_.items():
            if k in _DEPLOY_INJECTED:
                continue
            entries.append((k, str(v), rel))

    # Group by key=value
    kv_group: dict[str, list[str]] = {}
    for k, v, rel in entries:
        kv_group.setdefault(f"{k}={v}", []).append(rel)

    total = len(kv_group)
    redundant = 0
    for kv, files in kv_group.items():
        if len(files) < 3:
            continue
        redundant += 1
        k, v = kv.split("=", 1)
        chk.items.append(ShannonItem(
            path=k,
            kind="config_redundancy",
            redundancy=1.0 - 1.0 / len(files),
            detail=f"{k}={v} in {len(files)} files",
        ))

    chk.violations = redundant
    chk.score = _cap(100 - (redundant / total * 100) if total > 0 else 100)
    if redundant > 0:
        chk.details = f"{redundant}/{total} config key=value pairs appear in 3+ files"
    return chk


# ── check 6: dead code entropy ─────────────────────────────────────────────────

_GO_FN_RE = re.compile(r"^(?:func\s+\w+|func\s+\([^)]+\)\s+\w+)\s*\(", re.MULTILINE)
_GO_EMPTY_RE = re.compile(r"func\s+\w+[^{]*\{\s*\}", re.MULTILINE)
_GO_STUB_RE = re.compile(r"func\s+\w+[^{]*\{\s*(?:panic\(|// TODO)", re.MULTILINE)
_TS_FN_RE = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+\w+", re.MULTILINE)
_TS_EMPTY_RE = re.compile(r"function\s+\w+[^{]*\{\s*\}", re.MULTILINE)
_TS_STUB_RE = re.compile(r"function\s+\w+[^{]*\{\s*(?:throw|// TODO)", re.MULTILINE)


def check_dead_code_entropy(ws: Path) -> ShannonCheck:
    chk = ShannonCheck(name="dead_code_entropy")
    total_fns = 0
    dead_fns = 0

    scan_dirs = [
        ws / "projects",
        ws / "infra" / "cloudflare",
        ws / "60-apps",
        ws / "20-actors",
    ]

    for base in scan_dirs:
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if any(part in _SKIP_DIRS for part in f.parts):
                continue
            if not f.is_file():
                continue
            try:
                text = f.read_text(errors="replace")
            except OSError:
                continue
            rel = str(f.relative_to(ws))

            if f.suffix == ".go" and not f.name.endswith("_test.go"):
                t = len(_GO_FN_RE.findall(text))
                e = len(_GO_EMPTY_RE.findall(text))
                s = len(_GO_STUB_RE.findall(text))
                total_fns += t
                dead_fns += e + s
                if e > 0:
                    chk.items.append(ShannonItem(path=rel, kind="dead_code_entropy", redundancy=1.0,
                                                  detail=f"{e} empty Go func bodies"))
                if s > 0:
                    chk.items.append(ShannonItem(path=rel, kind="dead_code_entropy", redundancy=0.9,
                                                  detail=f"{s} stub Go funcs (panic/TODO)"))

            elif f.suffix == ".ts" and not f.name.endswith((".d.ts", ".test.ts")):
                t = len(_TS_FN_RE.findall(text))
                e = len(_TS_EMPTY_RE.findall(text))
                s = len(_TS_STUB_RE.findall(text))
                total_fns += t
                dead_fns += e + s
                if e > 0:
                    chk.items.append(ShannonItem(path=rel, kind="dead_code_entropy", redundancy=1.0,
                                                  detail=f"{e} empty TS function bodies"))
                if s > 0:
                    chk.items.append(ShannonItem(path=rel, kind="dead_code_entropy", redundancy=0.9,
                                                  detail=f"{s} stub TS functions (throw/TODO)"))

    chk.violations = dead_fns
    chk.score = _cap(100 - (dead_fns / total_fns * 100) if total_fns > 0 else 100)
    if dead_fns > 0:
        chk.details = f"{dead_fns}/{total_fns} functions are dead (empty/stub/TODO-only)"
    return chk


# ── check 7: doc/code drift ────────────────────────────────────────────────────

_EVIDENCE_RE = re.compile(r"(?:evidence:\s*)?`([^`]+)`")
_STATUS_TAG_RE = re.compile(r"\[(PRODUCTION|IMPLEMENTED)\]")


def check_doc_code_drift(ws: Path) -> ShannonCheck:
    chk = ShannonCheck(name="doc_code_drift")
    total_claims = 0
    stale = 0

    for f in _walk(ws, name="CLAUDE.md"):
        try:
            lines = f.read_text(errors="replace").splitlines()
        except OSError:
            continue
        rel = str(f.relative_to(ws))
        for line in lines:
            if not _STATUS_TAG_RE.search(line):
                continue
            for m in _EVIDENCE_RE.finditer(line):
                total_claims += 1
                ev = m.group(1)
                file_part = ev
                if ":" in file_part:
                    file_part = file_part.rsplit(":", 1)[0]
                if " (" in file_part:
                    file_part = file_part.split(" (", 1)[0]
                full = ws / file_part
                if not full.exists():
                    stale += 1
                    chk.items.append(ShannonItem(
                        path=rel, kind="doc_code_drift", redundancy=1.0,
                        detail=f"evidence file missing: {ev}",
                    ))

    chk.violations = stale
    chk.score = _cap(100 - (stale / total_claims * 100) if total_claims > 0 else 100)
    if total_claims == 0:
        chk.details = "no [PRODUCTION]/[IMPLEMENTED] evidence links found"
    elif stale > 0:
        chk.details = f"{stale}/{total_claims} evidence links are stale (file missing)"
    return chk


# ── check 9: stale symbol entropy ─────────────────────────────────────────────

_STRIKETHROUGH_RE = re.compile(r"~~.+~~")
_PROHIBITED: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bDOSqlExec\b"), "prohibited-api", "DOSqlExec — use G() or ComAtprotoRepoCreateRecord"),
    (re.compile(r"\bSqlExec\s*\("), "prohibited-api", "SqlExec() — use G() builder"),
    (re.compile(r"\bSqlQueryMap\s*\("), "prohibited-api", "SqlQueryMap() — use G() builder"),
    (re.compile(r'\bappId:\s*"pds"'), "prohibited-magic", 'appId: "pds" — use repo-derived appId'),
]


def check_stale_symbol_entropy(ws: Path) -> ShannonCheck:
    chk = ShannonCheck(name="stale_symbol_entropy")
    total_checked = 0
    items: list[ShannonItem] = []

    # Sub-check 1: CLAUDE.md strikethrough remnants
    for f in _walk(ws, name="CLAUDE.md"):
        try:
            lines = f.read_text(errors="replace").splitlines()
        except OSError:
            continue
        rel = str(f.relative_to(ws))
        for ln, line in enumerate(lines, 1):
            total_checked += 1
            if _STRIKETHROUGH_RE.search(line):
                if "禁止" in line or "PROHIBITED" in line:
                    continue
                items.append(ShannonItem(
                    path=f"{rel}:{ln}",
                    kind="claude-md-strikethrough",
                    redundancy=0.8,
                    detail="strikethrough in CLAUDE.md — delete (git has history)",
                ))

    # Sub-check 2: prohibited symbol usage in Go/TS
    for f in _walk(ws, suffixes=(".go", ".ts")):
        if any(s in str(f) for s in ("code_quality.go", "shannon.go", "shannon.py")):
            continue
        if f.name.endswith(("_test.go", ".test.ts", ".spec.ts", ".d.ts")):
            continue
        if any(g in str(f) for g in ("/generated/", "/gen/")):
            continue
        try:
            lines = f.read_text(errors="replace").splitlines()
        except OSError:
            continue
        rel = str(f.relative_to(ws))
        for ln, line in enumerate(lines, 1):
            for pattern, kind, msg in _PROHIBITED:
                if pattern.search(line):
                    total_checked += 1
                    items.append(ShannonItem(
                        path=f"{rel}:{ln}", kind=kind, redundancy=1.0, detail=msg,
                    ))

    chk.items = _dedup(items)
    chk.violations = len(chk.items)
    score = 100.0 * (1.0 - len(chk.items) / total_checked) if total_checked > 0 else 100.0
    chk.score = _cap(score)
    chk.details = f"checked {total_checked} symbols/lines, found {len(chk.items)} stale/prohibited"
    return chk


# ── build report ───────────────────────────────────────────────────────────────

def run_all_checks(ws: Path) -> list[ShannonCheck]:
    return [
        check_claude_md_duplication(ws),
        _go_only_stub("code_clone_cross"),
        _go_only_stub("collection_write_fan"),
        _go_only_stub("wit_type_duplication"),
        check_config_redundancy(ws),
        check_dead_code_entropy(ws),
        check_doc_code_drift(ws),
        _go_only_stub("rust_duplication"),
        check_stale_symbol_entropy(ws),
    ]


def build_report(checks: list[ShannonCheck], top_n: int = 15) -> ShannonReport:
    weighted_sum = 0.0
    total_weight = 0.0
    all_items: list[ShannonItem] = []

    for chk in checks:
        w = WEIGHTS.get(chk.name, 0.0)
        chk.weight = w
        weighted_sum += chk.score * w
        total_weight += w
        all_items.extend(chk.items)

    overall = weighted_sum / total_weight if total_weight > 0 else 100.0
    all_items.sort(key=lambda x: x.redundancy, reverse=True)
    hotspots = all_items[:top_n]

    check_labels = "+".join(
        f"{c.name}({c.score:.0f}%×{c.weight*100:.0f})" for c in checks
    )

    return ShannonReport(
        evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        overall_score=round(overall, 1),
        redundancy_rate=round(1 - overall / 100, 3),
        checks=checks,
        hotspots=hotspots,
        scoring_model=f"weighted: {check_labels}",
    )


def _print_text(r: ShannonReport) -> None:
    click.echo(f"shannon:")
    click.echo(f"  evaluated_at: {r.evaluated_at}")
    click.echo(f"  overall_score: {r.overall_score:.1f}")
    click.echo(f"  redundancy_rate: {r.redundancy_rate*100:.1f}%")
    click.echo(f"  checks:")
    for c in r.checks:
        click.echo(f"    {c.name}:")
        click.echo(f"      score: {c.score:.1f} (weight: {c.weight*100:.0f}%)")
        click.echo(f"      violations: {c.violations}")
        if c.details:
            click.echo(f"      details: {c.details!r}")
    if r.hotspots:
        click.echo(f"  hotspots:")
        for h in r.hotspots:
            click.echo(f"    - [{h.redundancy*100:.0f}%] {h.kind}: {h.path}")
            if h.detail:
                click.echo(f"            {h.detail}")


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("shannon")
def shannon():
    """Shannon redundancy scoring for the repository."""


@shannon.command("scan")
@click.option("--json", "json_out", is_flag=True, default=False, help="Output as JSON")
@click.option("--top", default=15, show_default=True, help="Number of hotspots to show")
@click.option("--workspace-dir", "workspace_dir", default=None, help="Workspace root (default: git root)")
def scan(json_out: bool, top: int, workspace_dir: str | None):
    """Run all redundancy checks and output full report."""
    ws = _resolve_root(workspace_dir)
    checks = run_all_checks(ws)
    report = build_report(checks, top)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_text(report)


@shannon.command("violations")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", "workspace_dir", default=None)
def violations(json_out: bool, workspace_dir: str | None):
    """List redundancy violations only (no scoring)."""
    ws = _resolve_root(workspace_dir)
    checks = run_all_checks(ws)
    all_items: list[ShannonItem] = []
    for c in checks:
        all_items.extend(c.items)
    all_items.sort(key=lambda x: x.redundancy, reverse=True)
    if json_out:
        click.echo(json.dumps([i.to_dict() for i in all_items], ensure_ascii=False, indent=2))
    else:
        for item in all_items:
            click.echo(f"  [{item.redundancy*100:.0f}%] {item.kind}: {item.path} — {item.detail}")
        click.echo(f"\ntotal violations: {len(all_items)}")


# ── Shannon graph helpers (haisen adapter) ────────────────────────────────────

_EDGE_TYPE_WEIGHTS: dict[str, float] = {
    "invoke":          0.8,
    "writes":          0.5,
    "subscribe":       0.4,
    "reads":           0.3,
    "follow":          0.1,
    "service_binding": 0.6,
}


def _sh_entropy(counts: dict) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log2(p)
    return h


def _sh_scan(ws: Path) -> tuple[list[str], dict, dict, dict]:
    """Return (sorted_apps, adj, adj_typed, app_proj) from haisen workspace scan."""
    from .haisen import _scan_workspace, _read_jsonld

    report = _scan_workspace(ws)

    # Build project map by re-reading jsonld
    app_proj: dict[str, str] = {}
    for root_dir in (ws / "60-apps", ws / "projects"):
        if root_dir.exists():
            for jsonld_path in root_dir.rglob("magatama.jsonld"):
                data = _read_jsonld(jsonld_path)
                nanoid = data.get("nanoid", "")
                if nanoid:
                    app_proj[nanoid] = data.get("project", "") or ""
            break

    apps = sorted({a.nanoid for a in report.apps})

    adj: dict[str, dict[str, int]] = {}
    adj_typed: dict[str, dict[str, dict[str, int]]] = {}

    for e in report.edges:
        frm, to, etype = e.from_nanoid, e.to_nanoid, e.edge_type
        if not frm or not to or frm == to:
            continue
        if frm not in adj:
            adj[frm] = {}
        adj[frm][to] = adj[frm].get(to, 0) + 1
        if frm not in adj_typed:
            adj_typed[frm] = {}
        if to not in adj_typed[frm]:
            adj_typed[frm][to] = {}
        adj_typed[frm][to][etype] = adj_typed[frm][to].get(etype, 0) + 1

    return apps, adj, adj_typed, app_proj


# ── DSM ────────────────────────────────────────────────────────────────────────

def _dsm_cuthill_mckee(matrix: list[list[int]], n: int) -> list[int]:
    degree = [0] * n
    for i in range(n):
        neighbors = {j for j in range(n) if i != j and (matrix[i][j] > 0 or matrix[j][i] > 0)}
        degree[i] = len(neighbors)

    visited = [False] * n
    result: list[int] = []

    while len(result) < n:
        start = -1
        min_deg = n + 1
        for i in range(n):
            if not visited[i] and degree[i] < min_deg:
                min_deg = degree[i]
                start = i
        if start == -1:
            break

        queue = [start]
        visited[start] = True
        while queue:
            node = queue.pop(0)
            result.append(node)
            neighbors = sorted(
                [j for j in range(n) if not visited[j] and (matrix[node][j] > 0 or matrix[j][node] > 0)],
                key=lambda x: degree[x],
            )
            for nb in neighbors:
                if not visited[nb]:
                    visited[nb] = True
                    queue.append(nb)

    result.reverse()
    return result


def _dsm_detect_cycles(apps: list[str], adj: dict) -> list[dict]:
    max_len = 8
    max_cycles = 50
    cycles: list[dict] = []
    seen: set[str] = set()

    def _canon(path: list[str]) -> str:
        if not path:
            return ""
        min_idx = min(range(len(path)), key=lambda i: path[i])
        rotated = [path[(i + min_idx) % len(path)] for i in range(len(path))]
        return "→".join(rotated)

    for start in apps:
        if len(cycles) >= max_cycles:
            break

        def dfs(node: str, path: list[str]) -> None:
            if len(cycles) >= max_cycles or len(path) > max_len:
                return
            for nxt in (adj.get(node) or {}):
                if nxt == start and len(path) >= 2:
                    cycle_path = path + [start]
                    canon = _canon(cycle_path[:-1])
                    if canon not in seen:
                        seen.add(canon)
                        cycles.append({"path": cycle_path, "length": len(cycle_path) - 1})
                    continue
                if nxt not in path:
                    dfs(nxt, path + [nxt])

        dfs(start, [start])

    cycles.sort(key=lambda c: c["length"])
    return cycles


def _dsm_find_clusters(apps: list[str], adj: dict) -> list[dict]:
    neighbors: dict[str, set[str]] = {}
    for frm, targets in adj.items():
        for to in targets:
            neighbors.setdefault(frm, set()).add(to)
            neighbors.setdefault(to, set()).add(frm)

    visited: set[str] = set()
    clusters: list[dict] = []

    for start in apps:
        if start in visited:
            continue
        members: list[str] = []
        queue = [start]
        visited.add(start)
        while queue:
            node = queue.pop(0)
            members.append(node)
            for nb in (neighbors.get(node) or set()):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        members.sort()
        member_set = set(members)
        internal = sum(
            count for m in members for to, count in (adj.get(m) or {}).items() if to in member_set
        )
        external = sum(
            count for m in members for to, count in (adj.get(m) or {}).items() if to not in member_set
        )
        clusters.append({
            "name": f"cluster-{len(clusters) + 1}",
            "members": members,
            "internal_deps": internal,
            "external_deps": external,
        })
    return clusters


def _build_dsm_report(apps: list[str], adj: dict, top_n: int, no_reorder: bool) -> dict:
    n = len(apps)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if n == 0:
        return {"generated_at": now, "size": 0, "apps": [], "matrix": [], "entries": [],
                "clusters": [], "cycles": [], "bandwidth": 0, "score": 100.0}

    idx = {a: i for i, a in enumerate(apps)}
    matrix = [[0] * n for _ in range(n)]
    for frm, targets in adj.items():
        fi = idx.get(frm)
        if fi is None:
            continue
        for to, count in targets.items():
            ti = idx.get(to)
            if ti is not None:
                matrix[fi][ti] = count

    perm = list(range(n))
    if not no_reorder and n > 2:
        perm = _dsm_cuthill_mckee(matrix, n)

    reordered = [apps[perm[i]] for i in range(n)]
    rm = [[matrix[perm[i]][perm[j]] for j in range(n)] for i in range(n)]

    entries = [
        {"from": reordered[i], "to": reordered[j], "count": rm[i][j]}
        for i in range(n) for j in range(n) if rm[i][j] > 0
    ]

    bw = max(
        (abs(i - j) for i in range(n) for j in range(n) if rm[i][j] > 0),
        default=0,
    )

    cycles = _dsm_detect_cycles(reordered, adj)
    clusters = sorted(_dsm_find_clusters(reordered, adj), key=lambda c: len(c["members"]), reverse=True)
    if len(clusters) > top_n:
        clusters = clusters[:top_n]

    score = max(0.0, 100.0 * (1.0 - bw / n)) if n > 1 else 100.0

    return {
        "generated_at": now,
        "size": n,
        "apps": reordered,
        "matrix": rm,
        "entries": entries,
        "clusters": clusters,
        "cycles": cycles,
        "bandwidth": bw,
        "score": round(score, 1),
    }


def _print_dsm_text(r: dict) -> None:
    click.echo("shannon dsm:")
    click.echo(f"  generated_at: {r['generated_at']}")
    click.echo(f"  size: {r['size']} × {r['size']}")
    click.echo(f"  bandwidth: {r['bandwidth']}")
    click.echo(f"  score: {r['score']}")

    display_n = min(r["size"], 40)
    if display_n > 0:
        click.echo(f"\n  matrix ({display_n} apps):")
        names = [(a[:8] if len(a) > 8 else a) for a in r["apps"][:display_n]]
        header = "  " + " " * 9 + " ".join(n[0] for n in names)
        click.echo(header)
        for i in range(display_n):
            row = "  " + f"{names[i]:8s} "
            for j in range(display_n):
                v = r["matrix"][i][j]
                row += ("· " if i == j else "+ " if v > 0 else ". ")
            click.echo(row)

    clusters = r.get("clusters", [])
    if clusters:
        click.echo(f"\n  clusters: {len(clusters)}")
        for c in clusters:
            click.echo(f"    {c['name']} ({len(c['members'])} members, "
                       f"{c['internal_deps']} internal, {c['external_deps']} external)")
            if len(c["members"]) <= 10:
                click.echo(f"      members: {', '.join(c['members'])}")

    cycles = r.get("cycles", [])
    if cycles:
        click.echo(f"\n  cycles: {len(cycles)}")
        for cyc in cycles[:10]:
            click.echo(f"    [len={cyc['length']}] {' → '.join(cyc['path'])}")
        if len(cycles) > 10:
            click.echo(f"    ... and {len(cycles) - 10} more")


@shannon.command("dsm")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--top", default=10, show_default=True)
@click.option("--no-reorder", "no_reorder", is_flag=True, default=False)
def dsm(json_out: bool, workspace_dir: str | None, top: int, no_reorder: bool) -> None:
    """Dependency Structure Matrix — N×N adjacency with Cuthill-McKee bandwidth minimization."""
    ws = _resolve_root(workspace_dir)
    apps, adj, _, _ = _sh_scan(ws)
    r = _build_dsm_report(apps, adj, top, no_reorder)
    if json_out:
        click.echo(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        _print_dsm_text(r)


# ── BayesNet ───────────────────────────────────────────────────────────────────

def _bayes_dijkstra_from(
    source: str,
    edge_adj: dict[str, list[dict]],
    max_depth: int,
) -> list[dict]:
    pq: list[tuple[float, int, str, list[str]]] = []
    counter = 0
    heapq.heappush(pq, (0.0, counter, source, [source]))

    visited: set[str] = set()
    paths: list[dict] = []
    max_paths_per_source = 5

    while pq and len(paths) < max_paths_per_source:
        neg_log_p, _, node, path = heapq.heappop(pq)

        if node in visited and len(path) > 1:
            continue
        visited.add(node)

        if len(path) >= 3:
            prob = math.exp(-neg_log_p)
            if prob > 0.01:
                paths.append({"nodes": list(path), "probability": prob, "length": len(path) - 1})

        if len(path) > max_depth:
            continue

        for edge in edge_adj.get(node, []):
            if edge["conditional"] <= 0:
                continue
            if edge["to"] in path:
                continue
            new_neg_log_p = neg_log_p + (-math.log(edge["conditional"]))
            counter += 1
            heapq.heappush(pq, (new_neg_log_p, counter, edge["to"], path + [edge["to"]]))

    return paths


def _build_bayesnet_report(apps: list[str], adj_typed: dict, top_n: int, max_depth: int) -> dict:
    n = len(apps)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if n == 0:
        return {"generated_at": now, "total_apps": 0, "total_edges": 0, "nodes": [],
                "edges": [], "high_risk_paths": [], "mean_propagation_probability": 0.0,
                "max_propagation_probability": 0.0, "score": 100.0}

    fan_in: dict[str, int] = {}
    fan_out: dict[str, int] = {}
    for frm, targets in adj_typed.items():
        for to in targets:
            fan_out[frm] = fan_out.get(frm, 0) + 1
            fan_in[to] = fan_in.get(to, 0) + 1

    max_fan_out = max(fan_out.values(), default=1)

    nodes = [
        {
            "app": a,
            "fan_in": fan_in.get(a, 0),
            "fan_out": fan_out.get(a, 0),
            "prior": fan_out.get(a, 0) / max_fan_out,
        }
        for a in apps
    ]

    edges: list[dict] = []
    edge_adj: dict[str, list[dict]] = {}

    for frm, targets in adj_typed.items():
        for to, types in targets.items():
            strength = 0.0
            edge_types: list[str] = []
            for t, count in types.items():
                w = _EDGE_TYPE_WEIGHTS.get(t, 0.2)
                strength += w * count
                edge_types.append(t)
            if strength > 1.0:
                strength = 1.0 - 1.0 / (1.0 + strength)
            conditional = strength
            edge_types.sort()
            edge = {"from": frm, "to": to, "strength": strength, "conditional": conditional, "edge_types": edge_types}
            edges.append(edge)
            edge_adj.setdefault(frm, []).append({"to": to, "conditional": conditional})

    all_paths: list[dict] = []
    for src in apps:
        all_paths.extend(_bayes_dijkstra_from(src, edge_adj, max_depth))

    all_paths.sort(key=lambda p: p["probability"], reverse=True)
    high_risk_paths = all_paths[:top_n]

    mean_p = sum(e["conditional"] for e in edges) / len(edges) if edges else 0.0
    max_p = max((e["conditional"] for e in edges), default=0.0)

    edges.sort(key=lambda e: e["conditional"], reverse=True)
    score = max(0.0, 100.0 * (1.0 - mean_p))

    return {
        "generated_at": now,
        "total_apps": n,
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "high_risk_paths": high_risk_paths,
        "mean_propagation_probability": round(mean_p, 4),
        "max_propagation_probability": round(max_p, 4),
        "score": round(score, 1),
    }


def _print_bayesnet_text(r: dict) -> None:
    click.echo("shannon bayesnet:")
    click.echo(f"  generated_at: {r['generated_at']}")
    click.echo(f"  total_apps: {r['total_apps']}")
    click.echo(f"  total_edges: {r['total_edges']}")
    click.echo(f"  mean_propagation: {r['mean_propagation_probability']:.3f}")
    click.echo(f"  max_propagation: {r['max_propagation_probability']:.3f}")
    click.echo(f"  score: {r['score']}")

    paths = r.get("high_risk_paths", [])
    if paths:
        click.echo("\n  high-risk paths:")
        for i, p in enumerate(paths, 1):
            click.echo(f"    {i}. [P={p['probability']:.3f}, len={p['length']}] {' → '.join(p['nodes'])}")

    edges = r.get("edges", [])[:10]
    if edges:
        click.echo("\n  strongest couplings:")
        for e in edges:
            click.echo(f"    {e['from']} → {e['to']} (P={e['conditional']:.3f}, types={','.join(e['edge_types'])})")


@shannon.command("bayesnet")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--top", default=10, show_default=True)
@click.option("--max-depth", "max_depth", default=6, show_default=True)
def bayesnet(json_out: bool, workspace_dir: str | None, top: int, max_depth: int) -> None:
    """Bayesian change-propagation network — edge coupling strengths and high-risk paths."""
    ws = _resolve_root(workspace_dir)
    _, _, adj_typed, _ = _sh_scan(ws)
    apps = sorted({frm for frm in adj_typed} | {to for targets in adj_typed.values() for to in targets})
    r = _build_bayesnet_report(apps, adj_typed, top, max_depth)
    if json_out:
        click.echo(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        _print_bayesnet_text(r)


# ── Bottleneck ─────────────────────────────────────────────────────────────────

def _build_bottleneck_report(apps: list[str], adj_typed: dict, top_n: int, min_fan: int) -> dict:
    n = len(apps)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if n == 0:
        return {"generated_at": now, "total_apps": 0, "bottlenecks": [], "system_mutual_information": 0.0, "score": 100.0}

    stats: dict[str, dict] = {
        a: {"inbound": set(), "outbound": set(), "in_types": {}, "out_types": {}} for a in apps
    }

    for frm, targets in adj_typed.items():
        for to, types in targets.items():
            if frm in stats:
                stats[frm]["outbound"].add(to)
                for t, c in types.items():
                    stats[frm]["out_types"][t] = stats[frm]["out_types"].get(t, 0) + c
            if to in stats:
                stats[to]["inbound"].add(frm)
                for t, c in types.items():
                    stats[to]["in_types"][t] = stats[to]["in_types"].get(t, 0) + c

    all_fans = [len(s["inbound"]) for s in stats.values()] + [len(s["outbound"]) for s in stats.values()]
    max_fan = max(all_fans, default=1) or 1

    modules: list[dict] = []
    critical_high_count = 0

    for app in apps:
        s = stats[app]
        fi = len(s["inbound"])
        fo = len(s["outbound"])
        if fi < min_fan and fo < min_fan:
            continue

        b_score = min(1.0, math.sqrt(fi * fo) / max_fan)

        h_in = _sh_entropy(s["in_types"])
        h_out = _sh_entropy(s["out_types"])
        joint = {f"in:{t}": c for t, c in s["in_types"].items()}
        for t, c in s["out_types"].items():
            joint[f"out:{t}"] = joint.get(f"out:{t}", 0) + c
        h_joint = _sh_entropy(joint)
        mi = max(0.0, h_in + h_out - h_joint)

        if b_score >= 0.7 and fi >= 5 and fo >= 5:
            severity = "critical"
        elif b_score >= 0.5:
            severity = "high"
        elif b_score >= 0.3:
            severity = "medium"
        else:
            severity = "low"

        if severity in ("critical", "high"):
            critical_high_count += 1

        in_apps = sorted(s["inbound"])
        out_apps = sorted(s["outbound"])
        modules.append({
            "app": app, "fan_in": fi, "fan_out": fo,
            "bottleneck_score": round(b_score, 4),
            "inbound_apps": in_apps, "outbound_apps": out_apps,
            "inbound_types": s["in_types"], "outbound_types": s["out_types"],
            "mutual_information": round(mi, 4), "severity": severity,
        })

    modules.sort(key=lambda m: m["bottleneck_score"], reverse=True)
    if len(modules) > top_n:
        modules = modules[:top_n]

    system_mi = sum(m["mutual_information"] for m in modules)
    score = max(0.0, 100.0 * (1.0 - critical_high_count / n)) if n > 0 else 100.0

    return {
        "generated_at": now,
        "total_apps": n,
        "bottlenecks": modules,
        "system_mutual_information": round(system_mi, 4),
        "score": round(score, 1),
    }


def _print_bottleneck_text(r: dict) -> None:
    click.echo("shannon bottleneck:")
    click.echo(f"  generated_at: {r['generated_at']}")
    click.echo(f"  total_apps: {r['total_apps']}")
    click.echo(f"  system_mi: {r['system_mutual_information']:.3f} bits")
    click.echo(f"  score: {r['score']}")

    bottlenecks = r.get("bottlenecks", [])
    if bottlenecks:
        click.echo("\n  bottlenecks:")
        for b in bottlenecks:
            badge = b["severity"].upper()
            click.echo(f"    [{badge}] {b['app']} (score={b['bottleneck_score']:.2f}, "
                       f"fan_in={b['fan_in']}, fan_out={b['fan_out']}, MI={b['mutual_information']:.3f})")
            in_apps = b["inbound_apps"]
            if len(in_apps) <= 5:
                click.echo(f"      inbound: {', '.join(in_apps)}")
            else:
                click.echo(f"      inbound: {', '.join(in_apps[:5])} ... (+{len(in_apps) - 5})")
            out_apps = b["outbound_apps"]
            if len(out_apps) <= 5:
                click.echo(f"      outbound: {', '.join(out_apps)}")
            else:
                click.echo(f"      outbound: {', '.join(out_apps[:5])} ... (+{len(out_apps) - 5})")


@shannon.command("bottleneck")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--top", default=15, show_default=True)
@click.option("--min-fan", "min_fan", default=2, show_default=True)
def bottleneck(json_out: bool, workspace_dir: str | None, top: int, min_fan: int) -> None:
    """Information bottleneck detection — fan-in × fan-out mutual information analysis."""
    ws = _resolve_root(workspace_dir)
    apps, _, adj_typed, _ = _sh_scan(ws)
    r = _build_bottleneck_report(apps, adj_typed, top, min_fan)
    if json_out:
        click.echo(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        _print_bottleneck_text(r)


# ── Minimize ───────────────────────────────────────────────────────────────────

def _minimize_merge_proposals(apps: list[str], adj: dict, app_proj: dict) -> list[dict]:
    proposals: list[dict] = []
    checked: set[str] = set()

    for a in apps:
        proj_a = app_proj.get(a, "")
        if not proj_a:
            continue
        for b in apps:
            if a >= b:
                continue
            key = f"{a}|{b}"
            if key in checked:
                continue
            checked.add(key)
            if app_proj.get(b, "") != proj_a:
                continue
            ab = (adj.get(a) or {}).get(b, 0)
            ba = (adj.get(b) or {}).get(a, 0)
            mutual = ab + ba
            if mutual < 2:
                continue
            h_a = _sh_entropy(adj.get(a) or {})
            h_b = _sh_entropy(adj.get(b) or {})
            current_h = h_a + h_b
            merged = {}
            for to, c in (adj.get(a) or {}).items():
                if to != b:
                    merged[to] = merged.get(to, 0) + c
            for to, c in (adj.get(b) or {}).items():
                if to != a:
                    merged[to] = merged.get(to, 0) + c
            predicted_h = _sh_entropy(merged)
            reduction = current_h - predicted_h
            if reduction <= 0:
                continue
            pct = reduction / current_h * 100 if current_h > 0 else 0.0
            proposals.append({
                "action": "merge", "targets": [a, b],
                "reason": f"high mutual coupling ({mutual} edges) in project {proj_a}",
                "current_entropy": round(current_h, 4), "predicted_entropy": round(predicted_h, 4),
                "reduction": round(reduction, 4), "reduction_pct": round(pct, 1),
            })
    return proposals


def _minimize_split_proposals(apps: list[str], adj: dict, threshold: float) -> list[dict]:
    proposals: list[dict] = []
    for app in apps:
        targets = adj.get(app) or {}
        if len(targets) < 3:
            continue
        h = _sh_entropy(targets)
        if h < threshold:
            continue
        sorted_targets = sorted(targets.items(), key=lambda x: x[1], reverse=True)
        mid = len(sorted_targets) // 2
        g1 = {name: c for name, c in sorted_targets[:mid]}
        g2 = {name: c for name, c in sorted_targets[mid:]}
        n1 = sum(g1.values())
        n2 = sum(g2.values())
        total_n = n1 + n2
        if total_n == 0:
            continue
        h1, h2 = _sh_entropy(g1), _sh_entropy(g2)
        predicted_h = (n1 * h1 + n2 * h2) / total_n
        reduction = h - predicted_h
        if reduction <= 0:
            continue
        pct = reduction / h * 100 if h > 0 else 0.0
        proposals.append({
            "action": "split", "targets": [app],
            "reason": f"high coupling entropy ({h:.2f} bits, {len(targets)} targets)",
            "current_entropy": round(h, 4), "predicted_entropy": round(predicted_h, 4),
            "reduction": round(reduction, 4), "reduction_pct": round(pct, 1),
        })
    return proposals


def _minimize_move_proposals(apps: list[str], adj: dict, app_proj: dict) -> list[dict]:
    proposals: list[dict] = []
    for app in apps:
        targets = adj.get(app) or {}
        if len(targets) < 2:
            continue
        my_proj = app_proj.get(app, "")
        if not my_proj:
            continue
        proj_edges: dict[str, int] = {}
        total_edges = sum(targets.values())
        for to, c in targets.items():
            proj = app_proj.get(to, "")
            if proj:
                proj_edges[proj] = proj_edges.get(proj, 0) + c
        if total_edges == 0:
            continue
        best_proj, best_count = "", 0
        for proj, count in proj_edges.items():
            if proj != my_proj and count > best_count:
                best_count = count
                best_proj = proj
        if not best_proj:
            continue
        cross_ratio = best_count / total_edges
        if cross_ratio < 0.7:
            continue
        current_h = _sh_entropy(targets)
        predicted_h = current_h * (1.0 - cross_ratio * 0.5)
        reduction = current_h - predicted_h
        if reduction <= 0:
            continue
        pct = reduction / current_h * 100 if current_h > 0 else 0.0
        proposals.append({
            "action": "move", "targets": [app],
            "reason": f"{cross_ratio*100:.0f}% of edges go to project {best_proj} (current: {my_proj})",
            "current_entropy": round(current_h, 4), "predicted_entropy": round(predicted_h, 4),
            "reduction": round(reduction, 4), "reduction_pct": round(pct, 1),
        })
    return proposals


def _build_minimize_report(apps: list[str], adj: dict, app_proj: dict, top_n: int, threshold: float) -> dict:
    n = len(apps)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if n == 0:
        return {"generated_at": now, "total_apps": 0, "system_entropy": 0.0,
                "cohesion_entropy": 0.0, "modules": [], "proposals": [],
                "potential_reduction": 0.0, "score": 100.0}

    modules: list[dict] = []
    total_coupling = 0.0
    total_cohesion = 0.0

    for app in apps:
        targets = adj.get(app) or {}
        proj = app_proj.get(app, "")
        coupling_h = _sh_entropy(targets)
        cohesion_counts = {to: c for to, c in targets.items() if app_proj.get(to, "") == proj and proj}
        cohesion_h = _sh_entropy(cohesion_counts)
        net_h = coupling_h - cohesion_h
        modules.append({
            "app": app, "project": proj,
            "coupling_entropy": round(coupling_h, 4),
            "cohesion_entropy": round(cohesion_h, 4),
            "net_entropy": round(net_h, 4),
        })
        total_coupling += coupling_h
        total_cohesion += cohesion_h

    modules.sort(key=lambda m: m["net_entropy"], reverse=True)

    proposals: list[dict] = []
    proposals.extend(_minimize_merge_proposals(apps, adj, app_proj))
    proposals.extend(_minimize_split_proposals(apps, adj, threshold))
    proposals.extend(_minimize_move_proposals(apps, adj, app_proj))
    proposals.sort(key=lambda p: p["reduction"], reverse=True)
    if len(proposals) > top_n:
        proposals = proposals[:top_n]

    potential_reduction = sum(p["reduction"] for p in proposals)
    total = total_coupling + total_cohesion
    score = min(100.0, 100.0 * total_cohesion / total) if total > 0 else 50.0

    return {
        "generated_at": now,
        "total_apps": n,
        "system_entropy": round(total_coupling, 4),
        "cohesion_entropy": round(total_cohesion, 4),
        "modules": modules,
        "proposals": proposals,
        "potential_reduction": round(potential_reduction, 4),
        "score": round(score, 1),
    }


def _print_minimize_text(r: dict) -> None:
    click.echo("shannon minimize:")
    click.echo(f"  generated_at: {r['generated_at']}")
    click.echo(f"  total_apps: {r['total_apps']}")
    click.echo(f"  system_entropy: {r['system_entropy']:.3f} bits (coupling)")
    click.echo(f"  cohesion_entropy: {r['cohesion_entropy']:.3f} bits")
    click.echo(f"  potential_reduction: {r['potential_reduction']:.3f} bits")
    click.echo(f"  score: {r['score']}")

    modules = r.get("modules", [])[:10]
    if modules:
        click.echo("\n  highest entropy modules:")
        for m in modules:
            click.echo(f"    {m['app']} (coupling={m['coupling_entropy']:.2f}, "
                       f"cohesion={m['cohesion_entropy']:.2f}, net={m['net_entropy']:.2f}) [{m['project']}]")

    proposals = r.get("proposals", [])
    if proposals:
        click.echo("\n  proposals:")
        for i, p in enumerate(proposals, 1):
            click.echo(f"    {i}. [{p['action'].upper()}] {' + '.join(p['targets'])}")
            click.echo(f"       reason: {p['reason']}")
            click.echo(f"       entropy: {p['current_entropy']:.2f} → {p['predicted_entropy']:.2f} "
                       f"(−{p['reduction']:.2f}, −{p['reduction_pct']:.0f}%)")


@shannon.command("minimize")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--top", default=15, show_default=True)
@click.option("--threshold", default=2.0, show_default=True, help="Entropy threshold for split proposals (bits)")
def minimize(json_out: bool, workspace_dir: str | None, top: int, threshold: float) -> None:
    """Entropy minimization proposals — merge/split/move suggestions to reduce coupling."""
    ws = _resolve_root(workspace_dir)
    apps, adj, _, app_proj = _sh_scan(ws)
    r = _build_minimize_report(apps, adj, app_proj, top, threshold)
    if json_out:
        click.echo(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        _print_minimize_text(r)
