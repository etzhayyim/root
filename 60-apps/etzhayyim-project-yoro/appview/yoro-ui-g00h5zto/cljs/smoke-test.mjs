// Headless render smoke test for the cljs UI (reuses svelte's playwright).
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(here, '..', 'svelte', 'package.json'));
const { chromium } = require('@playwright/test');

const browser = await chromium.launch({ channel: 'chrome' });
const page = await browser.newPage();
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(`PAGEERROR: ${e.message}`));

await page.goto('http://localhost:8700/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);

const text = await page.locator('#app').innerText().catch(() => '');
console.log('--- #app text (first 400 chars) ---');
console.log(text.slice(0, 400) || '(EMPTY — blank screen)');
console.log('--- console/page errors ---');
console.log(errors.length ? errors.join('\n') : '(none)');

// exercise tabs
for (const tab of ['History', 'HITL', 'Topology']) {
  await page.getByRole('button', { name: tab, exact: true }).click().catch((e) => errors.push(`tab ${tab}: ${e.message}`));
  await page.waitForTimeout(300);
}
const histBtn = page.getByRole('button', { name: 'プロフィール閲覧を記録' });
await page.getByRole('button', { name: 'History', exact: true }).click();
await histBtn.click().catch((e) => errors.push(`history click: ${e.message}`));
await page.waitForTimeout(300);
const histText = await page.locator('#app').innerText().catch(() => '');
console.log('--- after history record ---');
console.log(histText.includes('Demo Profile') ? 'history entry rendered ✓' : 'history entry MISSING ✗');

// exercise InferenceConsent modal: open → scroll → check → accept
await page.getByRole('button', { name: 'Components', exact: true }).click();
await page.evaluate(() => localStorage.removeItem('yoro-inference-tos-accepted'));
await page.getByRole('button', { name: /推論に参加/ }).click();
await page.waitForTimeout(300);
const modalVisible = await page.getByRole('dialog').isVisible().catch(() => false);
console.log('--- inference consent ---');
console.log(modalVisible ? 'modal opened ✓' : 'modal MISSING ✗');
if (modalVisible) {
  const acceptBtn = page.getByRole('button', { name: 'Agree and Join Inference' });
  console.log('accept disabled before scroll:', await acceptBtn.isDisabled() ? '✓' : '✗');
  await page.locator('.overflow-y-auto').evaluate((el) => { el.scrollTop = el.scrollHeight; });
  await page.waitForTimeout(200);
  // click (not check): reagent controlled inputs re-render async, check()'s
  // immediate post-click assertion races the next animation frame
  await page.getByRole('checkbox').click();
  await page.waitForTimeout(200);
  console.log('checkbox checked:', await page.getByRole('checkbox').isChecked() ? '✓' : '✗');
  console.log('accept enabled after scroll+check:', await acceptBtn.isEnabled() ? '✓' : '✗');
  await acceptBtn.click();
  await page.waitForTimeout(300);
  const accepted = await page.evaluate(() => localStorage.getItem('yoro-inference-tos-accepted'));
  const resolvedText = await page.locator('#app').innerText();
  console.log('localStorage accepted:', accepted === 'accepted' ? '✓' : `✗ (${accepted})`);
  console.log('promise resolved:', resolvedText.includes('consent resolved') ? '✓' : '✗');
}

await page.screenshot({ path: 'smoke-screenshot.png', fullPage: false });
console.log('screenshot: smoke-screenshot.png');
console.log('--- final errors ---');
console.log(errors.length ? errors.join('\n') : '(none)');
await browser.close();
