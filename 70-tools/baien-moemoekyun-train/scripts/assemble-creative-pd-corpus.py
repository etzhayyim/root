#!/usr/bin/env python3
"""assemble-creative-pd-corpus.py — cold-path creative-pd corpus assembler.

Per ADR-2605265000 §10. Consumes a recipe TOML → streams source works →
per-work PD attestation generation → Charter Rider §2(d) framing scan →
modality-specific preprocessing → NDJSON shard write → IPFS pin →
publish-ipfs CID → com.etzhayyim.substrate.datasetPin emit.

Sibling pattern to:
- 70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py (ADR-2605262400 §2)
- 70-tools/baien-moemoekyun-train/scripts/assemble-legal-corpus.py (ADR-2605262800)

Usage:
    python assemble-creative-pd-corpus.py \\
        --recipe creative-audio-speech-foundations-r1 \\
        --target-shard-mb 512

R1 anchor recipes (creative/ subdirectory):
- creative-audio-speech-foundations-r1.toml (LibriVox)
- creative-music-symbolic-foundations-r1.toml (Mutopia)
- creative-film-vision-foundations-r1.toml (Internet Archive PD feature_films)

R2 adds:
- creative-video-temporal-foundations-r1.toml (Prelinger + NASA)
- creative-music-recording-foundations-r1.toml (Musopen PD + Wikimedia Commons PD audio)
- creative-audio-sound-foundations-r1.toml (British Library + archive.org oldtimeradio)
- creative-audio-folklife-foundations-r1.toml (LoC American Folklife)

Discipline:
- G1: per-work publicDomainStatusAttestation REQUIRED before admission
- G2: 7-jurisdiction pessimistic threshold
- G3: music modality dual-attestation (composition + recording)
- G4: PASSIVE-ONLY ingestion (IPFS-pinned snapshot only; no live network)
- G7: Charter Rider §2(d) Wellbecoming framing scan per work
- G8: attribution chain in every record
- G10: emission to 90-docs/baien/creative-memorization-eval-{R-step}.jsonl
       (downstream at baien-distill commit_node)

PASSIVE-ONLY invariant: this script reads from pre-pinned IPFS snapshots only;
NEVER live-queries source archives.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


CORPUS_ROOT = Path("/var/lib/e7m-dataset/creative-pd-corpus")
RECIPE_ROOT = Path(__file__).parent.parent / "recipes" / "creative"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recipe",
        required=True,
        help="Recipe name (e.g. 'creative-audio-speech-foundations-r1')",
    )
    parser.add_argument(
        "--target-shard-mb",
        type=int,
        default=512,
        help="Target NDJSON shard size in MB",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Stream + validate but do NOT write shards or emit datasetPin",
    )
    args = parser.parse_args()

    recipe_path = RECIPE_ROOT / f"{args.recipe}.toml"
    if not recipe_path.exists():
        print(f"ERROR: recipe not found at {recipe_path}", file=sys.stderr)
        sys.exit(1)

    recipe = _load_recipe(recipe_path)
    print(f"Loaded recipe: {recipe['name']}")
    print(f"Modality: {recipe['modality']}")
    print(f"Sources: {[s['name'] for s in recipe['sources']]}")

    if args.dry_run:
        print("Dry-run mode: validate only")

    assembled = assemble(
        recipe=recipe,
        target_shard_mb=args.target_shard_mb,
        dry_run=args.dry_run,
    )

    print(f"Assembled corpus: {assembled['record_count']} records")
    print(f"Shards: {assembled['shard_count']}")
    print(f"Manifest CID: {assembled.get('manifest_cid', '(dry-run)')}")
    print(f"Dataset pin: {assembled.get('dataset_pin_uri', '(dry-run)')}")


def assemble(recipe: dict[str, Any], target_shard_mb: int, dry_run: bool) -> dict[str, Any]:
    """Stream sources → per-work attestation → preprocessing → NDJSON shards → IPFS pin."""
    shard_dir = CORPUS_ROOT / recipe["name"]
    shard_dir.mkdir(parents=True, exist_ok=True)

    shard_idx = 0
    shard_size_bytes = 0
    shard_records: list[dict[str, Any]] = []
    manifest_records: list[dict[str, Any]] = []
    target_shard_bytes = target_shard_mb * 1024 * 1024

    total_admitted = 0
    total_rejected = 0

    for source in recipe["sources"]:
        for work in _stream_source(source):
            # G1+G2+G3: per-work PD attestation + multi-juris check
            attestation = _build_attestation(work, source)
            if not _verify_attestation(work, attestation):
                total_rejected += 1
                continue

            # G7: Charter Rider §2(d) Wellbecoming framing scan
            scan = _wellbecoming_scan(work, source["modality"])
            if scan["verdict"] == "exclude":
                total_rejected += 1
                continue

            # Modality-specific preprocessing
            preprocessed = _preprocess(work, source["modality"])

            # G8: attribution chain in every record
            record = {
                "workId": attestation["workId"],
                "modality": source["modality"],
                "tierClassification": attestation["tierClassification"],
                "attestationCid": _pin_attestation(attestation),
                "wellbecomingScanCid": _pin_scan(scan),
                "attribution": _build_attribution(work, attestation),
                "preprocessed": preprocessed,
            }
            shard_records.append(record)
            shard_size_bytes += len(json.dumps(record).encode("utf-8"))
            total_admitted += 1

            if shard_size_bytes >= target_shard_bytes:
                shard_cid = _write_shard(shard_dir, shard_idx, shard_records, dry_run)
                manifest_records.append({
                    "shard_idx": shard_idx,
                    "cid": shard_cid,
                    "record_count": len(shard_records),
                })
                shard_idx += 1
                shard_size_bytes = 0
                shard_records = []

    # Flush remainder
    if shard_records:
        shard_cid = _write_shard(shard_dir, shard_idx, shard_records, dry_run)
        manifest_records.append({
            "shard_idx": shard_idx,
            "cid": shard_cid,
            "record_count": len(shard_records),
        })

    if dry_run:
        return {
            "record_count": total_admitted,
            "rejected_count": total_rejected,
            "shard_count": len(manifest_records),
        }

    # Emit manifest + datasetPin
    manifest_cid = _pin_manifest(shard_dir, manifest_records)
    pin_uri = _emit_dataset_pin(
        source_namespace=f"creative-pd/{recipe['name']}",
        snapshot_cid=manifest_cid,
        recipe_name=recipe["name"],
        record_count=total_admitted,
    )

    return {
        "record_count": total_admitted,
        "rejected_count": total_rejected,
        "shard_count": len(manifest_records),
        "manifest_cid": manifest_cid,
        "dataset_pin_uri": pin_uri,
    }


# ── Recipe loading ─────────────────────────────────────────────


def _load_recipe(path: Path) -> dict[str, Any]:
    """Load TOML recipe. TODO R1.1: parse modality + sources + preprocessing config."""
    import tomllib
    return tomllib.loads(path.read_text())


# ── Source streaming (PASSIVE-ONLY via IPFS-pinned snapshot) ──


def _stream_source(source: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Stream works from a pre-pinned IPFS snapshot.

    G4 PASSIVE-ONLY: NEVER live-query the source; only read from
    pre-pinned snapshot at source['snapshot_cid'].

    TODO R1.1: implement IPFS cat + manifest parse + work iteration
    """
    raise NotImplementedError(
        "R1.1: implement IPFS-pinned source stream "
        "(librivox / mutopia / internet_archive_pd_films / etc.)"
    )


