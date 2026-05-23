import asyncio
import os
import tempfile
import sys
from pathlib import Path

# Setup temp dir for organism SQLite
tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

# Add path so we can import pymagatama
sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import hub_worker_main

def test_hub_crud():
    actor = "test_actor"

    # Create Endpoint
    ep = hub_worker_main._create_endpoint_sync("Test EP", "http://test", "POST", "did:web:test", actor)
    ep_id = ep["endpointId"]
    assert ep["status"] == "active"

    # List Endpoints
    eps = hub_worker_main._list_endpoints_sync(50, 0, actor)
    assert eps["total"] == 1
    assert eps["endpoints"][0]["id"] == ep_id

    # Create Webhook
    wh = hub_worker_main._create_webhook_sync(ep_id, "http://webhook", ["*"], "did:web:test", actor)
    wh_id = wh["webhookId"]
    assert wh["status"] == "active"

    # List Webhooks (no filter)
    whs = hub_worker_main._list_webhooks_sync("", 50, 0, actor)
    assert whs["total"] == 1
    assert whs["webhooks"][0]["id"] == wh_id

    # List Webhooks (filter)
    whs_filtered = hub_worker_main._list_webhooks_sync(ep_id, 50, 0, actor)
    assert whs_filtered["total"] == 1
    assert whs_filtered["webhooks"][0]["endpoint_id"] == ep_id

    # Metrics
    metrics = hub_worker_main._get_metrics_sync(ep_id, actor)
    assert metrics["totalEndpoints"] == 1
    assert metrics["totalWebhooks"] == 1

    print("hub_worker_main CRUD tests passed!")

if __name__ == "__main__":
    test_hub_crud()
