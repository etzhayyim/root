const ACTOR = 'did:web:mailer.gftd.ai';
const APP = 'mailer';
const DEFAULT_DISPATCHER_URL = 'https://dispatcher.gftd.ai';
// Dispatcher is reached only via the public `dispatcher.gftd.ai` host (CF Tunnel
// → bpmn-dispatcher). The old plaintext dev IPs (66.42.104.29.sslip.io etc.) are
// dead and were passing their bare "error code: 520" back to the client whenever
// the primary returned a transient CF error — so the fallback list is empty.
// Override the primary via the `DISPATCHER_URL` secret if ever needed.
const DISPATCHER_FALLBACK_URLS: string[] = [];
const NSID_PREFIX = 'ai.gftd.apps.mailer.';
const PDS_ORIGIN = 'https://atproto.gftd.ai';

type SecretBinding = { get(): Promise<string> };
type Env = Record<string, unknown> & {
  APP_NANOID?: string;
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | SecretBinding;
};

type PlatformLike = {
  env?: Env;
};

export function metaResponse(platform: PlatformLike | undefined): Response {
  return json({
    ok: true,
    actor: ACTOR,
    nanoid: platform?.env?.APP_NANOID ?? 'a8wwtz73',
    execution: 'edge-assets+xrpc-proxy+bpmn+langserver',
    businessLogic: '20-actors/magatama/py/src/pymagatama/ingest/mailer.py',
    bpmn: 'etzhayyim-root/00-contracts/bpmn/ai/gftd/mailer',
  });
}

export async function proxyApi(
  platform: PlatformLike | undefined,
  nsid: string,
  url: URL,
): Promise<Response> {
  const direct = await directMailerRead(nsid, url);
  if (direct) {
    return direct;
  }
  return proxyToDispatcher(platform?.env ?? {}, nsid, queryBody(url));
}

export async function proxyXrpc(
  platform: PlatformLike | undefined,
  request: Request,
  nsid: string,
): Promise<Response> {
  const url = new URL(request.url);
  if (nsid.startsWith(NSID_PREFIX) && (request.method === 'POST' || request.method === 'GET')) {
    const direct = await directMailerRead(nsid, url);
    if (direct) {
      return direct;
    }
    const body = await bodyWithQuery(request, url);
    if (body.__invalidJson) {
      return json({ error: 'InvalidJson' }, 400);
    }
    return proxyToDispatcher(platform?.env ?? {}, nsid, body);
  }
  return proxyToPds(request, nsid);
}

async function directMailerRead(nsid: string, url: URL): Promise<Response | null> {
  if (nsid === 'ai.gftd.apps.mailer.health') {
    return json({ ok: true, app: 'mailer', ts: new Date().toISOString() });
  }
  if (nsid === 'ai.gftd.apps.mailer.listBindings') {
    return json({ items: [], count: 0 });
  }
  return null;
}

function queryBody(url: URL): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const [key, value] of url.searchParams) {
    body[key] = value;
  }
  return body;
}

async function bodyWithQuery(request: Request, url: URL): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  if (request.method === 'POST') {
    const text = await request.text();
    try {
      body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
    } catch {
      return { __invalidJson: true };
    }
  }
  for (const [key, value] of url.searchParams) {
    if (!(key in body)) {
      body[key] = value;
    }
  }
  return body;
}

async function proxyToDispatcher(env: Env, nsid: string, body: Record<string, unknown>): Promise<Response> {
  const base = (env.DISPATCHER_URL ?? DEFAULT_DISPATCHER_URL).replace(/\/+$/, '');
  const bases = [base, ...DISPATCHER_FALLBACK_URLS].filter(
    (item, index, items) => items.indexOf(item) === index,
  );
  const headers: Record<string, string> = { 'content-type': 'application/json' };
  const trust = await internalTrustSecret(env);
  if (trust) {
    headers['x-internal-trust'] = trust;
  }

  const payload = JSON.stringify(body);
  let lastError = '';
  for (const origin of bases) {
    try {
      const response = await fetch(`${origin}/xrpc/${nsid}`, {
        method: 'POST',
        headers,
        body: payload,
        signal: AbortSignal.timeout(25_000),
      });
      const text = await response.text();
      if (isCloudflareOriginError(response.status, text)) {
        lastError = `Cloudflare ${response.status} from ${origin}`;
        continue;
      }
      return new Response(text, {
        status: response.status,
        headers: {
          'content-type': response.headers.get('content-type') ?? 'application/json',
          'cache-control': 'no-store',
          'x-dispatcher-origin': origin,
        },
      });
    } catch (error) {
      lastError = `${origin}: ${String(error)}`;
    }
  }
  return json({ error: 'DispatcherUnavailable', message: lastError }, 502);
}

function isCloudflareOriginError(status: number, text: string): boolean {
  return (
    (status === 403 && text.includes('error code: 1003')) ||
    (status >= 500 &&
      status < 600 &&
      (text.toLowerCase().includes('cloudflare') || /error code:\s*\d+/i.test(text)))
  );
}

async function proxyToPds(request: Request, nsid: string): Promise<Response> {
  const inUrl = new URL(request.url);
  const outUrl = new URL(`/xrpc/${nsid}${inUrl.search}`, PDS_ORIGIN);
  const headers = new Headers(request.headers);
  headers.delete('host');
  headers.delete('content-length');

  const method = request.method.toUpperCase();
  const body = method === 'GET' || method === 'HEAD' ? undefined : await request.arrayBuffer();
  const response = await fetch(outUrl, {
    method,
    headers,
    body: body && body.byteLength > 0 ? body : undefined,
  });
  const outHeaders = new Headers(response.headers);
  outHeaders.set('access-control-allow-origin', '*');
  return new Response(response.body, { status: response.status, headers: outHeaders });
}

async function internalTrustSecret(env: Env): Promise<string> {
  const binding = env.DISPATCHER_INTERNAL_SECRET;
  if (!binding) {
    return '';
  }
  try {
    return typeof binding === 'string' ? binding : await binding.get();
  } catch {
    return '';
  }
}

export function notFound(): Response {
  return json({ error: 'NotFound', message: `${APP} not found` }, 404);
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json',
      'cache-control': 'no-store',
    },
  });
}
