<script lang="ts">
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount, untrack } from 'svelte';
	import {
		DEFAULT_CLERK_PUBLISHABLE_KEY,
		clerkLoaded,
		initClerk,
		isSignedIn,
		clerkUser,
		displayName as clerkDisplayName,
		getSessionToken,
		headerCacaoSignIn,
	} from '$lib/auth';
	import { SuperAppLayout, Tuner } from '$lib/superapp';
	import { currentTab, pathToTab } from '$lib/superapp';
	import { ActionSheet } from '@etzhayyim/design-system';
	import { playClick } from '$lib/sound';
	import { playTap, haptic } from '@etzhayyim/design-system/audio';
	import { setTokenProvider } from '$lib/atproto-agent';
	import { useProviderWorker, useBrowserInference, useLocalLLM, useShinkaInference } from '$lib/provider';
	import { useEvolutionTasks } from '$lib/provider/evolution-tasks.svelte.js';
	import { useEmbedding } from '$lib/provider/embedding.svelte.js';
	import AppDrawer from '$lib/components/AppDrawer.svelte';
	import OpsFAB from '$lib/components/OpsFAB.svelte';
	import InferenceConsent from '$lib/components/InferenceConsent.svelte';
	import NoCookieBanner from '$lib/components/NoCookieBanner.svelte';
	import { hasInferenceConsent, requestInferenceConsent } from '$lib/components/inference-consent-state.svelte.js';
	import { useGamification, AchievementToast } from '$lib/gamification';
	import { hitl } from '$lib/hitl-store.svelte';
	import '../app.css';

	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	const { children }: Props = $props();
	const worker = useProviderWorker();
	const inference = useBrowserInference();
	const localLLM = useLocalLLM();
	const shinka = useShinkaInference();
	const evo = useEvolutionTasks();
	const embeddingModel = useEmbedding();
	const gf = useGamification();

	let menuOpen = $state(false);
	let drawerOpen = $state(false);
	let bootstrapped = $state(false);

	// Auth status banner for the same-origin CACAO sign-in (gated/error feedback;
	// success is reflected by `isSignedIn` flipping the header).
	let authMsg = $state('');
	let authBusy = $state(false);

	// ADR-2606061500: the interactive session is a member-held CACAO ceremony, not
	// a server-minted accessJwt. The legacy authn-backed JWT path survives ONLY as
	// an explicit rollback flag (default OFF) — when off, no authn hop + no
	// server-minted session exist in the interactive path.
	const LEGACY_JWT = import.meta.env.PUBLIC_AUTH_LEGACY_JWT === '1';

	// Same-origin passkey → CACAO sign-in (the header "ログイン / 新規登録" path).
	// No authn.etzhayyim.com redirect, no server key. The wrap-store accessors hit
	// the kotoba zero-access ARK custody (NOT authn); per ADR-2606061500 §4 the
	// wrap-store CACAO-hardening is a kotoba-node follow-up.
	async function headerSignIn(): Promise<void> {
		if (authBusy) return;
		authBusy = true;
		authMsg = '';
		try {
			const res = await headerCacaoSignIn();
			if (res.status === 'verified') {
				authMsg = '';
			} else if (res.status === 'gated') {
				authMsg =
					res.reason ??
					'サインインは kotoba ノードで完了します（初回デバイス / 新規登録）。';
			} else {
				authMsg = res.reason ?? 'サインインに失敗しました。';
			}
		} catch (e) {
			authMsg = e instanceof Error ? e.message : String(e);
		} finally {
			authBusy = false;
		}
	}

	const menuActions = [
		{ label: 'New message', onclick: () => { playClick(); goto('/projects'); } },
		{ label: 'Activities', onclick: () => { playClick(); goto('/activities'); } },
		{ label: 'Settings', onclick: () => { playClick(); goto('/settings'); } },
	];

	// Auth bootstrap. CACAO-only (default): no authn restore + no JWT provider —
	// the CACAO write provider is registered on sign-in (a key-ceremony session is
	// not persisted, so a cold load starts signed-out until the user taps login).
	// LEGACY_JWT (rollback): restore the authn-minted session + JWT token provider.
	$effect(() => {
		if (bootstrapped) return;
		bootstrapped = true;
		if (LEGACY_JWT) {
			const clerkTimeout = setTimeout(() => {
				if (!get(clerkLoaded)) clerkLoaded.set(true);
			}, 8000);
			setTokenProvider(async () => (await getSessionToken()) ?? '');
			void (async () => {
				await initClerk({ publishableKey: DEFAULT_CLERK_PUBLISHABLE_KEY }).catch((e) => console.warn('initClerk failed', e));
				clearTimeout(clerkTimeout);
			})();
			return () => { clearTimeout(clerkTimeout); };
		}
		clerkLoaded.set(true);
	});

	// URL → tab store sync
	$effect(() => {
		currentTab.set(pathToTab($page.url.pathname));
	});

	// Gamification init (streak check, daily XP)
	$effect(() => {
		if (typeof window === 'undefined') return;
		gf.init();
	});

	/*
	 * Browser inference — auto-load DISABLED.
	 * Users must explicitly accept the Inference TOS via InferenceConsent modal
	 * before any model loading or inference participation occurs.
	 * Model loading is triggered only via the header model selector after TOS acceptance.
	 */

	/**
	 * Auto-start shinka + evolution tasks when local LLM becomes ready.
	 *
	 * Delayed by 3s after LLM ready to avoid overloading the device
	 * immediately after a heavy model load. Uses `untrack` on running
	 * state to prevent reactive start→cleanup-stop→start infinite loop.
	 */
	$effect(() => {
		if (typeof window === 'undefined') return;
		if (!localLLM.isReady) return;
		if (!hasInferenceConsent()) return;

		const timer = setTimeout(() => {
			if (untrack(() => !shinka.isRunning)) {
				shinka.start();
			}
			const evoEnabled = localStorage.getItem('yoro-evo-enabled') === '1';
			if (evoEnabled && untrack(() => !evo.isRunning && !evo.isPaused)) {
				evo.start();
			}
		}, 3000);

		return () => clearTimeout(timer);
	});

	/** Clean up shinka & evolution on layout destroy (e.g. full page unload). */
	onMount(() => {
		// kotoba browser node (ADR-2606013600): a module Service Worker at the
		// origin root that serves /xrpc/...searchActors from the live server when
		// online and from the in-browser kotoba-wasm read engine when offline
		// (network-first; no staleness while online). @etzhayyim/yoro-rw-free is
		// unchanged. Best-effort — failure to register never blocks the app.
		if ('serviceWorker' in navigator) {
			navigator.serviceWorker
				.register('/kotoba-sw.js', { type: 'module', scope: '/' })
				.then(() => import('$lib/kotoba-identity'))
				// Re-bind the passkey-derived signing key ONLY if the member opted in
				// earlier (never prompts unprompted). Best-effort.
				.then((m) => m.maybeRebindPasskeyIdentity())
				.catch((e) => console.warn('[kotoba-sw] register failed', e));
		}
		// Auto-init embedding model (45MB, cached in OPFS after first download)
		if (embeddingModel.state === 'idle') void embeddingModel.init();
		hitl.start();
		return () => {
			shinka.stop();
			evo.stop();
			hitl.stop();
		};
	});
