/**
 * Worker wrapper — fixes Content-Type for .htm files served by Workers Assets.
 *
 * Workers Assets serves .htm as application/octet-stream by default.
 * This wrapper intercepts and corrects MIME types.
 */
const MIME_FIX = {
  '.htm': 'text/html; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.jsonld': 'application/ld+json; charset=utf-8',
  '.wasm': 'application/wasm',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Embed redirect: ?embed=1 or / → serve game HTML
    if (url.pathname === '/' || url.pathname === '/embed') {
      const gameUrl = new URL('/isekai.htm', url.origin);
      if (url.search) gameUrl.search = url.search;
      const assetReq = new Request(gameUrl.toString(), request);
      const res = await env.ASSETS.fetch(assetReq);
      return new Response(res.body, {
        status: res.status,
        headers: {
          ...Object.fromEntries(res.headers.entries()),
          'content-type': 'text/html; charset=utf-8',
          'access-control-allow-origin': '*',
        },
      });
    }

    // Pass through to Assets
    const res = await env.ASSETS.fetch(request);

    // Fix MIME types
    const ext = url.pathname.match(/(\.[a-z]+)$/i)?.[1]?.toLowerCase();
    const correctMime = ext ? MIME_FIX[ext] : null;
    if (correctMime && res.headers.get('content-type') !== correctMime) {
      const fixed = new Response(res.body, { status: res.status, headers: new Headers(res.headers) });
      fixed.headers.set('content-type', correctMime);
      fixed.headers.set('access-control-allow-origin', '*');
      return fixed;
    }

    return res;
  },
};
