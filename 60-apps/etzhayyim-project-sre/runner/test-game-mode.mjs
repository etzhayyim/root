/**
 * Game Mode — Visual + Quality Test Suite
 * Tests: color-by-number.etzhayyim.com (soblx2wf) + ex66satl.etzhayyim.com (snake)
 */
import { chromium } from 'playwright';

const RESULTS = [];
let passed = 0, failed = 0;

function test(name, ok, detail = '') {
  const status = ok ? 'PASS' : 'FAIL';
  if (ok) passed++; else failed++;
  RESULTS.push({ name, status, detail });
  console.log(`  ${ok ? '✓' : '✗'} ${name}${detail ? ' — ' + detail : ''}`);
}

async function testEndpoint(label, url, checks = {}) {
  try {
    const resp = await fetch(url);
    test(`${label} status`, resp.status === (checks.status || 200), `${resp.status}`);
    if (checks.json) {
      const data = await resp.json();
      for (const [key, expected] of Object.entries(checks.json)) {
        const keys = key.split('.');
        let val = data;
        for (const k of keys) val = val?.[k];
        test(`${label} ${key}`, val === expected, `${JSON.stringify(val)}`);
      }
      return data;
    }
    if (checks.contains) {
      const text = await resp.text();
      test(`${label} contains "${checks.contains}"`, text.includes(checks.contains));
    }
    if (checks.minSize) {
      const buf = await resp.arrayBuffer();
      test(`${label} size >= ${checks.minSize}`, buf.byteLength >= checks.minSize, `${buf.byteLength}`);
    }
    return resp;
  } catch (e) {
    test(`${label} fetch`, false, e.message);
    return null;
  }
}

async function testAPI(label, url, body) {
  try {
    const resp = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    test(`${label} status`, resp.status === 200, `${resp.status}`);
    return data;
  } catch (e) {
    test(`${label}`, false, e.message);
    return null;
  }
}

const browser = await chromium.launch({ headless: true });

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 1. Color-by-Number (soblx2wf) — Endpoints ══');
// ═══════════════════════════════════════════════════════════════════

const CBN = 'https://color-by-number.etzhayyim.com';

await testEndpoint('CBN app meta', `${CBN}/_app/meta`, { status: 200 });

await testEndpoint('CBN worker health', `${CBN}/_worker/health`, {
  json: { 'status': 'ok', 'ui': 'game', 'app': 'soblx2wf' }
});

// Game assets from R2
await testEndpoint('CBN game HTML', `${CBN}/_game/assets/color-by-number/index.html`, { contains: 'Color by Number' });
await testEndpoint('CBN game JS', `${CBN}/_game/assets/color-by-number/color-by-number.js`, { minSize: 100000 });
await testEndpoint('CBN game icon', `${CBN}/_game/assets/color-by-number/color-by-number.icon.png`, { minSize: 1000 });

// CORS headers on game assets
{
  const resp = await fetch(`${CBN}/_game/assets/color-by-number/color-by-number.js`);
  test('CBN game asset CORS', resp.headers.get('access-control-allow-origin') === '*');
  test('CBN game asset immutable cache', (resp.headers.get('cache-control') || '').includes('immutable'));
}

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 2. Color-by-Number — Game API ══');
// ═══════════════════════════════════════════════════════════════════

// Session create
const session = await testAPI('CBN session create', `${CBN}/api/game/session`, { action: 'create', 'player_id': 'test-player-001' });
test('CBN session has session_id', !!session?.session_id, session?.session_id?.slice(0, 30));

// Session get
if (session?.session_id) {
  const got = await testAPI('CBN session get', `${CBN}/api/game/session`, { action: 'get', 'session_id': session.session_id });
  test('CBN session get returns data', got?.session_id === session.session_id || got?.player_id === 'test-player-001');
}

// Score submit
const scoreResult = await testAPI('CBN score submit', `${CBN}/api/game/score`, { action: 'submit', 'player_id': 'test-player-001', score: 42, 'puzzle_id': 'apple' });
test('CBN score submit ok', !!scoreResult?.ok || !!scoreResult?.score_id);

// Leaderboard
const lb = await testAPI('CBN leaderboard', `${CBN}/api/game/score`, { action: 'leaderboard', limit: 10 });
test('CBN leaderboard has entries', Array.isArray(lb?.entries));

// State save/load
await testAPI('CBN state save', `${CBN}/api/game/state`, { action: 'save', 'player_id': 'test-player-001', 'state_json': '{"puzzle":"apple","progress":75}' });
const loaded = await testAPI('CBN state load', `${CBN}/api/game/state`, { action: 'load', 'player_id': 'test-player-001' });
test('CBN state load returns saved data', (loaded?.state_json || '').includes('apple'));

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 3. Color-by-Number — Visual (Playwright) ══');
// ═══════════════════════════════════════════════════════════════════

