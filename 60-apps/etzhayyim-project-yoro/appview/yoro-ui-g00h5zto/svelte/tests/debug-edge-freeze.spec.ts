/**
 * Debug Edge freeze — profile main-thread blocking during page load.
 * Captures console logs, JS errors, network timing, and long tasks.
 */
import { test, expect } from '@playwright/test';

const BASE = process.env.YORO_BASE_URL || 'https://yoro.etzhayyim.com';

test('debug: profile page load for main-thread blocking', async ({ page }) => {
  const consoleLogs: string[] = [];
  const jsErrors: string[] = [];
  const networkRequests: { url: string; status: number; duration: number; size: number }[] = [];

  // Capture console output
  page.on('console', (msg) => {
    consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
  });

  // Capture JS errors
  page.on('pageerror', (err) => {
    jsErrors.push(err.message);
  });

  // Track network requests
  const requestTimings = new Map<string, number>();
  page.on('request', (req) => {
    requestTimings.set(req.url(), Date.now());
  });
  page.on('response', (res) => {
    const start = requestTimings.get(res.url()) || Date.now();
    const duration = Date.now() - start;
    networkRequests.push({
      url: res.url().substring(0, 120),
      status: res.status(),
      duration,
      size: Number(res.headers()['content-length'] || 0),
    });
  });

  // Inject Long Task observer before navigation
  await page.addInitScript(() => {
    (window as any).__longTasks = [];
    const obs = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        (window as any).__longTasks.push({
          name: entry.name,
          duration: entry.duration,
          startTime: entry.startTime,
        });
      }
    });
    obs.observe({ type: 'longtask', buffered: true });
  });

  const navStart = Date.now();
  const response = await page.goto(BASE, { waitUntil: 'commit', timeout: 30_000 });
  const commitTime = Date.now() - navStart;
  console.log(`[timing] navigation commit: ${commitTime}ms, status: ${response?.status()}`);

  // Wait for DOMContentLoaded
  const dclStart = Date.now();
  await page.waitForFunction(() => document.readyState !== 'loading', { timeout: 30_000 });
  const dclTime = Date.now() - dclStart;
  console.log(`[timing] DOMContentLoaded wait: ${dclTime}ms`);

  // Wait for load event
  const loadStart = Date.now();
  await page.waitForLoadState('load', { timeout: 60_000 }).catch((error) => {
    console.warn('[silent-fail] debug-edge-freeze.spec.ts: waitForLoadState failed', error);
    console.log(`[timing] load event timed out after 60s`);
  });
  const loadTime = Date.now() - loadStart;
  console.log(`[timing] load event wait: ${loadTime}ms`);

  // Check if page is interactive (can we click?)
  const interactiveStart = Date.now();
  const isInteractive = await page.evaluate(() => {
    return new Promise<boolean>((resolve) => {
      // Try to schedule a microtask — if main thread is blocked this won't run
      setTimeout(() => resolve(true), 0);
      // Fallback timeout
      setTimeout(() => resolve(false), 5000);
    });
  }).catch((error) => {
    console.warn('[silent-fail] debug-edge-freeze.spec.ts: interactive evaluation failed', error);
    return false;
  });
  const interactiveTime = Date.now() - interactiveStart;
  console.log(`[timing] interactive check: ${interactiveTime}ms, interactive: ${isInteractive}`);

  // Collect Long Tasks
  const longTasks = await page.evaluate(() => (window as any).__longTasks || []);
  console.log(`\n=== Long Tasks (>${50}ms main-thread blocks) ===`);
  if (longTasks.length === 0) {
    console.log('  (none detected)');
  } else {
    for (const t of longTasks) {
      console.log(`  ${t.duration.toFixed(0)}ms at ${t.startTime.toFixed(0)}ms — ${t.name}`);
    }
  }

  // Collect Performance entries (resources)
  const resources = await page.evaluate(() => {
    return performance.getEntriesByType('resource')
      .filter((r: any) => r.duration > 500)
      .map((r: any) => ({
        name: r.name.substring(0, 100),
        duration: r.duration.toFixed(0),
        transferSize: r.transferSize,
        type: r.initiatorType,
      }))
      .sort((a: any, b: any) => Number(b.duration) - Number(a.duration))
      .slice(0, 15);
  });
  console.log(`\n=== Slow Resources (>500ms) ===`);
  for (const r of resources) {
    console.log(`  ${r.duration}ms ${r.type} ${(r.transferSize / 1024).toFixed(0)}KB — ${r.name}`);
  }

  // Check for SharedArrayBuffer availability
  const hasSharedArrayBuffer = await page.evaluate(() => typeof SharedArrayBuffer !== 'undefined');
  console.log(`\n=== Browser Capabilities ===`);
  console.log(`  SharedArrayBuffer: ${hasSharedArrayBuffer}`);

  // Check COEP/COOP headers from response
  const headers = response?.headers() || {};
  console.log(`  COEP: ${headers['cross-origin-embedder-policy'] || '(not set)'}`);
  console.log(`  COOP: ${headers['cross-origin-opener-policy'] || '(not set)'}`);

  // Slow network requests
  const slowReqs = networkRequests
    .filter((r) => r.duration > 500)
    .sort((a, b) => b.duration - a.duration)
    .slice(0, 10);
  console.log(`\n=== Slow Network Requests (>500ms) ===`);
  for (const r of slowReqs) {
    console.log(`  ${r.duration}ms [${r.status}] ${r.url}`);
  }

  // Failed network requests
  const failedReqs = networkRequests.filter((r) => r.status >= 400);
  console.log(`\n=== Failed Network Requests ===`);
  if (failedReqs.length === 0) {
    console.log('  (none)');
  } else {
    for (const r of failedReqs) {
      console.log(`  [${r.status}] ${r.url}`);
    }
  }

  // JS Errors
  console.log(`\n=== JS Errors ===`);
  if (jsErrors.length === 0) {
    console.log('  (none)');
  } else {
    for (const e of jsErrors) {
      console.log(`  ${e.substring(0, 200)}`);
    }
  }

  // Console warnings/errors
  const warnErrors = consoleLogs.filter((l) => l.startsWith('[error]') || l.startsWith('[warn'));
  console.log(`\n=== Console Warnings/Errors (${warnErrors.length} total) ===`);
  for (const l of warnErrors.slice(0, 20)) {
    console.log(`  ${l.substring(0, 200)}`);
  }

  // Memory usage
  const memory = await page.evaluate(() => {
    const perf = performance as any;
    if (perf.memory) {
      return {
        usedJSHeapSize: (perf.memory.usedJSHeapSize / 1024 / 1024).toFixed(1),
        totalJSHeapSize: (perf.memory.totalJSHeapSize / 1024 / 1024).toFixed(1),
        jsHeapSizeLimit: (perf.memory.jsHeapSizeLimit / 1024 / 1024).toFixed(1),
      };
    }
    return null;
  });
  if (memory) {
    console.log(`\n=== Memory ===`);
    console.log(`  Used: ${memory.usedJSHeapSize}MB / Total: ${memory.totalJSHeapSize}MB / Limit: ${memory.jsHeapSizeLimit}MB`);
  }

  // Take screenshot
  await page.screenshot({ path: 'tests/screenshots/debug-edge-freeze.png', fullPage: false });
  console.log('\n[screenshot] tests/screenshots/debug-edge-freeze.png');

  // Basic assertion: page should be interactive
  expect(isInteractive).toBe(true);
});

