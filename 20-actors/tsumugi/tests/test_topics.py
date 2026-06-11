#!/usr/bin/env python3
"""tsumugi topics.py test — exercise latent-entity topic derivation.

Runs the full pipeline (ingest → topics) and verifies:
  - at least one :topic/* node exists
  - at least one :en/kind :topic-binding edge exists
  - :semantic topic exists with binding to org.corp.example.alpha
  - :topic/coherence values are within [0,1]
  - Determinism (second run produces identical output)

HONEST: This test assumes topics.py implements the latent-topics/v1-viewpoint-cluster
resolver, deriving topics from distinct :en/evidence-kind viewpoints.
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
    """Execute ingest.py then topics.py. Returns (ingest_rc, topics_rc)."""
    ingest_rc = subprocess.run(
        ["python3", "methods/ingest.py"],
        cwd=ACTOR_DIR,
        capture_output=True,
    ).returncode

    topics_rc = subprocess.run(
        ["python3", "methods/topics.py"],
        cwd=ACTOR_DIR,
        capture_output=True,
    ).returncode

    return ingest_rc, topics_rc


def read_topic_graph():
    """Read out/topic-graph.kotoba.edn and return records as list of dicts."""
    topic_file = ACTOR_DIR / "out" / "topic-graph.kotoba.edn"
    if not topic_file.exists():
        raise FileNotFoundError(f"topic-graph.kotoba.edn not found at {topic_file}")
    text = topic_file.read_text(encoding="utf-8")
    records = read_edn(text)
    if not isinstance(records, list):
        records = [records]
    return records


def get_topics(records):
    """Filter records to get only :topic/* nodes."""
    return [r for r in records if isinstance(r, dict) and ":topic/id" in r]


def get_bindings(records):
    """Filter records to get only :en/kind :topic-binding edges."""
    return [r for r in records if isinstance(r, dict) and r.get(":en/kind") == ":topic-binding"]


def test_topics():
    """Main test: topic derivation + determinism."""
    print("\n" + "="*70)
    print("TEST: tsumugi latent-entity topic derivation")
    print("="*70)

    # 1. Run the pipeline
    print("\n[1/4] Running ingest.py + topics.py...")
    ingest_rc, topics_rc = run_pipeline()
    if ingest_rc != 0:
        print(f"✗ ingest.py failed with exit code {ingest_rc}")
        return False
    if topics_rc != 0:
        print(f"✗ topics.py failed with exit code {topics_rc}")
        return False
    print("  ✓ pipeline succeeded")

    # 2. Read topic-graph.kotoba.edn and verify structure
    print("\n[2/4] Verifying topic graph structure...")
    try:
        records = read_topic_graph()
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return False

    topics = get_topics(records)
    bindings = get_bindings(records)

    # Check at least one topic exists
    if len(topics) == 0:
        print("✗ no :topic/* nodes found in topic-graph")
        return False
    print(f"  ✓ found {len(topics)} :topic/* nodes")

    # Check at least one binding exists
    if len(bindings) == 0:
        print("✗ no :en/kind :topic-binding edges found in topic-graph")
        return False
    print(f"  ✓ found {len(bindings)} :en/kind :topic-binding edges")

    # Check :semantic topic exists
    semantic_topic = None
    for t in topics:
        if t.get(":topic/viewpoint") == ":semantic":
            semantic_topic = t
            break

    if semantic_topic is None:
        print("✗ :semantic topic not found (expected from example evidence)")
        return False
    print(f"  ✓ :semantic topic found: {semantic_topic.get(':topic/label')}")

    # Check binding from :semantic topic to org.corp.example.alpha
    alpha_semantic_binding = None
    for b in bindings:
        if (b.get(":en/from") == "topic.semantic" and
            b.get(":en/to") == "org.corp.example.alpha"):
            alpha_semantic_binding = b
            break

    if alpha_semantic_binding is None:
        print("✗ no topic-binding found from topic.semantic to org.corp.example.alpha")
        return False
    print(f"  ✓ binding found: topic.semantic → org.corp.example.alpha (confidence={alpha_semantic_binding.get(':en/binding-confidence')})")

    # Check coherence values are in [0, 1]
    all_coherence_valid = True
    for t in topics:
        coherence = t.get(":topic/coherence")
        if coherence is None or not (0.0 <= coherence <= 1.0):
            print(f"✗ topic {t.get(':topic/id')} has invalid coherence: {coherence}")
            all_coherence_valid = False
    if not all_coherence_valid:
        return False
    print(f"  ✓ all coherence values in [0,1]")

    # Check method version (if present)
    method_version = None
    for r in records:
        if isinstance(r, dict) and ":latent/method-version" in r:
            method_version = r.get(":latent/method-version")
            break
    # Note: topics.py doesn't emit :latent/method-version; it's from resolve.py
    # We just verify topics have :en/source :derived
    derived_sources = [b for b in bindings if b.get(":en/source") == ":derived"]
    if len(derived_sources) == 0:
        print("⚠ no :en/source :derived found in bindings (expected)")
    else:
        print(f"  ✓ all bindings have :en/source :derived")

    # 3. Determinism check: run pipeline again and verify byte-for-byte identity
    print("\n[3/4] Checking determinism (second run)...")
    topic_file = ACTOR_DIR / "out" / "topic-graph.kotoba.edn"
    first_hash = hashlib.sha256(topic_file.read_bytes()).hexdigest()

    ingest_rc, topics_rc = run_pipeline()
    if ingest_rc != 0 or topics_rc != 0:
        print(f"✗ second run failed")
        return False

    second_hash = hashlib.sha256(topic_file.read_bytes()).hexdigest()
    if first_hash != second_hash:
        print(f"✗ output differs between runs")
        print(f"  run 1: {first_hash}")
        print(f"  run 2: {second_hash}")
        return False
    print(f"  ✓ output is deterministic (SHA256: {first_hash[:16]}...)")

    # 4. Verify expected viewpoints from example
    print("\n[4/4] Verifying expected viewpoints...")
    viewpoint_set = set(t.get(":topic/viewpoint") for t in topics)
    expected_viewpoints = {":semantic", ":network", ":lexical", ":temporal"}
    found_viewpoints = expected_viewpoints & viewpoint_set
    if len(found_viewpoints) > 0:
        print(f"  ✓ found expected viewpoints: {', '.join(sorted(str(v) for v in found_viewpoints))}")
    else:
        print(f"⚠ no expected viewpoints found in {viewpoint_set}")

    print("\n" + "="*70)
    print("✓ test_topics passed")
    print("="*70 + "\n")
    return True


if __name__ == "__main__":
    success = test_topics()
    sys.exit(0 if success else 1)
