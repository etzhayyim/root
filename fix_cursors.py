import re

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    py_code = f.read()

py_code = re.sub(
    r'def get_cursor\(.*?return float\(row\[0\]\) if row and row\[0\] is not None else 0\.0\n.*?except Exception as exc:\n.*?conn\.rollback\(\)\n.*?if attempt >= RW_DML_RETRIES or not is_retryable_rw_error\(exc\):\n.*?raise.*?time\.sleep\(delay\)',
    """def get_cursor(client, key: str) -> str:
    rows = client.select_where("vertex_medical_coverage_cursor", "target_key", key, limit=1)
    if not rows:
        return ""
    return str(rows[0].get("cursor_value") or "")


def set_cursor(client, key: str, cursor_value: str, count: int, coverage: float, error: str | None = None) -> None:
    updated_at = now_iso()
    client.insert_row("vertex_medical_coverage_cursor", {
        "target_key": key,
        "cursor_value": cursor_value,
        "records_ingested": count,
        "last_coverage_rate": coverage,
        "last_error": error,
        "updated_at": updated_at,
        "actor_did": REPO,
        "org_did": "anon"
    })


def coverage_rate(client, target: dict[str, str]) -> float:
    for attempt in range(RW_DML_RETRIES + 1):
        try:
            rows = client.select_where("mv_world_collection_coverage_live", "collection", target["collection"], limit=5)
            filtered = [r for r in rows if r.get("domain") == target["domain"]]
            return float(filtered[0].get("coverage_rate") or 0.0) if filtered else 0.0
        except Exception as exc:
            if attempt >= RW_DML_RETRIES or not is_retryable_rw_error(exc):
                raise
            delay = retry_delay(attempt)
            log(f"[kotoba] read retry {attempt + 1}/{RW_DML_RETRIES} after {delay:.1f}s: {exc}")
            time.sleep(delay)""",
    py_code,
    flags=re.DOTALL
)

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.write(py_code)
