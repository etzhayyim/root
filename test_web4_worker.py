import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import web4_worker_main

def test_web4_crud():
    actor = "test_actor"

    # Register Expert
    expert = web4_worker_main._create_expert_sync("Alice", "did:web:alice", "NLP", actor)
    exp_id = expert["expertId"]
    assert expert["status"] == "active"

    # List Experts
    experts = web4_worker_main._list_experts_sync(50, 0, actor)
    assert len(experts["experts"]) == 1
    assert experts["experts"][0]["id"] == exp_id

    # Update Expert
    updated = web4_worker_main._update_expert_sync(exp_id, "inactive", actor)
    assert updated["status"] == "inactive"

    # Submit Inference
    job = web4_worker_main._submit_inference_sync(exp_id, "model-v1", {"input": "test"}, actor)
    job_id = job["jobId"]
    assert job["status"] == "pending"

    # Get Inference Result
    res = web4_worker_main._get_inference_result_sync(job_id, actor)
    assert res["status"] == "pending"
    assert res["model"] == "model-v1"

    # List Jobs
    jobs = web4_worker_main._list_jobs_sync(50, 0, actor)
    assert len(jobs["jobs"]) == 1

    # Get Job Status
    status = web4_worker_main._get_job_status_sync(job_id, actor)
    assert status["status"] == "pending"

    # Cluster Stats
    stats = web4_worker_main._get_cluster_stats_sync(actor)
    # expert is inactive now, so activeExperts is 0
    assert stats["activeExperts"] == 0
    assert stats["totalJobs"] == 1

    print("web4_worker_main CRUD tests passed!")

if __name__ == "__main__":
    test_web4_crud()
