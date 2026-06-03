import { test, expect } from '@playwright/test';

const BASE = 'https://yabai.etzhayyim.com';
const SVC = `${BASE}/xrpc/etzhayyim.yabai.v1.YabaiService`;

test.describe('yabai.etzhayyim.com — Health', () => {
  test('worker health', async ({ request }) => {
    const r = await request.get(`${BASE}/_worker/health`);
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).status).toBe('ok');
  });

  test('app health', async ({ request }) => {
    const r = await request.get(`${BASE}/health`);
    expect(r.ok()).toBeTruthy();
    expect((await r.json()).status).toBe('ok');
  });

  test('app meta endpoint is available', async ({ request }) => {
    const r = await request.get(`${BASE}/_app/meta`);
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.appId).toBe('yabai');
  });
});

test.describe('yabai.etzhayyim.com — Card API', () => {
  const hdr = { 'Content-Type': 'application/json', 'X-etzhayyim-USER-ID': 'e2e' };

  test('card.home returns list with 5 items', async ({ request }) => {
    const r = await request.post(`${SVC}/card.home`, { headers: hdr, data: {} });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.list');
    expect(b.payload.items.length).toBe(5);
  });

  test('card.action: summary returns metric-dashboard', async ({ request }) => {
    const r = await request.post(`${SVC}/card.action`, { headers: hdr, data: { action: 'yabai.summary' } });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.metric-dashboard');
    expect(b.payload.metrics.length).toBe(4);
  });

  test('card.action: search returns form', async ({ request }) => {
    const r = await request.post(`${SVC}/card.action`, { headers: hdr, data: { action: 'yabai.search' } });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.form');
    expect(b.payload.action).toBe('yabai.search.exec');
  });

  test('card.action: ingest returns form with 3 fields', async ({ request }) => {
    const r = await request.post(`${SVC}/card.action`, { headers: hdr, data: { action: 'yabai.ingest' } });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.form');
    expect(b.payload.fields.length).toBe(3);
  });

  test('card.action: entities returns list', async ({ request }) => {
    const r = await request.post(`${SVC}/card.action`, { headers: hdr, data: { action: 'yabai.entities' } });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.list');
  });

  test('card.action: alerts returns list', async ({ request }) => {
    const r = await request.post(`${SVC}/card.action`, { headers: hdr, data: { action: 'yabai.alerts' } });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.list');
  });

  test('card.action: unknown returns home', async ({ request }) => {
    const r = await request.post(`${SVC}/card.action`, { headers: hdr, data: { action: 'unknown' } });
    expect(r.ok()).toBeTruthy();
    const b = await r.json();
    expect(b.contentType).toBe('application/vnd.etzhayyim.card.list');
  });
});

test.describe('yabai.etzhayyim.com — Visual', () => {
  test('page renders with YABAI branding', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    // SuperAppLayout renders app name in header
    const body = await page.content();
    expect(body).toContain('YABAI');
  });

  test('SuperAppLayout tab bar visible', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle' });
    const nav = page.locator('nav.fixed, nav[class*="fixed"]');
    await expect(nav).toBeVisible({ timeout: 15_000 });
    const tabs = await nav.locator('button, a').allTextContents();
    expect(tabs.map(t => t.trim())).toEqual(expect.arrayContaining(['Live', 'Talk']));
  });

  test('visual snapshot — homepage', async ({ page }) => {
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await expect(page).toHaveScreenshot('yabai-homepage.png', { maxDiffPixelRatio: 0.05 });
  });

  test('no critical JS errors on load', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => {
      // Ignore Svelte hydration warnings (expected for SSR mismatch)
      if (!e.message.includes('root.svelte') && !e.message.includes('hydrat')) {
        errors.push(e.message);
      }
    });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    expect(errors).toHaveLength(0);
  });

  test('no failed asset requests', async ({ page }) => {
    const failed: string[] = [];
    page.on('requestfailed', (r) => { if (r.url().includes('/_app/')) failed.push(r.url()); });
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    expect(failed).toHaveLength(0);
  });
});
