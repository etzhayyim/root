#!/usr/bin/env python3
"""format-deps-edn — canonical line-split formatter for deps.edn.

deps.edn was emitted by the toml→edn migration as ONE ~1.3 MB line. EDN is
whitespace-insensitive, but a one-line registry makes EVERY concurrent change
a guaranteed whole-file merge conflict (observed 2026-06-12: one docs PR
needed three rebuilds, and the #1680 main tree-wipe was hit while rebasing
around such a conflict).

Canonical layout produced here:

  {:simple-key value
   :adrs
   [{:id "..." :title "..." :status "..." :path "..."}
    {:id "..." ...}
   ]
   :other value}

- Each TOP-LEVEL map entry starts its own line (1-space indent).
- A vector whose elements are all maps (e.g. :adrs, :modules) is split one
  element per line, with the closing `]` alone on its own line — appending an
  entry is a pure one-line insertion that merges/rebases cleanly unless two
  siblings append at the exact same anchor (and then the conflict is one line,
  not 1.3 MB).
- Everything nested deeper stays inline on its entry's line.

Safety: the formatter is whitespace-only by construction — it re-emits the
exact token stream. Before writing it ASSERTS that the output's token
sequence equals the input's and that re-formatting is idempotent.

Usage:
  format-deps-edn.py [path]               # rewrite in place (default: deps.edn)
  format-deps-edn.py --check [path]       # exit 1 if not canonical (lefthook)
  format-deps-edn.py --append-adrs 'EDN' [path]
      # STRUCTURALLY append one or more {…} entries to the :adrs vector and
      # write canonically. THIS is how agents must add registry entries —
      # 2026-06-12 deps.edn was corrupted twice by string-surgery appends
      # (raw bracket counting landed an entry INSIDE another entry's title
      # string, producing invalid EDN that the one-line format then hid).

Pure stdlib.
"""

from __future__ import annotations

import sys

DELIMS = "{}[]()"
WS = " \t\r\n,"  # comma is whitespace in EDN


# ── tokenizer ────────────────────────────────────────────────────────────────

def tokenize(src: str) -> list[str]:
    """Split EDN source into tokens, preserving every non-whitespace byte."""
    toks: list[str] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in WS:
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == '"':
                    break
                j += 1
            if j >= n:
                raise ValueError("unterminated string")
            toks.append(src[i : j + 1])
            i = j + 1
            continue
        if c == ";":
            j = src.find("\n", i)
            j = n if j == -1 else j
            toks.append(src[i:j])
            i = j
            continue
        if c == "\\":  # char literal: \c, \newline, \uXXXX …
            j = i + 2 if i + 1 < n else i + 1
            while j < n and src[j] not in WS and src[j] not in DELIMS and src[j] != '"':
                j += 1
            toks.append(src[i:j])
            i = j
            continue
        if c == "#":
            if i + 1 < n and src[i + 1] == "{":
                toks.append("#{")
                i += 2
                continue
            j = i + 1  # dispatch / tagged literal: #inst, #uuid, #_ …
            while j < n and src[j] not in WS and src[j] not in DELIMS and src[j] != '"':
                j += 1
            toks.append(src[i:j])
            i = j
            continue
        if c in DELIMS:
            toks.append(c)
            i += 1
            continue
        j = i
        while j < n and src[j] not in WS and src[j] not in DELIMS and src[j] != '"' and src[j] != ";":
            j += 1
        toks.append(src[i:j])
        i = j
    return toks


# ── parser (token tree; no EDN value semantics needed) ───────────────────────

OPEN = {"{": "}", "[": "]", "(": ")", "#{": "}"}


class Coll:
    __slots__ = ("opener", "children")

    def __init__(self, opener: str):
        self.opener = opener
        self.children: list = []  # str (atom) | Coll | Tagged


class Tagged:
    """A dispatch token (#inst / #_ / …) glued to the following form so that
    map key/value pairing counts the pair as ONE value."""

    __slots__ = ("tag", "form")

    def __init__(self, tag: str, form):
        self.tag = tag
        self.form = form


