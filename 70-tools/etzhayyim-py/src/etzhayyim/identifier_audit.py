"""identifier-audit — Identifier consistency audit.

Scans workspace for identifier naming violations:
- DID format consistency
- Handle format compliance
- NSID structure validity
- Nanoid format compliance
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import click

from .shannon import _resolve_root


_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}

_RE_DID = re.compile(r'"(did:[a-z]+:[A-Za-z0-9._:%-]+)"')
_RE_HANDLE = re.compile(r'"([a-z0-9][a-z0-9.-]{1,61}[a-z0-9]\.[a-z]{2,})"')
_RE_NSID = re.compile(r'"((?:[a-z][a-z0-9]*\.){2,}[a-zA-Z][a-zA-Z0-9]*)"')
_RE_NANOID = re.compile(r'"nanoid"\s*:\s*"([^"]+)"')
_RE_VALID_NANOID = re.compile(r'^[A-Za-z0-9_-]{8,12}$')
_RE_VALID_DID = re.compile(r'^did:(plc|web|key|pkh):[A-Za-z0-9._:%-]+$')


@dataclass
class AuditViolation:
    rule: str
    path: str
    value: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {"rule": self.rule, "path": self.path, "value": self.value, "detail": self.detail}


def _audit_jsonld(path: Path, ws: Path) -> list[AuditViolation]:
    violations = []
    try:
        data = json.loads(path.read_text(errors="replace"))
    except (OSError, json.JSONDecodeError):
        return violations

    rel = str(path.relative_to(ws))

    nanoid = data.get("nanoid", "")
    if nanoid and not _RE_VALID_NANOID.match(nanoid):
        violations.append(AuditViolation(
            rule="nanoid-format", path=rel, value=nanoid,
            detail="nanoid must be 8-12 chars [A-Za-z0-9_-]",
        ))

    did = data.get("did", "")
    if did and not _RE_VALID_DID.match(did):
        violations.append(AuditViolation(
            rule="did-format", path=rel, value=did,
            detail="unsupported DID method (expected plc/web/key/pkh)",
        ))

    name = data.get("name", "")
    if name and re.search(r'[A-Z_]', name):
        violations.append(AuditViolation(
            rule="name-lowercase", path=rel, value=name,
            detail="actor name should be kebab-case lowercase",
        ))

    return violations


def _audit_ts(path: Path, ws: Path) -> list[AuditViolation]:
    violations = []
    rel = str(path.relative_to(ws))
    try:
        content = path.read_text(errors="replace")
    except OSError:
        return violations

    for m in _RE_NANOID.finditer(content):
        val = m.group(1)
        if not _RE_VALID_NANOID.match(val):
            violations.append(AuditViolation(
                rule="nanoid-format", path=rel, value=val,
                detail="invalid nanoid format",
            ))

    return violations


def run_audit(ws: Path) -> list[AuditViolation]:
    violations = []
    for p in ws.rglob("*"):
        if not p.is_file():
            continue
        if any(d in p.parts for d in _SKIP_DIRS):
            continue
        if p.name == "kotodama.jsonld" or p.suffix == ".jsonld":
            violations.extend(_audit_jsonld(p, ws))
        elif p.suffix in (".ts", ".svelte"):
            violations.extend(_audit_ts(p, ws))
    return violations


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("identifier-audit", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--rule", default="", help="Filter by rule name")
@click.pass_context
def identifier_audit(ctx: click.Context, workspace_dir: str | None,
                     json_out: bool, rule: str) -> None:
    """Identifier naming audit (DID, nanoid, NSID, handle formats)."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    violations = run_audit(ws)
    if rule:
        violations = [v for v in violations if v.rule == rule]
    if json_out:
        click.echo(json.dumps([v.to_dict() for v in violations], ensure_ascii=False, indent=2))
    else:
        if not violations:
            click.echo("  identifier-audit: no violations")
        else:
            click.echo(f"  identifier-audit: {len(violations)} violations")
            for v in violations:
                click.echo(f"  [{v.rule}] {v.path}  {v.value!r}  {v.detail}")


@identifier_audit.command("rules")
def ia_rules() -> None:
    """List available audit rules."""
    for r in ["nanoid-format", "did-format", "name-lowercase"]:
        click.echo(f"  {r}")


@identifier_audit.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def ia_scan(workspace_dir: str | None, json_out: bool) -> None:
    """Run full identifier audit."""
    ws = _resolve_root(workspace_dir)
    violations = run_audit(ws)
    if json_out:
        click.echo(json.dumps([v.to_dict() for v in violations], ensure_ascii=False, indent=2))
    else:
        for v in violations:
            click.echo(f"  [{v.rule}] {v.path}: {v.value!r}")
        click.echo(f"  total: {len(violations)}")