test('debug: simulate real user interaction (scroll + navigate + DuckDB queries)', async ({ page }) => {
  const consoleLogs: string[] = [];
  page.on('console', (msg) => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
  page.on('pageerror', (err) => consoleLogs.push(`[pageerror] ${err.message}`));

  await page.addInitScript(() => {
    (window as any).__longTasks = [];
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        (window as any).__longTasks.push({
          duration: entry.duration,
          startTime: entry.startTime,
          name: entry.name,
        });
      }
    }).observe({ type: 'longtask', buffered: true });
  });

  // Step 1: Navigate to home
  console.log('\n=== Step 1: Navigate to home ===');
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await page.waitForTimeout(3000);

  // Step 2: Scroll feed (triggers infinite scroll / DuckDB queries)
  console.log('=== Step 2: Scroll feed ===');
  for (let i = 0; i < 5; i++) {
    await page.evaluate(() => window.scrollBy(0, 800));
    await page.waitForTimeout(500);
  }
  await page.waitForTimeout(2000);

  // Step 3: Navigate to search (triggers actor search + DuckDB)
  console.log('=== Step 3: Navigate to search ===');
  const searchStart = Date.now();
  await page.click('a[href="/search"]').catch((error) => {
    console.warn('[silent-fail] debug-edge-freeze.spec.ts: search click failed, using fallback goto', error);
    // fallback: direct navigation
    return page.goto(`${BASE}/search`, { waitUntil: 'domcontentloaded', timeout: 15_000 });
  });
  await page.waitForTimeout(3000);
  const searchTime = Date.now() - searchStart;
  console.log(`  Search page load: ${searchTime}ms`);

  // Step 4: Navigate to a profile (SSR + DuckDB graph queries)
  console.log('=== Step 4: Navigate to profile ===');
  const profileStart = Date.now();
  await page.goto(`${BASE}/profile/did:web:yoro.etzhayyim.com`, { waitUntil: 'domcontentloaded', timeout: 15_000 }).catch((error) => {
    console.warn('[silent-fail] debug-edge-freeze.spec.ts: profile goto failed', error);
  });
  await page.waitForTimeout(3000);
  const profileTime = Date.now() - profileStart;
  console.log(`  Profile page load: ${profileTime}ms`);

  // Step 5: Go back to home
  console.log('=== Step 5: Back to home ===');
  const homeStart = Date.now();
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 15_000 });
  await page.waitForTimeout(3000);
  const homeTime = Date.now() - homeStart;
  console.log(`  Home reload: ${homeTime}ms`);

  // Check interactivity
  const pingStart = Date.now();
  await page.evaluate(() => 1 + 1);
  const pingTime = Date.now() - pingStart;
  console.log(`\n  Final ping: ${pingTime}ms`);

  // Collect all long tasks
  const allTasks = await page.evaluate(() => (window as any).__longTasks || []);
  const totalBlocking = allTasks.reduce((sum: number, t: any) => sum + t.duration, 0);
  console.log(`\n=== All Long Tasks ===`);
  console.log(`  Count: ${allTasks.length}, Total blocking: ${totalBlocking.toFixed(0)}ms`);
  for (const t of allTasks.sort((a: any, b: any) => b.duration - a.duration).slice(0, 15)) {
    console.log(`  ${t.duration.toFixed(0)}ms at +${(t.startTime / 1000).toFixed(1)}s — ${t.name}`);
  }

  // Memory
  const memory = await page.evaluate(() => {
    const perf = performance as any;
    return perf.memory ? {
      used: (perf.memory.usedJSHeapSize / 1024 / 1024).toFixed(1),
      total: (perf.memory.totalJSHeapSize / 1024 / 1024).toFixed(1),
    } : null;
  });
  if (memory) console.log(`\n  Memory: ${memory.used}MB / ${memory.total}MB`);

  // Console errors
  const errors = consoleLogs.filter(l => l.includes('[error]') || l.includes('[pageerror]') || l.includes('[warn]'));
  console.log(`\n=== Console Warnings/Errors (${errors.length}) ===`);
  for (const e of errors.slice(0, 15)) {
    console.log(`  ${e.substring(0, 200)}`);
  }

  await page.screenshot({ path: 'tests/screenshots/debug-edge-interaction.png', fullPage: false });
  expect(pingTime).toBeLessThan(5000);
});

