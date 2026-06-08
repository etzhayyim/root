import os
from pathlib import Path

def fix_test(app, prefix):
    path = Path(f"60-apps/etzhayyim-project-{app}/appview/{app}-mcp-component/svelte/test/{app}.test.ts")
    if not path.exists():
        return
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(f"com.etzhayyim.apps.{app}", f"{prefix}.{app}")
    with open(path, "w") as f:
        f.write(content)

fix_test("mailer", "ai.etzhayyim.apps")
fix_test("calendar", "com.etzhayyim.apps")