def parse(toks: list[str]):
    pos = 0

    def read_form():
        nonlocal pos
        t = toks[pos]
        if t in OPEN:
            pos += 1
            coll = Coll(t)
            closer = OPEN[t]
            while True:
                if pos >= len(toks):
                    raise ValueError(f"unclosed {t}")
                if toks[pos] == closer:
                    pos += 1
                    return coll
                coll.children.append(read_form())
        if t.startswith("#") and t != "#{":
            pos += 1
            return Tagged(t, read_form())
        pos += 1
        return t

    form = read_form()
    if pos != len(toks):
        raise ValueError(f"trailing tokens after top-level form: {toks[pos]!r}")
    return form


# ── renderer ─────────────────────────────────────────────────────────────────

def inline(node) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, Tagged):
        return f"{node.tag} {inline(node.form)}"
    parts = " ".join(inline(c) for c in node.children)
    return node.opener + parts + OPEN[node.opener]


def is_map_vector(node) -> bool:
    return (
        isinstance(node, Coll)
        and node.opener == "["
        and len(node.children) >= 2
        and all(isinstance(c, Coll) and c.opener == "{" for c in node.children)
    )


def render_top(root) -> str:
    if not (isinstance(root, Coll) and root.opener == "{"):
        return inline(root) + "\n"  # not a top-level map — nothing to split
    kids = root.children
    if len(kids) % 2 != 0:
        raise ValueError("top-level map has odd number of forms")
    lines: list[str] = []
    for k in range(0, len(kids), 2):
        key, val = kids[k], kids[k + 1]
        if is_map_vector(val):
            lines.append(inline(key))
            for idx, el in enumerate(val.children):
                lines.append(("[" if idx == 0 else " ") + inline(el))
            lines.append("]")
        else:
            lines.append(f"{inline(key)} {inline(val)}")
    # first line fuses with "{"; the rest get a 1-space indent so columns align
    body = "\n ".join(lines)
    return "{" + body + "}\n"


def format_once(src: str) -> str:
    return render_top(parse(tokenize(src)))


def format_edn(src: str) -> str:
    toks = tokenize(src)
    formatted = format_once(src)
    if tokenize(formatted) != toks:
        raise AssertionError("token stream changed — refusing to write")
    if format_once(formatted) != formatted:
        raise AssertionError("formatter not idempotent — refusing to write")
    return formatted


# ── structural append (the safe way to add registry entries) ─────────────────

def append_adrs(src: str, entries_edn: str) -> str:
    """Parse `src`, append the map(s) in `entries_edn` to the :adrs vector,
    and return the canonical rendering. Raises if `src` is invalid EDN — a
    string-surgery append can NEVER corrupt the file through this path."""
    root = parse(tokenize(src))
    if not (isinstance(root, Coll) and root.opener == "{"):
        raise ValueError("top-level form is not a map")
    target = None
    kids = root.children
    for k in range(0, len(kids), 2):
        if kids[k] == ":adrs":
            target = kids[k + 1]
    if not (isinstance(target, Coll) and target.opener == "["):
        raise ValueError(":adrs vector not found")
    wrapped = parse(tokenize("[" + entries_edn + "]"))
    if not wrapped.children:
        raise ValueError("no entries given")
    for e in wrapped.children:
        if not (isinstance(e, Coll) and e.opener == "{"):
            raise ValueError("each appended entry must be a map")
        target.children.append(e)
    out = render_top(root)
    if format_once(out) != out:
        raise AssertionError("append result not canonical")
    return out


# ── cli ──────────────────────────────────────────────────────────────────────

def main() -> int:
    args = sys.argv[1:]
    check = "--check" in args
    append = None
    if "--append-adrs" in args:
        i = args.index("--append-adrs")
        append = args[i + 1]
        del args[i : i + 2]
    paths = [a for a in args if not a.startswith("--")] or ["deps.edn"]
    path = paths[0]
    src = open(path, encoding="utf-8").read()
    if append is not None:
        out = append_adrs(src, append)
        open(path, "w", encoding="utf-8").write(out)
        print(f"{path}: appended to :adrs (canonical, {out.count(chr(10)) + 1} lines)")
        return 0
    formatted = format_edn(src)
    if check:
        if src != formatted:
            print(f"✘ {path} is not in canonical line-split format.")
            print(f"  Run: python3 70-tools/scripts/lint/format-deps-edn.py {path}")
            return 1
        print(f"✔ {path} is canonically formatted.")
        return 0
    if src == formatted:
        print(f"{path}: already canonical")
        return 0
    open(path, "w", encoding="utf-8").write(formatted)
    print(f"{path}: reformatted ({src.count(chr(10)) + 1} → {formatted.count(chr(10)) + 1} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
