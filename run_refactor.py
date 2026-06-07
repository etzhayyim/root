import glob
import re
import os

def safe_refactor():
    files = glob.glob("20-actors/magatama/py/src/pymagatama/**/*.py", recursive=True)
    count = 0
    for path in files:
        with open(path, "r") as f:
            code = f.read()

        if "sync_cursor" not in code:
            continue
            
        orig = code

        # 1. Imports (handling indentation)
        code = re.sub(r'^[ \t]*from pymagatama\.db_sync import sync_cursor\b.*$\n?', '', code, flags=re.MULTILINE)
        
        # 2. Add client import if not present
        if "from pymagatama.kotoba_datomic import get_kotoba_client" not in code:
            # find first import
            m = re.search(r'^(import|from)\s+', code, flags=re.MULTILINE)
            if m:
                # Add after __future__ if it exists
                if "__future__" in code:
                    code = re.sub(r'^(from __future__ import .*?)$', r'\1\nfrom pymagatama.kotoba_datomic import get_kotoba_client', code, flags=re.MULTILINE)
                else:
                    code = re.sub(r'^(import|from)\s+', r'from pymagatama.kotoba_datomic import get_kotoba_client\n\1 ', code, count=1, flags=re.MULTILINE)

        # 3. block
        code = re.sub(r'^(\s*)with (?:_)?sync_cursor\(\) as (\w+):', r'\1if True:\n\1    client = get_kotoba_client()', code, flags=re.MULTILINE)

        # 4. execution
        code = re.sub(r'\b\w+\.execute\(', '_res = client.q(', code)
        code = re.sub(r'\b\w+\.executemany\(', '_res = client.q(', code)

        # 5. fetch
        code = re.sub(r'\b\w+\.fetchall\(\)', '_res', code)
        code = re.sub(r'\b\w+\.fetchone\(\)', '(_res[0] if _res else None)', code)
        
        # 6. rowcount, description
        code = re.sub(r'\b\w+\.rowcount\b', '(len(_res) if isinstance(_res, list) else 1)', code)
        code = re.sub(r'\b\w+\.description\b', '([("col",)] if _res else [])', code)

        if code != orig:
            with open(path, "w") as f:
                f.write(code)
            count += 1
            print(f"Patched {path}")

    print(f"Patched {count} files")

if __name__ == "__main__":
    safe_refactor()
