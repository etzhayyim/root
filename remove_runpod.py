import os
import glob
import re

def refactor_runpod():
    # Target files based on grep
    files = glob.glob("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/**/*.py", recursive=True)
    count = 0
    for path in files:
        with open(path, "r") as f:
            code = f.read()

        if "runpod" not in code.lower() and "RunPod" not in code:
            continue
            
        orig = code

        # Redirect runpod -> kotoba-server
        code = re.sub(r'api\.runpod\.ai', 'kotoba-server.etzhayyim.internal', code)
        code = re.sub(r'runpod(?!_client)', 'kotoba_server', code, flags=re.IGNORECASE)
        code = code.replace("RunPod", "kotoba-server")
        
        # Vendor-only guard logic for specific files mentioned in notes
        filename = os.path.basename(path)
        vendor_files = ["training_http_server.py", "runpod_client.py", "training_run.py", "billing.py"]
        if filename in vendor_files and "import os" in code:
            # Need to add guard
            guard = 'if os.environ.get("ETZHAYYIM_BUILD"):\n    raise ImportError("vendor-only")\n'
            if "raise ImportError" not in code:
                # Add after imports
                lines = code.split("\n")
                new_lines = []
                guard_added = False
                for line in lines:
                    new_lines.append(line)
                    if not guard_added and (line.startswith("import ") or line.startswith("from ")):
                        # Look ahead to see if imports are done
                        pass # Actually, just appending at top after future is safer
                
                # Safer: regex to put it after future or module docstring
                if "from __future__" in code:
                    code = re.sub(r'(from __future__ import .*?\n)', r'\1\n' + guard, code, count=1)
                else:
                    code = guard + code

        if code != orig:
            with open(path, "w") as f:
                f.write(code)
            count += 1
            print(f"Patched {path}")

    print(f"Patched {count} files")

if __name__ == "__main__":
    refactor_runpod()
