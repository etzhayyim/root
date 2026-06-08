import os
import json
import csv
from pathlib import Path

apps_dir = Path("60-apps")
projects = [d for d in apps_dir.iterdir() if d.is_dir() and d.name.startswith("etzhayyim-project-")]

data = []
for p in projects:
    name = p.name
    has_test = False
    has_kotodama = False
    has_src = False
    has_readme = (p / "README.md").exists()
    has_claude = (p / "CLAUDE.md").exists()

    # Check deeper for test, src, kotodama
    for root, dirs, files in os.walk(p):
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if ".git" in dirs:
            dirs.remove(".git")

        if "test" in dirs:
            has_test = True
        if "src" in dirs:
            has_src = True
        if "kotodama.jsonld" in files:
            has_kotodama = True

    data.append({
        "project": name,
        "has_src": has_src,
        "has_test": has_test,
        "has_kotodama": has_kotodama,
        "has_readme": has_readme,
        "has_claude": has_claude
    })

data.sort(key=lambda x: x["project"])

# Write CSV
with open("apps_maturity_report.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["project", "has_src", "has_test", "has_kotodama", "has_readme", "has_claude"])
    writer.writeheader()
    writer.writerows(data)

# Print Summary
total = len(data)
with_test = sum(1 for d in data if d["has_test"])
with_kotodama = sum(1 for d in data if d["has_kotodama"])

print(f"Total projects: {total}")
print(f"Projects with tests: {with_test} ({with_test/total*100:.1f}%)")
print(f"Projects with kotodama.jsonld: {with_kotodama} ({with_kotodama/total*100:.1f}%)")
