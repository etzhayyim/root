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
    return text.replace('                        "source_url": record.get("sourceUrl"),',
                        '                "source_url": record.get("sourceUrl"),')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", fix_bunken_app)

# 2. business_manager_app.py
def fix_business_manager_app(text):
    return text.replace('                },\n        )\n        return {"uri": vid}',
                        '                },\n            )\n        return {"uri": vid}')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py", fix_business_manager_app)

# 3. gov_chn.py
def fix_gov_chn(text):
    return text.replace('\n.task(\n        task_type="xrpc.com.etzhayyim.govChn.followSiteDeps",',
                        '\n    worker.task(\n        task_type="xrpc.com.etzhayyim.govChn.followSiteDeps",')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", fix_gov_chn)

# 4. hazelcast_bridge.py
def fix_hazelcast(text):
    return text.replace('            elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":',
                        '        elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", fix_hazelcast)

# 5. jp_fiscal.py
def fix_jp_fiscal(text):
    return text.replace('                        },\n                    )',
                        '            },\n        )')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", fix_jp_fiscal)

# 6. open_lei.py
def fix_open_lei(text):
    return text.replace('                    except Exception as exc:\n                            skipped += 1\n                            errors.append(str(exc)[:120])',
                        '                    except Exception as exc:\n                        skipped += 1\n                        errors.append(str(exc)[:120])')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", fix_open_lei)

# 7. patent.py
def fix_patent(text):
    return text.replace('        get_kotoba_client().insert_rows(citationEdgeTable, kotoba_cit_rows)\n            citation_edges += len(cit_rows)',
                        '        get_kotoba_client().insert_rows(citationEdgeTable, kotoba_cit_rows)\n        citation_edges += len(cit_rows)')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", fix_patent)

# 8. intel.py
def fix_intel(text):
    text = text.replace('        except Exception as e:  # noqa: BLE001\n        pass\n    try:\n            return {"error": f"intel.run.create failed: {e}", "runId": run_id, "vertexId": vid}',
                        '        except Exception as e:  # noqa: BLE001\n            return {"error": f"intel.run.create failed: {e}", "runId": run_id, "vertexId": vid}')
    text = text.replace('    # R0: Multi-predicate WHERE and ORDER BY require raw Datalog (q)\n    rows = get_kotoba_client().q(',
                        '    try:\n        # R0: Multi-predicate WHERE and ORDER BY require raw Datalog (q)\n        rows = get_kotoba_client().q(')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", fix_intel)

print("Done")
