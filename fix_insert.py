import re

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    py_code = f.read()

# Fix the broken medical_row function and update it to return dictionaries
py_code = re.sub(
    r'def medical_row.*?def parse_raw_ndjson',
    """def medical_row(record: tuple[str, str, str, str, str, str, str, int, str]) -> dict:
    uri, _cid, collection, rkey, repo, value_json, indexed_at, _ts_ms, created_at = record
    try:
        value = json.loads(value_json)
    except Exception:
        value = {}
    source = str(value.get("source") or "")
    category = collection.rsplit(".", 1)[-1]
    code = str(
        value.get("pmid")
        or value.get("trialId")
        or value.get("facilityId")
        or value.get("categoryName")
        or rkey
    )
    name = str(
        value.get("title")
        or value.get("briefTitle")
        or value.get("officialTitle")
        or value.get("name")
        or value.get("categoryName")
        or code
        or ""
    )
    description = str(value.get("fullJournalName") or value.get("taxonomy") or value.get("overallStatus") or "")
    standard = {
        "com.etzhayyim.apps.iryo.pubmedPaper": "PubMed",
        "com.etzhayyim.apps.iryo.rinshou": "ClinicalTrials.gov",
        "com.etzhayyim.apps.iryo.dsmCategory": "DSM",
        "com.etzhayyim.apps.iryo.shisetsu": "Healthcare facility",
    }.get(collection, "medical")
    
    return {
        "vertex_id": uri,
        "_seq": 0,
        "created_date": created_at[:10],
        "sensitivity_ord": 2,
        "owner_did": repo,
        "rkey": rkey,
        "repo": repo,
        "label": name[:256],
        "did": uri,
        "name": name[:1024],
        "display_name": name[:1024],
        "description": description[:4096],
        "category": category,
        "code": code[:512],
        "standard": standard,
        "effective_date": str(value.get("pubDate") or value.get("ingestedAt") or ""),
        "props": value_json,
        "collection": collection,
        "source": source,
        "source_id": source,
        "ingested_at": str(value.get("ingestedAt") or indexed_at),
        "created_at": created_at,
        "actor_did": ACTOR_DID,
        "org_did": ORG_DID
    }


def medical_source_edge(record: tuple[str, str, str, str, str, str, str, int, str]) -> dict:
    uri, cid, collection, rkey, _repo, value_json, indexed_at, _ts_ms, _created_at = record
    try:
        value = json.loads(value_json)
    except Exception:
        value = {}
    source_id = str(value.get("source") or "unknown")
    edge_id = f"medical-source-record:{source_id}:{cid or rkey}"
    return {
        "edge_id": edge_id,
        "source_id": source_id,
        "record_vid": uri,
        "collection": collection,
        "relation_kind": "emits_record",
        "created_at": indexed_at,
        "updated_at": indexed_at
    }


def parse_raw_ndjson""",
    py_code,
    flags=re.DOTALL
)

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.write(py_code)
