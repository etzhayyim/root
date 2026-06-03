// Wrapper: fix Content-Type for static assets (CF edge cached wrong MIME from previous broken deploy)
import worker from './svelte/.svelte-kit/cloudflare/_worker.js';

const MIME = {
  '.js': 'application/javascript',
  '.mjs': 'application/javascript',
  '.css': 'text/css',
  '.wasm': 'application/wasm',
  '.json': 'application/json',
  '.htm': 'text/html',
  '.html': 'text/html',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.mp3': 'audio/mpeg',
  '.woff2': 'font/woff2',
  '.map': 'application/json',
};

export default {
  async fetch(request, env, ctx) {
    const res = await worker.fetch(request, env, ctx);
    const url = new URL(request.url);
    const path = url.pathname;

    // Fix MIME for static assets that CF edge may have cached with wrong content-type
    const ext = path.includes('.') ? '.' + path.split('.').pop() : '';
    const correctMime = MIME[ext];
    if (correctMime && res.headers.get('content-type') !== correctMime) {
      const fixed = new Response(res.body, res);
      fixed.headers.set('content-type', correctMime);
      fixed.headers.set('x-mime-fix', `${ext}:${res.headers.get('content-type')}->${correctMime}`);
      // Bust the bad cache by setting a short max-age then re-caching correctly
      if (path.includes('/immutable/')) {
        fixed.headers.set('cache-control', 'public, immutable, max-age=31536000');
      }
      return fixed;
    }
    return res;
  }
};
