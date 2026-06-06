"""karakuri (絡繰) T3 structured-export — the data-portability / anti-lock-in leg, stdlib (G9).

The structural inverse of vendor lock-in: pull the MEMBER's OWN data out of a service into a portable
kotoba-native form (or push it into another service). Two G9 invariants are enforced by construction:
the export owner is always the member (no third-party PII), and the export is always encrypted (an
encrypted-envelope ref per com.etzhayyim.encrypted.*, ADR-2605181100 — the artifact carries a CID/ref,
never plaintext). Live fetch is G6-gated; R0 produces an export PLAN only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MEMBER = "member"                                   # G9 — own data only
EXPORT_FORMATS = ("kotoba-edn", "json", "csv", "markdown")
ENCREF_PREFIX = "encref:"


class OwnerViolation(ValueError):
    """Raised when an export would cover anything but the member's OWN data (G9)."""


@dataclass
class ExportArtifact:
    service: str
    fmt: str
    owner: str = MEMBER                 # G9 const
    encrypted: bool = True             # G9 const
    cid: str = ""                       # content-addressed ref of the encrypted export (set on live run)
    secret_ref: str = ""               # encrypted-envelope ref (G9; never plaintext)
    dry_run: bool = True               # G6
    roundtrip_ok: bool = False


def build_export_plan(
    service: str,
    fmt: str = "kotoba-edn",
    *,
    owner: str = MEMBER,
    secret_ref: str = "",
) -> ExportArtifact:
    """Build a dry-run T3 export plan for the MEMBER's OWN data (G9). Raises on a non-member owner or
    an unknown format. The plan is encrypted-by-construction; the live fetch is G6-gated."""
    if owner != MEMBER:
        raise OwnerViolation(
            "G9 violation: export covers the member's OWN data only; no third-party data/PII"
        )
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"unknown export format {fmt!r}; allowed: {EXPORT_FORMATS}")
    if secret_ref and not secret_ref.startswith(ENCREF_PREFIX):
        raise ValueError("G9 violation: secret_ref must be an encrypted-envelope ref (encref:…)")

    return ExportArtifact(
        service=service, fmt=fmt, owner=MEMBER, encrypted=True,
        secret_ref=secret_ref or f"encref:com.etzhayyim.encrypted/{service}-export",
        dry_run=True,
    )


def verify_roundtrip(artifact: ExportArtifact) -> ExportArtifact:
    """Portability check: an export must be re-importable in the same kotoba-native shape it left in.

    At R0 this validates the artifact's portability invariants (member-owned, encrypted, known format)
    rather than moving bytes — the live pull/push is G6-gated. Returns the artifact with
    `roundtrip_ok` set; raises if it could not be a faithful, charter-clean round-trip."""
    if artifact.owner != MEMBER:
        raise OwnerViolation("G9 violation: round-trip of non-member data is refused")
    if not artifact.encrypted:
        raise ValueError("G9 violation: an export must be encrypted to round-trip")
    if artifact.fmt not in EXPORT_FORMATS:
        raise ValueError(f"non-portable format {artifact.fmt!r}")
    artifact.roundtrip_ok = True
    return artifact
