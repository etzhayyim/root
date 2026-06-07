"""Minimal Python → EDN encoder + decoder helpers for kotoba datomic.

Ported from 60-apps/etzhayyim-project-hakken/lg/lg_hakken/edn.py. Targets the
subset kotoba-server ``kotoba_edn::parse`` understands for ``datomic.transact``
tx-data: a vector of ``[:db/add E A V]`` / ``[:db/retract E A V]`` ops and entity
maps. Strings are escaped per EDN spec.
"""

from __future__ import annotations

import re
from typing import Any, Iterable


class EdnSymbol(str):
    """Bare EDN symbol or keyword (no quoting). Example: EdnSymbol(':db/add')."""


def kw(name: str) -> EdnSymbol:
    """Keyword shortcut: kw('cal/summary') → :cal/summary, kw('db/add') → :db/add."""
    return EdnSymbol(name if name.startswith(":") else f":{name}")


def encode(value: Any) -> str:
    if isinstance(value, EdnSymbol):
        return str(value)
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # datomic doubles are allowed at the wire level; calendar avoids them by
        # contract (epoch-ms ints), but keep the encoder total.
        return repr(value)
    if isinstance(value, str):
        return _encode_str(value)
    if isinstance(value, (list, tuple)):
        return "[" + " ".join(encode(v) for v in value) + "]"
    if isinstance(value, set):
        return "#{" + " ".join(encode(v) for v in value) + "}"
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(encode(kw(k) if isinstance(k, str) and not isinstance(k, EdnSymbol) else k))
            parts.append(encode(v))
        return "{" + " ".join(parts) + "}"
    raise TypeError(f"unsupported EDN value: {type(value).__name__}")


def _encode_str(s: str) -> str:
    out = ['"']
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def tx_add(e: str, a: str, v: Any) -> list[Any]:
    """``[:db/add <e> <a> <v>]`` tx op."""
    return [kw("db/add"), e, kw(a) if not a.startswith(":") else EdnSymbol(a), v]


def tx_retract(e: str, a: str, v: Any) -> list[Any]:
    """``[:db/retract <e> <a> <v>]`` tx op."""
    return [kw("db/retract"), e, kw(a) if not a.startswith(":") else EdnSymbol(a), v]


def tx_retract_entity(e: str) -> list[Any]:
    """``[:db.fn/retractEntity <e>]`` — atomic full-entity delete (hard delete)."""
    return [kw("db.fn/retractEntity"), e]


def encode_tx_data(ops: Iterable[list[Any]]) -> str:
    """Encode a sequence of tx-ops as a single EDN vector string."""
    return "[" + " ".join(encode(op) for op in ops) + "]"


# ── EDN scalar decode (server returns rows / datom values as EDN strings) ──────

_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+([eE][+-]?\d+)?$")


def parse_edn_value(s: Any) -> Any:
    """Decode a single EDN scalar string to a Python value (tolerant)."""
    if not isinstance(s, str):
        return s
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        body = s[1:-1]
        return body.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")
    if s == "true":
        return True
    if s == "false":
        return False
    if s == "nil":
        return None
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    return s
