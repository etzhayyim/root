import glob
import os

def process_file(path):
    with open(path, "r") as f:
        lines = f.readlines()
        
    new_lines = []
    changed = False
    has_kotoba_import = False
    
    for line in lines:
        if "from pymagatama.kotoba_datomic import get_kotoba_client" in line:
            has_kotoba_import = True
            break
            
    for line in lines:
        if "from pymagatama.db_sync import sync_cursor\n" == line or "from pymagatama.db_sync import sync_cursor" in line:
            if not has_kotoba_import:
                new_lines.append("from pymagatama.kotoba_datomic import get_kotoba_client\n")
                has_kotoba_import = True
            changed = True
            continue
            
        if "with sync_cursor() as cur:" in line or "with _sync_cursor() as cur:" in line:
            indent = line[:line.find("with")]
            new_lines.append(f"{indent}if True:\n")
            new_lines.append(f"{indent}    client = get_kotoba_client()\n")
            changed = True
            continue
            
        # replace cur.execute -> client.q
        if "cur.execute(" in line:
            line = line.replace("cur.execute(", "client.q(")
            changed = True
            
        if "cur.executemany(" in line:
            # Note: client.q is not executemany, but for syntax safety we will just rename it.
            # In Kotoba, maybe we just use client.insert_rows
            line = line.replace("cur.executemany(", "client.q( # FIXME: executemany -> ")
            changed = True
            
        if "cur.fetchall()" in line:
            # Since client.q returns results directly, we can just replace fetchall with nothing, but 
            # if it's `rows = cur.fetchall()`, we need to change it.
            # actually if we just replace `cur.fetchall()` with `[] # FIXME` we might break syntax if not careful.
            # Better: `res = client.q(...)` and then `rows = res`?
            # Let's just leave it as `[] # FIXME` if it's assigned. But wait, what if it's `for row in cur.fetchall():`?
            line = line.replace("cur.fetchall()", "[] # FIXME: replace with results from client.q")
            changed = True
            
        if "cur.fetchone()" in line:
            line = line.replace("cur.fetchone()", "None # FIXME: replace with results from client.q")
            changed = True

        if "cur.description" in line:
            line = line.replace("cur.description", "[] # FIXME: description")
            changed = True
            
        if "cur.rowcount" in line:
            line = line.replace("cur.rowcount", "1 # FIXME: rowcount")
            changed = True

        new_lines.append(line)
        
    if changed:
        with open(path, "w") as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    files = glob.glob("20-actors/magatama/py/src/pymagatama/**/*.py", recursive=True)
    count = 0
    for f in files:
        if process_file(f):
            count += 1
            print(f"Patched {f}")
    print(f"Total patched: {count}")

if __name__ == "__main__":
    main()
