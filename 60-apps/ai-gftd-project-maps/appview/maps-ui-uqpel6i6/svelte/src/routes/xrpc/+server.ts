import { json } from '@sveltejs/kit';

const XRPC_BASE = '/xrpc';
const UPSTREAM = 'https://uqpel6i6.gftd.ai';

export async function GET() {
  return json({
    ok: true,
    endpoint: XRPC_BASE,
    usage: `${XRPC_BASE}/{nsid}`,
    upstream: UPSTREAM,
  });
}

export async function POST() {
  return json({ error: 'NsidRequired', message: 'Use /xrpc/{nsid}' }, { status: 400 });
}
