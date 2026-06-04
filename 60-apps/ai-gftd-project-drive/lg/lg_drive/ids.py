"""Identity helpers for drive items.

Canonical entity id = ``drive:file:{slug}`` (the datomic entity ref).
Path-based DID    = ``did:web:drive.gftd.ai:file:{slug}``.
AT URI            = ``at://{did}/ai.gftd.apps.drive.file/{slug}``.
"""

from __future__ import annotations

import re
import secrets

_SLUG_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_DOMAIN = "drive.gftd.ai"
_COLLECTION = "ai.gftd.apps.drive.file"

try:
    from nanoid import generate as _nanoid_generate
except ModuleNotFoundError:  # pragma: no cover
    _nanoid_generate = None


def new_slug() -> str:
    if _nanoid_generate is not None:
        return _nanoid_generate(_SLUG_ALPHABET, 16)
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(16))


def eid_for_slug(slug: str) -> str:
    return f"drive:file:{slug}"


def slug_from_eid(eid: str) -> str:
    return eid.rsplit(":", 1)[-1]


def did_for_slug(slug: str) -> str:
    return f"did:web:{_DOMAIN}:file:{slug}"


def uri_for_slug(slug: str) -> str:
    return f"at://{did_for_slug(slug)}/{_COLLECTION}/{slug}"


_SLUG_RE = re.compile(r"^[0-9a-z]{6,32}$")


def resolve_slug(file_id: str) -> str | None:
    """Resolve a caller-supplied id (slug, eid, DID, or 'root') to a bare slug."""
    if not file_id:
        return None
    if file_id.startswith("drive:file:"):
        return slug_from_eid(file_id)
    if file_id.startswith("did:web:") and ":file:" in file_id:
        return file_id.rsplit(":file:", 1)[-1]
    if _SLUG_RE.match(file_id):
        return file_id
    return None
