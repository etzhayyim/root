import re

def fix(path, cb):
    with open(path) as f: t = f.read()
    nt = cb(t)
    if nt != t:
        with open(path, "w") as f: f.write(nt)

# bunken_app
def fb(t):
    return re.sub(r'\n            job_row = \{\n                "vertex_id": vertex_id,',
                  r'\n    job_row = {\n        "vertex_id": vertex_id,', t)
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py", fb)

# business_manager_app.py
def fbm(t):
    t = t.replace('            )\n            return {"uri": vid}\n        if kind == "invoice":',
                  '        )\n        return {"uri": vid}\n    if kind == "invoice":')
    return t
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py", fbm)

# gov_bol
def fgb(t):
    t = t.replace('    )(task_gov_bol_heartbeat_tick)\ns=timeout_ms,\n    )(task_gov_bol_follow_site_deps)',
                  '    )(task_gov_bol_heartbeat_tick)\n    worker.task(task_type="xrpc.com.etzhayyim.govBol.followSiteDeps", single_value=False, timeout_ms=timeout_ms)(task_gov_bol_follow_site_deps)')
    return t
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_bol.py", fgb)

# gov_chn.py
def fgc(t):
    t = t.replace('    )(task_gov_chn_heartbeat_tick)\ntask_gov_chn_heartbeat_tick)\nlue=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_chn_heartbeat_tick)\ntask_gov_chn_heartbeat_tick)\nnka)',
                  '    )(task_gov_chn_heartbeat_tick)')
    t = t.replace('    worker.task(\n        task_type="xrpc.com.etzhayyim.govChn.heartbeatTick",\n        single_value=False,\n        timeout_ms=timeout_ms,\n    )(task_gov_chn_heartbeat_tick)\ntask_gov_chn_heartbeat_tick)',
                  '')
    return t
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py", fgc)

# hazelcast_bridge.py
def fhb(t):
    t = t.replace('            if vtype == "PROCESS":', '        if vtype == "PROCESS":')
    return t
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py", fhb)

# jp_fiscal
def fjp(t):
    t = t.replace('                try:\n                    get_kotoba_client().insert_row(',
                  '        try:\n            get_kotoba_client().insert_row(')
    t = t.replace('                try:\n                    sync_cursor().execute(',
                  '        try:\n            sync_cursor().execute(') # In origin/main it's sync_cursor
    return t
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py", fjp)

# open_lei
def folei(text):
    return text.replace('                        except Exception as exc:', '                    except Exception as exc:')
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py", folei)

# patent
def fp(t):
    return t.replace('            get_kotoba_client().insert_rows', '        get_kotoba_client().insert_rows').replace('            sync_cursor().executemany', '        sync_cursor().executemany')
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py", fp)

# intel
def fi(t):
    return t.replace('    except Exception as e:  # noqa: BLE001', '    except Exception as e:  # noqa: BLE001\n        pass\n    try:')
fix("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py", fi)

