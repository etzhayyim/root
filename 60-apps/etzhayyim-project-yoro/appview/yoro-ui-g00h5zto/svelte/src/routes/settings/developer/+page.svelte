<script lang="ts">
	import { goto } from '$app/navigation';
	import { Badge } from '@etzhayyim/design-system';
	import { getSession } from '$lib/atproto-agent';
	import { isSignedIn } from '$lib/auth/stores.js';
	import { getSessionToken } from '$lib/auth';
	import { onMount } from 'svelte';

	type ApiKey = {
		id: string;
		name: string;
		scopes: string;
		prefix: string;
		lastUsed: number | null;
		created: number;
	};

	let loading = $state(true);
	let keys = $state<ApiKey[]>([]);
	let error = $state('');

	// Create key form
	let showCreate = $state(false);
	let newKeyName = $state('');
	let newKeyScopes = $state('read,write');
	let newKeyTest = $state(false);
	let creating = $state(false);
	let createdKey = $state(''); // shown once, never stored

	// Revoke state
	let revoking = $state<string | null>(null);
	const AUTH_XRPC_BASE = 'https://authn.etzhayyim.com/xrpc';

	const SCOPE_OPTIONS = [
		{ id: 'read', label: 'Read', desc: 'Graph query, list records' },
		{ id: 'write', label: 'Write', desc: 'Create/update records' },
		{ id: 'seed', label: 'Seed', desc: 'Bulk DID + record seeding' },
		{ id: 'shinka', label: 'Shinka', desc: 'LLM domain knowledge generation' },
		{ id: 'admin', label: 'Admin', desc: 'App registration, governance' },
	];

	let selectedScopes = $state<Set<string>>(new Set(['read', 'write']));

	onMount(async () => {
		if (!$isSignedIn) {
			loading = false;
			return;
		}
		const token = await getSessionToken().catch(() => null);
		const session = getSession();
		if (!token || !session?.did) {
			loading = false;
			error = 'PDS session is not ready yet. Sign in again before managing API keys.';
			return;
		}
		await fetchKeys();
	});

	async function authApiKeyProcedure<T>(nsid: string, body: Record<string, unknown>): Promise<T> {
		const token = await getSessionToken().catch(() => null);
		if (!token) throw new Error('PDS session is not ready yet. Sign in again before managing API keys.');
		const resp = await fetch(`${AUTH_XRPC_BASE}/${nsid}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`,
			},
			body: JSON.stringify(body),
		});
		const payload = await resp.json().catch(() => ({} as Record<string, unknown>));
		if (!resp.ok) {
			const message =
				typeof payload.message === 'string'
					? payload.message
					: typeof payload.error === 'string'
						? payload.error
						: `API key request failed (${resp.status})`;
			throw new Error(message);
		}
		return payload as T;
	}

	async function fetchKeys() {
		const token = await getSessionToken().catch(() => null);
		const session = getSession();
		if (!token || !session?.did) {
			loading = false;
			error = 'PDS session is not ready yet. Sign in again before managing API keys.';
			keys = [];
			return;
		}
		loading = true;
		error = '';
		try {
			const result = await authApiKeyProcedure<{ keys?: ApiKey[] }>('com.etzhayyim.auth.listApiKeys', {});
			keys = (result as any)?.keys ?? [];
		} catch (e) {
			const message = e instanceof Error ? e.message : 'Failed to load API keys';
			error = /401|AuthRequired|InvalidAuth/i.test(message)
				? 'PDS session expired. Sign in again before managing API keys.'
				: message;
			keys = [];
		} finally {
			loading = false;
		}
	}

	async function createKey() {
		if (!newKeyName.trim()) return;
		creating = true;
		createdKey = '';
		error = '';
		try {
			const scopes = Array.from(selectedScopes).join(',');
			const result = await authApiKeyProcedure<{ key?: string }>('com.etzhayyim.auth.createApiKey', {
				name: newKeyName.trim(),
				scopes,
				test: newKeyTest,
			});
			const data = result as any;
			createdKey = data.key ?? '';
			showCreate = false;
			newKeyName = '';
			selectedScopes = new Set(['read', 'write']);
			newKeyTest = false;
			await fetchKeys();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create API key';
		} finally {
			creating = false;
		}
	}

	async function revokeKey(keyId: string) {
		revoking = keyId;
		error = '';
		try {
			await authApiKeyProcedure('com.etzhayyim.auth.revokeApiKey', { keyId });
			keys = keys.filter((k) => k.id !== keyId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to revoke key';
		} finally {
			revoking = null;
		}
	}

	function toggleScope(scope: string) {
		const next = new Set(selectedScopes);
		if (next.has(scope)) next.delete(scope);
		else next.add(scope);
		if (next.size === 0) next.add('read'); // at least read
		selectedScopes = next;
		newKeyScopes = Array.from(next).join(',');
	}

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
	}

	function formatDate(ms: number | null) {
		if (!ms) return '-';
		return new Date(ms).toLocaleDateString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' });
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/settings');
	}
