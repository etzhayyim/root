import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import gov_worker_main

def test_gov_crud():
    actor = "test_actor"

    # Register Agency
    agency = gov_worker_main._register_agency_sync("Health Dept", "保健省", "Japan", "executive", "national", "07", "", "2000-01-01", "law1", "http", actor)
    agency_did = agency["did"]
    agency_id = agency["uri"].split("/")[-1]
    assert "uri" in agency

    # List Agencies
    agencies = gov_worker_main._list_agencies_sync("Japan", "", "", "", 50, 0, actor)
    assert agencies["total"] == 1

    # Get Agency
    ag = gov_worker_main._get_agency_sync(agency_id, actor)
    assert ag["agency"]["name"] == "Health Dept"

    # Record Official
    official = gov_worker_main._record_official_sync(agency_did, "did:web:person", "minister", "2020-01-01", "2024-01-01", "did:web:president", "appointment", actor)
    assert "uri" in official

    # List Officials
    officials = gov_worker_main._list_officials_sync(agency_did, "", 50, 0, actor)
    assert len(officials["officials"]) == 1

    # Submit Consult
    consult = gov_worker_main._submit_consult_sync("did:web:citizen", "healthcare", "info", "query", "13101", "normal", actor)
    consult_id = consult["id"]
    assert consult["status"] == "open"

    # List Consults
    consults = gov_worker_main._list_consults_sync("did:web:citizen", "", "", 50, 0, actor)
    assert len(consults["consults"]) == 1

    # List Municipalities
    munis = gov_worker_main._list_municipalities_sync("Tokyo", 50, 0, actor)
    assert len(munis["municipalities"]) == 0 # we didn't insert any

    print("gov_worker_main tests passed!")

if __name__ == "__main__":
    test_gov_crud()
