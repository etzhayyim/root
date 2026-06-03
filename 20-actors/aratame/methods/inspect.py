#!/usr/bin/env python3
"""aratame 改め — static-source vulnerability inspector (R0 offline demonstrator).

ADR-2606024000. Reads a target source tree (default: data/sample-repo/) READ-ONLY
and emits:

  1. an AGGREGATE-FIRST, NON-ADJUDICATING inspection report (out/inspection-report.md)
     — what weaknesses the source carries, framed as evidence for the owner +
     a remediation handoff to tsukuroi (繕い). NOT a verdict, NOT a target-list.
  2. the derived findings (out/findings.kotoba.edn), flagged :derived /
     :non-adjudicating — never re-ingested as authoritative fact; shaped to seed
     com.etzhayyim.aratame.vulnFinding records.

Three legs, all OFFLINE + stdlib-only:
  • SAST  — Python `ast` walk for CWE weakness patterns (a :representative rule
            set; an honest stand-in for Semgrep OSS / CodeQL — those are R1/G5).
  • SCA   — parse dependency manifests → purl → join data/seed-cve-table.kotoba.edn
            (mirrors giemon purl_vuln_match, ADR-2605312330; a stand-in for
            OSV-Scanner / Trivy — R1/G5).
  • SECRET— regex detectors; the matched value is NEVER written out — only a
            sha256 envelope-ref + a redacted hint (G7 / ADR-2605181100).

CONSTITUTIONAL framing (ADR-2606024000):
  • READ-ONLY / STATIC-ONLY (G3): the target is parsed, NEVER executed. Python is
    read via `ast.parse` (no import, no exec). The script never writes the target.
  • NON-ADJUDICATING (G8): severities mirror the rule/advisory; no exploitation
    framing. DEFENSIVE-ONLY (G9): no PoC emitted.
  • Triage is DETERMINISTIC here. The Murakumo-only LLM triage (gemma4-26b-a4b via
    judah LiteLLM 127.0.0.1:4000, G10) is R1-gated and intentionally NOT called.

stdlib only. Usage:
    python3 inspect.py [TARGET_DIR] [--out OUTDIR] [--cve data/seed-cve-table.kotoba.edn]
"""
from __future__ import annotations
import sys
import re
import ast
import hashlib
import pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from watatsuna
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':
        return True
    if t == 'false':
        return False
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            v = _parse(it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def load_edn(path: pathlib.Path):
    it = _tokens(path.read_text(encoding='utf-8'))
    out = []
    try:
        while (x := _parse(it)) is not _END:
            out.append(x)
    except StopIteration:
        pass
    return out[0] if len(out) == 1 and isinstance(out[0], list) else out


# ── severity rank (non-adjudicating; mirrors rule/advisory) ───────────────────
SEV_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _edn_str(s: str) -> str:
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


# ── SAST: Python AST weakness rules (:representative; static, never executed) ──
def _call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Attribute):
        base = f.value.id if isinstance(f.value, ast.Name) else getattr(f.value, "attr", "")
        return f"{base}.{f.attr}" if base else f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _has_kw(node: ast.Call, key: str, want_true=True) -> bool:
    for kw in node.keywords:
        if kw.arg == key:
            return (not want_true) or (isinstance(kw.value, ast.Constant) and kw.value.value is True)
    return False


def _yaml_load_unsafe(node: ast.Call) -> bool:
    # yaml.load(...) is unsafe unless Loader= is a Safe* loader.
    for kw in node.keywords:
        if kw.arg in ("Loader", "loader"):
            v = kw.value
            name = v.attr if isinstance(v, ast.Attribute) else (v.id if isinstance(v, ast.Name) else "")
            return "Safe" not in name and "safe" not in name
    return True  # no Loader at all → unsafe


