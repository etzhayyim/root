/**
 * run.ts — SRE Playwright Runner entry point.
 *
 * 1. Fetches the SpinApp registry from sre.etzhayyim.com
 * 2. For each registered SpinApp, runs the generic smoke suite against its hostname
 * 3. Reports results back to sre.etzhayyim.com via reportPlaywrightResult
 */
// Using require here avoids a TypeScript complaint about missing Node type
// definitions (install @types/node and add "node" to tsconfig.types to fix).
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
const { execFileSync } = require("child_process");
const fs = require("fs");

const SRE_BASE_URL = process.env.SRE_BASE_URL ?? "https://sre.etzhayyim.com";
const SRE_ACCESS_TOKEN = process.env.SRE_ACCESS_TOKEN ?? "";

interface SpinApp {
  id: string;
  name: string;
  hostname: string;
  'playwrightEnabled': boolean;
}

interface ListSpinAppsResponse {
  spinapps: SpinApp[];
}

interface PWTestResult {
  title: string;
  status: "passed" | "failed" | "skipped";
  error?: string;
  'durationMs': number;
}

interface PWRunResult {
  passed: number;
  failed: number;
  skipped: number;
  tests: PWTestResult[];
}

async function listSpinApps(): Promise<SpinApp[]> {
  const res = await fetch(
    `${SRE_BASE_URL}/xrpc/etzhayyim.sre.v1.SREService/listSpinapps`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(SRE_ACCESS_TOKEN ? { Authorization: `Bearer ${SRE_ACCESS_TOKEN}` } : {}),
      },
      body: JSON.stringify({ offset: 0, limit: 100 }),
    }
  );
  if (!res.ok) {
    throw new Error(`listSpinapps failed: ${res.status} ${await res.text()}`);
  }
  const data = (await res.json()) as ListSpinAppsResponse;
  return data.spinapps ?? [];
}

async function reportResult(
  spinappId: string,
  run: PWRunResult,
  targetURL: string
): Promise<void> {
  const res = await fetch(
    `${SRE_BASE_URL}/xrpc/etzhayyim.sre.v1.SREService/reportPlaywrightResult`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(SRE_ACCESS_TOKEN ? { Authorization: `Bearer ${SRE_ACCESS_TOKEN}` } : {}),
      },
      body: JSON.stringify({
        'spinappId': spinappId,
        'targetUrl': targetURL,
        passed: run.passed,
        failed: run.failed,
        skipped: run.skipped,
        tests: run.tests,
      }),
    }
  );
  if (!res.ok) {
    console.error(`reportPlaywrightResult failed for ${spinappId}: ${res.status}`);
  }
}

function runSmoke(targetURL: string): PWRunResult {
  const resultFile = "/tmp/pw-results.json";
  if (fs.existsSync(resultFile)) {
    fs.unlinkSync(resultFile);
  }

  try {
    execFileSync("npx", ["playwright", "test"], {
      env: { ...process.env, TARGET_URL: targetURL },
      stdio: "inherit",
    });
  } catch {
    // playwright exits non-zero on test failures — we capture results from JSON
  }

  if (!fs.existsSync(resultFile)) {
    return { passed: 0, failed: 0, skipped: 0, tests: [] };
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw = JSON.parse(fs.readFileSync(resultFile, "utf-8")) as any;
  let passed = 0;
  let failed = 0;
  let skipped = 0;
  const tests: PWTestResult[] = [];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const suite of raw.suites ?? []) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const spec of suite.specs ?? []) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const result = spec.tests?.[0]?.results?.[0] as any;
      const status: "passed" | "failed" | "skipped" = result?.status ?? "skipped";
      const durationMs: number = result?.duration ?? 0;
      const error: string | undefined = result?.error?.message;

      tests.push({ title: spec.title, status, durationMs, ...(error ? { error } : {}) });

      if (status === "passed") passed++;
      else if (status === "failed") failed++;
      else skipped++;
    }
  }

  return { passed, failed, skipped, tests };
}

async function main() {
  console.log(`SRE Playwright Runner — fetching SpinApp list from ${SRE_BASE_URL}`);
  const apps = await listSpinApps();
  const enabled = apps.filter((a) => a.playwrightEnabled);
  console.log(`${enabled.length} SpinApp(s) with playwrightEnabled=true`);

  for (const app of enabled) {
    const targetURL = `https://${app.hostname}`;
    console.log(`\n==> ${app.name} (${app.id}) — ${targetURL}`);

    const run = runSmoke(targetURL);
    console.log(
      `   passed=${run.passed} failed=${run.failed} skipped=${run.skipped}`
    );

    await reportResult(app.id, run, targetURL);
  }

  console.log("\nDone.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
