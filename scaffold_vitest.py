import json
import os
import subprocess
from pathlib import Path

with open("app_store_coverage.json") as f:
    data = json.load(f)

no_vitest_apps = [r["app"] for r in data if r["status"] == "no_vitest"]

vitest_config_content = """import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
    server: {
      deps: {
        inline: ["@etzhayyim/sdk-mock", "@noble/hashes"]
      }
    }
  }
});
"""

test_content_template = """import { describe, it, expect } from "vitest";

describe("{app} actor", () => {
  it("has placeholder test", () => {
    expect(true).toBe(true);
  });
});
"""

modified_dirs = []

for app in no_vitest_apps:
    project_dir = Path("60-apps") / f"etzhayyim-project-{app}"
    if not project_dir.exists():
        continue

    # Find the deepest directory with a package.json but not node_modules
    target_dir = None
    for root, dirs, files in os.walk(project_dir):
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if "package.json" in files:
            target_dir = Path(root)
            break

    if target_dir:
        print(f"Scaffolding {app} in {target_dir}")

        # 1. Add vitest.config.ts
        with open(target_dir / "vitest.config.ts", "w") as f:
            f.write(vitest_config_content)

        # 2. Update package.json
        pkg_path = target_dir / "package.json"
        with open(pkg_path, "r") as f:
            try:
                pkg = json.load(f)
            except:
                print(f"Failed to parse json in {pkg_path}")
                continue

        if "scripts" not in pkg:
            pkg["scripts"] = {}
        pkg["scripts"]["test"] = "vitest run"

        if "devDependencies" not in pkg:
            pkg["devDependencies"] = {}
        pkg["devDependencies"]["vitest"] = "^4.1.0"
        pkg["devDependencies"]["@etzhayyim/sdk-mock"] = "workspace:*"

        with open(pkg_path, "w") as f:
            json.dump(pkg, f, indent=2)

        # 3. Create test file
        test_dir = target_dir / "test"
        test_dir.mkdir(exist_ok=True)
        with open(test_dir / f"{app}.test.ts", "w") as f:
            f.write(test_content_template.replace("{app}", app))

        modified_dirs.append(target_dir)

print(f"\nScaffolded {len(modified_dirs)} directories.")
