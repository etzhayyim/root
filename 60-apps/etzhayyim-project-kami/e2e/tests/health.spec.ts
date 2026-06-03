import { test, expect } from '@playwright/test';

const KAMI = process.env.KAMI_BASE_URL ?? 'https://kami.etzhayyim.com';
const WORLDS = process.env.WORLDS_BASE_URL ?? 'https://worlds.etzhayyim.com';
const RT = process.env.KAMI_RT_BASE_URL ?? 'https://kami-rt.etzhayyim.com';

test.describe('KAMI Platform Health', () => {
  test('kami.etzhayyim.com health', async ({ request }) => {
    const res = await request.get(`${KAMI}/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe('ok');
  });

  test('worlds.etzhayyim.com health', async ({ request }) => {
    const res = await request.get(`${WORLDS}/health`);
    expect(res.ok()).toBeTruthy();
  });

  test('kami-rt.etzhayyim.com health', async ({ request }) => {
    const res = await request.get(`${RT}/health`);
    expect(res.ok()).toBeTruthy();
  });

  test('kami.etzhayyim.com _app/meta', async ({ request }) => {
    const res = await request.get(`${KAMI}/_app/meta`);
    expect(res.ok()).toBeTruthy();
    const meta = await res.json();
    expect(meta.version).toBeDefined();
  });
});
