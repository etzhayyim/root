import glob
import os
import re

def refactor_all():
    files = glob.glob("20-actors/magatama/py/src/pymagatama/**/*.py", recursive=True)
    count = 0
    for path in files:
        with open(path, "r") as f:
            code = f.read()

        original_code = code

        # Replace imports
        code = code.replace("from pymagatama.db_sync import sync_cursor\n", "")
        code = code.replace("from pymagatama.db_sync import sync_cursor as _sync_cursor\n", "")
        
        # We might have inline imports
        code = code.replace("from pymagatama.db_sync import sync_cursor", "")

        # Only proceed if we still have sync_cursor usage to fix
        if "with sync_cursor() as cur:" in code or "with _sync_cursor() as cur:" in code:
            if "from pymagatama.kotoba_datomic import get_kotoba_client" not in code:
                # Add import right after the docstring or at the top
                code = "from pymagatama.kotoba_datomic import get_kotoba_client\n" + code

            # Replace with client instantiation and if True block to maintain indentation
            code = code.replace("with sync_cursor() as cur:", "client = get_kotoba_client()\n        if True:")
            code = code.replace("with _sync_cursor() as cur:", "client = get_kotoba_client()\n        if True:")
            
            # replace cur.execute -> client.q
            # Since client.q returns the result directly, assignments like rows = cur.fetchall() need to be handled.
            # For simplicity, we'll replace cur.execute with res = client.q if we can detect fetchall
            
            # This is tricky without AST. Let's do a basic text replacement for cur.execute
            code = code.replace("cur.execute(", "client.q(")
            
            # We'll just replace cur.fetchall() with a generic warning or try to fix common patterns
            # Actually, `client.q()` returns the rows. So if a code has:
            # client.q(...)
            # rows = cur.fetchall()
            # This is broken. We need to be a bit smarter.
            
            # Let's fix the common pattern:
            # cur.execute(...)
            # ... = cur.fetchall()
            
            code = re.sub(r'client\.q\((.*?)\)\n(\s+)rows = cur\.fetchall\(\)', r'rows = client.q(\1)', code, flags=re.DOTALL)
            code = re.sub(r'client\.q\((.*?)\)\n(\s+)return cur\.fetchall\(\)', r'return client.q(\1)', code, flags=re.DOTALL)
            code = re.sub(r'client\.q\((.*?)\)\n(\s+)return list\(cur\.fetchall\(\)\)', r'return list(client.q(\1))', code, flags=re.DOTALL)
            
            # Other fetchall
            code = code.replace("cur.fetchall()", "[]  # FIXME: refactored fetchall")
            code = code.replace("cur.fetchone()", "None  # FIXME: refactored fetchone")
            
            # cur.rowcount
            code = code.replace("cur.rowcount", "1  # FIXME: rowcount assumption")

        if code != original_code:
            with open(path, "w") as f:
                f.write(code)
            count += 1
            print(f"Patched {path}")
    print(f"Total files patched: {count}")

if __name__ == "__main__":
    refactor_all()