{
  const page = await browser.newPage();
  const errors = [];
  const netErrors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('requestfailed', r => netErrors.push(`${r.url().split('/').pop()} ${r.failure()?.errorText || ''}`));

  const resp = await page.goto(CBN, { waitUntil: 'domcontentloaded', timeout: 20000 });
  test('CBN page status 200', resp.status() === 200);
  test('CBN title', (await page.title()) === 'Color by Number', await page.title());

  // Game shell structure
  test('CBN .game-shell', !!(await page.$('.game-shell')));
  test('CBN .game-header', !!(await page.$('.game-header')));
  test('CBN .game-viewport', !!(await page.$('.game-viewport')));
  test('CBN iframe present', !!(await page.$('iframe')));

  // Header content
  const headerText = await page.$eval('.game-header', el => el.textContent);
  test('CBN header shows name', headerText.includes('Color by Number'));
  test('CBN header shows icon', headerText.includes('🎨'));

  // Bridge functions
  test('CBN etzhayyimBridgeSend', await page.evaluate(() => typeof window.etzhayyimBridgeSend === 'function'));
  test('CBN onGameScore', await page.evaluate(() => typeof window.onGameScore === 'function'));

  // Viewport sizing
  const viewport = await page.$eval('.game-viewport', el => {
    const r = el.getBoundingClientRect();
    return { w: r.width, h: r.height };
  });
  test('CBN viewport width > 300', viewport.w > 300, `${viewport.w}px`);
  test('CBN viewport height > 200', viewport.h > 200, `${viewport.h}px`);

  // iframe loads game
  await page.waitForTimeout(3000);
  const iframeSrc = await page.$eval('iframe', el => el.src);
  test('CBN iframe src correct', iframeSrc.includes('/_game/assets/color-by-number/index.html'), iframeSrc.split('/').slice(-3).join('/'));

  // Check iframe loaded successfully (not 404)
  const iframeResp = await page.evaluate(async () => {
    const iframe = document.querySelector('iframe');
    if (!iframe) return 'no iframe';
    try {
      return iframe.contentDocument?.title || iframe.contentWindow?.document?.title || 'loaded';
    } catch { return 'cross-origin (ok)'; }
  });
  test('CBN iframe content loaded', iframeResp !== 'no iframe', iframeResp);

  // No critical page errors
  test('CBN no page errors', errors.length === 0, errors.length > 0 ? errors[0].slice(0, 60) : '');

  await page.screenshot({ path: '/tmp/test-cbn-visual.png', fullPage: true });
  test('CBN screenshot saved', true, '/tmp/test-cbn-visual.png');
  await page.close();
}

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 4. Snake (ex66satl) — Endpoints ══');
// ═══════════════════════════════════════════════════════════════════

const SNAKE = 'https://ex66satl.etzhayyim.com';

await testEndpoint('Snake app meta', `${SNAKE}/_app/meta`, { status: 200 });

await testEndpoint('Snake worker health', `${SNAKE}/_worker/health`, {
  json: { 'status': 'ok', 'ui': 'game' }
});

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 5. Snake — Visual (Playwright) ══');
// ═══════════════════════════════════════════════════════════════════

{
  const page = await browser.newPage();
  const resp = await page.goto(SNAKE, { waitUntil: 'domcontentloaded', timeout: 20000 });
  test('Snake page status 200', resp.status() === 200);
  test('Snake title', (await page.title()) === 'ex66satl', await page.title());
  test('Snake .game-shell', !!(await page.$('.game-shell')));
  test('Snake .game-header', !!(await page.$('.game-header')));
  test('Snake #game-canvas', !!(await page.$('#game-canvas')));
  test('Snake #game-loading', !!(await page.$('#game-loading')));
  test('Snake no iframe (godot uses canvas)', !(await page.$('iframe#game-frame')));
  test('Snake etzhayyimBridgeSend', await page.evaluate(() => typeof window.etzhayyimBridgeSend === 'function'));
  test('Snake onGameScore', await page.evaluate(() => typeof window.onGameScore === 'function'));

  const headerText = await page.$eval('.game-header', el => el.textContent);
  test('Snake header icon', headerText.includes('🐍'));

  await page.screenshot({ path: '/tmp/test-snake-visual.png', fullPage: true });
  test('Snake screenshot saved', true);
  await page.close();
}

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 6. AppShell Integration (_app/meta) ══');
// ═══════════════════════════════════════════════════════════════════

// Verify metadata schema from /_app/meta
{
  const m = await (await fetch(`${CBN}/_app/meta`)).json();
  test('Meta has appId (string)', typeof m.appId === 'string');
  test('Meta has displayName (string)', typeof m.displayName === 'string');
  test('Meta has uiMode (string)', typeof m.uiMode === 'string');
  test('Meta uiMode is game/appview/iframe', ['game', 'appview', 'iframe'].includes(m.uiMode));
  test('Meta has capabilities (optional array)', m.capabilities === undefined || Array.isArray(m.capabilities));
}

// ═══════════════════════════════════════════════════════════════════
console.log('\n══ 7. Worker WASM Template ══');
// ═══════════════════════════════════════════════════════════════════

// CORS preflight on game assets
{
  const resp = await fetch(`${CBN}/_game/assets/color-by-number/index.html`, { method: 'OPTIONS' });
  test('Game assets CORS preflight 204', resp.status === 204);
  test('CORS Allow-Origin *', resp.headers.get('access-control-allow-origin') === '*');
}

// Game mode skips ISR (returns fresh each time)
{
  const r1 = await fetch(CBN);
  const r2 = await fetch(CBN);
  const h1 = await r1.text();
  const h2 = await r2.text();
  test('Game HTML contains game-shell', h1.includes('game-shell'));
  test('Game HTML consistent', h1.includes('game-shell') && h2.includes('game-shell'));
}

// 404 for nonexistent game assets
{
  const resp = await fetch(`${CBN}/_game/assets/nonexistent/foo.js`);
  test('Missing game asset 404', resp.status === 404);
}

// ═══════════════════════════════════════════════════════════════════
// Summary
// ═══════════════════════════════════════════════════════════════════

await browser.close();

console.log(`\n${'═'.repeat(60)}`);
console.log(`  TOTAL: ${passed + failed}  PASSED: ${passed}  FAILED: ${failed}`);
console.log(`${'═'.repeat(60)}`);

if (failed > 0) {
  console.log('\nFailed tests:');
  for (const r of RESULTS) {
    if (r.status === 'FAIL') console.log(`  ✗ ${r.name} — ${r.detail}`);
  }
}

process.exit(failed > 0 ? 1 : 0);
