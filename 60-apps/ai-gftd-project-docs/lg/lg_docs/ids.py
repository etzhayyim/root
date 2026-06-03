"""Identity helpers for documents.

Canonical entity id = ``doc:doc:{slug}`` (the datomic entity ref).
Path-based DID    = ``did:web:docs.gftd.ai:document:{slug}``.
AT URI            = ``at://{did}/ai.gftd.apps.docs.document/{slug}``.
"""

from __future__ import annotations

import re
import secrets

_SLUG_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_DOMAIN = "docs.gftd.ai"
_COLLECTION = "ai.gftd.apps.docs.document"

try:
    from nanoid import generate as _nanoid_generate
except ModuleNotFoundError:  # pragma: no cover
    _nanoid_generate = None


def new_slug() -> str:
    if _nanoid_generate is not None:
        return _nanoid_generate(_SLUG_ALPHABET, 16)
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(16))


def new_element_id() -> str:
    return "el-" + "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(10))


def eid_for_slug(slug: str) -> str:
    return f"doc:doc:{slug}"


def slug_from_eid(eid: str) -> str:
    return eid.rsplit(":", 1)[-1]


def did_for_slug(slug: str) -> str:
    return f"did:web:{_DOMAIN}:document:{slug}"


def uri_for_slug(slug: str) -> str:
    return f"at://{did_for_slug(slug)}/{_COLLECTION}/{slug}"


_SLUG_RE = re.compile(r"^[0-9a-z]{6,32}$")


def resolve_slug(document_id: str) -> str | None:
    if not document_id:
        return None
    if document_id.startswith("doc:doc:"):
        return slug_from_eid(document_id)
    if document_id.startswith("did:web:") and ":document:" in document_id:
        return document_id.rsplit(":document:", 1)[-1]
    if _SLUG_RE.match(document_id):
        return document_id
    return None
