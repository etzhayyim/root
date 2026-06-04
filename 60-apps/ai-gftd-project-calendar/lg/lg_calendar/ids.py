"""Identity helpers for calendar events.

Canonical entity id = ``cal:event:{slug}`` (the datomic entity ref).
Path-based DID    = ``did:web:calendar.gftd.ai:event:{slug}``.
AT URI            = ``at://{did}/ai.gftd.apps.calendar.event/{slug}``.
"""

from __future__ import annotations

import re
import secrets

_SLUG_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
_DOMAIN = "calendar.gftd.ai"
_COLLECTION = "ai.gftd.apps.calendar.event"

try:  # nanoid is the deployed generator; fall back to stdlib for local/CI runs.
    from nanoid import generate as _nanoid_generate
except ModuleNotFoundError:  # pragma: no cover
    _nanoid_generate = None


def new_slug() -> str:
    if _nanoid_generate is not None:
        return _nanoid_generate(_SLUG_ALPHABET, 16)
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(16))


def eid_for_slug(slug: str) -> str:
    return f"cal:event:{slug}"


def slug_from_eid(eid: str) -> str:
    return eid.rsplit(":", 1)[-1]


def did_for_slug(slug: str) -> str:
    return f"did:web:{_DOMAIN}:event:{slug}"


def uri_for_slug(slug: str) -> str:
    return f"at://{did_for_slug(slug)}/{_COLLECTION}/{slug}"


def ical_uid_for_slug(slug: str) -> str:
    return f"{slug}@{_DOMAIN}"


_SLUG_RE = re.compile(r"^[0-9a-z]{6,32}$")


def resolve_slug(event_id: str) -> str | None:
    """Resolve a caller-supplied id (slug, eid, or DID) to a bare slug.

    Returns None when the input is a provider-native or iCalUid form that needs a
    datomic lookup instead (handled by the store).
    """
    if not event_id:
        return None
    if event_id.startswith("cal:event:"):
        return slug_from_eid(event_id)
    if event_id.startswith("did:web:") and ":event:" in event_id:
        return event_id.rsplit(":event:", 1)[-1]
    if _SLUG_RE.match(event_id):
        return event_id
    return None
