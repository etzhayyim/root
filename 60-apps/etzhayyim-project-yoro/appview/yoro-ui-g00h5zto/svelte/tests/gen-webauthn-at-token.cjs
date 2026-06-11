#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  ({ chromium } = require('@playwright/test'));
}

const DEFAULT_OUT = path.resolve(process.cwd(), '../../../../../tmp/e2e/yoro-at-token.json');
const RETURN_TO = 'https://yoro.etzhayyim.com/profile/did:web:a7m8oocs.etzhayyim.com.writer.llm';

function argValue(name) {
  const i = process.argv.indexOf(name);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return '';
}

const outPath = argValue('--out') || process.env.YORO_AT_TOKEN_CACHE_FILE || DEFAULT_OUT;
const quiet = process.argv.includes('--quiet');

function log(...args) {
  if (!quiet) console.log(...args);
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);

  let authenticatorId = '';
  try {
    await cdp.send('WebAuthn.enable');
    const added = await cdp.send('WebAuthn.addVirtualAuthenticator', {
      options: {
        protocol: 'ctap2',
        transport: 'internal',
        hasResidentKey: true,
        hasUserVerification: true,
        isUserVerified: true,
        automaticPresenceSimulation: true,
      },
    });
    authenticatorId = String(added.authenticatorId || '');

    // Create account with passkey and handoff to yoro.
    await page.goto(`https://auth.etzhayyim.com/sign-up?returnTo=${encodeURIComponent(RETURN_TO)}`, {
      waitUntil: 'domcontentloaded',
      timeout: 60_000,
    });

    const createBtn = page.getByRole('button', { name: /create account/i });
    await createBtn.waitFor({ timeout: 15_000 });
    await createBtn.click();

    const freePlanBtn = page.getByRole('button', { name: /^free/i }).first();
    await freePlanBtn.waitFor({ timeout: 20_000 });
    await freePlanBtn.click();

    const startFreeBtn = page.getByRole('button', { name: /start free/i });
    await startFreeBtn.waitFor({ timeout: 15_000 });
    await startFreeBtn.click();

    await page.waitForURL(/yoro\.etzhayyim\.ai/i, { timeout: 30_000 });
    await page.waitForTimeout(3000);

    const session = await page.evaluate(() => {
      const raw = localStorage.getItem('etzhayyim-auth-session');
      return raw ? JSON.parse(raw) : null;
    });

    const accessJwt = session && session.accessJwt ? String(session.accessJwt) : '';
    if (!accessJwt) {
      throw new Error('WebAuthn completed but accessJwt was not found in etzhayyim-auth-session');
    }

    const payload = {
      source: 'webauthn-e2e',
      obtainedAt: new Date().toISOString(),
      accessJwt,
      refreshJwt: session.refreshJwt ? String(session.refreshJwt) : '',
      did: session.did ? String(session.did) : '',
      handle: session.handle ? String(session.handle) : '',
      expiresAt: session.expiresAt || 0,
    };

    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, JSON.stringify(payload, null, 2));
    log(`saved token cache: ${outPath}`);
    process.stdout.write(accessJwt);
  } finally {
    if (authenticatorId) {
      await cdp.send('WebAuthn.removeVirtualAuthenticator', { authenticatorId }).catch((error) => {
        console.warn('[silent-fail] gen-webauthn-at-token.cjs: removeVirtualAuthenticator failed', error);
      });
    }
    await browser.close();
  }
})().catch((e) => {
  console.error(String(e && e.message ? e.message : e));
  process.exit(1);
});
