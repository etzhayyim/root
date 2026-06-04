#!/usr/bin/env node
/**
 * Post a sponsored `app.bsky.feed.post` with a self `!ad` label.
 *
 * Auth: mints a 60s Service Auth JWT scoped to `com.atproto.repo.createRecord`
 * via `etzhayyim agent-token`. Caller must have run `etzhayyim authn signin` once, or
 * have a `sk_live_*` API key in `etzhayyim_TOKEN`.
 *
 * Usage:
 *   70-tools/scripts/ads/post-sponsored.mjs \
 *     --did did:web:ads.etzhayyim.com:campaign:example \
 *     --text "Try etzhayyim — religious-corp AT Protocol substrate." \
 *     --embed-uri https://etzhayyim.com --embed-title "etzhayyim.com"
 *
 * ADR: 90-docs/adr/0039-yoro-ads-integration.md §Sponsored Feed
 */
import { execFileSync } from 'node:child_process';
import { parseArgs } from 'node:util';

const { values } = parseArgs({
	options: {
		did:            { type: 'string' },
		text:           { type: 'string' },
		'embed-uri':    { type: 'string' },
		'embed-title':  { type: 'string' },
		'embed-desc':   { type: 'string' },
		'embed-thumb':  { type: 'string' },
		pds:            { type: 'string', default: 'https://atproto.etzhayyim.com' },
		ttl:            { type: 'string', default: '120' },
	},
});

if (!values.did || !values.text) {
	console.error('required: --did <did> --text <text>');
	process.exit(2);
}

let token;
try {
	token = execFileSync('etzhayyim', ['agent-token', '--lxm', 'com.atproto.repo.createRecord', '--ttl', values.ttl], {
		encoding: 'utf8',
		stdio: ['ignore', 'pipe', 'inherit'],
	}).trim();
} catch (e) {
	console.error('failed to mint agent-token. run `etzhayyim authn signin` first.');
	process.exit(1);
}

const record = {
	$type: 'app.bsky.feed.post',
	text: values.text,
	createdAt: new Date().toISOString(),
	labels: {
		$type: 'com.atproto.label.defs#selfLabels',
		values: [{ val: '!ad' }],
	},
};

if (values['embed-uri']) {
	record.embed = {
		$type: 'app.bsky.embed.external',
		external: {
			uri: values['embed-uri'],
			title: values['embed-title'] ?? '',
			description: values['embed-desc'] ?? '',
			...(values['embed-thumb'] ? { thumb: values['embed-thumb'] } : {}),
		},
	};
}

const body = {
	repo: values.did,
	collection: 'app.bsky.feed.post',
	record,
};

const res = await fetch(`${values.pds}/xrpc/com.atproto.repo.createRecord`, {
	method: 'POST',
	headers: {
		'Content-Type': 'application/json',
		Authorization: `Bearer ${token}`,
	},
	body: JSON.stringify(body),
});

const out = await res.json();
if (!res.ok) {
	console.error(`createRecord failed: HTTP ${res.status}`);
	console.error(JSON.stringify(out, null, 2));
	process.exit(1);
}

console.log(JSON.stringify(out, null, 2));
