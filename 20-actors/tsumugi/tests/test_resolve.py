#!/usr/bin/env python3
"""tsumugi resolve.py test — exercise latent-entity frontier classification.

Runs the full pipeline (ingest → resolve) and verifies:
  - alpha → :fission-ready (existence >= 0.7, distinct-kind-count >= 2, edges >= 2)
  - beta → :candidate (existence >= 0.4, count >= 1)
  - gamma → :observed (existence < 0.4)
  - Determinism (second run produces identical output)

HONEST: This test assumes resolve.py implements the latent-resolve/v1-noisy-or classifier.
"""
import sys
import os
import pathlib
import subprocess
import hashlib

# Locate the actor directory (parent's parent of this file)
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
METHODS_DIR = ACTOR_DIR / "methods"

# Add methods dir to path so we can import analyze.read_edn
sys.path.insert(0, str(METHODS_DIR))

try:
    from analyze import read_edn
except ImportError as e:
    sys.exit(f"ERROR: Could not import analyze.read_edn from {METHODS_DIR}: {e}")


def run_pipeline():
    """Execute ingest.py then resolve.py. Returns (ingest_rc, resolve_rc)."""
    ingest_rc = subprocess.run(
        ["python3", "methods/ingest.py"],
        cwd=ACTOR_DIR,
        capture_output=True,
    ).returncode

    resolve_rc = subprocess.run(
        ["python3", "methods/resolve.py"],
        cwd=ACTOR_DIR,
        capture_output=True,
    ).returncode

    return ingest_rc, resolve_rc


def read_latent_frontier():
    """Read out/latent-frontier.kotoba.edn and return records as list of dicts."""
    frontier_file = ACTOR_DIR / "out" / "latent-frontier.kotoba.edn"
    if not frontier_file.exists():
        raise FileNotFoundError(f"latent-frontier.kotoba.edn not found at {frontier_file}")
    text = frontier_file.read_text(encoding="utf-8")
    records = read_edn(text)
    if not isinstance(records, list):
        records = [records]
    return records


def get_frontier_record(records, organism_id):
    """Find the latent frontier record for the given organism ID."""
    for rec in records:
        if isinstance(rec, dict) and rec.get(":latent/organism") == organism_id:
            return rec
    return None


def test_resolve():
    """Main test: frontier classification + determinism."""
    print("\n" + "="*70)
    print("TEST: tsumugi latent-entity frontier resolver")
    print("="*70)

    # 1. Run the pipeline
    print("\n[1/3] Running ingest.py + resolve.py...")
    ingest_rc, resolve_rc = run_pipeline()
    if ingest_rc != 0:
        print(f"✗ ingest.py failed with exit code {ingest_rc}")
        return False
    if resolve_rc != 0:
        print(f"✗ resolve.py failed with exit code {resolve_rc}")
        return False
    print("  ✓ pipeline succeeded")

    # 2. Read latent-frontier.kotoba.edn and verify classifications
    print("\n[2/3] Verifying frontier classifications...")
    try:
        records = read_latent_frontier()
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return False

    # Check alpha → :fission-ready
    alpha_rec = get_frontier_record(records, "org.corp.example.alpha")
    if not alpha_rec:
        print("✗ org.corp.example.alpha not found in latent-frontier")
        return False
    alpha_frontier = alpha_rec.get(":latent/frontier")
    alpha_existence = alpha_rec.get(":latent/existence")
    if alpha_frontier != ":fission-ready":
        print(f"✗ alpha frontier is {alpha_frontier}, expected :fission-ready")
        return False
    if not (alpha_existence and alpha_existence >= 0.7):
        print(f"✗ alpha existence is {alpha_existence}, expected >= 0.7")
        return False
    print(f"  ✓ alpha → :fission-ready (existence={alpha_existence:.3f})")

    # Check beta → :candidate
    beta_rec = get_frontier_record(records, "org.corp.example.beta")
    if not beta_rec:
        print("✗ org.corp.example.beta not found in latent-frontier")
        return False
    beta_frontier = beta_rec.get(":latent/frontier")
    if beta_frontier != ":candidate":
        print(f"✗ beta frontier is {beta_frontier}, expected :candidate")
        return False
    print(f"  ✓ beta → :candidate (existence={beta_rec.get(':latent/existence'):.3f})")

    # Check gamma → :observed
    gamma_rec = get_frontier_record(records, "org.corp.example.gamma")
    if not gamma_rec:
        print("✗ org.corp.example.gamma not found in latent-frontier")
        return False
    gamma_frontier = gamma_rec.get(":latent/frontier")
    if gamma_frontier != ":observed":
        print(f"✗ gamma frontier is {gamma_frontier}, expected :observed")
        return False
    print(f"  ✓ gamma → :observed (existence={gamma_rec.get(':latent/existence'):.3f})")

    # Check method version
    method_version = None
    for rec in records:
        if isinstance(rec, dict) and ":latent/method-version" in rec:
            method_version = rec.get(":latent/method-version")
            break
    if method_version != "latent-resolve/v1-noisy-or":
        print(f"⚠ method-version is {method_version}, expected latent-resolve/v1-noisy-or")
    else:
        print(f"  ✓ method-version = {method_version}")

    # 3. Determinism check: run pipeline again and verify byte-for-byte identity
    print("\n[3/3] Checking determinism (second run)...")
    frontier_file = ACTOR_DIR / "out" / "latent-frontier.kotoba.edn"
    first_hash = hashlib.sha256(frontier_file.read_bytes()).hexdigest()

    ingest_rc, resolve_rc = run_pipeline()
    if ingest_rc != 0 or resolve_rc != 0:
        print(f"✗ second run failed")
        return False

    second_hash = hashlib.sha256(frontier_file.read_bytes()).hexdigest()
    if first_hash != second_hash:
        print(f"✗ output differs between runs")
        print(f"  run 1: {first_hash}")
        print(f"  run 2: {second_hash}")
        return False
    print(f"  ✓ output is deterministic (SHA256: {first_hash[:16]}...)")

    print("\n" + "="*70)
    print("✓ test_resolve passed")
    print("="*70 + "\n")
    return True


if __name__ == "__main__":
    success = test_resolve()
    sys.exit(0 if success else 1)
