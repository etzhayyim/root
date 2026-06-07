import re

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    py_code = f.read()

# Replace the giant assert_rw_health_gate with the kotoba version
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

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.write(py_code)
