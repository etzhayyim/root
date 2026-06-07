import re

# Fix bunken_app.py
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", "r") as f:
    text = f.read()
text = re.sub(r'        "id": record\.get\("id"\),\n                "scheme":', r'        "id": record.get("id"),\n        "scheme":', text)
text = text.replace('                "source_url"', '        "source_url"')
text = text.replace('                "source_domain"', '        "source_domain"')
text = text.replace('                "crawl_id"', '        "crawl_id"')
text = text.replace('                "status"', '        "status"')
text = text.replace('                "discovered_count"', '        "discovered_count"')
text = text.replace('                "registered_count"', '        "registered_count"')
text = text.replace('                "started_at"', '        "started_at"')
text = text.replace('                "completed_at"', '        "completed_at"')
text = text.replace('                "error"', '        "error"')
text = text.replace('                "org_id"', '        "org_id"')
text = text.replace('                "user_id"', '        "user_id"')
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", "w") as f:
    f.write(text)

# Fix gov_bol.py
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_bol.py", "r") as f:
    text = f.read()
text = text.replace("    )(task_gov_bol_heartbeat_tick)\ns=timeout_ms,\n    )(task_gov_bol_follow_site_deps)", 
                    "    )(task_gov_bol_heartbeat_tick)\n    worker.task(\n        task_type=\"xrpc.com.etzhayyim.govBol.followSiteDeps\",\n        single_value=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_bol_follow_site_deps)")
with open("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_bol.py", "w") as f:
    f.write(text)
