import os

def fix_file(filepath, callback):
    with open(filepath, "r") as f:
        text = f.read()
    new_text = callback(text)
    if new_text != text:
        with open(filepath, "w") as f:
            f.write(new_text)

# hazelcast_bridge.py
def fix_hazelcast(text):
    text = text.replace('        if vtype == "PROCESS":\n                get_kotoba_client()',
                        '        if vtype == "PROCESS":\n            get_kotoba_client()')
    text = text.replace('        elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":\n                # Only store root-level events (not sub-elements)\n                pik = rec["process_instance_key"]\n                get_kotoba_client()',
                        '        elif vtype == "PROCESS_INSTANCE" and rec.get("bpmn_element_type") == "PROCESS":\n            # Only store root-level events (not sub-elements)\n            pik = rec["process_instance_key"]\n            get_kotoba_client()')
    text = text.replace('        elif vtype == "JOB":\n                get_kotoba_client()',
                        '        elif vtype == "JOB":\n            get_kotoba_client()')
    text = text.replace('        elif vtype == "INCIDENT":\n                get_kotoba_client()',
                        '        elif vtype == "INCIDENT":\n            get_kotoba_client()')
    text = text.replace('        elif vtype == "MESSAGE":\n                get_kotoba_client()',
                        '        elif vtype == "MESSAGE":\n            get_kotoba_client()')
    text = text.replace('        elif vtype == "VARIABLE":\n                get_kotoba_client()',
                        '        elif vtype == "VARIABLE":\n            get_kotoba_client()')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", fix_hazelcast)

# intel.py
def fix_intel(text):
    text = text.replace('    except Exception as e:  # noqa: BLE001\n        return {"error": f"intel.candidate.scan failed: {e}", "candidates": [], "count": 0}',
                        '    except Exception as e:  # noqa: BLE001\n        return {"error": f"intel.candidate.scan failed: {e}", "candidates": [], "count": 0}')
    return text
# Oh wait, intel.py line 215 had the error:
#     return {"resolvedEdges": edges, "count": len(edges), "runId": runId}
#     ^^^^^^
# SyntaxError: expected 'except' or 'finally' block
# In read_file of intel.py around line 210:
def fix_intel2(text):
    text = text.replace('    except Exception as e:  # noqa: BLE001\n        pass\n    try:\n        return {"error": f"intel.langgraph.resolve LLM failed: {e}", "resolvedEdges": [], "runId": runId}',
                        '    except Exception as e:  # noqa: BLE001\n        return {"error": f"intel.langgraph.resolve LLM failed: {e}", "resolvedEdges": [], "runId": runId}')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", fix_intel2)

# jp_fiscal.py
def fix_jp_fiscal(text):
    text = text.replace('            },\n        )\n                    written += 1',
                        '                        },\n                    )\n                    written += 1')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", fix_jp_fiscal)

# open_lei.py
def fix_open_lei(text):
    text = text.replace('from kotodama.kotoba_datomic import get_kotoba_client\n\n            kotoba_client = get_kotoba_client()',
                        'from kotodama.kotoba_datomic import get_kotoba_client\n\n    if True:\n        kotoba_client = get_kotoba_client()')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", fix_open_lei)

# patent.py
def fix_patent(text):
    text = text.replace('        get_kotoba_client().insert_rows(familyEdgeTable, kotoba_fam_rows)\n            family_edges += len(fam_rows)',
                        '        get_kotoba_client().insert_rows(familyEdgeTable, kotoba_fam_rows)\n        family_edges += len(fam_rows)')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", fix_patent)

print("Done")
