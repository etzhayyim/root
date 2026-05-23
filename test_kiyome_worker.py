import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import kiyome_worker_main

def test_kiyome_crud():
    actor = "test_actor"

    # Submit Clearance
    clearance = kiyome_worker_main._submit_clearance_sync("did:web:subject", "security", "Check", "did:web:owner", actor)
    clearance_id = clearance["clearanceId"]
    assert clearance["status"] == "pending"

    # List Clearances
    clearances = kiyome_worker_main._list_clearances_sync(50, 0, "pending", actor)
    assert clearances["total"] == 1

    # Approve Clearance
    appr = kiyome_worker_main._approve_clearance_sync(clearance_id, "did:web:approver", actor)
    assert appr["status"] == "approved"

    # Reject Clearance
    clearance2 = kiyome_worker_main._submit_clearance_sync("did:web:subject", "security", "Check 2", "did:web:owner", actor)
    rej = kiyome_worker_main._reject_clearance_sync(clearance2["clearanceId"], "failed", actor)
    assert rej["status"] == "rejected"

    # Create Audit Log
    log = kiyome_worker_main._create_audit_log_sync("did:web:actor", "read", "res1", "did:web:owner", actor)
    assert "logId" in log

    # List Audit Logs
    logs = kiyome_worker_main._list_audit_logs_sync(50, 0, "did:web:actor", actor)
    assert logs["total"] == 1

    # Compliance Status
    comp = kiyome_worker_main._get_compliance_status_sync("did:web:subject", actor)
    assert comp["approvedClearances"] == 1
    assert comp["rejectedClearances"] == 1
    assert comp["pendingClearances"] == 0
    assert comp["compliant"] == True

    print("kiyome_worker_main tests passed!")

if __name__ == "__main__":
    test_kiyome_crud()
