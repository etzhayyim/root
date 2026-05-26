import { OrganismPostDrainer } from './index';

describe('OrganismPostDrainer', () => {
  it('should parse and process a valid app.bsky.feed.post line', async () => {
    const drainer = new OrganismPostDrainer('dummy.ndjson', 'https://dummy.pds');

    // Spy on console.log to verify behavior without mocking the sdk yet
    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    const validPost = JSON.stringify({
      v: 1,
      ts: 1748131234567,
      actorDid: "did:web:etzhayyim.com:actor:c10101500",
      code: "10101500",
      text: "Test post",
      lexicon: "app.bsky.feed.post",
      createdAt: "2026-05-24T01:23:45Z"
    });

    await drainer.processLine(validPost);

    expect(logSpy).toHaveBeenCalledWith(
      expect.stringContaining('[Drainer] Dispatching post for did:web:etzhayyim.com:actor:c10101500')
    );

    logSpy.mockRestore();
  });

  it('should parse and process a valid app.etzhayyim.apps.etzhayyim.message line', async () => {
    const drainer = new OrganismPostDrainer('dummy.ndjson', 'https://dummy.pds');

    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    const validMessage = JSON.stringify({
      v: 1,
      ts: 1748131234568,
      actorDid: "did:web:etzhayyim.com:actor:c10101500",
      recipientDid: "did:web:etzhayyim.com:actor:c10101501",
      encryptedPayload: "base64encodedencrypteddata",
      lexicon: "app.etzhayyim.apps.etzhayyim.message",
      createdAt: "2026-05-26T01:23:45Z"
    });

    await drainer.processLine(validMessage);

    expect(logSpy).toHaveBeenCalledWith(
      expect.stringContaining('[Drainer] Dispatching message from did:web:etzhayyim.com:actor:c10101500 to did:web:etzhayyim.com:actor:c10101501')
    );

    logSpy.mockRestore();
  });

  it('should handle invalid JSON gracefully', async () => {
    const drainer = new OrganismPostDrainer('dummy.ndjson', 'https://dummy.pds');
    const errSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    await drainer.processLine('invalid json {');

    expect(errSpy).toHaveBeenCalledWith(
      'Failed to parse line:', 'invalid json {'
    );

    errSpy.mockRestore();
  });
});
