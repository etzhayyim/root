#!/usr/bin/env python3
"""tsumugi fission_gate.py test — exercise covenant-claim PROPOSAL generation.

Runs the full pipeline (ingest → resolve → fission_gate) and verifies:
  - org.corp.example.alpha (fission-ready) → :proposal/status ":awaiting-council"
  - org.corp.example.beta (candidate) → NOT in proposals
  - org.corp.example.gamma (observed) → NOT in proposals
  - --execute flag REFUSED with exit code ≠ 0 and message contains "REFUSED"
  - Determinism (second run produces identical output)

HONEST: This test assumes fission_gate.py is observer-only and emits proposals for
Council review only. No DID is minted. No server key is held.
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
    """Execute ingest.py, resolve.py, then fission_gate.py. Returns (ingest_rc, resolve_rc, fission_rc)."""
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

    fission_rc = subprocess.run(
        ["python3", "methods/fission_gate.py"],
        cwd=ACTOR_DIR,
        capture_output=True,
    ).returncode

    return ingest_rc, resolve_rc, fission_rc


def read_fission_proposals():
    """Read out/fission-proposals.kotoba.edn and return records as list of dicts."""
    proposals_file = ACTOR_DIR / "out" / "fission-proposals.kotoba.edn"
    if not proposals_file.exists():
        raise FileNotFoundError(f"fission-proposals.kotoba.edn not found at {proposals_file}")
    text = proposals_file.read_text(encoding="utf-8")
    records = read_edn(text)
    if not isinstance(records, list):
        records = [records]
    return records


def get_proposal_by_organism(proposals, organism_id):
    """Find the proposal record for the given organism ID."""
    for rec in proposals:
        if isinstance(rec, dict) and rec.get(":proposal/organism") == organism_id:
            return rec
    return None


def test_fission_gate():
    """Main test: proposal generation + refusal of --execute + determinism."""
    print("\n" + "="*70)
    print("TEST: tsumugi covenant-claim PROPOSAL observer")
    print("="*70)

    # 1. Run the full pipeline
    print("\n[1/5] Running ingest.py + resolve.py + fission_gate.py...")
    ingest_rc, resolve_rc, fission_rc = run_pipeline()
    if ingest_rc != 0:
        print(f"✗ ingest.py failed with exit code {ingest_rc}")
        return False
    if resolve_rc != 0:
        print(f"✗ resolve.py failed with exit code {resolve_rc}")
        return False
    if fission_rc != 0:
        print(f"✗ fission_gate.py failed with exit code {fission_rc}")
        return False
    print("  ✓ pipeline succeeded")

    # 2. Read fission-proposals.kotoba.edn and verify alpha appears with :awaiting-council
    print("\n[2/5] Verifying covenant-claim proposals...")
    try:
        proposals = read_fission_proposals()
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return False

    # Check alpha → :proposal/status ":awaiting-council"
    alpha_proposal = get_proposal_by_organism(proposals, "org.corp.example.alpha")
    if not alpha_proposal:
        print("✗ org.corp.example.alpha not found in fission-proposals")
        return False
    alpha_status = alpha_proposal.get(":proposal/status")
    alpha_kind = alpha_proposal.get(":proposal/kind")
    if alpha_status != ":awaiting-council":
        print(f"✗ alpha status is {alpha_status}, expected :awaiting-council")
        return False
    if alpha_kind != ":covenant-claim-review":
        print(f"✗ alpha kind is {alpha_kind}, expected :covenant-claim-review")
        return False
    alpha_existence = alpha_proposal.get(":proposal/existence")
    print(f"  ✓ alpha → :proposal/status :awaiting-council (existence={alpha_existence:.3f})")

    # Check beta → NOT in proposals
    beta_proposal = get_proposal_by_organism(proposals, "org.corp.example.beta")
    if beta_proposal:
        print("✗ org.corp.example.beta should NOT be in proposals (:candidate, not :fission-ready)")
        return False
    print("  ✓ beta NOT in proposals (:candidate)")

    # Check gamma → NOT in proposals
    gamma_proposal = get_proposal_by_organism(proposals, "org.corp.example.gamma")
    if gamma_proposal:
        print("✗ org.corp.example.gamma should NOT be in proposals (:observed, not :fission-ready)")
        return False
    print("  ✓ gamma NOT in proposals (:observed)")

    # 3. Test --execute flag refusal (must exit non-zero with "REFUSED" in message)
    print("\n[3/5] Testing --execute flag refusal...")
    result = subprocess.run(
        ["python3", "methods/fission_gate.py", "--execute"],
        cwd=ACTOR_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"✗ fission_gate.py --execute should exit with non-zero code, got {result.returncode}")
        return False
    stderr = result.stderr
    stdout = result.stdout
    combined = (stderr + stdout).lower()
    if "refused" not in combined:
        print(f"✗ --execute should print/stderr 'REFUSED', got:\n  stdout: {stdout}\n  stderr: {stderr}")
        return False
    print(f"  ✓ --execute correctly REFUSED (exit code {result.returncode})")

    # 4. Test with TSUMUGI_OPERATOR_GATE present: still should refuse
    print("\n[4/5] Testing --execute with TSUMUGI_OPERATOR_GATE env (still REFUSED)...")
    env = os.environ.copy()
    env["TSUMUGI_OPERATOR_GATE"] = "fake-council-token"
    result = subprocess.run(
        ["python3", "methods/fission_gate.py", "--execute"],
        cwd=ACTOR_DIR,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        print(f"✗ fission_gate.py --execute should REFUSE even with gate set")
        return False
    stderr = result.stderr
    stdout = result.stdout
    combined = (stderr + stdout).lower()
    if "refused" not in combined:
        print(f"✗ should still refuse with gate present, got:\n  stdout: {stdout}\n  stderr: {stderr}")
        return False
    print(f"  ✓ --execute correctly REFUSED even with TSUMUGI_OPERATOR_GATE (exit code {result.returncode})")

    # 5. Determinism check: run pipeline again and verify byte-for-byte identity
    print("\n[5/5] Checking determinism (second run)...")
    proposals_file = ACTOR_DIR / "out" / "fission-proposals.kotoba.edn"
    first_hash = hashlib.sha256(proposals_file.read_bytes()).hexdigest()

    ingest_rc, resolve_rc, fission_rc = run_pipeline()
    if ingest_rc != 0 or resolve_rc != 0 or fission_rc != 0:
        print(f"✗ second pipeline run failed")
        return False

    second_hash = hashlib.sha256(proposals_file.read_bytes()).hexdigest()
    if first_hash != second_hash:
        print(f"✗ output differs between runs")
        print(f"  run 1: {first_hash}")
        print(f"  run 2: {second_hash}")
        return False
    print(f"  ✓ output is deterministic (SHA256: {first_hash[:16]}...)")

    print("\n" + "="*70)
    print("✓ test_fission_gate passed")
    print("="*70 + "\n")
    return True


if __name__ == "__main__":
    success = test_fission_gate()
    sys.exit(0 if success else 1)
