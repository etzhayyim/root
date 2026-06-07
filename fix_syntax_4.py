import re
import os

def fix_file(filepath, callback):
    with open(filepath, "r") as f:
        text = f.read()
    new_text = callback(text)
    if new_text != text:
        with open(filepath, "w") as f:
            f.write(new_text)

# 1. bunken_app.py
def fix_bunken_app(text):
    text = text.replace('                "actor_id": "bunken",\n                "sensitivity_ord": 2,\n                "owner_did": APP_DID,\n            }\n            get_kotoba_client().insert_row(',
                        '        "actor_id": "bunken",\n        "sensitivity_ord": 2,\n        "owner_did": APP_DID,\n    }\n    get_kotoba_client().insert_row(')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", fix_bunken_app)

# 2. business_manager_app.py
def fix_business_manager_app(text):
    text = text.replace('            )\n            return {"uri": vid}\n        if kind == "invoice":',
                        '        )\n        return {"uri": vid}\n    if kind == "invoice":')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py", fix_business_manager_app)

# 3. gov_bol.py
def fix_gov_bol(text):
    text = text.replace('     single_value=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_bol_heartbeat_tick)',
                        '        single_value=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_bol_heartbeat_tick)')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_bol.py", fix_gov_bol)

# 4. gov_chn.py
def fix_gov_chn(text):
    text = text.replace('.task(\n        task_type="xrpc.com.etzhayyim.govChn.followSiteDeps",',
                        '    worker.task(\n        task_type="xrpc.com.etzhayyim.govChn.followSiteDeps",')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", fix_gov_chn)

# 5. hazelcast_bridge.py
def fix_hazelcast(text):
    text = text.replace('            elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":',
                        '        elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", fix_hazelcast)

# 6. intel.py
def fix_intel(text):
    text = text.replace('    try:\n        # R0: Multi-predicate WHERE and ORDER BY require raw Datalog (q)\n    rows = get_kotoba_client().q(\n        query_edn=sql,\n        args=tuple(args),\n    ) or []',
                        '    try:\n        # R0: Multi-predicate WHERE and ORDER BY require raw Datalog (q)\n        rows = get_kotoba_client().q(\n            query_edn=sql,\n            args=tuple(args),\n        ) or []')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", fix_intel)

# 7. jp_fiscal.py
def fix_jp_fiscal(text):
    text = text.replace('                get_kotoba_client().insert_row(\n                        "vertex_jp_fiscal_beneficial_owner",',
                        '        get_kotoba_client().insert_row(\n            "vertex_jp_fiscal_beneficial_owner",')
    text = text.replace('                            "vertex_id": vid,', '                "vertex_id": vid,')
    text = text.replace('                            "created_date": target_date,', '                "created_date": target_date,')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", fix_jp_fiscal)

# 8. lawfirm_reply_record.py
def fix_lawfirm_reply_record(text):
    text = text.replace('    existing = [{"vertex_id": item[0]} for item in existing_raw]\n        if existing:',
                        '    existing = [{"vertex_id": item[0]} for item in existing_raw]\n    if existing:')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/lawfirm_reply_record.py", fix_lawfirm_reply_record)

# 9. open_lei.py
def fix_open_lei(text):
    text = text.replace('                    except Exception as exc:\n                            skipped += 1',
                        '                    except Exception as exc:\n                        skipped += 1')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", fix_open_lei)

# 10. patent.py
def fix_patent(text):
    text = text.replace('        get_kotoba_client().insert_rows(edgeTable, kotoba_batch)\n            rows_inserted += len(batch)\n            batch = []\n\n    if batch:\n            kotoba_batch = []',
                        '        get_kotoba_client().insert_rows(edgeTable, kotoba_batch)\n        rows_inserted += len(batch)\n        batch = []\n\n    if batch:\n        kotoba_batch = []')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", fix_patent)

# 11. wellbecoming_influence.py
def fix_wellbecoming(text):
    text = text.replace('[(contains? #{"{"}" ".join(\'"{}"\'.format(d) for d in agent_dids)} } ?src_did)]',
                        '[(contains? #{{ {" ".join(\'"{}"\'.format(d) for d in agent_dids)} }} ?src_did)]')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/wellbecoming_influence.py", fix_wellbecoming)

# 12. training_export.py
def fix_training_export(text):
    # Find `def _run_export():` and add `pass`
    text = re.sub(r'def _run_export\(\):\s*if __name__', 'def _run_export():\n    pass\n\nif __name__', text)
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_export.py", fix_training_export)

print("Done")
