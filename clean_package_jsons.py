import json
import os
from pathlib import Path

with open("failing_scaffolded_tests.json") as f:
    failing_apps = json.load(f)

for item in failing_apps:
    pkg_path = Path(item["path"]) / "package.json"
    if not pkg_path.exists():
        continue

    with open(pkg_path, "r") as f:
        pkg = json.load(f)

    modified = False
    for section in ["dependencies", "devDependencies"]:
        if section in pkg:
            keys_to_delete = []
            for k, v in pkg[section].items():
                if k.startswith("@etzhayyim") and v == "workspace:*":
                    # Keep sdk-mock as we use it in tests
                    if k != "@etzhayyim/sdk-mock":
                        keys_to_delete.append(k)
                if k.startswith("@etzhayyimcojp") and v == "workspace:*":
                    keys_to_delete.append(k)

            for k in keys_to_delete:
                del pkg[section][k]
                modified = True

    if modified:
        with open(pkg_path, "w") as f:
            json.dump(pkg, f, indent=2)
        print(f"Cleaned {pkg_path}")
