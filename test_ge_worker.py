import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import ge_worker_main

def test_ge_crud():
    actor = "test_actor"

    # Create Org
    org = ge_worker_main._create_org_sync("Test Org", "JP", "Tech", "did:web:test", actor)
    org_id = org["orgId"]
    assert org["status"] == "active"

    # List Orgs
    orgs = ge_worker_main._list_orgs_sync(50, 0, "JP", actor)
    assert orgs["total"] == 1
    assert orgs["orgs"][0]["id"] == org_id

    # Create Project
    proj = ge_worker_main._create_project_sync(org_id, "Project X", "Desc", "did:web:test", actor)
    proj_id = proj["projectId"]
    assert proj["status"] == "active"

    # List Projects
    projs = ge_worker_main._list_projects_sync(50, 0, org_id, actor)
    assert projs["total"] == 1
    assert projs["projects"][0]["id"] == proj_id

    # Assign Resource
    assign = ge_worker_main._assign_resource_sync(proj_id, "did:web:resource", "engineer", "did:web:test", actor)
    assign_id = assign["assignmentId"]
    assert assign["status"] == "assigned"

    # List Resources
    res = ge_worker_main._list_resources_sync(50, 0, proj_id, actor)
    assert res["total"] == 1
    assert res["resources"][0]["id"] == assign_id

    # Org Metrics
    metrics = ge_worker_main._get_org_metrics_sync(org_id, actor)
    assert metrics["projectCount"] == 1
    assert metrics["resourceCount"] == 1

    # Plan Workforce (stub)
    plan = ge_worker_main._plan_workforce_sync(org_id, 10, 6, actor)
    assert plan["targetHeadcount"] == 10

    print("ge_worker_main CRUD + JOIN metrics tests passed!")

if __name__ == "__main__":
    test_ge_crud()
