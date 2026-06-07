"""Mutopia Project PD sheet music fetcher.

Per ADR-2605265000 §4. Implements CreativeMusicSymbolicSensor for music-
symbolic modality (G3 sidesteps recording-layer dual-attestation).

Mutopia Project (mutopiaproject.org) provides ~2000 PD musical scores
in MusicXML / MIDI / LilyPond / PDF formats. Per-work license is one of:
- Public Domain (Tier-A)
- Creative Commons Zero (Tier-A)
- CC-BY 3.0/4.0 (Tier-B with attribution chain via tierBCcByAttestation)
- CC-BY-SA 3.0/4.0 (Tier-B with attribution + share-alike propagation)

Tier-A licenses admitted to creative-pd/music/compositions/mutopia/.
Tier-B licenses admitted to same path but with `tierClassification` flag
+ tierBCcByAttestation record per work.

PASSIVE-ONLY (G4): reads from pre-pinned IPFS snapshots only.

Per-work PD attestation (G1) MANDATORY. G3 sidesteps recording layer
for symbolic-only modality. G7 Charter Rider §2(d) scan per work.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from kotodama.organism.sensors.creative.base import (
    CreativeMusicSymbolicObservation,
    CreativeMusicSymbolicSensor,
    ScoreFormat,
    TierClassification,
)
from kotodama.organism.sensors.base import DatasetPin


PASSIVE_ARCHIVE_ROOT = Path("/var/lib/e7m-dataset/creative-pd/music/compositions/mutopia")
PESSIMISTIC_PMA_YEARS = 70
SAFE_COMPOSER_DEATH_CUTOFF = datetime.now(UTC).year - PESSIMISTIC_PMA_YEARS  # 1956 in 2026

TIER_A_LICENSE_TAGS = frozenset({
    "Public Domain",
    "CC0 1.0",
    "Creative Commons Zero",
})

TIER_B_LICENSE_TAGS = frozenset({
    "CC-BY 3.0",
    "CC-BY 4.0",
    "Creative Commons Attribution 3.0",
    "Creative Commons Attribution 4.0",
    "CC-BY-SA 3.0",
    "CC-BY-SA 4.0",
    "Creative Commons Attribution-ShareAlike 3.0",
    "Creative Commons Attribution-ShareAlike 4.0",
})

REQUIRED_JURISDICTIONS = ("USA", "EUR", "GBR", "JPN", "AUS", "CAN", "CHN")


class MutopiaSensor:
    """Mutopia Project PD sheet music sensor (CreativeMusicSymbolicSensor implementation)."""

    sensor_id = "creative_music_mutopia_sensor"
    source_archive = "mutopiaproject.org"

    def latest_pin(self) -> DatasetPin:
        """Resolve latest com.etzhayyim.substrate.datasetPin for mutopia source.

        TODO R1.1: implement via etzhayyim_sdk.substrate.resolve_latest_dataset_pin
        """
        raise NotImplementedError("R1.1")

    def hot_sample(self, n: int = 32) -> Iterator[CreativeMusicSymbolicObservation]:
        """Bounded hot-path joucho-cadence sample.

        G3 sidesteps recording-layer; symbolic-only.
        TODO R1.1: implement manifest read + Tier-A/B dispatch + admission filter.
        """
        raise NotImplementedError(
            "R1.1: implement IPFS-pinned manifest read + Tier-A/Tier-B dispatch + "
            "publicDomainStatusAttestation per work"
        )


def _classify_tier(license_tag: str) -> TierClassification | None:
    """Tier-A for PD/CC0; Tier-B for CC-BY/CC-BY-SA; None = REJECT."""
    if license_tag in TIER_A_LICENSE_TAGS:
        return "A"
    if license_tag in {"CC-BY 3.0", "CC-BY 4.0",
                        "Creative Commons Attribution 3.0",
                        "Creative Commons Attribution 4.0"}:
        return "B-cc-by"
    if license_tag in {"CC-BY-SA 3.0", "CC-BY-SA 4.0",
                        "Creative Commons Attribution-ShareAlike 3.0",
                        "Creative Commons Attribution-ShareAlike 4.0"}:
        return "B-cc-by-sa"
    return None  # not whitelisted → REJECT


def _is_pd_globally(work_metadata: dict) -> bool:
    """G2: composer must have died ≥70 yr ago for global PD admission."""
    death_year = work_metadata.get("composer_death_year")
    if death_year is None:
        return False
    return death_year <= SAFE_COMPOSER_DEATH_CUTOFF


def _build_pd_attestation(work_metadata: dict, snapshot_cid: str, tier: TierClassification) -> dict:
    """Build com.etzhayyim.creative.publicDomainStatusAttestation record per Mutopia work.

    G1: per-work attestation REQUIRED.
    G2: 7-jurisdiction pessimistic threshold.
    G3: music-symbolic modality — composition-only attestation; recording layer sidestepped.
    """
    return {
        "lexicon": 1,
        "id": "com.etzhayyim.creative.publicDomainStatusAttestation",
        "createdAt": datetime.now(UTC).isoformat(),
        "workId": f"mutopia:{work_metadata['id']}",
        "modality": "music-symbolic",
        "sourceArchive": "mutopiaproject.org",
        "sourceArchiveLicenseTemplate": work_metadata.get("license_text", "Public Domain"),
        "pdStatusByJurisdiction": [
            {
                "jurisdictionIso3": jurisdiction,
                "status": "public-domain" if tier == "A" else "creative-commons-attribution",
                "legalBasisCid": f"bafy-placeholder-pd-basis-{jurisdiction.lower()}-mutopia-{work_metadata['id']}",
            }
            for jurisdiction in REQUIRED_JURISDICTIONS
        ],
        "pessimisticThresholdYearsPostMortem": PESSIMISTIC_PMA_YEARS,
        "compositionPdStatus": {
            "status": "public-domain",
            "composer": work_metadata.get("composer"),
            "composerDeathYear": work_metadata.get("composer_death_year"),
            "publicationYear": work_metadata.get("composition_year"),
            "anonymousOrCorporate": False,
        },
        # G3: music-symbolic — no recordingPdStatus / performerRightPdStatus
        "wellbecomingFramingScanCid": _wellbecoming_scan_cid(work_metadata),
        "attributionChainCid": _attribution_chain_cid(work_metadata),
        "tierClassification": tier,
        "internalOnly": False,  # Tier-A and Tier-B both publishable
        "attestingDid": "did:web:e7m-dataset.etzhayyim.com",
    }


def _wellbecoming_scan_cid(work_metadata: dict) -> str:
    """G7: Charter Rider §2(d) scan CID."""
    return f"bafy-placeholder-wellbecoming-scan-mutopia-{work_metadata['id']}"


def _attribution_chain_cid(work_metadata: dict) -> str:
    """G8: attribution chain CID."""
    return f"bafy-placeholder-attribution-mutopia-{work_metadata['id']}"