def sast_python(path: pathlib.Path, rel: str, findings: list):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=rel)
    except (SyntaxError, UnicodeDecodeError):
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        ln = getattr(node, "lineno", 0)

        def add(rule, cwe, sev, msg):
            findings.append({
                "category": "Sast", "tool": "aratame-pyrules(:representative)",
                "rule_id": rule, "cwe": cwe, "severity": sev,
                "location": f"{rel}:{ln}", "message": msg,
            })

        if name in ("subprocess.call", "subprocess.run", "subprocess.Popen", "os.system") \
                and (name == "os.system" or _has_kw(node, "shell")):
            add("py.subprocess-shell-true", "CWE-78", "high",
                "OS command built/executed via a shell — command-injection risk.")
        elif name in ("eval", "exec"):
            arg_literal = bool(node.args) and isinstance(node.args[0], ast.Constant)
            if not arg_literal:
                add("py.eval-exec", "CWE-95", "high",
                    f"`{name}()` on a non-literal argument — code-injection risk.")
        elif name in ("pickle.loads", "pickle.load"):
            add("py.pickle-load", "CWE-502", "high",
                "Insecure deserialization via pickle on untrusted data.")
        elif name == "yaml.load" and _yaml_load_unsafe(node):
            add("py.yaml-load-unsafe", "CWE-20", "medium",
                "yaml.load without SafeLoader — arbitrary object construction.")
        elif name in ("hashlib.md5", "hashlib.sha1"):
            add("py.weak-hash", "CWE-327", "low",
                f"Weak hash `{name}` used for a security-relevant value.")


