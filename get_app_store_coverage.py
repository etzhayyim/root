import os
import subprocess
import json
from pathlib import Path

target_apps = [
    "kiyome", "harai",
    "gmail", "outlook",
    "drive", "organizer", "sheets", "docs", "mailer", "calendar", "forms",
    "news", "oshikatsu", "videos", "music", "manga", "anime", "games", "narou",
    "search", "translate", "images", "aima", "robot",
    "manimani", "6ir", "maps", "kareyanagi", "oshinobi", "matrix", "gameya", "cards",
    "tenki", "yadoya", "fleamarket", "shopping", "briefing", "tsukuru", "cowork", "shigotoba",
    "web4", "society6", "lawfirm", "lawyer", "ekyc", "global", "worlds", "pachinko",
    "casino", "oshiete", "webpage", "marketer", "omikuji", "wire", "lawfirm-admin",
    "hub", "scheduler", "performers", "analytics", "ops", "sre", "os", "po", "gov",
    "resources", "completer", "har", "provider", "ge", "lo", "tia", "wvme", "tasklist"
]

apps_dir = Path("60-apps")
results = []

for app in target_apps:
    project_dir = apps_dir / f"etzhayyim-project-{app}"
    if not project_dir.exists():
        print(f"Directory not found for app: {app}")
        results.append({"app": app, "status": "not_found"})
        continue

    print(f"Checking {app}...")

    # Check if there's a package.json and vitest.config.ts anywhere in this project
    has_vitest = False
    test_dir = None
    for root, dirs, files in os.walk(project_dir):
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if "vitest.config.ts" in files:
            has_vitest = True
            test_dir = root
            break

    if has_vitest and test_dir:
        print(f"  Found vitest in {test_dir}. Running coverage...")
        # Run tests with coverage
        try:
            cmd = ["pnpm", "run", "test", "--coverage"]
            process = subprocess.run(cmd, cwd=test_dir, capture_output=True, text=True, timeout=60)

            # Simple heuristic: if it mentions 'Coverage report', it ran.
            if "Coverage summary" in process.stdout:
                # Try to parse the summary table
                lines = process.stdout.splitlines()
                stmts = "unknown"
                for line in lines:
                    if "Statements" in line and ":" in line:
                        stmts = line.split(":")[1].strip().split("%")[0]

                results.append({"app": app, "status": "has_coverage", "statements": stmts})
                print(f"  Coverage: {stmts}%")
            else:
                results.append({"app": app, "status": "test_failed"})
                print("  Test failed or no coverage report.")
        except subprocess.TimeoutExpired:
            results.append({"app": app, "status": "timeout"})
            print("  Timeout.")
    else:
        results.append({"app": app, "status": "no_vitest"})
        print("  No vitest config found.")

# Write summary
with open("app_store_coverage.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n--- Summary ---")
print(f"Total checked: {len(target_apps)}")
print(f"Not found: {sum(1 for r in results if r['status'] == 'not_found')}")
print(f"No vitest: {sum(1 for r in results if r['status'] == 'no_vitest')}")
print(f"Has coverage: {sum(1 for r in results if r['status'] == 'has_coverage')}")
print(f"Test failed: {sum(1 for r in results if r['status'] == 'test_failed')}")
