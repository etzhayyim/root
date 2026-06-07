import re
import os

files = [
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/bunken_app.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/business_manager_app.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_bol.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/gov_chn.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/hazelcast_bridge.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/intel.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/jp_fiscal.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_lei.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/patent.py",
    "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/training_export.py",
]

for path in files:
    with open(path, "r") as f:
        code = f.read()

    if "sync_cursor" not in code:
        continue
        
    orig = code

    # 1. Imports
    code = re.sub(r'^[ \t]*from kotodama\.db_sync import sync_cursor\b.*$\n?', '', code, flags=re.MULTILINE)
    if "from kotodama.kotoba_datomic import get_kotoba_client" not in code:
        if "__future__" in code:
            code = re.sub(r'^(from __future__ import .*?)$', r'\1\nfrom kotodama.kotoba_datomic import get_kotoba_client', code, flags=re.MULTILINE)
        else:
            code = re.sub(r'^(import|from)\s+', r'from kotodama.kotoba_datomic import get_kotoba_client\n\1 ', code, count=1, flags=re.MULTILINE)

    # 2. block
    code = re.sub(r'^(\s*)with (?:_)?sync_cursor\(\) as (\w+):', r'\1if True:\n\1    client = get_kotoba_client()', code, flags=re.MULTILINE)

    # 3. execution
    code = re.sub(r'\b\w+\.execute\(', '_res = client.q(', code)
    code = re.sub(r'\b\w+\.executemany\(', '_res = client.q(', code)

    # 4. fetch
    code = re.sub(r'\b\w+\.fetchall\(\)', '_res', code)
    code = re.sub(r'\b\w+\.fetchone\(\)', '(_res[0] if _res else None)', code)
    
    # 5. rowcount, description
    code = re.sub(r'\b\w+\.rowcount\b', '(len(_res) if isinstance(_res, list) else 1)', code)
    
    # FOR description, we need to be careful not to replace it inside a string literal like EXCLUDED.description
    # We will ONLY replace `cur.description` specifically.
    code = re.sub(r'\bcur\.description\b', '([("col",)] if _res else [])', code)

    if code != orig:
        with open(path, "w") as f:
            f.write(code)
        print(f"Patched {path}")

print("Done")
