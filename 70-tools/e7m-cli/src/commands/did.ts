import { Command } from 'commander';

const DEFAULT_DID_URL = 'https://etzhayyim.com/.well-known/did.json';
const UNI_RESOLVER = 'https://dev.uniresolver.io/1.0/identifiers/did:web:etzhayyim.com';

type DidDoc = {
  id?: string;
  '@context'?: string | string[];
  verificationMethod?: Array<{ id?: string; type?: string; controller?: string; publicKeyMultibase?: string }>;
  service?: Array<{ id?: string; type?: string; serviceEndpoint?: string }>;
  alsoKnownAs?: string[];
};

async function fetchJson(url: string): Promise<{ status: number; body: unknown }> {
  const res = await fetch(url, { redirect: 'follow' });
  const text = await res.text();
  let body: unknown;
  try { body = JSON.parse(text); } catch { body = text; }
  return { status: res.status, body };
}

export const didCmd = new Command('did').description('Manage did:web:etzhayyim.com identifiers');

didCmd
  .command('verify')
  .description('Fetch and validate did:web:etzhayyim.com')
  .option('--url <url>', 'override DID document URL', DEFAULT_DID_URL)
  .option('--uniresolver', 'also resolve via dev.uniresolver.io')
  .action(async (opts: { url: string; uniresolver?: boolean }) => {
    console.log(`>> GET ${opts.url}`);
    let failed = false;
    try {
      const { status, body } = await fetchJson(opts.url);
      if (status !== 200) {
        console.error(`HTTP ${status}`);
        failed = true;
      }
      if (typeof body !== 'object' || body === null) {
        console.error('Body is not JSON object.');
        failed = true;
      } else {
        const d = body as DidDoc;
        const checks: Array<[string, boolean, string]> = [
          ['id == did:web:etzhayyim.com', d.id === 'did:web:etzhayyim.com', String(d.id)],
          ['@context present',            !!d['@context'],                  JSON.stringify(d['@context'])],
          ['verificationMethod >= 1',     (d.verificationMethod ?? []).length >= 1, `${(d.verificationMethod ?? []).length}`],
          ['service present',             Array.isArray(d.service),         String(Array.isArray(d.service))],
        ];
        for (const [name, ok, detail] of checks) {
          console.log(`${ok ? 'OK  ' : 'FAIL'}  ${name.padEnd(34)}  ${detail}`);
          if (!ok) failed = true;
        }
      }
    } catch (err) {
      console.error('Fetch failed.', err);
      failed = true;
    }

    if (opts.uniresolver) {
      console.log('');
      console.log(`>> GET ${UNI_RESOLVER}`);
      try {
        const { status } = await fetchJson(UNI_RESOLVER);
        console.log(`${status === 200 ? 'OK  ' : 'FAIL'}  uniresolver status=${status}`);
        if (status !== 200) failed = true;
      } catch (err) {
        console.error('uniresolver fetch failed.', err);
        failed = true;
      }
    }

    if (failed) process.exitCode = 1;
  });

didCmd
  .command('print')
  .description('Print did:web:etzhayyim.com DID document (raw JSON)')
  .option('--url <url>', 'override DID document URL', DEFAULT_DID_URL)
  .action(async (opts: { url: string }) => {
    const { status, body } = await fetchJson(opts.url);
    if (status !== 200) {
      console.error(`HTTP ${status}`);
      process.exit(1);
    }
    console.log(typeof body === 'string' ? body : JSON.stringify(body, null, 2));
  });
