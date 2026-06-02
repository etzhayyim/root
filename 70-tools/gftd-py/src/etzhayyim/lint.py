"""lint — Code linting (port of lint.go).

Targets:
  nsid-regression   : detect "nsid" placeholder strings
  legacy-pds-nsid   : detect deprecated PDS NSIDs
  silent-catch      : detect error-swallowing catch blocks
  ts-camel          : enforce camelCase on TS identifiers
  json-sql          : enforce JSON/JSON-LD naming conventions
  deps-drift        : detect deps.toml drift vs working tree
  all               : run all targets (default)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click

from .shannon import _resolve_root


_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}

# ── lint rules ─────────────────────────────────────────────────────────────────

_RE_NSID_PLACEHOLDER = re.compile(r'"nsid"')
_RE_LEGACY_PDS_NSID = re.compile(
    r'app\.bsky\.feed\.getTimeline|com\.atproto\.sync\.getBlob|'
    r'app\.bsky\.actor\.getProfile'
)
_RE_SILENT_CATCH = re.compile(r'catch\s*\([^)]*\)\s*\{\s*\}|except\s+\w+\s*:\s*pass\b')
_RE_TS_SNAKE = re.compile(r'\b[a-z]+_[a-z_]+\s*[=:(]')
_RE_JSON_SQL_MISMATCH = re.compile(r'"[A-Z][a-zA-Z]+"\s*:')  # PascalCase key in JSON


@dataclass
class LintViolation:
    rule: str
    path: str
    line: int
    snippet: str

    def to_dict(self) -> dict:
        return {"rule": self.rule, "path": self.path, "line": self.line, "snippet": self.snippet}


@dataclass
class LintResult:
    rule: str
    violations: list[LintViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict:
        return {"rule": self.rule, "ok": self.ok,
                "violations": [v.to_dict() for v in self.violations]}


def _scan_files(ws: Path, exts: set[str]) -> list[Path]:
    out = []
    for p in ws.rglob("*"):
        if not p.is_file():
            continue
        if any(d in p.parts for d in _SKIP_DIRS):
            continue
        if p.suffix in exts:
            out.append(p)
    return out


def _lint_rule(ws: Path, rule: str) -> LintResult:
    result = LintResult(rule=rule)

    if rule == "nsid-regression":
        for p in _scan_files(ws, {".ts", ".svelte"}):
            try:
                for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    if _RE_NSID_PLACEHOLDER.search(line):
                        result.violations.append(LintViolation(
                            rule=rule, path=str(p.relative_to(ws)),
                            line=i, snippet=line.strip()[:80],
                        ))
            except OSError:
                pass

    elif rule == "legacy-pds-nsid":
        for p in _scan_files(ws, {".ts", ".svelte", ".go"}):
            try:
                for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    if _RE_LEGACY_PDS_NSID.search(line):
                        result.violations.append(LintViolation(
                            rule=rule, path=str(p.relative_to(ws)),
                            line=i, snippet=line.strip()[:80],
                        ))
            except OSError:
                pass

    elif rule == "silent-catch":
        for p in _scan_files(ws, {".ts", ".svelte", ".py"}):
            try:
                content = p.read_text(errors="replace")
                for m in _RE_SILENT_CATCH.finditer(content):
                    line = content[:m.start()].count("\n") + 1
                    result.violations.append(LintViolation(
                        rule=rule, path=str(p.relative_to(ws)),
                        line=line, snippet=m.group()[:80],
                    ))
            except OSError:
                pass

    elif rule == "ts-camel":
        for p in _scan_files(ws, {".ts", ".svelte"}):
            try:
                for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    if _RE_TS_SNAKE.search(line) and "snake_case" not in line:
                        result.violations.append(LintViolation(
                            rule=rule, path=str(p.relative_to(ws)),
                            line=i, snippet=line.strip()[:80],
                        ))
            except OSError:
                pass

    elif rule == "json-sql":
        for p in _scan_files(ws, {".json", ".jsonld"}):
            try:
                for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    if _RE_JSON_SQL_MISMATCH.search(line):
                        result.violations.append(LintViolation(
                            rule=rule, path=str(p.relative_to(ws)),
                            line=i, snippet=line.strip()[:80],
                        ))
            except OSError:
                pass

    elif rule == "deps-drift":
        deps_file = ws / "deps.toml"
        if deps_file.exists():
            # Just check if deps.toml is parseable (full drift check requires Go)
            try:
                content = deps_file.read_text()
                if "[[migrations]]" in content and 'status = "done"' in content:
                    result.violations.append(LintViolation(
                        rule=rule, path="deps.toml", line=0,
                        snippet="completed migrations with status='done' found",
                    ))
            except OSError:
                pass

    return result


_ALL_RULES = ["nsid-regression", "legacy-pds-nsid", "silent-catch", "ts-camel",
              "json-sql", "deps-drift"]

_UPDATE_TARGETS = ["silent-catch-update", "ts-camel-update", "json-sql-update"]

_UPDATE_SCRIPTS: dict[str, str] = {
    "silent-catch-update": "70-tools/scripts/lint/no-silent-catch.mjs",
    "ts-camel-update": "70-tools/scripts/lint/ts-camelcase.mjs",
    "json-sql-update": "70-tools/scripts/lint/json-sql-case.mjs",
}

_ALL_TARGETS = ["all", "rules"] + _ALL_RULES + _UPDATE_TARGETS


def _run_update_target(ws: Path, target: str) -> None:
    script_rel = _UPDATE_SCRIPTS[target]
    script = ws / script_rel
    if not script.exists():
        raise click.ClickException(
            f"script not found: {script_rel} — run from repo root with node installed"
        )
    click.echo(f"==> lint update: {target}", err=True)
    result = subprocess.run(
        ["node", str(script), "--update-baseline"],
        cwd=str(ws),
    )
    if result.returncode != 0:
        raise click.ClickException(f"lint update failed: {target}")
    click.echo(f"  baseline updated: {target}")


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.command("lint")
@click.argument("target", default="all",
                type=click.Choice(_ALL_TARGETS, case_sensitive=False))
@click.option("--root", default=None, help="Repo root (default: git root)")
@click.option("--json", "json_out", is_flag=True, default=False)
def lint(target: str, root: str | None, json_out: bool) -> None:
    """Code linting (nsid-regression, silent-catch, ts-camel, json-sql, deps-drift)."""
    if target == "rules":
        for r in _ALL_RULES:
            click.echo(f"  {r}")
        return

    ws = _resolve_root(root)

    if target in _UPDATE_TARGETS:
        _run_update_target(ws, target)
        return

    rules = _ALL_RULES if target == "all" else [target]
    results = [_lint_rule(ws, r) for r in rules]
    all_ok = all(r.ok for r in results)

    if json_out:
        click.echo(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "OK  " if r.ok else "FAIL"
            click.echo(f"  [{status}] {r.rule}  ({len(r.violations)} violations)")
            for v in r.violations[:5]:
                click.echo(f"         {v.path}:{v.line}  {v.snippet}")

    if not all_ok:
        sys.exit(1)
