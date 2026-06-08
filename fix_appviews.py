import json
import os
import subprocess
from pathlib import Path

with open("failing_scaffolded_tests.json") as f:
    failing_apps = json.load(f)

# Read pnpm-workspace.yaml and add these paths
with open("pnpm-workspace.yaml", "r") as f:
    pnpm_content = f.read()

# Add to Baseline appviews for Phase 3 testing section
marker = "  # Baseline appviews for Phase 3 testing\n"
if marker not in pnpm_content:
    pnpm_content = pnpm_content.replace(
        '  - "40-engine/kami-engine/kami-engine-sdk"\n',
        '  - "40-engine/kami-engine/kami-engine-sdk"\n\n' + marker
    )

lines_to_add = []
for item in failing_apps:
    line = f'  - "{item["path"]}"'
    if line not in pnpm_content:
        lines_to_add.append(line)

if lines_to_add:
    parts = pnpm_content.split(marker)
    pnpm_content = parts[0] + marker + "\n".join(lines_to_add) + "\n" + parts[1]
    with open("pnpm-workspace.yaml", "w") as f:
        f.write(pnpm_content)
    print("Updated pnpm-workspace.yaml")

# Fix each app
for item in failing_apps:
    app = item["app"]
    path = Path(item["path"])
    print(f"\nFixing {app} at {path}")

    # Check where src is
    src_dir = path / "src"
    app_ts = src_dir / "app.ts"
    rel_src = "src"
    if not app_ts.exists():
        src_dir = path.parent / "src"
        app_ts = src_dir / "app.ts"
        rel_src = "../src"

    if not app_ts.exists():
        print(f"Could not find app.ts for {app}")
        continue

    # 1. Fix app.ts
    with open(app_ts, "r") as f:
        app_content = f.read()

    app_content = app_content.replace(
        "ASSETS?: Fetcher;",
        "ASSETS?: { fetch(req: Request): Promise<Response> };"
    )
    app_content = app_content.replace(
        "} satisfies ExportedHandler<Env>;",
        "};"
    )
    with open(app_ts, "w") as f:
        f.write(app_content)

    # 2. Fix vitest.config.ts
    vitest_config_path = path / "vitest.config.ts"
    if vitest_config_path.exists():
        with open(vitest_config_path, "r") as f:
            v_content = f.read()
        if "coverage" not in v_content:
            v_content = v_content.replace(
                "    }\n  }\n});",
                f'    }},\n    coverage: {{\n      include: ["{rel_src}/**/*.ts"]\n    }}\n  }}\n}});'
            )
            with open(vitest_config_path, "w") as f:
                f.write(v_content)

    # 3. Create test file
    test_content = f"""import {{ describe, it, expect, vi }} from "vitest";
import app from "{rel_src}/app.js";

global.fetch = vi.fn();

describe("{app} appview facade", () => {{
  it("returns health check on /health", async () => {{
    const req = new Request("https://{app}.etzhayyim.com/health");
    const res = await app.fetch(req, {{}});
    expect(res.status).toBe(200);
    const data = await res.json() as any;
    expect(data.ok).toBe(true);
    expect(data.actor).toBe("did:web:{app}.etzhayyim.com");
  }});

  it("handles invalid json in POST gracefully", async () => {{
    const req = new Request("https://{app}.etzhayyim.com/xrpc/com.etzhayyim.apps.{app}.test", {{
      method: "POST",
      body: "{{ bad json",
    }});
    const res = await app.fetch(req, {{}});
    expect(res.status).toBe(400);
    const data = await res.json() as any;
    expect(data.error).toBe("InvalidJson");
  }});

  it("proxies valid XRPC to dispatcher", async () => {{
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify({{ success: true }})));
    const req = new Request("https://{app}.etzhayyim.com/xrpc/com.etzhayyim.apps.{app}.ping");
    const res = await app.fetch(req, {{}});
    expect(res.status).toBe(200);
    const data = await res.json() as any;
    expect(data.success).toBe(true);
  }});

  it("returns 404 for unknown path without ASSETS", async () => {{
    const req = new Request("https://{app}.etzhayyim.com/unknown");
    const res = await app.fetch(req, {{}});
    expect(res.status).toBe(404);
  }});
}});
"""
    test_path = path / "test" / f"{app}.test.ts"
    test_path.parent.mkdir(exist_ok=True)
    with open(test_path, "w") as f:
        f.write(test_content)
