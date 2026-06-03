import '../lib/components/SreToolbar.svelte';

const TOOLBAR_TAG = 'etzhayyim-project-sre-toolbar';

function init() {
  if (document.querySelector(TOOLBAR_TAG)) return;

  const el = document.createElement(TOOLBAR_TAG);
  document.body.appendChild(el);

  // Inject page-context script for Clerk token extraction
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('content/inject.js');
  script.type = 'module';
  (document.head || document.documentElement).appendChild(script);
  script.onload = () => script.remove();

  // Listen for Clerk token
  window.addEventListener('message', (event) => {
    if (event.data?.type === 'CLERK_TOKEN') {
      el.setAttribute('auth-token', event.data.token || '');
    }
  });

  // Request token periodically
  window.postMessage({ type: 'GET_CLERK_TOKEN' }, '*');
  setInterval(() => {
    window.postMessage({ type: 'GET_CLERK_TOKEN' }, '*');
  }, 60_000);
}

if (document.readyState === 'complete') {
  init();
} else {
  window.addEventListener('load', init);
}
