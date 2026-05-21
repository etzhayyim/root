chrome.runtime.onInstalled.addListener(() => {
  console.log('[SRE Toolbar] Extension installed');
});

chrome.runtime.onMessage.addListener(
  (
    message: { type?: string },
    _sender: chrome.runtime.MessageSender,
    sendResponse: (response?: unknown) => void
  ) => {
  if (message.type === 'GET_STATUS') {
    sendResponse({ status: 'ok', version: '1.0.0' });
  }
  return true;
});
