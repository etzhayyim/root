import os

# gov_chn
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", "r") as f:
    text = f.read()
# find the first occurrence of task_gov_chn_heartbeat_tick) and remove everything after
idx = text.find('    )(task_gov_chn_heartbeat_tick)')
if idx != -1:
    text = text[:idx + len('    )(task_gov_chn_heartbeat_tick)\n')]
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", "w") as f:
    f.write(text)

# jp_fiscal
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", "r") as f:
    lines = f.read().split('\n')
for i, line in enumerate(lines):
    if line.startswith('\t'):
        lines[i] = line.replace('\t', '    ')
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", "w") as f:
    f.write('\n'.join(lines))

# patent
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", "r") as f:
    text = f.read()
text = text.replace('        get_kotoba_client().insert_rows(familyEdgeTable, kotoba_fam_rows)\n            family_edges += len(fam_rows)',
                    '        get_kotoba_client().insert_rows(familyEdgeTable, kotoba_fam_rows)\n        family_edges += len(fam_rows)')
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", "w") as f:
    f.write(text)

# intel
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", "r") as f:
    text = f.read()
text = text.replace('        except Exception as e:  # noqa: BLE001\n        pass\n    try:\n        return {"error": f"intel.langgraph.resolve LLM failed: {e}", "resolvedEdges": [], "runId": runId}',
                    '    except Exception as e:  # noqa: BLE001\n        return {"error": f"intel.langgraph.resolve LLM failed: {e}", "resolvedEdges": [], "runId": runId}')
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", "w") as f:
    f.write(text)
