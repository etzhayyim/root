"""LibriVox CC0+PD audiobook narration fetcher.

Per ADR-2605265000 §4. Implements CreativeAudioSensor (modality-subkind
= 'audio-speech') for the creative-pd substrate's first anchor sensor.

LibriVox provides volunteer-narrated audiobooks of public-domain text
works (Gutenberg + similar). Narrator volunteers donate their recordings
under CC0 1.0; source text PD verified via per-work attestation chain.

Cleanest first audio sensor for R1:
- CC0 1.0 (volunteer-donated narration) → no Tier-B attribution-chain overhead
- PD text source (Gutenberg etc.) → composition layer already PD globally
- Active maintenance + per-work metadata fields (author + author-death + publication-year)
- API at https://librivox.org/api/feed/audiobooks/

PASSIVE-ONLY (G4): this fetcher reads from pre-pinned IPFS snapshots at
``e7m-dataset:creative-pd/audio/speech/librivox/``. Does NOT live-query
librivox.org/api/ at organism-tick time.

Per-work PD attestation (G1) MANDATORY before admission. Multi-juris
pessimistic threshold (G2) applied: composer death year ≤ current_year - 70.
Charter Rider §2(d) Wellbecoming framing scan (G7) per work.

Memorization guardrail (G6) at baien-distill commit_node — this fetcher
emits Chromaprint fingerprint CID for downstream spectral-distance eval.

Inference of derived artifacts is Murakumo-only (ADR-2605215000).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from kotodama.organism.sensors.creative.base import (
    CreativeAudioObservation,
    CreativeAudioSensor,
)
from kotodama.organism.sensors.base import DatasetPin


PASSIVE_ARCHIVE_ROOT = Path("/var/lib/e7m-dataset/creative-pd/audio/speech/librivox")
PESSIMISTIC_PMA_YEARS = 70  # EU/UK/JP-post-2018/AU baseline
SAFE_AUTHOR_DEATH_CUTOFF = datetime.now(UTC).year - PESSIMISTIC_PMA_YEARS  # 1956 in 2026

REQUIRED_JURISDICTIONS = ("USA", "EUR", "GBR", "JPN", "AUS", "CAN", "CHN")


class LibrivoxSensor:
    """LibriVox CC0+PD audiobook sensor (CreativeAudioSensor implementation).

    PASSIVE-ONLY (G4): reads from IPFS-pinned snapshot only.
    """

    sensor_id = "creative_audio_librivox_sensor"
    source_archive = "librivox.org"

    def latest_pin(self) -> DatasetPin:
        """Resolve latest com.etzhayyim.substrate.datasetPin for librivox source.

        Per ADR-2605241500 + ADR-2605262400 §G7 PASSIVE-ONLY discipline.
        TODO R1.1: implement via etzhayyim_sdk.substrate.resolve_latest_dataset_pin
        with recency-horizon staleness audit (≤30 days).
        """
        raise NotImplementedError(
            "R1.1: implement etzhayyim_sdk.substrate.resolve_latest_dataset_pin "
            "with recency_horizon_days=30 staleness audit"
        )

    def hot_sample(self, n: int = 32) -> Iterator[CreativeAudioObservation]:
        """Bounded hot-path joucho-cadence sample.

        Streams admitted works from pinned snapshot manifest.
        Per ADR-2605265000 G1+G2+G7 enforced before emission.
        TODO R1.1: implement manifest read + per-work attestation generation.
        """
        raise NotImplementedError(
            "R1.1: implement IPFS-pinned manifest read + admission filter + "
            "publicDomainStatusAttestation emission per work"
        )


def _build_pd_attestation(work_metadata: dict, snapshot_cid: str) -> dict:
    """Build com.etzhayyim.creative.publicDomainStatusAttestation record per LibriVox work.

    G1: per-work attestation REQUIRED.
    G2: 7-jurisdiction pessimistic threshold.
    G3: audio-speech modality requires composition + recording attestation;
        recording layer satisfied by CC0 1.0 volunteer donation.

    TODO R1.2: legal-basis CID generation per jurisdiction
    """
    return {
        "lexicon": 1,
        "id": "com.etzhayyim.creative.publicDomainStatusAttestation",
        "createdAt": datetime.now(UTC).isoformat(),
        "workId": f"librivox:{work_metadata['id']}",
        "modality": "audio-speech",
        "sourceArchive": "librivox.org",
        "sourceArchiveLicenseTemplate": "CC0-1.0",
        "pdStatusByJurisdiction": [
            {
                "jurisdictionIso3": jurisdiction,
                "status": "public-domain",
                "legalBasisCid": f"bafy-placeholder-pd-basis-{jurisdiction.lower()}-{work_metadata['id']}",
            }
            for jurisdiction in REQUIRED_JURISDICTIONS
        ],
        "pessimisticThresholdYearsPostMortem": PESSIMISTIC_PMA_YEARS,
        "compositionPdStatus": {
            "status": "public-domain",
            "composer": work_metadata.get("author"),
            "composerDeathYear": work_metadata.get("author_death_year"),
            "publicationYear": work_metadata.get("publication_year"),
            "anonymousOrCorporate": False,
        },
        "recordingPdStatus": {
            "status": "creative-commons-zero",  # LibriVox volunteer CC0
            "releaseYear": work_metadata.get("recording_year"),
            "phonogramProducer": "LibriVox",
            "uraaRestorationStatus": "not-applicable",
        },
        "performerRightPdStatus": {
            "status": "performer-cc0-self-donated",
            "performerNames": work_metadata.get("narrator_names", []),
            "volunteerCc0Declaration": True,
            "performanceYear": work_metadata.get("recording_year"),
        },
        "wellbecomingFramingScanCid": _wellbecoming_scan_cid(work_metadata),
        "attributionChainCid": _attribution_chain_cid(work_metadata),
        "tierClassification": "A",
        "internalOnly": False,
        "attestingDid": "did:web:e7m-dataset.etzhayyim.com",
    }


def _is_pd_globally(work_metadata: dict) -> bool:
    """G2: composer must have died ≥70 yr ago for global PD admission."""
    death_year = work_metadata.get("author_death_year")
    if death_year is None:
        return False
    return death_year <= SAFE_AUTHOR_DEATH_CUTOFF


def _wellbecoming_scan_cid(work_metadata: dict) -> str:
    """G7: Charter Rider §2(d) Wellbecoming framing scan CID.

    TODO R1.2: integrate with kotodama.organism.sensors.charter_rider.scan_sample
    on metadata + first chapter excerpt; emit wellbecomingFramingScan record;
    return CID.
    """
    return f"bafy-placeholder-wellbecoming-scan-librivox-{work_metadata['id']}"


def _attribution_chain_cid(work_metadata: dict) -> str:
    """G8: attribution chain document CID."""
    return f"bafy-placeholder-attribution-librivox-{work_metadata['id']}"


def _chromaprint_fingerprint_cid(audio_payload_cid: str) -> str:
    """G6: Chromaprint spectral-fingerprint CID for memorization-eval downstream check.

    TODO R1.2: read audio at audio_payload_cid; compute Chromaprint fingerprint;
    pin fingerprint document; return CID.
    """
    return f"bafy-placeholder-chromaprint-{audio_payload_cid[:16]}"
