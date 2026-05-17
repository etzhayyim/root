// MF CSV Ingest Helper — background service worker.
//
// The extension maintains a single "pending download name" slot. When the user
// picks a target in the popup, that slot is set. Chrome's onDeterminingFilename
// listener watches every new download; if the URL is from moneyforward.com AND
// a pending name is set, the download is rewritten to ~/Downloads/mf-ingest/<name>
// (conflictAction=overwrite) and the slot is cleared.
//
// This design lets the user trigger MoneyForward's native export UI (which knows
// the right CSRF / cookies / date ranges) while the extension only intervenes at
// the download step to put the file in a predictable place with a canonical name.

const STORAGE_KEY = 'pendingName';

async function getPending() {
  const { [STORAGE_KEY]: name } = await chrome.storage.session.get(STORAGE_KEY);
  return name ?? null;
}

async function setPending(name) {
  await chrome.storage.session.set({ [STORAGE_KEY]: name });
}

async function clearPending() {
  await chrome.storage.session.remove(STORAGE_KEY);
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    if (msg?.type === 'setNext') {
      await setPending(msg.filename);
      sendResponse({ ok: true, pending: msg.filename });
    } else if (msg?.type === 'getPending') {
      sendResponse({ pending: await getPending() });
    } else if (msg?.type === 'clear') {
      await clearPending();
      sendResponse({ ok: true });
    }
  })();
  return true; // keep sendResponse alive for async
});

chrome.downloads.onDeterminingFilename.addListener(async (item, suggest) => {
  try {
    if (!item.url || !item.url.includes('moneyforward.com')) {
      suggest();
      return;
    }
    const pending = await getPending();
    if (!pending) {
      suggest();
      return;
    }
    await clearPending();
    suggest({
      filename: `mf-ingest/${pending}`,
      conflictAction: 'overwrite'
    });
    // Broadcast completion so popup can refresh
    chrome.runtime.sendMessage({ type: 'captured', filename: pending, original: item.filename }).catch(() => {});
  } catch (err) {
    console.error('[mf-ingest] onDeterminingFilename error', err);
    suggest();
  }
});
