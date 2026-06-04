#!/usr/bin/env npx tsx
/**
 * Generate an AT Protocol access token for E2E testing.
 *
 * Preferred:
 *   - run WebAuthn E2E and extract accessJwt
 *   - node tests/gen-webauthn-at-token.cjs
 *
 * This helper is fallback for password-based createSession:
 *   - identifier (handle/DID) + password
 *   - returns accessJwt + refreshJwt
 *
 * Usage:
 *   # Preferred: WebAuthn-based
 *   node tests/gen-webauthn-at-token.cjs > /tmp/yoro-access.jwt
 *   YORO_AT_TOKEN=$(cat /tmp/yoro-access.jwt) npx playwright test tests/pds-e2e.spec.ts
 *
 *   # Fallback: createSession
 *   AT_IDENTIFIER=yoro.etzhayyim.com AT_PASSWORD=<secret> npx tsx tests/gen-at-token.ts
 *   YORO_AT_TOKEN=$(AT_IDENTIFIER=... AT_PASSWORD=... npx tsx tests/gen-at-token.ts) npx playwright test tests/pds-e2e.spec.ts
 */

const PDS = process.env.PDS_BASE_URL || 'https://atproto.etzhayyim.com';

async function main() {
	// Fallback: AT Protocol createSession
	const identifier = process.env.AT_IDENTIFIER?.trim();
	const password = process.env.AT_PASSWORD?.trim() || process.env.AT_BOT_SECRET?.trim();

	if (!identifier || !password) {
		process.stderr.write(
			'Usage:\n' +
			'  Preferred: node tests/gen-webauthn-at-token.cjs\n' +
			'  Fallback:  AT_IDENTIFIER=<handle> AT_PASSWORD=<password> npx tsx tests/gen-at-token.ts\n'
		);
		process.exit(1);
	}

	const res = await fetch(`${PDS}/xrpc/com.atproto.server.createSession`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ identifier, password }),
	});

	if (!res.ok) {
		const err = await res.text().catch((_err) => '');
		process.stderr.write(`createSession failed: ${res.status} ${err}\n`);
		process.exit(1);
	}

	const data = await res.json() as { accessJwt: string; refreshJwt: string; did: string; handle: string };

	if (process.argv.includes('--json')) {
		process.stdout.write(JSON.stringify(data, null, 2) + '\n');
	} else {
		process.stdout.write(data.accessJwt);
	}
}

main().catch((e) => {
	process.stderr.write(`Error: ${e.message}\n`);
	process.exit(1);
});
