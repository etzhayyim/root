#!/usr/bin/env python3
"""Resolve NSID_* constants in the atproto Worker source tree to literal NSIDs,
union with direct string usages, output complete routed-handler set.

Handles:
  - const NAME = "..." [as const]
  - const NAME = [A, B, "..."].join(".") (chained constants OK)
  - const NAME = `${A}.foo.bar` template string
  - case NAME: / method === NAME / method === "..." usage patterns
"""
from __future__ import annotations
import os, re, sys
from pathlib import Path

ROOT = Path("/Users/junkawasaki/github/etzhayyim-root/50-infra/cloudflare/workers/atproto/src")

EXCLUDE_DIRS = {"_deprecated", "test-mocks"}
EXCLUDE_FILENAME_SUFFIX = (".test.ts",)
EXCLUDE_FILENAMES = {"lexicon-registry.gen.ts", "bundled.ts"}

# Patterns — strictly distinguish string literal vs template literal
RE_CONST_STR    = re.compile(r'^\s*(?:export\s+)?const\s+([A-Z_][A-Z_0-9]*)\s*=\s*"([^"]+)"\s*(?:as\s+const)?\s*;', re.M)
RE_CONST_JOIN   = re.compile(r'^\s*(?:export\s+)?const\s+([A-Z_][A-Z_0-9]*)\s*=\s*\[([^\]]+)\]\s*\.join\(["`]\.["`]\)\s*;', re.M)
RE_CONST_TMPL   = re.compile(r'^\s*(?:export\s+)?const\s+([A-Z_][A-Z_0-9]*)\s*=\s*`([^`]+)`\s*;', re.M)

_NSID_LIT = r'"[a-z][a-zA-Z0-9.]*[a-zA-Z0-9]"|\'[a-z][a-zA-Z0-9.]*[a-zA-Z0-9]\'|`[a-z][a-zA-Z0-9.]*[a-zA-Z0-9]`'
_NSID_REF = r'[A-Z_][A-Z_0-9]*'
RE_USE_CASE     = re.compile(rf'case\s+({_NSID_REF}|{_NSID_LIT})\s*:')
RE_USE_METHOD_EQ = re.compile(rf'method\s*===?\s*({_NSID_REF}|{_NSID_LIT})')

def walk_ts():
    for p in ROOT.rglob("*.ts"):
        parts = p.relative_to(ROOT).parts
        if any(d in EXCLUDE_DIRS for d in parts): continue
        if p.name in EXCLUDE_FILENAMES: continue
        if any(p.name.endswith(suf) for suf in EXCLUDE_FILENAME_SUFFIX): continue
        yield p

# Pass 1: gather all constant definitions (NAME → raw RHS expr)
raw_defs: dict[str, str] = {}

def classify_rhs(body: str) -> tuple[str, str]:
    """Return (kind, raw). kind in {literal, join, template}."""
    return ("?", body)

RE_CONST_SET = re.compile(
    r'^\s*(?:export\s+)?const\s+([A-Z_][A-Z_0-9]*)\s*=\s*new\s+Set(?:<[^>]+>)?\s*\(\s*\[(.*?)\]\s*\)\s*;',
    re.M | re.S,
)

for p in walk_ts():
    try: text = p.read_text(errors="ignore")
    except: continue
    for m in RE_CONST_STR.finditer(text):
        name, val = m.group(1), m.group(2)
        raw_defs.setdefault(name, ("literal", val))
    for m in RE_CONST_JOIN.finditer(text):
        name, inner = m.group(1), m.group(2)
        raw_defs.setdefault(name, ("join", inner))
    for m in RE_CONST_TMPL.finditer(text):
        name, tpl = m.group(1), m.group(2)
        raw_defs.setdefault(name, ("template", tpl))
    for m in RE_CONST_SET.finditer(text):
        name, body = m.group(1), m.group(2)
        raw_defs.setdefault(name, ("set", body))

