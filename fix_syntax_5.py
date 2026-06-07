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
    text = text.replace('        "source_url": record.get("sourceUrl"),\n                "title":',
                        '                "source_url": record.get("sourceUrl"),\n                "title":')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", fix_bunken_app)

# 2. business_manager_app.py
def fix_business_manager_app(text):
    # It might have tab/spaces mixed. Let's just normalize the indentations of that block
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('\t'):
            lines[i] = line.replace('\t', '    ')
    return '\n'.join(lines)
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py", fix_business_manager_app)

# 3. gov_bol.py
def fix_gov_bol(text):
    text = text.replace('     single_value=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_bol_heartbeat_tick)\n,\n        single_value=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_bol_heartbeat_tick)\nmeout_ms,\n    )(task_gov_bol_heartbeat_tick)\n', '')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_bol.py", fix_gov_bol)

# 4. gov_chn.py
def fix_gov_chn(text):
    text = text.replace('    worker    worker.task(', '    worker.task(')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", fix_gov_chn)

# 5. hazelcast_bridge.py
def fix_hazelcast(text):
    text = text.replace('            elif vtype == "JOB":', '        elif vtype == "JOB":')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", fix_hazelcast)

# 6. intel.py
def fix_intel(text):
    text = text.replace('    candidates = [\n        {\n            "vertexId":',
                        '        candidates = [\n            {\n                "vertexId":')
    text = text.replace('            "canonicalKey": r["canonical_key"], "label": r["label"],',
                        '                "canonicalKey": r["canonical_key"], "label": r["label"],')
    text = text.replace('            "lei": r["lei"], "jurisdiction": r["jurisdiction"],',
                        '                "lei": r["lei"], "jurisdiction": r["jurisdiction"],')
    text = text.replace('            "attributes": json.loads(r["attributes_json"] or "{}"),',
                        '                "attributes": json.loads(r["attributes_json"] or "{}"),')
    text = text.replace('        }\n        for r in rows\n    ]',
                        '            }\n            for r in rows\n        ]')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", fix_intel)

# 7. jp_fiscal.py
def fix_jp_fiscal(text):
    # Normalizing tabs
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('\t'):
            lines[i] = line.replace('\t', '    ')
    return '\n'.join(lines)
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", fix_jp_fiscal)

# 9. open_lei.py
def fix_open_lei(text):
    text = text.replace('                        except Exception as exc:', '                    except Exception as exc:')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", fix_open_lei)

# 10. patent.py
def fix_patent(text):
    text = text.replace('            rows_inserted += len(batch)\n            batch = []\n\n    if batch:\n            kotoba_batch = []',
                        '        rows_inserted += len(batch)\n        batch = []\n\n    if batch:\n        kotoba_batch = []')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", fix_patent)

# 11. wellbecoming_influence.py
def fix_wellbecoming(text):
    # To output #{"a" "b"}, we need #{{a_b}} in python.
    # The f-string is f"... [(contains? #{{ {expr} }} ?src_did)]"
    # But `{expr}` cannot contain spaces? No, it can.
    # The problem was `#{{ {" ".join(...) } }}` has `}}` next to each other.
    text = text.replace('[(contains? #{{ {" ".join(\'"{}"\'.format(d) for d in agent_dids)} }} ?src_did)]',
                        '[(contains? #{{ { " ".join(\'"{}"\'.format(d) for d in agent_dids) } }} ?src_did)]')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/wellbecoming_influence.py", fix_wellbecoming)

# 12. training_export.py
def fix_training_export(text):
    text = text.replace('def _to_jsonl_gz(records: list[dict[str, Any]]) -> bytes:\n\n\n# ──',
                        'def _to_jsonl_gz(records: list[dict[str, Any]]) -> bytes:\n    pass\n\n\n# ──')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_export.py", fix_training_export)

print("Done")
