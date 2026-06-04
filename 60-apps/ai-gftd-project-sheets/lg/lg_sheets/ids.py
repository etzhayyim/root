"""Identity helpers for spreadsheets.

Canonical entity id = ``sheet:book:{slug}`` (the datomic entity ref).
Path-based DID    = ``did:web:sheets.gftd.ai:spreadsheet:{slug}``.
AT URI            = ``at://{did}/ai.gftd.apps.sheets.spreadsheet/{slug}``.
"""

from __future__ import annotations

import re
import secrets

_SLUG_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_DOMAIN = "sheets.gftd.ai"
_COLLECTION = "ai.gftd.apps.sheets.spreadsheet"

try:
    from nanoid import generate as _nanoid_generate
except ModuleNotFoundError:  # pragma: no cover
    _nanoid_generate = None


def new_slug() -> str:
    if _nanoid_generate is not None:
        return _nanoid_generate(_SLUG_ALPHABET, 16)
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(16))


def eid_for_slug(slug: str) -> str:
    return f"sheet:book:{slug}"


def slug_from_eid(eid: str) -> str:
    return eid.rsplit(":", 1)[-1]


def did_for_slug(slug: str) -> str:
    return f"did:web:{_DOMAIN}:spreadsheet:{slug}"


def uri_for_slug(slug: str) -> str:
    return f"at://{did_for_slug(slug)}/{_COLLECTION}/{slug}"


_SLUG_RE = re.compile(r"^[0-9a-z]{6,32}$")


def resolve_slug(spreadsheet_id: str) -> str | None:
    if not spreadsheet_id:
        return None
    if spreadsheet_id.startswith("sheet:book:"):
        return slug_from_eid(spreadsheet_id)
    if spreadsheet_id.startswith("did:web:") and ":spreadsheet:" in spreadsheet_id:
        return spreadsheet_id.rsplit(":spreadsheet:", 1)[-1]
    if _SLUG_RE.match(spreadsheet_id):
        return spreadsheet_id
    return None
