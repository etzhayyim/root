#!/usr/bin/env python3
"""Entity mirror-actor social-timeline projector (ADR-2606042330 D4).

Projects a kotoba Datom `as-of` delta for a public/power entity into a
`com.etzhayyim.mirror.mirrorPost` envelope — the entity's social timeline IS its
append-only as-of history (非終末論). Charter invariants enforced HERE by
construction:

  - G1 mirror-only: `isMirror=True` always; the post is etzhayyim's record of a
    public fact, never the entity speaking. The text is prefixed so it can never
    be mistaken for the entity's own voice.
  - G6 Murakumo-only: `narrator="murakumo"` (this module does NOT call any model;
    it shapes the envelope — the narrated `text` is produced upstream by Murakumo
    and passed in, or a deterministic factual summary is used in dry-run).
  - G8 outward-gated: `published=False` ALWAYS in this module. Flipping it to
    publish to the atproto firehose requires Council + operator authorization and
    happens in a separate, gated path — never here. `project()` will refuse to
    emit a published envelope.

stdlib only. R0 = dry-run projection; no network, no firehose.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

# The handle namespaces that may carry a mirror timeline (must match the TS
# entity-actor registry; person namespaces do not exist by construction — G3).
VALID_NAMESPACES = {"gov", "corp", "cable", "station", "craft"}

MIRROR_PREFIX = "[etzhayyim mirror]"


class GateError(RuntimeError):
    """Raised when a projection would violate a charter gate."""


@dataclass(frozen=True)
class MirrorPost:
    actorHandle: str
    datomTxCid: str
    asOf: str
    changeKind: str
    narrator: str
    isMirror: bool
    published: bool
    text: str

    def to_record(self) -> dict[str, Any]:
        return {"$type": "com.etzhayyim.mirror.mirrorPost", **asdict(self)}


def _namespace_of(handle: str) -> str:
    ns = handle.split("-", 1)[0] if "-" in handle else ""
    if ns not in VALID_NAMESPACES:
        raise GateError(
            f"handle {handle!r} is not an entity-actor namespace "
            f"({sorted(VALID_NAMESPACES)}); persons/members are not mirrorable (G3)"
        )
    return ns


def project(
    *,
    actor_handle: str,
    datom_tx_cid: str,
    as_of: str,
    change_kind: str,
    narrated_text: str,
    request_publish: bool = False,
) -> MirrorPost:
    """Project one as-of delta into a (dry-run) mirrorPost envelope.

    `request_publish=True` is REFUSED (G8): live firehose publication is not this
    module's job and is Council + operator gated. The returned envelope always has
    `published=False`.
    """
    _namespace_of(actor_handle)  # G3 person-exclusion + namespace validation
    if request_publish:
        raise GateError(
            "live publication is Council + operator gated (G8); this projector "
            "only emits dry-run envelopes (published=False)"
        )
    if not datom_tx_cid:
        raise GateError("datomTxCid required — a post must be auditable to the Datom log")

    text = narrated_text.strip()
    if not text.startswith(MIRROR_PREFIX):
        # G1 — make the mirror framing unspoofable in the post body itself.
        text = f"{MIRROR_PREFIX} {text}"

    return MirrorPost(
        actorHandle=actor_handle,
        datomTxCid=datom_tx_cid,
        asOf=as_of,
        changeKind=change_kind,
        narrator="murakumo",  # G6
        isMirror=True,  # G1
        published=False,  # G8 — never published from here
        text=text,
    )