# ── SECRET: regex detectors; value NEVER persisted (G7) ───────────────────────
SECRET_RULES = [
    ("aws-access-key-id", re.compile(r'AKIA[0-9A-Z]{16}')),
    ("private-key-block", re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ("generic-assigned-secret",
     re.compile(r'(?i)(?:password|passwd|secret|api[_-]?key|api[_-]?token|access[_-]?token)'
                r'\s*[:=]\s*["\']([^"\']{8,})["\']')),
]
# Obvious placeholders we still report but mark low-confidence (demo honesty).
_PLACEHOLDER = re.compile(r'(?i)placeholder|example|dummy|changeme|your[_-]?')


def secret_scan(path: pathlib.Path, rel: str, findings: list):
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return
    for ln, line in enumerate(text.splitlines(), 1):
        for rule, rx in SECRET_RULES:
            m = rx.search(line)
            if not m:
                continue
            value = m.group(1) if m.groups() else m.group(0)
            digest = hashlib.sha256(value.encode()).hexdigest()
            redacted = (value[:4] + "…" + value[-4:]) if len(value) > 8 else "…"
            placeholder = bool(_PLACEHOLDER.search(value))
            findings.append({
                "category": "Secret", "tool": "aratame-secretrules(:representative)",
                "rule_id": f"secret.{rule}", "cwe": "CWE-798",
                "severity": "low" if placeholder else "high",
                "location": f"{rel}:{ln}",
                # G7: value is NEVER stored — only a sha256 envelope-ref + redaction.
                "secret_envelope_ref": f"vault://com.etzhayyim.encrypted/{digest[:16]}",
                "secret_redacted": redacted,
                "message": ("Likely placeholder/example secret (low confidence)."
                            if placeholder else "Hardcoded credential detected in source."),
            })


# ── SCA: parse manifests → purl → join CVE table ──────────────────────────────
def _vtuple(v: str):
    nums = re.findall(r'\d+', v)
    return tuple(int(n) for n in nums[:4]) or (0,)


def parse_requirements(path: pathlib.Path):
    deps = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        m = re.match(r'^([A-Za-z0-9_.\-]+)\s*==\s*([0-9][0-9A-Za-z.\-]*)', line)
        if m:
            deps.append(("pkg:pypi/" + m.group(1).lower(), m.group(1), m.group(2), path.name))
    return deps


def parse_package_json(path: pathlib.Path):
    import json
    deps = []
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return deps
    for section in ("dependencies", "devDependencies"):
        for name, ver in (obj.get(section) or {}).items():
            ver = re.sub(r'^[\^~>=<\s]+', '', str(ver))
            deps.append(("pkg:npm/" + name.lower(), name, ver, path.name))
    return deps


def sca_scan(target: pathlib.Path, cve_rows: list, findings: list):
    deps = []
    for p in sorted(target.rglob("requirements*.txt")):
        deps += parse_requirements(p)
    for p in sorted(target.rglob("package.json")):
        deps += parse_package_json(p)
    by_purl = defaultdict(list)
    for row in cve_rows:
        by_purl[row.get(":cve/affects-purl")].append(row)
    for purl, name, ver, manifest in deps:
        for cve in by_purl.get(purl, []):
            below = str(cve.get(":cve/affected-below", "0"))
            if _vtuple(ver) < _vtuple(below):
                findings.append({
                    "category": "Dependency", "tool": "aratame-sca(:representative)",
                    "rule_id": cve.get(":cve/id"), "cwe": cve.get(":cve/cwe", ""),
                    "severity": cve.get(":cve/severity", "medium"),
                    "location": manifest,
                    "purl": purl, "installed_version": ver,
                    "fixed_version": cve.get(":cve/fixed-version", ""),
                    "advisory": cve.get(":cve/advisory", ""),
                    "message": f"{name} {ver} < {cve.get(':cve/fixed-version')} "
                               f"({cve.get(':cve/id')}); upgrade to {cve.get(':cve/fixed-version')}.",
                })


# ── deterministic triage (LLM triage is R1/G10-gated, intentionally NOT called) ─
def triage(findings: list):
    seen = {}
    for f in findings:
        key = (f["category"], f["rule_id"], f["location"])
        if key not in seen:
            seen[key] = f
    deduped = list(seen.values())
    deduped.sort(key=lambda f: (-SEV_RANK.get(f["severity"], 0), f["category"], f["location"]))
    return deduped


# ── render ────────────────────────────────────────────────────────────────────
def render_report(target, findings, n_py, n_files):
    counts = defaultdict(int)
    cats = defaultdict(int)
    for f in findings:
        counts[f["severity"]] += 1
        cats[f["category"]] += 1
    L = []
    P = L.append
    P("# aratame 改め — static-source inspection report")
    P("")
    P(f"**Target**: `{target}` (`:representative` fixture)  ")
    P(f"**Files scanned**: {n_files} ({n_py} Python via AST)  ")
    P("**Mode**: READ-ONLY / STATIC-ONLY — the target was parsed, never executed (G3).  ")
    P("**Posture**: NON-ADJUDICATING evidence (G8) — a remediation worklist for the "
      "owner, handed to **tsukuroi 繕い** (propose-only). NOT a verdict, NOT a target-list.")
    P("")
    P("## Aggregate")
    P("")
    P("| Severity | Count |   | Category | Count |")
    P("|---|---|---|---|---|")
    order = ["critical", "high", "medium", "low", "info"]
    catord = ["Sast", "Dependency", "Secret"]
    rows = max(len(order), len(catord))
    for i in range(rows):
        sev = order[i] if i < len(order) else ""
        sc = str(counts.get(sev, 0)) if sev else ""
        cat = catord[i] if i < len(catord) else ""
        cc = str(cats.get(cat, 0)) if cat else ""
        P(f"| {sev} | {sc} |   | {cat} | {cc} |")
    P("")
    P(f"**Total findings**: {len(findings)}")
    P("")
    P("## Findings")
    P("")
    P("| Sev | Category | Rule / CVE | CWE | Location | Note |")
    P("|---|---|---|---|---|---|")
    for f in findings:
        note = f.get("message", "")
        if f["category"] == "Secret":
            note = f"{note} (value redacted `{f.get('secret_redacted')}` → `{f.get('secret_envelope_ref')}`)"
        P(f"| {f['severity']} | {f['category']} | `{f['rule_id']}` | {f.get('cwe','')} "
          f"| `{f['location']}` | {note} |")
    P("")
    P("## Remediation handoff")
    P("")
    P("These findings seed `com.etzhayyim.aratame.vulnFinding` records. Under a "
      "`tsukuroi.remediationMandate` referencing the same owner+repo, **tsukuroi 繕い** "
      "(ADR-2605291500) drafts a defensive patch — **propose-only**, a human owner merges. "
      "aratame never patches (G13).")
    P("")
    P("---")
    P("*Generated by `aratame/methods/inspect.py`. HONEST R0: the SAST rule set is a "
      "`:representative` stdlib `ast` stand-in (NOT Semgrep OSS / CodeQL); SCA joins a "
      "bounded `:representative` CVE seed table (NOT live OSV/Trivy); secret values are "
      "never persisted (sha256 envelope-ref only, G7). The Murakumo-only LLM triage "
      "(`gemma4-26b-a4b`, G10) is R1-gated and intentionally not invoked here — triage is "
      "deterministic. Live OSS scanners + advisory feeds + private-repo mandates are "
      "R1/R2 + Council/operator gated.*")
    return "\n".join(L) + "\n"


def render_datoms(findings):
    L = []
    P = L.append
    P(";; aratame — DERIVED findings (ADR-2606024000). :derived / :non-adjudicating.")
    P(";; Seeds com.etzhayyim.aratame.vulnFinding. NOT authoritative fact; do not re-ingest.")
    P("[")
    for f in findings:
        parts = [
            f':finding/category "{f["category"]}"',
            f':finding/rule-id {_edn_str(f["rule_id"])}',
            f':finding/severity "{f["severity"]}"',
            f':finding/location {_edn_str(f["location"])}',
            f':finding/cwe "{f.get("cwe","")}"',
            f':finding/tool {_edn_str(f["tool"])}',
        ]
        if f["category"] == "Dependency":
            parts += [
                f':finding/purl "{f.get("purl","")}"',
                f':finding/installed-version "{f.get("installed_version","")}"',
                f':finding/fixed-version "{f.get("fixed_version","")}"',
                f':finding/advisory "{f.get("advisory","")}"',
            ]
        if f["category"] == "Secret":
            # G7: envelope-ref + redaction only — NEVER the secret value.
            parts += [
                f':finding/secret-envelope-ref "{f.get("secret_envelope_ref","")}"',
                f':finding/secret-redacted {_edn_str(f.get("secret_redacted",""))}',
            ]
        parts += [
            ":finding/non-adjudicating true",
            ":finding/defensive-context-only true",
            ":finding/executed-code false",
            ":finding/derived true",
        ]
        P(" {" + " ".join(parts) + "}")
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    target = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "sample-repo"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    cve_path = here / "data" / "seed-cve-table.kotoba.edn"
    if "--cve" in argv:
        cve_path = pathlib.Path(argv[argv.index("--cve") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    cve_rows = load_edn(cve_path)
    findings: list = []
    n_py = n_files = 0
    SKIP = {".git", "node_modules", "__pycache__", "out"}
    for p in sorted(target.rglob("*")):
        if not p.is_file() or any(part in SKIP for part in p.parts):
            continue
        rel = str(p.relative_to(target))
        n_files += 1
        if p.suffix == ".py":
            n_py += 1
            sast_python(p, rel, findings)        # STATIC: ast.parse, never executed
        if p.suffix in (".py", ".yaml", ".yml", ".json", ".env", ".txt", ".cfg", ".ini", ".toml", ""):
            secret_scan(p, rel, findings)
    sca_scan(target, cve_rows, findings)
    findings = triage(findings)

    (outdir / "inspection-report.md").write_text(
        render_report(target, findings, n_py, n_files), encoding='utf-8')
    (outdir / "findings.kotoba.edn").write_text(render_datoms(findings), encoding='utf-8')

    by_cat = defaultdict(int)
    for f in findings:
        by_cat[f["category"]] += 1
    print(f"aratame: scanned {n_files} files ({n_py} python) in {target}")
    print("findings: " + ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())) +
          f" (total {len(findings)})")
    print(f"wrote {outdir/'inspection-report.md'} + {outdir/'findings.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
