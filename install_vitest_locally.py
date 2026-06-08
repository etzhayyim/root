import json
import os
import subprocess
from pathlib import Path

with open("app_store_coverage.json") as f:
    data = json.load(f)

no_vitest_apps = [r["app"] for r in data if r["status"] == "no_vitest"]

for app in no_vitest_apps:
    project_dir = Path("60-apps") / f"etzhayyim-project-{app}"
    if not project_dir.exists():
        continue

    target_dir = None
    for root, dirs, files in os.walk(project_dir):
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if "package.json" in files:
            target_dir = Path(root)
            break

    if target_dir:
        print(f"Testing {app} in {target_dir}")
        # Remove workspace dependency to allow isolated install
        pkg_path = target_dir / "package.json"
        with open(pkg_path, "r") as f:
            pkg = json.load(f)
        if "devDependencies" in pkg and "@etzhayyim/sdk-mock" in pkg["devDependencies"]:
            del pkg["devDependencies"]["@etzhayyim/sdk-mock"]
        with open(pkg_path, "w") as f:
            json.dump(pkg, f, indent=2)

        subprocess.run(["npm", "install", "vitest", "--save-dev"], cwd=target_dir, capture_output=True)
        res = subprocess.run(["npx", "vitest", "run"], cwd=target_dir, capture_output=True, text=True)
        if "passed" in res.stdout:
            print(f"  {app} tests passed.")
        else:
            print(f"  {app} tests failed.")
