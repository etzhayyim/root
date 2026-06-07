import yaml
import re

for filepath in [
    "50-infra/k8s/bpmn-dispatcher/configmap-kotodama-cache-fix.yaml",
    "50-infra/k8s/bpmn-dispatcher/configmap-kotodama-sse-fix.yaml"
]:
    with open(filepath, "r") as f:
        data = yaml.safe_load(f)

    py_code = data["data"]["dispatcher_main.py"]

    py_code = re.sub(r'from kotodama\.db_sync import sync_cursor', 'from kotodama.kotoba_datomic import get_kotoba_client', py_code)

    data["data"]["dispatcher_main.py"] = py_code

    with open(filepath, "w") as f:
        yaml.dump(data, f)
