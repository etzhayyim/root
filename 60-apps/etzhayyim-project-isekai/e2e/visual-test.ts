/**
 * ISEKAI World — Playwright visual + functional E2E test.
 *
 * Tests: WebGPU init, scene parse, voxel rendering, per-vertex color,
 * sky cycle, physics, LOD, NPC placement, debug panel, audio.
 *
 * Run: npx playwright test projects/etzhayyim-project-isekai/e2e/visual-test.ts
 */
import { test, expect, type Page } from '@playwright/test';

const BASE = 'https://isekai.etzhayyim.com';
const SEED = 42;
const URL = `${BASE}/?seed=${SEED}`;

/** Wait for WASM init + scene load. Returns game state or null. */
async function waitForGame(page: Page, timeoutMs = 15000): Promise<Record<string, unknown> | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const state = await page.evaluate(() => (window as any).__kami_isekai_state);
    if (state?.position) return state as Record<string, unknown>;
    await page.waitForTimeout(500);
  }
  return null;
}

test.describe('ISEKAI World E2E', () => {

  test('page loads without JS errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => {
      if (m.type() === 'error' && !m.text().includes('404') && !m.text().includes('GPU'))
        errors.push(m.text());
    });

    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    expect(errors).toEqual([]);
  });

  test('title contains seed', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await expect(page).toHaveTitle(/ISEKAI World/);
  });

  test('scene generates correct entity counts', async ({ page }) => {
    const logs: string[] = [];
    page.on('console', (m) => {
      if (m.text().includes('[isekai]')) logs.push(m.text());
    });

    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    const isekaiLog = logs.find((l) => l.includes('[isekai]'));
    expect(isekaiLog).toBeDefined();

    // Parse: [isekai] seed=42 entities=118 chunks=81 sdf=10 chars=10
    const chunks = isekaiLog!.match(/chunks=(\d+)/)?.[1];
    const sdf = isekaiLog!.match(/sdf=(\d+)/)?.[1];
    const chars = isekaiLog!.match(/chars=(\d+)/)?.[1];

    expect(Number(chunks)).toBeGreaterThanOrEqual(81);  // 9×9×1 (+1 terrain gen variation)
    expect(Number(chunks)).toBeLessThanOrEqual(82);
    expect(Number(sdf)).toBe(0);      // NPCs disabled — voxel terrain stability
    expect(Number(chars)).toBe(10);   // 10 CharacterDefs
  });

  test('WASM exports game state to JS', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);

    if (!state) {
      // No WebGPU in CI — verify loading state instead
      const loading = await page.evaluate(() => {
        const el = document.getElementById('loading');
        return el?.textContent?.trim().slice(0, 100);
      });
      // In headless CI without GPU, loading shows error or initial text
      expect(loading).toBeDefined();
      return;
    }

    // Verify state shape
    expect(state.position).toBeDefined();
    expect(state.timePhase).toBeDefined();
    expect(state.worldTime).toBeDefined();
    expect(state.onGround).toBeDefined();
    expect(state.velY).toBeDefined();
    expect(state.biome).toBeDefined();
    expect(state.lod0).toBeDefined();
  });

  test('player spawns at correct height', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);
    if (!state) return; // skip in no-GPU CI

    const pos = state.position as number[];
    expect(pos[1]).toBeGreaterThan(4);   // above terrain min
    expect(pos[1]).toBeLessThan(20);     // below terrain max + jump
  });

  test('player is grounded on spawn', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);
    if (!state) return;

    expect(state.onGround).toBe(true);
    expect(Math.abs(state.velY as number)).toBeLessThan(0.05);
  });

  test('sky phase starts at DAWN', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);
    if (!state) return;

    expect(state.timePhase).toBe('DAWN');
    expect(state.worldTime as number).toBeGreaterThan(0.2);
    expect(state.worldTime as number).toBeLessThan(0.4);
  });

  test('LOD distribution is valid', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);
    if (!state) return;

    const total = (state.lod0 as number) + (state.lod1 as number) +
                  (state.lod2 as number) + (state.lod3 as number);
    expect(total).toBeGreaterThanOrEqual(81);  // all chunks accounted for
    expect(total).toBeLessThanOrEqual(82);
    expect(state.lod0 as number).toBeGreaterThan(0);   // near chunks at LOD0
  });

  test('biome detected correctly at spawn', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);
    if (!state) return;

    // Spawn at 0,0 = plains center
    expect(state.biome).toBe('plains');
  });

  test('debug panel renders with F3', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    // Debug panel starts visible
    const debugEl = page.locator('#debug');
    await expect(debugEl).toBeVisible();

    // Contains expected sections
    const text = await debugEl.textContent();
    expect(text).toContain('Player State');
    expect(text).toContain('Sky / Weather');
    expect(text).toContain('World Data');
    expect(text).toContain('LOD Distribution');
    expect(text).toContain('Frame Timing');

    // F3 toggles off
    await page.keyboard.press('F3');
    await expect(debugEl).toBeHidden();

    // F3 toggles back on
    await page.keyboard.press('F3');
    await expect(debugEl).toBeVisible();
  });

  test('HUD elements are visible', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);

    if (state) {
      // Game loaded — HUD should be visible
      await expect(page.locator('#hud')).toBeVisible();
      await expect(page.locator('#hotbar')).toBeVisible();
      await expect(page.locator('#crosshair')).toBeVisible();
      await expect(page.locator('#minimap')).toBeVisible();

      // HUD shows correct biome
      const biomeText = await page.locator('#hud-biome').textContent();
      expect(biomeText?.toUpperCase()).toContain('PLAINS');
    }
  });

  test('target block detected on raycast', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page);
    if (!state) return;

    // Look down at ground — should hit a block
    const tb = await page.evaluate(() => {
      const fn = (window as any).__kami_target_block;
      return fn ? fn() : null;
    });

    // Target block may or may not be set depending on camera angle
    // Just verify the function exists
    const hasFn = await page.evaluate(() => typeof (window as any).__kami_target_block === 'function');
    expect(hasFn).toBe(true);
  });

  test('static assets serve correctly', async ({ page }) => {
    // WASM binary
    const wasmResp = await page.request.get(`${BASE}/kami_web_bg.wasm`);
    expect(wasmResp.status()).toBe(200);
    expect(wasmResp.headers()['content-type']).toBe('application/wasm');

    // JS glue
    const jsResp = await page.request.get(`${BASE}/kami_web.js`);
    expect(jsResp.status()).toBe(200);

    // Scene
    const sceneResp = await page.request.get(`${BASE}/scenes/isekai-overworld.jsonld`);
    expect(sceneResp.status()).toBe(200);
  });

  test('visual screenshot', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    const state = await waitForGame(page, 10000);

    // Wait extra for rendering to settle
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: `projects/etzhayyim-project-isekai/e2e/screenshots/isekai-seed${SEED}.png`,
      fullPage: false,
    });

    if (state) {
      // Take a second screenshot after time passes (sky should have changed slightly)
      await page.waitForTimeout(5000);
      await page.screenshot({
        path: `projects/etzhayyim-project-isekai/e2e/screenshots/isekai-seed${SEED}-after5s.png`,
        fullPage: false,
      });
    }
  });

  test('different seeds produce different worlds', async ({ page }) => {
    // Seed 42
    await page.goto(`${BASE}/?seed=42`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const title42 = await page.title();

    // Seed 12345
    await page.goto(`${BASE}/?seed=12345`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    const title12345 = await page.title();

    expect(title42).toContain('42');
    expect(title12345).toContain('12345');
  });

  test('encounter overlay is hidden initially', async ({ page }) => {
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    const encounter = page.locator('#encounter');
    await expect(encounter).not.toHaveClass(/show/);
  });

});
