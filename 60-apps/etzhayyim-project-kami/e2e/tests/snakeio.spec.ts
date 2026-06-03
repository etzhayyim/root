import { test, expect } from '@playwright/test';

const KAMI = process.env.KAMI_BASE_URL ?? 'https://kami.etzhayyim.com';
const RT = process.env.KAMI_RT_BASE_URL ?? 'https://kami-rt.etzhayyim.com';
const WORLDS = process.env.WORLDS_BASE_URL ?? 'https://worlds.etzhayyim.com';

const SNAKE_ISLAND_ID = 'isl-23ca92ce40';

test.describe('Snake Classic Island', () => {
  test('full lifecycle: create → generate → publish → portal → actor', async ({ request }) => {
    // Create
    const create = await request.post(`${KAMI}/xrpc/v1/create-island`, {
      data: { title: 'E2E Snake Arena', genre: 'arcade', 'maxPlayers': 4 },
    });
    expect(create.ok()).toBeTruthy();
    const { islandId } = await create.json();
    expect(islandId).toMatch(/^isl-/);

    // Generate
    const gen = await request.post(`${KAMI}/xrpc/v1/generate-island`, {
      data: { islandId, prompt: 'classic snake game arena with obstacles', genre: 'arcade' },
    });
    expect(gen.ok()).toBeTruthy();

    // Publish
    const pub = await request.post(`${KAMI}/xrpc/v1/publish-island`, {
      data: { islandId, title: 'E2E Snake Arena', tags: ['arcade', 'snake', 'e2e'] },
    });
    expect(pub.ok()).toBeTruthy();
    const pubData = await pub.json();
    expect(pubData.versionId).toMatch(/^ver-/);

    // Register portal
    const portal = await request.post(`${WORLDS}/xrpc/v1/register-portal`, {
      data: { islandId, title: 'E2E Snake Arena', genre: 'arcade', 'maxPlayers': 4 },
    });
    expect(portal.ok()).toBeTruthy();
    const portalData = await portal.json();
    expect(portalData.portal).toBeDefined();

    // Spawn actor
    const spawn = await request.post(`${RT}/xrpc/v1/spawn-actor`, {
      data: { 'actorType': 'player', islandId, position: [0, 1, 0] },
    });
    expect(spawn.ok()).toBeTruthy();
    const spawnData = await spawn.json();
    expect(spawnData.actorId).toMatch(/^act-/);
  });

  test('existing snake island: spawn + despawn', async ({ request }) => {
    // Spawn
    const spawn = await request.post(`${RT}/xrpc/v1/spawn-actor`, {
      data: { 'actorType': 'snake', 'islandId': SNAKE_ISLAND_ID, position: [5, 0.5, 5] },
    });
    expect(spawn.ok()).toBeTruthy();
    const { actorId } = await spawn.json();

    // Despawn
    const despawn = await request.post(`${RT}/xrpc/v1/despawn-actor`, {
      data: { actorId },
    });
    expect(despawn.ok()).toBeTruthy();
    const despawnData = await despawn.json();
    expect(despawnData.despawned).toBeTruthy();
  });

  test('register snake DID', async ({ request }) => {
    const res = await request.post(`${KAMI}/xrpc/v1/register-island-identity`, {
      data: {
        'islandId': SNAKE_ISLAND_ID,
        slug: 'snake-e2e',
        title: 'Snake Classic E2E',
        genre: 'arcade',
        'maxPlayers': 1,
      },
    });
    expect(res.ok()).toBeTruthy();
    const data = await res.json();
    expect(data.registered).toBeTruthy();
  });
});
