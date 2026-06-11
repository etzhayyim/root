<script lang="ts">
	/**
	 * ActorEmbed — dynamically loads a webcomponent-mode Svelte component.
	 *
	 * The component is an ESM module served from the actor's Worker at
	 * /_miniapp/ui/miniapp.js (R2-backed). It exports a default Svelte component.
	 *
	 * Bundle format: Vite library mode output (ESM, externals: svelte).
	 */
	import { onMount, onDestroy, mount, unmount } from 'svelte';
	import type { ActorProfile, ActorContext } from './types.js';
	import { atProcedure, getSession, getCurrentDID } from '$lib/atproto-agent';
	import { AtpAgent } from '@etzhayyim/sdk/atproto';

	interface Props {
		profile: ActorProfile;
		/** Base URL for the actor app (e.g. https://handotai.etzhayyim.com). */
		appBaseUrl: string;
	}

	let { profile, appBaseUrl }: Props = $props();

	let containerEl: HTMLDivElement | undefined = $state();
	let loadError = $state('');
	let loading = $state(true);
	let mountedComponent: Record<string, unknown> | null = null;

	function toBase64Utf8(input: string): string {
		const bytes = new TextEncoder().encode(input);
		let binary = '';
		const chunkSize = 0x8000;
		for (let i = 0; i < bytes.length; i += chunkSize) {
			binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
		}
		return btoa(binary);
	}

	onMount(async () => {
		if (!containerEl) return;

		try {
			const entryUrl = profile.customEntry ?? `${appBaseUrl}/_miniapp/ui/miniapp.js`;
			const mod = await import(/* @vite-ignore */ entryUrl);
			const Component = mod.default;
			if (!Component) {
				throw new Error('Actor module has no default export');
			}

			const did = await getCurrentDID().catch((_err) => '');
			const _agent = new AtpAgent({ service: 'https://atproto.etzhayyim.com' });
			const buildHeaders = (): Record<string, string> => {
				const h: Record<string, string> = { 'content-type': 'application/json' };
				const session = getSession();
				if (session?.accessJwt) h.authorization = `Bearer ${session.accessJwt}`;
				h['atproto-proxy'] = `did:web:${profile.nanoid}.etzhayyim.com#atproto_labeler`;
				return h;
			};
			const ctx: ActorContext = {
				nanoid: profile.nanoid,
				name: profile.name,
				userId: did ?? '',
				actorId: did ?? '',
				orgId: '',
				async wSend(kind, payload) {
					await atProcedure('com.etzhayyim.convo.send', { kind, payload: toBase64Utf8(JSON.stringify(payload)), contentType: 'application/json' });
				},
				async wQuery(method, params) {
					const lcMethod = method.charAt(0).toLowerCase() + method.slice(1);
					return atProcedure(`com.etzhayyim.convo.${lcMethod}`, params);
				},
				backend: {
					async call(service, method, body = {}) {
						const nsid = `${service}.${method.charAt(0).toLowerCase()}${method.slice(1)}`;
						const res = await _agent.api.call(nsid, body, undefined, { headers: buildHeaders() });
						return res.data;
					},
				},
				cypher: {
					async exec(stmt, params) {
						const session = getSession();
						if (!session?.accessJwt) return;
						await _agent.api.call('com.etzhayyim.kagami.sql', { statement: stmt, parameters: params ?? {} }, undefined, { headers: buildHeaders() });
					},
					async query(stmt, params) {
						const session = getSession();
						if (!session?.accessJwt) return [];
						try {
							const r = await _agent.api.call('com.etzhayyim.kagami.sql', { statement: stmt, parameters: params ?? {} }, undefined, { headers: buildHeaders() });
							return ((r.data as { rows?: Record<string, unknown>[] }).rows) ?? [];
						} catch {
							return [];
						}
					},
				},
				navigate(_path) { },
				async remoteCall(pkg, iface, func, params) {
					try {
						const r = await _agent.api.call('com.etzhayyim.wrpc.call', { package: pkg, interface: iface, function: func, params: Array.from(params) }, undefined, { headers: buildHeaders() });
						const data = r.data as ArrayBuffer | Uint8Array | undefined;
						if (!data) return new Uint8Array(0);
						return data instanceof Uint8Array ? data : new Uint8Array(data);
					} catch {
						return new Uint8Array(0);
					}
				},
			};

			mountedComponent = mount(Component, {
				target: containerEl,
				props: { ctx },
			});

			loading = false;
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
			loading = false;
		}
	});

	onDestroy(() => {
		if (mountedComponent) {
			try { unmount(mountedComponent); } catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/actor/ActorEmbed.svelte: suppressed error", error); }
			mountedComponent = null;
		}
	});
</script>

<div class="flex h-full w-full flex-col overflow-hidden">
	{#if loading}
		<div class="flex h-full items-center justify-center">
			<div class="flex flex-col items-center gap-3">
				<div class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--gv2-accent,#3b82f6)] border-t-transparent"></div>
				<span class="text-[13px] text-[var(--gv2-text-muted,#777)]">Loading UI...</span>
			</div>
		</div>
	{:else if loadError}
		<div class="flex h-full items-center justify-center px-8">
			<div class="flex flex-col items-center gap-3 text-center">
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--gv2-bg-hover,#252525)]">
					<svg class="h-8 w-8 text-[var(--gv2-text-muted,#666)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="10" />
						<path d="M12 8v4M12 16h.01" />
					</svg>
				</div>
				<p class="text-[15px] font-semibold text-[var(--gv2-text-primary,#fff)]">UI failed to load</p>
				<p class="text-[13px] text-[var(--gv2-text-muted,#777)] max-w-[300px] break-words">{loadError}</p>
				<a
					href={appBaseUrl}
					target="_blank"
					rel="noopener"
					class="mt-2 rounded-xl bg-[var(--gv2-accent,#3b82f6)] px-6 py-2.5 text-[14px] font-semibold text-white touch-manipulation active:opacity-80"
				>Open in new tab</a>
			</div>
		</div>
	{/if}

	<div
		bind:this={containerEl}
		class="flex-1 min-h-0 overflow-y-auto overscroll-y-contain w-full max-w-[600px] mx-auto"
		class:hidden={loading || !!loadError}
	></div>
</div>
