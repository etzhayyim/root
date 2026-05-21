import { test, expect } from '@playwright/test';

const KAMI = process.env.KAMI_BASE_URL ?? 'https://kami.etzhayyim.com';
const RT = process.env.KAMI_RT_BASE_URL ?? 'https://kami-rt.etzhayyim.com';

const COLOR_ISLAND_ID = 'isl-23e9ecedc0';
const COLOR_DID = 'did:web:kami.etzhayyim.com:island:colorbynumber';

test.describe('Color by Number Island', () => {
  test('create + generate + publish lifecycle', async ({ request }) => {
    // Create
    const create = await request.post(`${KAMI}/xrpc/v1/create-island`, {
      data: { title: 'E2E Color Puzzle', genre: 'puzzle', 'maxPlayers': 1 },
    });
    expect(create.ok()).toBeTruthy();
    const { islandId } = await create.json();
    expect(islandId).toBeTruthy();

    // Generate scene
    const gen = await request.post(`${KAMI}/xrpc/v1/generate-island`, {
      data: { islandId, prompt: 'relaxing color puzzle garden', genre: 'puzzle' },
    });
    expect(gen.ok()).toBeTruthy();
    const genData = await gen.json();
    expect(genData.source).toBe('llm');

    // Publish
    const pub = await request.post(`${KAMI}/xrpc/v1/publish-island`, {
      data: { islandId, title: 'E2E Color Puzzle', tags: ['puzzle', 'e2e'] },
    });
    expect(pub.ok()).toBeTruthy();
    const pubData = await pub.json();
    expect(pubData.state).toBe('published');
    expect(pubData.gamesUrl).toContain('games.etzhayyim.com');
  });

  test('spawn player actor on color island', async ({ request }) => {
    const res = await request.post(`${RT}/xrpc/v1/spawn-actor`, {
      data: { 'actorType': 'player', 'islandId': COLOR_ISLAND_ID, position: [0, 1, 0] },
    });
    expect(res.ok()).toBeTruthy();
    const data = await res.json();
    expect(data.actorId).toBeTruthy();
    expect(data.islandId).toBe(COLOR_ISLAND_ID);
  });

  test('register DID identity', async ({ request }) => {
    const res = await request.post(`${KAMI}/xrpc/v1/register-island-identity`, {
      data: {
        'islandId': COLOR_ISLAND_ID,
        slug: 'colorbynumber-e2e',
        title: 'Color Zen E2E',
        genre: 'puzzle',
        'maxPlayers': 1,
      },
    });
    expect(res.ok()).toBeTruthy();
    const data = await res.json();
    expect(data.did).toContain('did:web:kami.etzhayyim.com:island:');
    expect(data.registered).toBeTruthy();
  });
});
