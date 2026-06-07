#!/usr/bin/env python3
"""
rental-orchestrator.py — orchestrate a single commercial GPU rental train run
under CHARTER-RIDER §2(i)(2) carve-out (ADR-2605262200) for baien-server-moemoekyun.

Per ADR-2605262300 §7, this script:
  1. charter-rider scan all dataset CIDs (train + eval)
  2. publish com.etzhayyim.train.rentalAttestation (pre-flight)
  3. vendor.start_instance + provision train workload
  4. run train script remotely (poll for completion)
  5. fetch final checkpoint -> mac-260317
  6. e7m-dataset add (IPFS pin) + e7m-dataset verify
  7. fleet eval (Mac mini split-role per ADR-2605262100 §5)
  8. commit_gate (Δ_langgraph ≥ +3pp AND Δ_humaneval+ ≥ 0)
  9. publish com.etzhayyim.train.rentalCostLog (post-flight)
  10. instance terminate

SKELETON STATUS (R2.0 deliverable):
  - All vendor.* methods are stubs that raise NotImplementedError
  - Actual vendor SDK integration (RunPod / Lambda / CoreWeave) lands at R2.1 deliverable
  - This file is committed to confirm interface + sequence + Lexicon emit pattern

Gated on: ADR-2605262200 ratification (earliest 2026-07-19); execution before P4 is constitutional violation.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("rental-orchestrator")


# ─── Configuration types ──────────────────────────────────────────────────


@dataclass
class RentalConfig:
    """Per-rental configuration parsed from configs/r{N}-iter{MM}.yaml."""

    train_adr_ref: str  # e.g., "ADR-2605262300"
    vendor: str  # "runpod-community" etc.
    gpu_model: str  # "nvidia-b200-sxm" etc.
    gpu_count: int  # 1..8
    expected_wall_minutes: int                # integer per Lexicon AT Protocol restriction
    expected_usd_cost_millicents: int         # = USD × 100000 (integer per Lexicon)
    dataset_cids_train: list[str]
    dataset_cids_eval: list[str]
    model_tier: str  # "baien-server" or "baien-XL"
    model_artifact_name: str  # e.g., "baien-server-moemoekyun-r2-iter01"
    precision_mode: str  # "bf16" | "fp8-mixed" | "sparse-fp4"
    train_script_path: str  # path on rented instance, e.g., "/workspace/train.py"
    train_config_yaml: str  # path on local that gets uploaded
    attesting_did: str  # e.g., "did:web:mac-260317.etzhayyim.com"


@dataclass
class EvalMetrics:
    """Scores are stored as PERMILLE (parts per thousand, integer 0..1000) per
    AT Protocol Lexicon restriction (no float types). Divide by 10 for percentage."""
    langgraph_coding_pass1_permille: int = 0
    humanevalplus_pass1_permille: int = 0
    mbpp_plus_pass1_permille: int = 0
    delta_langgraph_coding_permille: int = 0    # signed, can be negative
    delta_humanevalplus_permille: int = 0


@dataclass
class RentalAttestation:
    """com.etzhayyim.train.rentalAttestation record body."""

    createdAt: str
    trainAdrRef: str
    vendor: str
    gpuModel: str
    gpuCount: int
    expectedWallMinutes: int
    expectedUsdCostMillicents: int            # = USD × 100000 per Lexicon
    datasetCidsTrain: list[str]
    datasetCidsEval: list[str]
    modelTier: str
    modelArtifactName: str
    precisionMode: str
    charterRiderScanPass: bool
    charterRiderScanRunCid: str
    attestingDid: str
    monthlyRentalCumulativeWallMinutes: Optional[int] = None
    monthlyRentalCumulativeUsdCostMillicents: Optional[int] = None


@dataclass
class RentalCostLog:
    """com.etzhayyim.train.rentalCostLog record body."""

    createdAt: str
    rentalAttestationUri: str
    actualWallMinutes: int
    actualUsdCostMillicents: int              # = USD × 100000 per Lexicon
    outputCheckpointCid: str
    ipfsPinVerifyCid: str
    evalMetrics: EvalMetrics
    commitDecision: str  # "committed-to-registry" / "aborted-..."
    attestingDid: str
    registryEntry: Optional[str] = None
    councilRatificationRequired: bool = False
    councilRatificationTicketUri: Optional[str] = None
    postMortemNotes: Optional[str] = None


# ─── Charter Rider §2(a)-(h) scan ─────────────────────────────────────────


def charter_rider_scan(dataset_cids: list[str]) -> tuple[bool, str]:
    """Run etzhayyim_organism.sensors.charter_rider.scan() over each dataset.

    Returns (passed: bool, scan_report_cid: str). Raises if any dataset fails.

    R2.0: shells out to kotodama if importable; otherwise WARN + assume PASS
    (matches ADR-2605241500 ETZ_DATASET_CHARTER_STRICT=0 default).
    """
    logger.info("Charter Rider §2(a)-(h) scan over %d datasets", len(dataset_cids))
    try:
        from etzhayyim_organism.sensors.charter_rider import scan  # type: ignore
    except ImportError:
        logger.warning("kotodama not importable; scan SKIPPED (warn-only). Set ETZ_DATASET_CHARTER_STRICT=1 to fail-closed.")
        if os.environ.get("ETZ_DATASET_CHARTER_STRICT") == "1":
            raise RuntimeError("Charter Rider scan required but kotodama not importable (STRICT=1)")
        return True, "scan-skipped-kotodama-unavailable"

    # R2.0 stub: actual scan invocation lands at R2.1
    raise NotImplementedError("R2.1: invoke scan() per dataset, aggregate findings, pin report to IPFS, return CID")


# ─── PDS emit ─────────────────────────────────────────────────────────────


def publish_to_pds(record_lexicon: str, record_body: dict, *, dry_run: bool = True) -> str:
    """Publish a record to the religious-corp PDS.

    Returns AT URI of the published record (or a synthetic dryRun URI).

    R2.0 default = dry_run=True (no actual PDS emit; matches ADR-2605241500 default).
    Set dry_run=False after PDS integration lands (R2.1).
    """
    if dry_run:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        synth_uri = f"at://did:web:mac-260317.etzhayyim.com/{record_lexicon}/dryrun-{ts}"
        logger.info("[DRY RUN] Would publish %s: %s", record_lexicon, json.dumps(record_body, indent=2, default=str)[:500])
        logger.info("[DRY RUN] Synthetic AT URI: %s", synth_uri)
        return synth_uri

    raise NotImplementedError("R2.1: actual atproto repo.createRecord call with rkey=tid")


# ─── Vendor abstraction ───────────────────────────────────────────────────


class VendorBase:
    """Vendor interface. Concrete implementations land at R2.1 (RunPod) / R2.2 (Lambda / CoreWeave)."""

    def start_instance(self, gpu_model: str, gpu_count: int, image: str) -> "VendorInstance":
        raise NotImplementedError("R2.1 deliverable")


@dataclass
class VendorInstance:
    instance_id: str
    ip: str
    ssh_key_path: str
    started_at: datetime

    def upload(self, local_path: str, remote_path: str) -> None:
        raise NotImplementedError("R2.1: rsync/scp wrapper")

    def run(self, command: str, *, timeout_minutes: int = 1440) -> int:
        raise NotImplementedError("R2.1: ssh -o ServerAliveInterval=30 wrapper")

    def fetch(self, remote_path: str, local_path: str) -> None:
        raise NotImplementedError("R2.1: rsync wrapper from rented instance to mac-260317")

    def terminate_and_bill(self) -> float:
        """Returns actual USD cost from vendor."""
        raise NotImplementedError("R2.1: vendor API termination + billing query")


def get_vendor(vendor_name: str) -> VendorBase:
    """Factory for vendor instances."""
    # R2.1 will add: from .vendors.runpod import RunPodVendor; etc.
    raise NotImplementedError(f"R2.1: implement {vendor_name} vendor adapter")


# ─── IPFS pin via e7m-dataset ─────────────────────────────────────────────


def e7m_dataset_add(local_checkpoint_dir: str, subdataset_name: str) -> str:
    """Pin a local checkpoint dir to IPFS via e7m-dataset add (local-import path).

    Returns the resulting IPFS map CID.
    """
    logger.info("e7m-dataset add: %s as subdataset %s", local_checkpoint_dir, subdataset_name)
    cmd = [
        "e7m-dataset", "add",
        f"local://{local_checkpoint_dir}",  # local-import flavor
        "--name", subdataset_name,
        "--kind", "model-checkpoint",
        "--license", "apache-2.0-plus-charter-rider",  # moemoekyun output license
    ]
    env = {**os.environ, "ETZ_DATASET_ROOT": "/Volumes/260317/etzhayyim",
           "IPFS_PATH": "/Volumes/260317/etzhayyim/ipfs-data"}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"e7m-dataset add failed: {result.stderr}")
    # Parse trailing JSON line from stdout (per e7m-dataset CLI convention)
    last_json_line = result.stdout.strip().split("\n")[-1]
    out = json.loads(last_json_line)
    return out["map_cid"]


def e7m_dataset_verify(subdataset_name: str) -> str:
    """Verify IPFS bytes round-trip via e7m-dataset verify.

    Returns verification CID (or raises on mismatch).
    """
    logger.info("e7m-dataset verify: %s", subdataset_name)
    cmd = ["e7m-dataset", "verify", subdataset_name]
    env = {**os.environ, "ETZ_DATASET_ROOT": "/Volumes/260317/etzhayyim"}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"e7m-dataset verify FAILED: {result.stderr}")
    # R2.1: parse verify output for verification CID
    return "verify-pending-r2.1-parse"


# ─── Fleet eval (Mac mini split-role per ADR-2605262100 §5) ───────────────


def run_fleet_eval(checkpoint_cid: str, dataset_cids_eval: list[str]) -> EvalMetrics:
    """Trigger parallel eval on Murakumo Mac mini fleet.

    R2.0 stub: writes NDJSON queue entries for each bench cell (naphtali=langgraph-coding,
    simeon=HumanEval+, etc.) and polls for results. Actual cell handlers land at R2.1.
    """
    logger.info("Fleet eval: checkpoint %s against %d eval datasets", checkpoint_cid, len(dataset_cids_eval))
    raise NotImplementedError(
        "R2.1: NDJSON queue emit to each Mac mini cell + poll for bench result aggregation via asher cell"
    )


# ─── Commit gate (ADR-2605262100 §5.4 extended for R2+) ───────────────────


def commit_gate(baseline_metrics: EvalMetrics, post_train_metrics: EvalMetrics) -> str:
    """commit_node decision per ADR-2605262100 §5.4."""
    # Permille units (per Lexicon AT Protocol integer-only restriction):
    # +30 permille = +3pp threshold per ADR-2605262100 §5.4
    delta_lg = post_train_metrics.langgraph_coding_pass1_permille - baseline_metrics.langgraph_coding_pass1_permille
    delta_he = post_train_metrics.humanevalplus_pass1_permille - baseline_metrics.humanevalplus_pass1_permille
    post_train_metrics.delta_langgraph_coding_permille = delta_lg
    post_train_metrics.delta_humanevalplus_permille = delta_he

    if delta_he < 0:
        return "aborted-regression"  # G10 honest scoring: regression on HumanEval+ → mandatory abort
    if delta_lg >= 30:               # +30 permille = +3 percentage points
        return "committed-to-registry"
    return "aborted-delta-insufficient"


# ─── Main orchestrator ────────────────────────────────────────────────────


def run_rental_train(config: RentalConfig, *, dry_run: bool = True) -> RentalCostLog:
    """Orchestrate a single rental train run end-to-end.

    Phase 0: Pre-flight checks (Charter Rider scan + cost cap validation)
    Phase 1: rentalAttestation publish
    Phase 2: Vendor provision + train + checkpoint fetch
    Phase 3: IPFS pin + verify
    Phase 4: Fleet eval (Mac mini parallel)
    Phase 5: commit_gate decision
    Phase 6: rentalCostLog publish
    Phase 7: Vendor instance terminate
    """
    started_at = datetime.now(timezone.utc)
    logger.info("rental-orchestrator START at %s", started_at.isoformat())

    # ─── Phase 0: Pre-flight ──────────────────────────────────────────────
    if config.expected_wall_minutes > 1440:
        raise ValueError(f"Single session wall {config.expected_wall_minutes}min exceeds 24h cap per §2(i)(2)(5)")
    if config.expected_usd_cost_millicents > 20_000_000:  # $200 = 20M millicents
        raise ValueError(f"Single session cost ${config.expected_usd_cost_millicents/100000:.2f} exceeds $200 cap per ADR-2605262300 §6")
    if config.model_tier not in ("baien-server", "baien-XL"):
        raise ValueError(
            f"Tier '{config.model_tier}' not in scope of §2(i)(2)(6). "
            "Only baien-server-* / baien-XL-* permitted; other tiers REJECTED at pre-flight."
        )

    scan_pass, scan_report_cid = charter_rider_scan(
        config.dataset_cids_train + config.dataset_cids_eval
    )
    if not scan_pass:
        raise RuntimeError("Charter Rider §2(a)-(h) scan FAILED; aborting rental")

    # ─── Phase 1: rentalAttestation publish ───────────────────────────────
    attestation = RentalAttestation(
        createdAt=started_at.isoformat(),
        trainAdrRef=config.train_adr_ref,
        vendor=config.vendor,
        gpuModel=config.gpu_model,
        gpuCount=config.gpu_count,
        expectedWallMinutes=config.expected_wall_minutes,
        expectedUsdCostMillicents=config.expected_usd_cost_millicents,
        datasetCidsTrain=config.dataset_cids_train,
        datasetCidsEval=config.dataset_cids_eval,
        modelTier=config.model_tier,
        modelArtifactName=config.model_artifact_name,
        precisionMode=config.precision_mode,
        charterRiderScanPass=scan_pass,
        charterRiderScanRunCid=scan_report_cid,
        attestingDid=config.attesting_did,
    )
    attestation_uri = publish_to_pds(
        "com.etzhayyim.train.rentalAttestation",
        asdict(attestation),
        dry_run=dry_run,
    )

    # ─── Phase 2-5: Vendor provision + train + eval ───────────────────────
    if dry_run:
        logger.info("[DRY RUN] Skipping Phase 2-5 (vendor provision + train + eval)")
        # Synthesize zeroed cost log for dry-run path
        cost_log = RentalCostLog(
            createdAt=datetime.now(timezone.utc).isoformat(),
            rentalAttestationUri=attestation_uri,
            actualWallMinutes=0,
            actualUsdCostMillicents=0,
            outputCheckpointCid="dry-run-no-checkpoint",
            ipfsPinVerifyCid="dry-run-no-verify",
            evalMetrics=EvalMetrics(),
            commitDecision="aborted-engineering-failure",
            attestingDid=config.attesting_did,
            postMortemNotes="DRY RUN: orchestrator skeleton executed without vendor integration (R2.1 deliverable pending)",
        )
        publish_to_pds(
            "com.etzhayyim.train.rentalCostLog",
            asdict(cost_log),
            dry_run=True,
        )
        return cost_log

    vendor = get_vendor(config.vendor)
    instance = vendor.start_instance(config.gpu_model, config.gpu_count, image="moemoekyun-train:r2")
    try:
        # upload train config + code
        instance.upload(config.train_config_yaml, "/workspace/config.yaml")
        instance.upload(str(Path(__file__).parent.parent), "/workspace/baien-moemoekyun-train")
        # run train (poll until exit)
        exit_code = instance.run(
            f"python /workspace/baien-moemoekyun-train/src/baien_moemoekyun/train.py "
            f"--config /workspace/config.yaml",
            timeout_minutes=int(config.expected_wall_minutes * 1.5),  # 50% headroom
        )
        if exit_code != 0:
            raise RuntimeError(f"Train script exited {exit_code}")
        # fetch checkpoint
        local_ckpt_dir = f"/Volumes/260317/etzhayyim/checkpoints/{config.model_artifact_name}"
        os.makedirs(local_ckpt_dir, exist_ok=True)
        instance.fetch("/workspace/output", local_ckpt_dir)
        # IPFS pin
        checkpoint_cid = e7m_dataset_add(local_ckpt_dir, config.model_artifact_name)
        verify_cid = e7m_dataset_verify(config.model_artifact_name)
    finally:
        actual_cost = instance.terminate_and_bill()

    actual_wall = (datetime.now(timezone.utc) - started_at).total_seconds() / 60

    # ─── Phase 4: Fleet eval ───────────────────────────────────────────────
    # baseline metrics should be loaded from the pre-train snapshot (caller responsibility)
    baseline = EvalMetrics()  # TODO load from previous iter or base BitNet
    post_metrics = run_fleet_eval(checkpoint_cid, config.dataset_cids_eval)

    # ─── Phase 5: commit_gate ─────────────────────────────────────────────
    decision = commit_gate(baseline, post_metrics)

    # ─── Phase 6: rentalCostLog publish ───────────────────────────────────
    cost_log = RentalCostLog(
        createdAt=datetime.now(timezone.utc).isoformat(),
        rentalAttestationUri=attestation_uri,
        actualWallMinutes=int(round(actual_wall)),
        actualUsdCostMillicents=int(round(actual_cost * 100000)),
        outputCheckpointCid=checkpoint_cid,
        ipfsPinVerifyCid=verify_cid,
        evalMetrics=post_metrics,
        commitDecision=decision,
        attestingDid=config.attesting_did,
    )
    publish_to_pds(
        "com.etzhayyim.train.rentalCostLog",
        asdict(cost_log),
        dry_run=dry_run,
    )

    return cost_log


# ─── CLI ──────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to RentalConfig YAML")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Default: skip vendor provision + train + eval; emit dry-run AT URIs")
    parser.add_argument("--live", dest="dry_run", action="store_false",
                        help="Live execution (requires ADR-2605262200 effective + vendor SDK integration R2.1)")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    import yaml  # type: ignore
    with open(args.config) as f:
        config_dict = yaml.safe_load(f)
    config = RentalConfig(**config_dict)

    if not args.dry_run:
        logger.warning("LIVE mode — verify ADR-2605262200 amendment is effective and Council ratification recorded")

    cost_log = run_rental_train(config, dry_run=args.dry_run)
    print(json.dumps(asdict(cost_log), indent=2, default=str))


if __name__ == "__main__":
    main()
