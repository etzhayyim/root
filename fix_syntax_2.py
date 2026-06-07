import os
import re

def fix_file(filepath, callback):
    with open(filepath, "r") as f:
        text = f.read()
    new_text = callback(text)
    if new_text != text:
        with open(filepath, "w") as f:
            f.write(new_text)

# 1. gmail_triage.py
def fix_gmail_triage(text):
    return text.replace('evidence_id = f"ev-{email_id}-{cls}"', 'evidence_id = "ev-" + email_id + "-" + cls')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/agents/gmail_triage.py", fix_gmail_triage)

# 2. gov_chl.py
def fix_gov_chl(text):
    idx = text.find('    )(task_gov_chl_heartbeat_tick)\n  timeout_ms=timeout_ms,')
    if idx != -1:
        text = text[:idx + len('    )(task_gov_chl_heartbeat_tick)\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chl.py", fix_gov_chl)

# 3. gov_chn.py
def fix_gov_chn(text):
    idx = text.find('    )(task_gov_chn_heartbeat_tick)\ntask_gov_chn_heartbeat_tick)')
    if idx != -1:
        text = text[:idx + len('    )(task_gov_chn_heartbeat_tick)\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", fix_gov_chn)

# 4. gov_civ.py
def fix_gov_civ(text):
    idx = text.find('    )(task_gov_civ_heartbeat_tick)\nartbeatTick",')
    if idx != -1:
        text = text[:idx + len('    )(task_gov_civ_heartbeat_tick)\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_civ.py", fix_gov_civ)

# 5. gov_irq.py
def fix_gov_irq(text):
    idx = text.find('    )(task_gov_irq_heartbeat_tick)\nimeout_ms=timeout_ms,')
    if idx != -1:
        text = text[:idx + len('    )(task_gov_irq_heartbeat_tick)\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_irq.py", fix_gov_irq)

# 6. hazelcast_bridge.py
def fix_hazelcast(text):
    return text.replace('            if vtype == "PROCESS":', '        if vtype == "PROCESS":')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", fix_hazelcast)

# 7. intel.py
def fix_intel(text):
    text = text.replace('    # R0: Multi-predicate WHERE', '    try:\n        # R0: Multi-predicate WHERE')
    text = text.replace('        for r in rows\n    ]\n    except Exception as e:', '            for r in rows\n        ]\n    except Exception as e:')
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", fix_intel)

# 8. jp_fiscal.py
def fix_jp_fiscal(text):
    text = text.replace('                try:\n                    get_kotoba_client().insert_row(', '                get_kotoba_client().insert_row(')
    text = text.replace('                            "evidence_url": evidence_url,\n                        },\n                    )', '                            "evidence_url": evidence_url,\n                        },\n                    )')
    # Just fix the try indent
    return text.replace('                try:\n                    get_kotoba_client()', '        try:\n            get_kotoba_client()')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", fix_jp_fiscal)

# 9. lawfirm_intake.py
def fix_lawfirm_intake(text):
    idx = text.find('    LOG.info("Registered tasks: lawfirm.intake.submit, lawfirm.matter.create")\nester_did,')
    if idx != -1:
        text = text[:idx + len('    LOG.info("Registered tasks: lawfirm.intake.submit, lawfirm.matter.create")\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/lawfirm_intake.py", fix_lawfirm_intake)

# 10. lawfirm_reply_record.py
def fix_lawfirm_reply_record(text):
    return text.replace('    if graph_event_id:\n    # R0:', '    if graph_event_id:\n        pass\n    # R0:')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/lawfirm_reply_record.py", fix_lawfirm_reply_record)

# 11. market.py
def fix_market(text):
    idx = text.find('        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)\ntzhayyim.market.wellKnownMarket": task_market_well_known,')
    if idx != -1:
        text = text[:idx + len('        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/market.py", fix_market)

# 12. myco_yeast.py
def fix_myco_yeast(text):
    return text.replace('    if total_flow < 100 or min_eta < 0.5:', '    except Exception:\n        pass\n    if total_flow < 100 or min_eta < 0.5:')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/myco_yeast.py", fix_myco_yeast)

# 13. open_lei.py
def fix_open_lei(text):
    return text.replace('                        except Exception as exc:', '                    except Exception as exc:')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", fix_open_lei)

# 14. open_unispsc.py
def fix_open_unispsc(text):
    return text.replace('    try:\n    except Exception as exc:', '    try:\n        pass\n    except Exception as exc:')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_unispsc.py", fix_open_unispsc)

# 15. os_app.py
def fix_os_app(text):
    return text.replace('        else:\n            raise ValueError', '        if False:\n            pass\n        else:\n            raise ValueError')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/os_app.py", fix_os_app)

# 16. oshikatsu_app.py
def fix_oshikatsu_app(text):
    idx = text.find('        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)\nFalse, timeout_ms=timeout_ms)(handler)')
    if idx != -1:
        text = text[:idx + len('        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)\n')]
    return text
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/oshikatsu_app.py", fix_oshikatsu_app)

# 17. patent.py
def fix_patent(text):
    return text.replace('            get_kotoba_client().insert_rows(edgeTable, kotoba_batch)', '        get_kotoba_client().insert_rows(edgeTable, kotoba_batch)')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", fix_patent)

# 18. wellbecoming_influence.py
def fix_wellbecoming(text):
    return text.replace('f\'"{d}"\' for d in agent_dids)}{"}"}', '\'"{}"\'.format(d) for d in agent_dids)} }')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/wellbecoming_influence.py", fix_wellbecoming)

# 19. training_export.py
def fix_training_export(text):
    return text.replace('def _run_export():\n\nif __name__', 'def _run_export():\n    pass\n\nif __name__')
fix_file("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_export.py", fix_training_export)

print("Done")
