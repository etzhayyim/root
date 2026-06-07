import re

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    py_code = f.read()

# Replace conn -> client in signatures
py_code = py_code.replace("def datasource_tables_available(conn)", "def datasource_tables_available(client)")
py_code = py_code.replace("def get_facility_cursor(conn)", "def get_facility_cursor(client)")
py_code = py_code.replace("def mark_facility_raw(conn,", "def mark_facility_raw(client,")
py_code = py_code.replace("def mark_facility_b2(conn,", "def mark_facility_b2(client,")
py_code = py_code.replace("def replay_facilities_from_b2(conn)", "def replay_facilities_from_b2(client)")
py_code = py_code.replace("def replay_facilities_from_b2_locked(conn)", "def replay_facilities_from_b2_locked(client)")
py_code = py_code.replace("def insert_records(conn,", "def insert_records(client,")
py_code = py_code.replace("def fetch_pubmed(conn)", "def fetch_pubmed(client)")
py_code = py_code.replace("def fetch_clinical_trials(conn)", "def fetch_clinical_trials(client)")
py_code = py_code.replace("def ingest_dsm_categories(conn)", "def ingest_dsm_categories(client)")
py_code = py_code.replace("def ingest_facilities_csv(conn)", "def ingest_facilities_csv(client)")
py_code = py_code.replace("def run_target(conn,", "def run_target(client,")

# Replace calls
py_code = py_code.replace("datasource_tables_available(conn)", "datasource_tables_available(client)")
py_code = py_code.replace("get_facility_cursor(conn)", "get_facility_cursor(client)")
py_code = py_code.replace("coverage_rate(conn,", "coverage_rate(client,")
py_code = py_code.replace("set_cursor(conn,", "set_cursor(client,")
py_code = py_code.replace("get_cursor(conn,", "get_cursor(client,")
py_code = py_code.replace("insert_records(conn,", "insert_records(client,")
py_code = py_code.replace("fetch_pubmed(conn)", "fetch_pubmed(client)")
py_code = py_code.replace("fetch_clinical_trials(conn)", "fetch_clinical_trials(client)")
py_code = py_code.replace("ingest_dsm_categories(conn)", "ingest_dsm_categories(client)")
py_code = py_code.replace("ingest_facilities_csv(conn)", "ingest_facilities_csv(client)")
py_code = py_code.replace("replay_facilities_from_b2(conn)", "replay_facilities_from_b2(client)")
py_code = py_code.replace("replay_facilities_from_b2_locked(conn)", "replay_facilities_from_b2_locked(client)")
py_code = py_code.replace("run_target(conn,", "run_target(client,")

# Rewrite datasource_tables_available
py_code = re.sub(
    r'def datasource_tables_available\(client\) -> bool:.*?return True',
    '''def datasource_tables_available(client) -> bool:
    try:
        client.select_where("vertex_medical_facility_raw", "vertex_id", "test", limit=1)
        return True
    except Exception:
        return False''',
    py_code,
    flags=re.DOTALL
)

# Rewrite get_facility_cursor
py_code = re.sub(
    r'def get_facility_cursor\(client\) -> str:.*?return get_cursor\(client, "facilities_csv"\) or "0"',
    '''def get_facility_cursor(client) -> str:
    if datasource_tables_available(client):
        try:
            rows = client.select_where("vertex_medical_facility_raw", "raw_key", "", limit=100)
            rows.sort(key=lambda r: int(r.get("_seq") or 0), reverse=True)
            if rows and rows[0].get("raw_key"):
                return str(rows[0]["raw_key"])
        except Exception:
            pass
    return get_cursor(client, "facilities_csv") or "0"''',
    py_code,
    flags=re.DOTALL
)

# Rewrite mark_facility_raw
py_code = re.sub(
    r'def mark_facility_raw\(client,\n    raw_key: str,\n    hash_val: str,\n\) -> None:.*?conn\.commit\(\)',
    '''def mark_facility_raw(client,
    raw_key: str,
    hash_val: str,
) -> None:
    if not datasource_tables_available(client):
        return
    client.insert_row("vertex_medical_facility_raw", {
        "vertex_id": f"raw:{raw_key}",
        "_seq": 0,
        "raw_key": raw_key,
        "hash_val": hash_val,
        "updated_at": now_iso()
    })''',
    py_code,
    flags=re.DOTALL
)

# Rewrite mark_facility_b2
py_code = re.sub(
    r'def mark_facility_b2\(client,\n    raw_key: str,\n    b2_key: str,\n\) -> None:.*?conn\.commit\(\)',
    '''def mark_facility_b2(client,
    raw_key: str,
    b2_key: str,
) -> None:
    if not datasource_tables_available(client):
        return
    client.insert_row("vertex_medical_facility_b2", {
        "vertex_id": f"b2:{raw_key}",
        "_seq": 0,
        "raw_key": raw_key,
        "b2_key": b2_key,
        "updated_at": now_iso()
    })''',
    py_code,
    flags=re.DOTALL
)

# Rewrite the loop in main
py_code = re.sub(
    r'with connect\(\) as conn:\n        with conn\.cursor\(\) as cur:\n.*?inserted = replay_facilities_from_b2\(conn\)',
    '''client = connect()
    if REPLAY_FACILITIES:
        inserted = replay_facilities_from_b2(client)''',
    py_code,
    flags=re.DOTALL
)

# Fix run_target try-except blocks
py_code = re.sub(
    r'run_target\(client, name\)\n.*?conn\.rollback\(\)',
    '''run_target(client, name)
            except Exception as exc:
                log(f"[{name}] unhandled error: {exc}")''',
    py_code,
    flags=re.DOTALL
)
py_code = re.sub(
    r'set_cursor\(client, name, get_cursor\(client, name\), 0, coverage_rate\(client, TARGETS\[name\]\), str\(exc\)\[:512\]\)\n.*?conn\.rollback\(\)',
    '''set_cursor(client, name, get_cursor(client, name), 0, coverage_rate(client, TARGETS[name]), str(exc)[:512])''',
    py_code,
    flags=re.DOTALL
)

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.write(py_code)
