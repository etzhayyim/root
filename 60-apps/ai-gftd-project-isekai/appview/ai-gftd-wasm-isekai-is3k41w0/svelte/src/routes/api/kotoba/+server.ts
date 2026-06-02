// Server-side proxy to a local `kotoba serve` direct-SPARQL endpoint.
// Keeps the bearer token server-side (read from env) and avoids browser CORS —
// the /fleet page POSTs { query } here and gets the kotoba JSON back.
import { error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  const { query } = await request.json().catch(() => ({}));
  if (!query || typeof query !== 'string') throw error(400, 'missing "query" (SPARQL string)');

  const base = (env.KOTOBA_URL ?? 'http://localhost:8080').replace(/\/$/, '');
  const tok = env.KOTOBA_TOKEN ?? '';
  let resp: Response;
  try {
    resp = await fetch(`${base}/xrpc/com.etzhayyim.apps.kotoba.graph.sparql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(tok ? { Authorization: `Bearer ${tok}` } : {})
      },
      body: JSON.stringify({ query })
    });
  } catch {
    throw error(502, `kotoba unreachable at ${base} — start it with: KOTOBA_IPFS=off kotoba serve`);
  }
  const body = await resp.text();
  return new Response(body, {
    status: resp.status,
    headers: { 'Content-Type': 'application/json' }
  });
};