# ── Attestation generation + verification ─────────────────────


def _build_attestation(work: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Build com.etzhayyim.creative.publicDomainStatusAttestation per work.

    Dispatches to per-source fetcher's _build_pd_attestation:
    - librivox.py → audio-speech with composition + recording + performer-right CC0
    - mutopia.py → music-symbolic (recording layer sidestepped per G3)
    - internet_archive_pd_films.py → film with URAA cross-check
    """
    from e7m_dataset.fetchers import librivox, mutopia, internet_archive_pd_films
    dispatch = {
        "librivox": librivox._build_pd_attestation,
        "mutopia": mutopia._build_pd_attestation,
        "internet_archive_pd_films": internet_archive_pd_films._build_pd_attestation,
    }
    builder = dispatch.get(source["fetcher_name"])
    if builder is None:
        raise NotImplementedError(f"R1.1: per-source attestation builder for {source['fetcher_name']}")
    return builder(work, source.get("snapshot_cid", ""))


def _verify_attestation(work: dict[str, Any], attestation: dict[str, Any]) -> bool:
    """G1+G2+G3 verification. Reject if any condition fails."""
    # G1: all required fields present
    required = ["workId", "modality", "pdStatusByJurisdiction",
                "pessimisticThresholdYearsPostMortem", "tierClassification"]
    if not all(k in attestation for k in required):
        return False

    # G2: 7-jurisdiction coverage + all PD
    statuses = attestation["pdStatusByJurisdiction"]
    if len(statuses) < 7:
        return False
    pd_statuses = {"public-domain", "creative-commons-zero", "creative-commons-attribution"}
    if not all(s["status"] in pd_statuses for s in statuses):
        return False

    # G2: pessimistic threshold ≥70
    if attestation["pessimisticThresholdYearsPostMortem"] < 70:
        return False

    # G3: music modality dual-attestation
    modality = attestation["modality"]
    if modality == "music-recording" and (
        "compositionPdStatus" not in attestation or "recordingPdStatus" not in attestation
    ):
        return False
    # music-symbolic intentionally sidesteps recording per G3
    return True


# ── Charter Rider §2(d) Wellbecoming framing scan ─────────────


def _wellbecoming_scan(work: dict[str, Any], modality: str) -> dict[str, Any]:
    """G7: Charter Rider §2(d) per-work scan.

    R1 manual: per-work review queue if auto-flag triggers
    R2+ rule-encoded: pre-1929 + US Southern setting + WW1+WW2 newsreels +
                       1920s exotic travelogue + pre-1955 advertising
    R3+ baien-distill specialist auto-score

    TODO R1.1: integrate with kotodama.organism.sensors.charter_rider
    """
    return {
        "verdict": "admit",  # placeholder; R1.1 implements full scan
        "auto_flags_triggered": [],
        "reviewer_dids": ["did:web:e7m-dataset.etzhayyim.com"],
    }


# ── Modality-specific preprocessing handlers ──────────────────


def _preprocess(work: dict[str, Any], modality: str) -> dict[str, Any]:
    """Dispatch to modality-specific preprocessor.

    Handlers at 70-tools/baien-moemoekyun-train/scripts/preprocess/:
    - audio_speech_handler.py (16kHz mono + 30-sec chunks + token-align)
    - audio_sound_handler.py (chunk + spectrogram + Chromaprint)
    - music_symbolic_handler.py (MusicXML → REMI-style token sequence)
    - music_recording_handler.py (audio preprocess + Chromaprint)
    - video_film_handler.py (frame downsample + scene-boundary + audio sidecar)
    - video_general_handler.py (lower constraints)

    TODO R1.1: implement per-modality handlers
    """
    return {
        "modality": modality,
        "preprocessing_status": "deferred-to-R1.1",
    }


# ── IPFS pinning + datasetPin emission ────────────────────────


def _write_shard(shard_dir: Path, shard_idx: int, records: list[dict[str, Any]],
                  dry_run: bool) -> str:
    """Write NDJSON shard + pin to IPFS."""
    if dry_run:
        return f"bafy-placeholder-shard-{shard_idx}"
    shard_path = shard_dir / f"shard-{shard_idx:04d}.ndjson.gz"
    with gzip.open(shard_path, "wt") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return _pin_to_ipfs(shard_path)


def _pin_to_ipfs(path: Path) -> str:
    """Pin file to IPFS and return CID. TODO R1.1: integrate with ipfs CLI."""
    raise NotImplementedError("R1.1: ipfs add + pin via kubo CLI")


def _pin_attestation(attestation: dict[str, Any]) -> str:
    """Pin attestation JSON to IPFS and return CID."""
    raise NotImplementedError("R1.1")


def _pin_scan(scan: dict[str, Any]) -> str:
    """Pin Wellbecoming scan JSON to IPFS and return CID."""
    raise NotImplementedError("R1.1")


def _pin_manifest(shard_dir: Path, manifest: list[dict[str, Any]]) -> str:
    """Pin corpus manifest to IPFS and return CID."""
    raise NotImplementedError("R1.1")


def _build_attribution(work: dict[str, Any], attestation: dict[str, Any]) -> dict[str, Any]:
    """G8: attribution chain document."""
    return {
        "workId": attestation["workId"],
        "modality": attestation["modality"],
        "sourceArchive": attestation["sourceArchive"],
        "attributionChainCid": attestation.get("attributionChainCid"),
    }


def _emit_dataset_pin(source_namespace: str, snapshot_cid: str,
                      recipe_name: str, record_count: int) -> str:
    """Emit com.etzhayyim.substrate.datasetPin record for this corpus.

    Per ADR-2605241500 + ADR-2605262400 §2 datasetPin Lexicon.
    """
    raise NotImplementedError(
        "R1.1: emit datasetPin via etzhayyim_sdk.substrate"
    )


if __name__ == "__main__":
    main()
