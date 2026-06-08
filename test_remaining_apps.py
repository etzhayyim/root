import json
import subprocess
from pathlib import Path

with open("failing_scaffolded_tests.json") as f:
    failing_apps = json.load(f)

for item in failing_apps:
    app = item["app"]
    path = item["path"]
    print(f"\nTesting {app} in {path}")
    res = subprocess.run(["pnpm", "exec", "vitest", "run", "--coverage"], cwd=path, capture_output=True, text=True)
    if res.returncode == 0 and "passed" in res.stdout:
        print(f"  PASSED: {app}")
    else:
        print(f"  FAILED: {app}")
        print("  Error excerpt:")
        lines = res.stdout.splitlines()
        for i, line in enumerate(lines):
            if "FAIL" in line or "Error" in line:
                print("    " + line)
                if i + 1 < len(lines):
                    print("    " + lines[i+1])
                break

