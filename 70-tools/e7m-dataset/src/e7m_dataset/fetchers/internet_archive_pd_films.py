"""Internet Archive PD feature_films fetcher.

Per ADR-2605265000 §4. Implements CreativeFilmSensor for the film
modality first anchor sensor.

Internet Archive (archive.org) maintains a curated PD subset at
/details/feature_films which archivists have flagged as public-domain
by US copyright rules (pre-1929 baseline + later works PD by non-renewal).

URAA §104A check is critical for IA's PD films collection: some foreign
films flagged "PD" by IA archivists were later URAA-restored in US.
Our per-work attestation cross-checks URAA status; URAA-restored works
are REJECTED pessimistic until restoration expires AND remains PD in
other 6 jurisdictions.

PASSIVE-ONLY (G4): reads from pre-pinned IPFS snapshots only. Does NOT
live-query archive.org API at organism-tick time.

Per-work PD attestation (G1) MANDATORY. Multi-juris pessimistic threshold
(G2). G7 Charter Rider §2(d) scan — pre-1929 silent films are HIGH
auto-flag risk for racial-caricature content (1915 The Birth of a Nation
class) so per-work review is essential.

Memorization guardrail (G6) downstream at baien-distill: video modality
eval uses CLIP-feature distance ≥0.3 + scene-LSH per ADR-2605265000 §5 L6
creativeMemorizationEvalReport.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from kotodama.organism.sensors.creative.base import (
    CreativeFilmObservation,
    CreativeFilmSensor,
)
from kotodama.organism.sensors.base import DatasetPin


PASSIVE_ARCHIVE_ROOT = Path("/var/lib/e7m-dataset/creative-pd/films/internet-archive")
PESSIMISTIC_PMA_YEARS = 70
SAFE_DIRECTOR_DEATH_CUTOFF = datetime.now(UTC).year - PESSIMISTIC_PMA_YEARS  # 1956 in 2026

REQUIRED_JURISDICTIONS = ("USA", "EUR", "GBR", "JPN", "AUS", "CAN", "CHN")


class InternetArchivePdFilmsSensor:
    """Internet Archive PD feature_films sensor (CreativeFilmSensor implementation).

    PASSIVE-ONLY (G4): IPFS-pinned snapshot only.
    G7 STRUCTURAL: pre-1929 films auto-flag to Council Lv6+ ≥3 queue.
    """

    sensor_id = "creative_film_internet_archive_sensor"
    source_archive = "archive.org/details/feature_films"

    def latest_pin(self) -> DatasetPin:
        """Resolve latest datasetPin for Internet Archive PD films.

        TODO R1.1: implement via etzhayyim_sdk.substrate.resolve_latest_dataset_pin
        """
        raise NotImplementedError("R1.1")

    def hot_sample(self, n: int = 32) -> Iterator[CreativeFilmObservation]:
        """Bounded hot-path joucho-cadence sample.

        Streams admitted films from pinned IA PD-collection manifest.
        Per-work URAA §104A check + multi-juris pessimistic threshold +
        Charter Rider §2(d) scan (especially aggressive for pre-1929
        silent films per G7 auto-flag).

        TODO R1.1: implement manifest read + URAA cross-check + admission
        filter + per-work attestation emission.
        """
        raise NotImplementedError(
            "R1.1: implement IPFS-pinned IA manifest read + URAA §104A "
            "cross-check + multi-juris pessimistic + Charter Rider §2(d) "
            "auto-flag (pre-1929 + US Southern setting) + per-work attestation"
        )


def _is_uraa_restored(work_metadata: dict) -> bool:
    """US-specific URAA §104A check.

    Foreign work + originally PD in US pre-1996 + still-protected in source
    country on 1996-01-01 → restored in US until 95 yr from US publication.

    TODO R1.2: implement URAA §104A cross-reference table for foreign films
    """
    return work_metadata.get("uraa_restoration_status") == "restored-still-active"


def _is_pd_globally(work_metadata: dict) -> bool:
    """G2: director death ≥70 yr ago + URAA cross-check."""
    death_year = work_metadata.get("director_death_year")
    if death_year is None:
        return False
    if death_year > SAFE_DIRECTOR_DEATH_CUTOFF:
        return False
    if _is_uraa_restored(work_metadata):
        return False  # URAA-restored in US → pessimistic REJECT
    return True


def _build_pd_attestation(work_metadata: dict, snapshot_cid: str) -> dict:
    """Build publicDomainStatusAttestation record per IA PD film.

    G1: per-work attestation REQUIRED.
    G2: 7-jurisdiction pessimistic + URAA §104A cross-check.
    G3: film modality — composition (n/a for film) + recording (film payload) +
        performer-right (named performers).
    """
    return {
        "lexicon": 1,
        "id": "com.etzhayyim.creative.publicDomainStatusAttestation",
        "createdAt": datetime.now(UTC).isoformat(),
        "workId": f"ia:{work_metadata['id']}",
        "modality": "film",
        "sourceArchive": "archive.org/details/feature_films",
        "sourceArchiveLicenseTemplate": work_metadata.get("license_text", "Public Domain"),
        "pdStatusByJurisdiction": [
            {
                "jurisdictionIso3": jurisdiction,
                "status": "public-domain",
                "legalBasisCid": f"bafy-placeholder-pd-basis-{jurisdiction.lower()}-ia-{work_metadata['id']}",
            }
            for jurisdiction in REQUIRED_JURISDICTIONS
        ],
        "pessimisticThresholdYearsPostMortem": PESSIMISTIC_PMA_YEARS,
        "recordingPdStatus": {
            "status": "public-domain",
            "releaseYear": work_metadata.get("release_year"),
            "phonogramProducer": work_metadata.get("studio_or_distributor"),
            "uraaRestorationStatus": work_metadata.get("uraa_restoration_status", "not-applicable"),
        },
        "performerRightPdStatus": _build_performer_right(work_metadata),
        "wellbecomingFramingScanCid": _wellbecoming_scan_cid(work_metadata),
        "attributionChainCid": _attribution_chain_cid(work_metadata),
        "tierClassification": "A",
        "internalOnly": False,
        "attestingDid": "did:web:e7m-dataset.etzhayyim.com",
    }


def _build_performer_right(work_metadata: dict) -> dict:
    """G3 performer-right entry for film (lead actors + director credits)."""
    performer_names = work_metadata.get("cast", [])
    performer_deaths = work_metadata.get("cast_death_years", [])
    return {
        "status": "public-domain",
        "performerNames": performer_names,
        "performerDeathYears": performer_deaths,
        "performanceYear": work_metadata.get("release_year"),
        "volunteerCc0Declaration": False,
    }


def _wellbecoming_scan_cid(work_metadata: dict) -> str:
    """G7: Charter Rider §2(d) scan CID.

    Pre-1929 films auto-flag to Council Lv6+ ≥3 queue.
    Additional flags: US Southern setting + WW1+WW2 newsreels +
    1920s-1940s exotic travelogue + pre-1955 advertising.
    """
    return f"bafy-placeholder-wellbecoming-scan-ia-{work_metadata['id']}"


def _attribution_chain_cid(work_metadata: dict) -> str:
    """G8: attribution chain CID."""
    return f"bafy-placeholder-attribution-ia-{work_metadata['id']}"
