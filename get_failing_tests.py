import json
import os
import subprocess
from pathlib import Path

with open("app_store_coverage.json") as f:
    data = json.load(f)

no_vitest_apps = [r["app"] for r in data if r["status"] == "no_vitest"]

failing_apps = []

for app in no_vitest_apps:
    if app in ["gmail", "docs"]:
        continue
    project_dir = Path("60-apps") / f"etzhayyim-project-{app}"
    if not project_dir.exists():
        continue

    target_dir = None
    for root, dirs, files in os.walk(project_dir):
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if "vitest.config.ts" in files:
            target_dir = Path(root)
            break

    if target_dir:
        res = subprocess.run(["npx", "vitest", "run"], cwd=target_dir, capture_output=True, text=True)
        if "failed" in res.stdout or "Error" in res.stdout or "FAIL" in res.stdout:
            failing_apps.append({"app": app, "path": str(target_dir)})

with open("failing_scaffolded_tests.json", "w") as f:
    json.dump(failing_apps, f, indent=2)

print(f"Found {len(failing_apps)} failing apps.")
for f in failing_apps:
    print(f"{f['app']}: {f['path']}")
