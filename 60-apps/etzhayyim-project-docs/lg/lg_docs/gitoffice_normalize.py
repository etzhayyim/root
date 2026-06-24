"""GitOffice edge adapter — :doc/bodyJson blob <-> element-granular :block/* datoms.

doc e (com-junkawasaki/orgs/docs/gftd-office/e-pull-request-system.md), §13 option 1.

The deployed docs store one document as a single ``:doc/bodyJson`` blob
(``[{elementId, kind, headingLevel?, text}]``). Semantic diff / 3-way merge / PR
review need each element as its own datom keyed by a save-stable id. This module
is the edge converter: blob -> ``[:db/add e a v]`` ops (so ``store.write_ops`` can
transact them) and rows -> blob (so the Google/MS-compat API keeps serving bodyJson).

The element ``elementId`` IS the stable block id, so re-normalizing is idempotent.
Order is a fractional-index string (insert-friendly), byte-for-byte matching the
reference ``gitoffice.cljc`` (docs/gftd-office/p1-gitoffice) and the kotoba CLJS
port (kotoba.gitoffice) — parity is asserted in tests/test_gitoffice_normalize.py.

NOTE (repo convention): the canonical normalizer also lives as Clojure
(kotoba.gitoffice / p1-gitoffice). This Python mirror exists because the deployed
appview is FastAPI/Python; keep the three in lockstep (the parity test guards drift).
"""

from __future__ import annotations

from typing import Any, Iterable

from .edn import tx_add

# --- fractional indexing (base-36 fractions, lexicographic order) -----------

_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
_BASE = len(_DIGITS)
_DVAL = {c: i for i, c in enumerate(_DIGITS)}


def order_between(a: str | None, b: str | None) -> str:
    """Fractional index strictly between a (lower, None/"" = 0) and b (upper, None = 1).

    Keys must be CANONICAL (no trailing '0'): a trailing zero makes a key
    fraction-equal to its prefix ("1" == "10"), leaving no key strictly between them
    and making the midpoint walk emit an out-of-range key. Generated keys are always
    canonical; a non-canonical key only enters via external/CRDT import, so reject it
    loudly rather than corrupt the order silently. Mirrors gitoffice.cljc order-between.
    """
    a = a or ""
    if a and a[-1] == "0":
        raise ValueError(f"invalid order key (trailing zero): {a!r}")
    if b is not None:
        if b == "" or b[-1] == "0":
            raise ValueError(f"invalid order key (trailing zero / empty): {b!r}")
        if a >= b:
            raise ValueError(f"order keys not ascending: {a!r} >= {b!r}")
    acc: list[int] = []
    i = 0
    while True:
        da = _DVAL[a[i]] if i < len(a) else 0
        db = _DVAL[b[i]] if (b and i < len(b)) else _BASE
        if da + 1 < db:
            acc.append((da + db) // 2)
            return "".join(_DIGITS[x] for x in acc)
        acc.append(da)
        i += 1


def initial_orders(n: int) -> list[str]:
    """n strictly-increasing order keys (one per body position)."""
    out: list[str] = []
    prev: str | None = None
    for _ in range(n):
        k = order_between(prev, None)
        out.append(k)
        prev = k
    return out


# --- kind mapping -----------------------------------------------------------

_KIND_TO_KW = {"paragraph": "block/paragraph", "heading": "block/heading",
               "listItem": "block/list-item"}
_KW_TO_KIND = {v: k for k, v in _KIND_TO_KW.items()}


def _bare(a: Any) -> str:
    s = str(a)
    return s[1:] if s.startswith(":") else s


def _bare_kw_val(v: Any) -> str:
    """Keyword value -> bare 'block/heading' (handles EdnSymbol ':block/heading')."""
    s = str(v)
    return s[1:] if s.startswith(":") else s


# --- blob -> datom ops ------------------------------------------------------

def body_to_block_ops(doc_id: str, body: list[dict[str, Any]]) -> list[list[Any]]:
    """``:doc/bodyJson`` element list -> ``[:db/add e a v]`` ops for ``store.write_ops``."""
    orders = initial_orders(len(body))
    ops: list[list[Any]] = []
    for el, order in zip(body, orders):
        bid = el["elementId"]
        from .edn import kw  # local import keeps top imports minimal
        ops.append(tx_add(bid, "block/parent", doc_id))
        ops.append(tx_add(bid, "block/kind", kw(_KIND_TO_KW.get(el.get("kind", "paragraph"),
                                                                "block/paragraph"))))
        ops.append(tx_add(bid, "block/order", order))
        ops.append(tx_add(bid, "block/text", el.get("text", "")))
        if el.get("headingLevel") is not None:
            ops.append(tx_add(bid, "block/heading-level", el["headingLevel"]))
    return ops


# --- datom rows -> blob -----------------------------------------------------

def blocks_to_body(rows: Iterable[tuple[Any, Any, Any]], doc_id: str) -> list[dict[str, Any]]:
    """Decoded ``(e, a, v)`` rows -> ``:doc/bodyJson`` element list (sorted by block order).

    ``a`` may carry a leading ':' or not; keyword values may be EdnSymbol or str.
    """
    by_block: dict[str, dict[str, Any]] = {}
    for e, a, v in rows:
        attr = _bare(a)
        if attr == "block/parent" and v != doc_id:
            continue
        if attr.startswith("block/") or attr == "block/parent":
            by_block.setdefault(e, {})[attr] = v
    # keep only blocks that are children of this doc
    blocks = {e: attrs for e, attrs in by_block.items()
              if attrs.get("block/parent") == doc_id}
    out: list[dict[str, Any]] = []
    # sort by (order, id): the id tie-break keeps duplicate order keys deterministic
    # (matches merged-doc->body in gitmerge.cljc).
    for bid in sorted(blocks, key=lambda e: (blocks[e].get("block/order", ""), e)):
        attrs = blocks[bid]
        el: dict[str, Any] = {
            "elementId": bid,
            "kind": _KW_TO_KIND.get(_bare_kw_val(attrs.get("block/kind", "block/paragraph")),
                                    "paragraph"),
            "text": attrs.get("block/text", ""),
        }
        if "block/heading-level" in attrs:
            el["headingLevel"] = attrs["block/heading-level"]
        out.append(el)
    return out


def ops_to_rows(ops: list[list[Any]]) -> list[tuple[Any, Any, Any]]:
    """``[:db/add e a v]`` ops -> ``(e, a, v)`` rows (drops the op verb) — test/helper."""
    return [(op[1], op[2], op[3]) for op in ops if len(op) == 4]
