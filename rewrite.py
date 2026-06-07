with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("def assert_rw_health_gate()"):
        new_lines.append("def assert_rw_health_gate() -> str:\n")
        new_lines.append('    if not RW_HEALTH_GATE:\n')
        new_lines.append('        log("[kotoba-health] disabled by RW_HEALTH_GATE")\n')
        new_lines.append('        return "normal"\n')
        new_lines.append('    try:\n')
        new_lines.append('        from kotoba_datomic import get_kotoba_client\n')
        new_lines.append('        client = get_kotoba_client()\n')
        new_lines.append('        client.q("[:find ?e :where [?e :db/ident :db/ident]]")\n')
        new_lines.append('        log("[kotoba-health] OK")\n')
        new_lines.append('        return "normal"\n')
        new_lines.append('    except Exception as exc:\n')
        new_lines.append('        raise RuntimeError(f"kotoba health gate failed: {exc}")\n')
        new_lines.append('\n')
        skip = True
        continue
    
    if skip and line.startswith("def "):
        skip = False

    if not skip:
        new_lines.append(line)

with open("50-infra/k8s/medical-coverage-ingester/ingester.py", "w") as f:
    f.writelines(new_lines)
