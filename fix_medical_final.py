import re

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    py_code = f.read()

py_code = re.sub(
    r'def insert_records\(client,.*?def is_retryable_rw_error',
    """def insert_records(client, rows: list[tuple[str, str, str, str, str, str, str, int, str]]) -> int:
    if not rows:
        return 0
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        medical_rows = [medical_row(r) for r in batch]
        edge_rows = [medical_source_edge(r) for r in batch]
        for attempt in range(RW_DML_RETRIES + 1):
            try:
                client.insert_rows("vertex_medical", medical_rows)
                client.insert_rows("edge_medical_source_record", edge_rows)
                break
            except Exception as exc:
                if attempt >= RW_DML_RETRIES or not is_retryable_rw_error(exc):
                    raise
                delay = retry_delay(attempt)
                log(f"[kotoba] DML retry {attempt + 1}/{RW_DML_RETRIES} after {delay:.1f}s: {exc}")
                time.sleep(delay)
        total += len(batch)
    return total

def is_retryable_rw_error""",
    py_code,
    flags=re.DOTALL
)

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.write(py_code)