</script>

<SuperAppLayout
	appName="YORO"
	initialTab="vibes"
	tabs={['vibes','search','talk','apps','profile']}
	{menuActions}
>
	{#snippet headerLeft()}
		{#if $isSignedIn}
			<button
				class="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
				onclick={() => { playClick(); drawerOpen = true; }}
				aria-label="メニューを開く"
			>
				<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
			</button>
		{/if}
	{/snippet}

	{#snippet headerRight()}
		{#if $isSignedIn}
			<!-- WebGPU model pulldown + inference status (TOS-gated) -->
			<div class="flex items-center gap-1 mr-1">
				{#if localLLM.isReady || localLLM.isLoading}
					<select
						class="h-7 rounded-md border border-gv2-border/40 bg-gv2-bg-primary px-1 text-[10px] font-bold text-gv2-text-primary appearance-none cursor-pointer touch-manipulation focus:outline-none focus:border-[#58CC02]/60"
						value={inference.selectedModelId}
						onchange={(e) => {
							const id = e.currentTarget.value;
							inference.selectedModelId = id;
							localStorage.setItem('yoro-local-llm-model', id);
							if (localLLM.state === 'ready' || localLLM.state === 'idle') {
								void localLLM.reset().then(() => localLLM.init(id));
							}
						}}
					>
						{#each inference.models as model}
							<option value={model.id}>{model.label}</option>
						{/each}
					</select>
				{:else}
					<button
						type="button"
						class="h-7 rounded-md border border-gv2-border/40 bg-gv2-bg-primary px-2 text-[10px] font-bold text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover transition-all duration-75"
						onclick={async () => {
							const accepted = await requestInferenceConsent();
							if (!accepted) return;
							const savedModel = localStorage.getItem('yoro-local-llm-model') || 'gemma4-e2b';
							localStorage.setItem('yoro-local-llm-enabled', '1');
							localStorage.setItem('yoro-evo-enabled', '1');
							inference.selectedModelId = savedModel;
							if (!inference.isJoined) void inference.join();
							const convoId = await evo.startInProject();
							if (convoId) {
								await goto(`/projects/${encodeURIComponent(convoId)}`);
							}
						}}
					>
						推論に参加
					</button>
				{/if}
				{#if localLLM.isLoading}
					<div class="flex items-center gap-1 rounded-md bg-amber-500/15 px-1.5 py-0.5">
						<div class="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400"></div>
						<span class="text-[10px] font-semibold text-amber-400">{localLLM.loadProgress}%</span>
					</div>
				{:else if shinka.isRunning || inference.isExecuting}
					<div class="flex items-center gap-1 rounded-md bg-[#58CC02]/15 px-1.5 py-0.5">
						<div class="h-1.5 w-1.5 animate-pulse rounded-full bg-[#58CC02]"></div>
						<span class="text-[10px] font-semibold text-[#58CC02]">推論中</span>
					</div>
				{:else if localLLM.isReady}
					<div class="h-1.5 w-1.5 rounded-full bg-[#58CC02]" title="Local LLM ready"></div>
				{/if}
			</div>
			<button
				class="flex items-center gap-1 rounded-lg border border-[var(--gv2-border,#2f2f2f)] px-2 py-1 active:opacity-80 transition-all duration-100 touch-manipulation focus-glow active:scale-95"
				onclick={() => { playTap(); haptic('light'); goto('/credits'); }}
			>
				<svg class="h-3.5 w-3.5 text-[var(--gv2-accent,#58CC02)]" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" opacity="0.2" /><circle cx="12" cy="12" r="6" /></svg>
				<span class="text-[11px] font-semibold tabular-nums text-[var(--gv2-text-primary,#fff)]">{worker.workerStats.totalEarned.toFixed(2)}</span>
				<span class="text-[10px] text-[var(--gv2-text-muted,#777)]">Credits</span>
			</button>
			<button
				type="button"
				class="relative flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover active:text-gv2-text-primary"
				onclick={() => goto('/activities')}
				aria-label="Activities"
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 01-3.46 0" /></svg>
			</button>
			<Tuner />
		{:else}
			<!-- ADR-2606061500: same-origin passkey → CACAO. No authn.etzhayyim.com hop. -->
			<button
				type="button"
				onclick={headerSignIn}
				disabled={authBusy}
				class="flex min-h-[36px] items-center rounded-full border border-gv2-border px-4 py-1.5 text-[14px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover active:scale-[0.97] transition-transform disabled:opacity-60"
			>
				{authBusy ? '…' : 'ログイン'}
			</button>
			<button
				type="button"
				onclick={headerSignIn}
				disabled={authBusy}
				class="flex min-h-[36px] items-center rounded-full bg-[#58CC02] px-4 py-1.5 text-[14px] font-bold text-white shadow-[0_3px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[3px] transition-all duration-75 disabled:opacity-60"
			>
				{authBusy ? '...' : '新規登録'}
			</button>
			{#if authMsg}
				<p class="ml-2 max-w-[200px] text-[11px] leading-tight text-gv2-text-muted">{authMsg}</p>
			{/if}
		{/if}
	{/snippet}

	<div class="mx-auto w-full max-w-[600px] pb-4">
		{@render children()}
	</div>
</SuperAppLayout>

<OpsFAB />
<AppDrawer bind:open={drawerOpen} />
<ActionSheet bind:open={menuOpen} actions={menuActions} cancelLabel="キャンセル" />
<AchievementToast />
<InferenceConsent />
<NoCookieBanner />