# Pass 2: resolve constants iteratively
resolved: dict[str, str] = {}
set_members: dict[str, set[str]] = {}  # name → set of NSIDs (after resolution)
changed = True
safety = 20  # max iterations
while changed and safety > 0:
    changed = False
    safety -= 1
    for name, (kind, raw) in list(raw_defs.items()):
        if name in resolved: continue
        if kind == "literal":
            resolved[name] = raw; changed = True; continue
        if kind == "join":
            # inner tokens: identifiers or strings, split by comma
            parts = [t.strip() for t in raw.split(",")]
            segs = []
            ok = True
            for t in parts:
                if not t: continue
                if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")) or (t.startswith('`') and t.endswith('`')):
                    segs.append(t[1:-1])
                elif re.fullmatch(r'[A-Z_][A-Z_0-9]*', t):
                    if t in resolved: segs.append(resolved[t])
                    else: ok = False; break
                else:
                    ok = False; break
            if ok:
                resolved[name] = ".".join(segs); changed = True
        elif kind == "template":
            # replace ${NAME} with resolved value
            def rep(mm):
                vname = mm.group(1)
                return resolved.get(vname, f"__UNRESOLVED_{vname}__")
            new = re.sub(r'\$\{([A-Z_][A-Z_0-9]*)\}', rep, raw)
            if "__UNRESOLVED_" not in new:
                resolved[name] = new; changed = True
        elif kind == "set":
            # Parse [..., "...", NSID_X, "...", ...]. Members may be quoted
            # strings or NSID_* refs. Comments / spreads (...OTHER_SET) ignored.
            if name in set_members: continue
            members = set()
            ok = True
            # Split on commas but be lenient with whitespace / newlines
            for token in re.split(r',(?![^(]*\))', raw):
                token = token.strip()
                if not token: continue
                if token.startswith("//"): continue
                m_str = re.match(r'^["`\']([^"`\']+)["`\']$', token)
                if m_str:
                    members.add(m_str.group(1)); continue
                m_ref = re.match(r'^([A-Z_][A-Z_0-9]*)$', token)
                if m_ref:
                    ref = m_ref.group(1)
                    if ref in resolved:
                        members.add(resolved[ref])
                    else:
                        ok = False; break
                    continue
                # Spread of another Set: ...OTHER_SET
                m_spread = re.match(r'^\.\.\.([A-Z_][A-Z_0-9]*)$', token)
                if m_spread:
                    ref = m_spread.group(1)
                    if ref in set_members:
                        members.update(set_members[ref])
                    else:
                        ok = False; break
                    continue
                # unrecognized token — skip silently (comments etc)
            if ok:
                set_members[name] = members; changed = True

# Pass 3: collect all usages (case X: and method === X) from live handler src files only
# Only routes: handlers/**/*.ts + app.ts + dispatch.ts
ROUTE_FILES = []
for p in walk_ts():
    rel = str(p.relative_to(ROOT))
    if rel.startswith("handlers/") or rel in ("app.ts", "dispatch.ts", "core.ts", "handlers.ts"):
        ROUTE_FILES.append(p)

RE_SET_HAS = re.compile(rf'([A-Z_][A-Z_0-9]*)\.has\s*\(\s*(?:nsid|method|m)\s*\)')

used_nsids: set[str] = set()
used_unresolved: set[str] = set()
used_set_refs: set[str] = set()
for p in ROUTE_FILES:
    try: text = p.read_text(errors="ignore")
    except: continue
    for rx in (RE_USE_CASE, RE_USE_METHOD_EQ):
        for m in rx.finditer(text):
            ref = m.group(1)
            if ref[0] in '"\'`':
                used_nsids.add(ref[1:-1])
            else:
                if ref in resolved:
                    used_nsids.add(resolved[ref])
                else:
                    used_unresolved.add(ref)
    # Dispatch via SET.has(nsid) — each member of the Set is a routed handler
    for m in RE_SET_HAS.finditer(text):
        used_set_refs.add(m.group(1))

for set_name in used_set_refs:
    if set_name in set_members:
        used_nsids.update(set_members[set_name])
    else:
        used_unresolved.add(set_name)

print(f"# routed NSIDs: {len(used_nsids)}")
print(f"# unresolved refs: {len(used_unresolved)}")
print(f"# constant defs discovered: {len(raw_defs)} (string/join/template/set)")
print(f"# string/join/template resolved: {len(resolved)}")
print(f"# Set<NSID> resolved: {len(set_members)}")
print(f"# Set refs used in dispatch: {len(used_set_refs)}")
print()
for nsid in sorted(used_nsids):
    print(nsid)

# Also write sidecar files
# NSID must have ≥ 3 dot-separated segments (domain authority + collection + method at minimum)
VALID_NSID = re.compile(r'^[a-z][a-zA-Z0-9]*(\.[a-z][a-zA-Z0-9]*){2,}$')
used_nsids = {n for n in used_nsids if VALID_NSID.match(n)}

with open("/tmp/pds-nsids-v2.txt", "w") as f:
    for nsid in sorted(used_nsids):
        f.write(nsid + "\n")
with open("/tmp/pds-nsids-unresolved.txt", "w") as f:
    for n in sorted(used_unresolved):
        f.write(n + "\n")
