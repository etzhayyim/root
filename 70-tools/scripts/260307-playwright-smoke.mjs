#!/usr/bin/env node
import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const DEFAULT_URLS = ['https://6ir.etzhayyim.com/', 'https://society6.etzhayyim.com/'];
const urls = process.argv.slice(2).length > 0 ? process.argv.slice(2) : DEFAULT_URLS;

const stamp = new Date().toISOString().replace(/[:.]/g, '-');
const outDir = path.join(process.cwd(), 'reports', `260307-playwright-smoke-${stamp}`);
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 390, height: 844 } });

let failed = false;

for (const url of urls) {
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const badResponses = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('response', (res) => {
    if (res.status() >= 400) {
      badResponses.push({
        status: res.status(),
        url: res.url(),
        type: res.request().resourceType(),
      });
    }
  });

  let status = null;
  let navError = null;
  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    status = response?.status() ?? null;
  } catch (error) {
    navError = String(error?.message ?? error);
  }

  await page.waitForTimeout(3000);

  const hostname = new URL(url).hostname;
  const screenshotPath = path.join(outDir, `${hostname}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });

  const summary = {
    url,
    status,
    navError,
    finalUrl: page.url(),
    title: await page.title().catch((_err) => ''),
    consoleErrorCount: consoleErrors.length,
    pageErrorCount: pageErrors.length,
    badResponseCount: badResponses.length,
    consoleErrors,
    pageErrors,
    badResponses,
    screenshotPath,
  };

  const summaryPath = path.join(outDir, `${hostname}.json`);
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

  const ok = status === 200 && !navError && consoleErrors.length === 0 && pageErrors.length === 0 && badResponses.length === 0;
  if (!ok) {
    failed = true;
  }

  console.log(JSON.stringify({ hostname, ok, status, navError, consoleErrors: consoleErrors.length, pageErrors: pageErrors.length, badResponses: badResponses.length }, null, 2));
  await page.close();
}

await context.close();
await browser.close();

if (failed) {
  console.error(`Smoke check failed. Reports: ${outDir}`);
  process.exit(1);
}

console.log(`Smoke check passed. Reports: ${outDir}`);
