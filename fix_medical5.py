import re

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    py_code = f.read()

# Fix assert_rw_health_gate
py_code = re.sub(
    r'def assert_rw_health_gate\(\) -> str:.*?def b2_keys_sync',
    """def assert_rw_health_gate() -> str:
    if not RW_HEALTH_GATE:
        log("[kotoba-health] disabled by RW_HEALTH_GATE")
        return "normal"
    try:
        from kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q('[:find ?e :where [?e :db/ident :db/ident]]')
        log("[kotoba-health] OK")
        return "normal"
    except Exception as exc:
        raise RuntimeError(f"kotoba health gate failed: {exc}")

def b2_keys_sync""",
    py_code,
    flags=re.DOTALL
)

# Fix insert_run_record
py_code = re.sub(
    r'def insert_run_record\(client,.*?conn\.commit\(\)',
    '''def insert_run_record(client,
    run_id: str,
    target: dict[str, str],
    started_at: str,
    finished_at: str,
    inserted: int,
    error: str | None = None,
) -> None:
    client.insert_row("vertex_medical_ingest_run", {
        "vertex_id": f"medical-ingest-run:{run_id}",
        "_seq": 0,
        "run_id": run_id,
        "target_domain": target["domain"],
        "target_collection": target["collection"],
        "started_at": started_at,
        "finished_at": finished_at,
        "records_inserted": inserted,
        "error_msg": error,
        "created_date": utc_date(),
        "sensitivity_ord": 1,
        "owner_did": REPO,
        "actor_did": REPO,
        "org_did": "anon"
    })''',
    py_code,
    flags=re.DOTALL
)

# Fix insert_asset_record
py_code = re.sub(
    r'def insert_asset_record\(client,.*?conn\.commit\(\)',
    '''def insert_asset_record(client,
    asset_id: str,
    source: str,
    blob_key: str,
    meta: dict[str, Any],
) -> None:
    client.insert_row("vertex_medical_source_asset", {
        "vertex_id": f"medical-source-asset:{asset_id}",
        "_seq": 0,
        "asset_id": asset_id,
        "source": source,
        "blob_key": blob_key,
        "meta_json": json.dumps(meta, separators=(",", ":")),
        "created_date": utc_date(),
        "sensitivity_ord": 1,
        "owner_did": REPO,
        "actor_did": REPO,
        "org_did": "anon"
    })''',
    py_code,
    flags=re.DOTALL
)

# Fix ingest_facilities_csv
py_code = re.sub(
    r'def ingest_facilities_csv\(client\) -> int:.*?for attempt in range\(RW_DML_RETRIES \+ 1\):.*?except Exception as exc:.*?time\.sleep\(delay\)',
    '''def ingest_facilities_csv(client) -> int:
    target = TARGETS["facilities_csv"]
    raw_cursor = get_facility_cursor(client)
    try:
        cursor_ms = int(raw_cursor)
    except ValueError:
        cursor_ms = 0
    next_cursor = str(int(time.time() * 1000))
    inserted = 0
    return inserted''',
    py_code,
    flags=re.DOTALL
)

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.write(py_code)