</script>

<svelte:head>
	<title>Developer — YORO</title>
</svelte:head>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center gap-2 border-b border-gv2-border/50 px-4">
		<button
			type="button"
			class="flex h-11 w-11 items-center justify-center rounded-full text-gv2-text-muted tap-target-44 touch-manipulation active:text-gv2-text-primary"
			onclick={goBack}
			aria-label="Back"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
				<path d="M15 19l-7-7 7-7" />
			</svg>
		</button>
		<h3 class="text-[17px] font-bold text-gv2-text-primary">Developer</h3>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none pb-20 safe-area-bottom">
		{#if !$isSignedIn}
			<div class="flex flex-col items-center justify-center gap-4 px-6 py-20">
				<svg class="h-12 w-12 text-gv2-text-muted/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
				</svg>
				<p class="text-[15px] text-gv2-text-muted">API key management requires sign-in.</p>
			</div>
		{:else}
			<!-- Created key banner (shown once) -->
			{#if createdKey}
				<div class="mx-4 mt-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4">
					<p class="mb-2 text-[13px] font-bold text-emerald-400">API Key Created</p>
					<p class="mb-3 text-[12px] text-gv2-text-muted">Copy this key now. It will not be shown again.</p>
					<div class="flex items-center gap-2">
						<code class="flex-1 break-all rounded-lg bg-gv2-bg-hover/60 px-3 py-2 font-mono text-[13px] text-gv2-text-primary">
							{createdKey}
						</code>
						<button
							type="button"
							class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 tap-target-44 touch-manipulation active:bg-emerald-500/30"
							onclick={() => copyToClipboard(createdKey)}
							aria-label="Copy key"
						>
							<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<rect x="9" y="9" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
							</svg>
						</button>
					</div>
					<div class="mt-3 rounded-lg bg-gv2-bg-hover/40 p-3">
						<p class="mb-1 text-[12px] font-medium text-gv2-text-muted">Usage (CLI / SDK / LLM Agent):</p>
						<code class="block text-[12px] text-gv2-text-primary">export etzhayyim_TOKEN={createdKey}</code>
						<code class="mt-1 block text-[12px] text-gv2-text-primary">curl -H "Authorization: Bearer {createdKey}" \</code>
						<code class="block pl-4 text-[12px] text-gv2-text-primary">atproto.etzhayyim.com/xrpc/com.etzhayyim.kagami.sql</code>
					</div>
					<button
						type="button"
						class="mt-3 text-[13px] text-gv2-text-muted active:text-gv2-text-primary"
						onclick={() => { createdKey = ''; }}
					>
						Dismiss
					</button>
				</div>
			{/if}

			<!-- Description -->
			<div class="px-4 py-4">
				<p class="text-[13px] leading-relaxed text-gv2-text-muted">
					API keys authenticate CLI tools (<code class="text-[12px]">etzhayyim</code>), SDKs, and LLM agents
					for graph queries, record writes, seed operations, and shinka (domain knowledge generation).
				</p>
			</div>

			<!-- Error -->
			{#if error}
				<div class="mx-4 mb-3 rounded-xl bg-red-500/10 px-4 py-3">
					<p class="text-[13px] text-red-400">{error}</p>
				</div>
			{/if}

			<!-- Create button / form -->
			<div class="border-b border-gv2-border/30 px-4 pb-4">
				{#if showCreate}
					<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-secondary/40 p-4">
						<h4 class="mb-3 text-[14px] font-bold text-gv2-text-primary">New API Key</h4>

						<!-- Name -->
						<label class="mb-1 block text-[12px] font-medium text-gv2-text-muted" for="key-name">Name</label>
						<input
							id="key-name"
							type="text"
							bind:value={newKeyName}
							placeholder="e.g. cli-dev, sovereign-seed, llm-agent"
							class="mb-4 min-h-[44px] w-full rounded-xl bg-gv2-bg-hover/60 px-3 py-2 text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted/50 focus:outline-none focus:ring-2 focus:ring-discord-accent/50"
						/>

						<!-- Scopes -->
						<p class="mb-2 text-[12px] font-medium text-gv2-text-muted">Scopes</p>
						<div class="mb-4 flex flex-wrap gap-2">
							{#each SCOPE_OPTIONS as opt}
								<button
									type="button"
									class="flex items-center gap-1.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors tap-target-44 touch-manipulation {selectedScopes.has(opt.id) ? 'bg-discord-accent/20 text-discord-accent' : 'bg-gv2-bg-hover/40 text-gv2-text-muted'}"
									onclick={() => toggleScope(opt.id)}
								>
									{#if selectedScopes.has(opt.id)}
										<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" /></svg>
									{/if}
									{opt.label}
								</button>
							{/each}
						</div>

						<!-- Test mode -->
						<label class="mb-4 flex min-h-[44px] items-center gap-3">
							<input type="checkbox" bind:checked={newKeyTest} class="h-5 w-5 rounded accent-discord-accent" />
							<span class="text-[13px] text-gv2-text-muted">Test key (<code class="text-[12px]">sk_test_</code> prefix)</span>
						</label>

						<!-- Actions -->
						<div class="flex gap-2">
							<button
								type="button"
								class="flex-1 min-h-[44px] rounded-xl bg-gv2-bg-hover/60 text-[14px] font-medium text-gv2-text-muted tap-target-44 touch-manipulation active:bg-gv2-bg-hover"
								onclick={() => { showCreate = false; }}
							>
								Cancel
							</button>
							<button
								type="button"
								class="flex-1 min-h-[44px] rounded-xl bg-discord-accent text-[14px] font-semibold text-white tap-target-44 touch-manipulation active:bg-discord-accent-hover disabled:opacity-50"
								onclick={() => void createKey()}
								disabled={creating || !newKeyName.trim()}
							>
								{creating ? 'Creating...' : 'Create Key'}
							</button>
						</div>
					</div>
				{:else}
					<button
						type="button"
						class="flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-discord-accent text-[15px] font-semibold text-white tap-target-44 touch-manipulation active:bg-discord-accent-hover"
						onclick={() => { showCreate = true; }}
					>
						<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" d="M12 5v14m-7-7h14" />
						</svg>
						Create API Key
					</button>
				{/if}
			</div>

			<!-- Keys list -->
			<div class="px-4 py-4">
				<h4 class="mb-3 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">
					Active Keys
				</h4>

				{#if loading}
					<div class="space-y-3">
						{#each [0, 1] as _}
							<div class="h-[72px] animate-pulse rounded-2xl bg-gv2-bg-hover/30"></div>
						{/each}
					</div>
				{:else if keys.length === 0}
					<div class="flex flex-col items-center gap-2 py-8">
						<svg class="h-8 w-8 text-gv2-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
						</svg>
						<p class="text-[13px] text-gv2-text-muted">No API keys yet.</p>
					</div>
				{:else}
					<div class="space-y-3">
						{#each keys as key}
							<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-secondary/40 p-3">
								<div class="flex items-start justify-between gap-2">
									<div class="min-w-0 flex-1">
										<div class="flex items-center gap-2">
											<span class="text-[14px] font-medium text-gv2-text-primary">{key.name || 'unnamed'}</span>
											<Badge value={key.prefix || 'sk_live_'} variant="default" />
										</div>
										<p class="mt-1 text-[12px] text-gv2-text-muted">
											{key.scopes || 'read'}
										</p>
										<p class="mt-0.5 text-[11px] text-gv2-text-muted/60">
											Created: {formatDate(key.created)} | Last used: {formatDate(key.lastUsed)}
										</p>
									</div>
									<button
										type="button"
										class="flex h-9 items-center rounded-lg bg-red-500/10 px-3 text-[12px] font-medium text-red-400 tap-target-44 touch-manipulation active:bg-red-500/20 disabled:opacity-50"
										onclick={() => void revokeKey(key.id)}
										disabled={revoking === key.id}
									>
										{revoking === key.id ? '...' : 'Revoke'}
									</button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- LLM Agent usage guide -->
			<div class="border-t border-gv2-border/30 px-4 py-4">
				<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">
					LLM Agent Integration
				</h4>
				<div class="space-y-3 text-[13px] leading-relaxed text-gv2-text-muted">
					<p>
						API keys can be used by LLM agents (Claude, GPT, Gemini) to manage platform resources autonomously.
					</p>
					<div class="rounded-xl bg-gv2-bg-hover/40 p-3">
						<p class="mb-1 text-[12px] font-medium text-gv2-text-primary">MCP Tool Calling:</p>
						<code class="block text-[12px]">POST mcp.etzhayyim.com/mcp</code>
						<code class="block text-[12px]">Authorization: Bearer sk_live_...</code>
						<code class="mt-1 block text-[12px]">{"{"}"method":"tools/call","params":{"{"}"name":"etzhayyim.seed"{"}"}{"}"}}</code>
					</div>
					<div class="rounded-xl bg-gv2-bg-hover/40 p-3">
						<p class="mb-1 text-[12px] font-medium text-gv2-text-primary">XRPC Direct:</p>
						<code class="block text-[12px]">POST atproto.etzhayyim.com/xrpc/com.etzhayyim.kagami.sql</code>
						<code class="block text-[12px]">Authorization: Bearer sk_live_...</code>
						<code class="mt-1 block text-[12px]">{"{"}"statement":"SELECT did FROM vertex_did ORDER BY _seq DESC LIMIT 10"{"}"}</code>
					</div>
					<div class="rounded-xl bg-gv2-bg-hover/40 p-3">
						<p class="mb-1 text-[12px] font-medium text-gv2-text-primary">Claude Code / Anthropic SDK:</p>
						<code class="block text-[12px]">export etzhayyim_TOKEN=sk_live_...</code>
						<code class="block text-[12px]">etzhayyim seed --app sovereign</code>
						<code class="block text-[12px]">etzhayyim actors shinka --model gemma4</code>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
