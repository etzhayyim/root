<script lang="ts">
	/**
	 * ActorFrame — AT Protocol actor view with hero section + content area.
	 *
	 * Hero: performerType-driven (compact for service/system, full for person/organization).
	 * Content: contentMode-driven (timeline/interactive/game).
	 */
	import { onMount } from 'svelte';
	import type { ActorProfileView, ActorLoadState } from './types.js';
	import { fetchActorProfileView, getCachedActorProfileView } from './actor-store.svelte.js';
	import ActorHero from './ActorHero.svelte';
	import ActorFeedList from './ActorFeedList.svelte';
	import ActorGame from './ActorGame.svelte';
	import { apps } from '../apps/apps.js';

	interface Props {
		nanoid: string;
		onClose?: () => void;
	}

	let { nanoid, onClose }: Props = $props();

	let profile = $state<ActorProfileView | null>(null);
	let loadState = $state<ActorLoadState>('loading');
	let error = $state('');

	const appEntry = $derived(apps.find((a) => a.id === nanoid || a.href.includes(nanoid)));
	const appBaseUrl = $derived(appEntry?.href ?? `https://${nanoid}.etzhayyim.com`);
	const appName = $derived(profile?.displayName ?? appEntry?.shortName ?? appEntry?.name ?? nanoid);
	const appIcon = $derived(profile?.icon ?? appEntry?.icon ?? '');
	const contentMode = $derived(profile?.contentMode ?? 'timeline');

	onMount(() => {
		const cached = getCachedActorProfileView(nanoid);
		if (cached) {
			profile = cached;
			loadState = 'ready';
			return;
		}
		void loadProfile();
	});

	async function loadProfile() {
		loadState = 'loading';
		try {
			profile = await fetchActorProfileView(nanoid, appBaseUrl);
			loadState = 'ready';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load actor';
			loadState = 'error';
		}
	}
</script>

<div class="flex h-full w-full flex-col">
	<!-- Header bar -->
	<div class="flex min-h-[48px] items-center gap-2 border-b border-[var(--gv2-border,#2f2f2f)] px-3 shrink-0">
		<button
			type="button"
			class="flex h-11 w-11 items-center justify-center rounded-full tap-target-44 touch-manipulation active:opacity-80"
			onclick={() => onClose?.()}
			aria-label="Back"
		>
			<svg class="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
				<path d="M13 4L7 10l6 6" />
			</svg>
		</button>
		{#if appIcon}
			<span class="text-xl">{appIcon}</span>
		{/if}
		<span class="flex-1 truncate text-[15px] font-semibold">{appName}</span>
		<a
			href={appBaseUrl}
			target="_blank"
			rel="noopener"
			class="flex h-11 w-11 items-center justify-center rounded-full tap-target-44 touch-manipulation active:opacity-80"
			aria-label="Open in new tab"
		>
			<svg class="h-4 w-4 text-[var(--gv2-text-muted,#777)]" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M11 3h6v6M17 3L9 11M15 11v5a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h5" />
			</svg>
		</a>
	</div>

	<!-- Content area -->
	<div class="flex-1 min-h-0 overflow-y-auto overscroll-y-contain">
		{#if loadState === 'loading'}
			<div class="flex h-full items-center justify-center">
				<div class="flex flex-col items-center gap-3">
					<div class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--gv2-accent,#3b82f6)] border-t-transparent"></div>
					<span class="text-[13px] text-[var(--gv2-text-muted,#777)]">Loading {appName}...</span>
				</div>
			</div>
		{:else if loadState === 'error'}
			<div class="flex h-full items-center justify-center px-8">
				<div class="flex flex-col items-center gap-3 text-center">
					<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--gv2-bg-hover,#252525)]">
						<svg class="h-8 w-8 text-[var(--gv2-text-muted,#666)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<circle cx="12" cy="12" r="10" />
							<path d="M12 8v4M12 16h.01" />
						</svg>
					</div>
					<p class="text-[15px] font-semibold text-[var(--gv2-text-primary,#fff)]">Failed to load</p>
					<p class="text-[13px] text-[var(--gv2-text-muted,#777)]">{error}</p>
					<button
						type="button"
						class="mt-2 rounded-xl bg-[var(--gv2-accent,#3b82f6)] px-6 py-2.5 text-[14px] font-semibold text-white touch-manipulation active:opacity-80"
						onclick={() => void loadProfile()}
					>Retry</button>
				</div>
			</div>
		{:else if profile}
			<!-- Hero Section -->
			<ActorHero {profile} />

			<!-- Content: timeline / interactive / game -->
			{#if contentMode === 'timeline'}
				<ActorFeedList did={profile.did} />
			{:else if contentMode === 'interactive'}
				<iframe
					src={profile.embedUrl ?? `${appBaseUrl}/?embed=1`}
					title={profile.displayName}
					class="w-full border-0"
					style="height: calc(100dvh - 48px - 200px); min-height: 400px;"
					sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-pointer-lock"
				></iframe>
			{:else if contentMode === 'game'}
				{@const legacyProfile = { nanoid, name: profile.displayName, ui: 'game' as const, gameConfig: profile.gameConfig }}
				<ActorGame profile={legacyProfile} {appBaseUrl} />
			{/if}
		{/if}
	</div>
</div>