test('debug: measure DuckDB init impact in isolation', async ({ page }) => {
  // Navigate and immediately check if DuckDB import blocks the thread
  await page.addInitScript(() => {
    (window as any).__duckdbTimings = {};
    const origImport = (window as any).__proto__; // track dynamic imports
    (window as any).__longTasks = [];
    const obs = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        (window as any).__longTasks.push({
          duration: entry.duration,
          startTime: entry.startTime,
        });
      }
    });
    obs.observe({ type: 'longtask', buffered: true });
  });

  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30_000 });

  // Wait a bit for DuckDB init to start
  await page.waitForTimeout(5000);

  // Check DuckDB-related console output
  const duckdbLogs = await page.evaluate(() => {
    return (window as any).__longTasks || [];
  });

  console.log(`\n=== Long Tasks during first 5s ===`);
  const totalBlocking = duckdbLogs.reduce((sum: number, t: any) => sum + t.duration, 0);
  console.log(`  Count: ${duckdbLogs.length}, Total blocking: ${totalBlocking.toFixed(0)}ms`);
  for (const t of duckdbLogs) {
    console.log(`  ${t.duration.toFixed(0)}ms at +${t.startTime.toFixed(0)}ms`);
  }

  // Check if page is still responsive after 5s
  const startPing = Date.now();
  await page.evaluate(() => 1 + 1);
  const pingTime = Date.now() - startPing;
  console.log(`\n  Page ping after 5s: ${pingTime}ms`);

  // Wait another 10s and check again
  await page.waitForTimeout(10000);
  const longTasksAfter15s = await page.evaluate(() => (window as any).__longTasks || []);
  const laterTasks = longTasksAfter15s.filter((t: any) => t.startTime > 5000);
  console.log(`\n=== Long Tasks between 5-15s ===`);
  const laterBlocking = laterTasks.reduce((sum: number, t: any) => sum + t.duration, 0);
  console.log(`  Count: ${laterTasks.length}, Total blocking: ${laterBlocking.toFixed(0)}ms`);
  for (const t of laterTasks) {
    console.log(`  ${t.duration.toFixed(0)}ms at +${t.startTime.toFixed(0)}ms`);
  }

  expect(pingTime).toBeLessThan(5000);
});
