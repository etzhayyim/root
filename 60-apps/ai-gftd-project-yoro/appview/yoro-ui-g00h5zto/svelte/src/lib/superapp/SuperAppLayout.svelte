<script lang="ts">
	/**
	 * SuperAppLayout — zero-boilerplate wrapper for App SvelteKit layouts.
	 *
	 * Bluesky-like tab layout: Vibes | Search | Talk | Apps | Profile
	 * Header: left = sheet menu, center = title, right = headerRight snippet
	 *
	 * Usage (minimal):
	 *   <SuperAppLayout appName="News">{@render children()}</SuperAppLayout>
	 *
	 * Usage (customized):
	 *   <SuperAppLayout appName="Gmail" accent="#ea4335">
	 *     {#snippet talk()}<ThreadView />{/snippet}
	 *     {@render children()}
	 *   </SuperAppLayout>
	 */
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
	import AppShell from '../AppShell.svelte';
	import Header from '../Header.svelte';
	import { ActionSheet } from '@etzhayyim/design-system';
	import SuperAppTabBar from './SuperAppTabBar.svelte';
	import AmbientBackground from './AmbientBackground.svelte';
	import SplashScreen from './SplashScreen.svelte';
	import { currentTab, type SuperAppTab } from './stores.js';
	import { vibesTuning, MOOD_META } from '../tuner/vibes-store.js';
	import { playNavForward, playNavBack } from '@etzhayyim/design-system/audio';
	import { page } from '$app/stores';

	// Embed mode: strip all chrome (Header, TabBar, splash) when loaded in iframe via ?embed=1
	const isEmbed = $derived(($page.url as URL).searchParams.has('embed'));

	interface Props {
		/** App display name for the header center. */
		appName?: string;
		/** Accent color CSS value (e.g. '#ea4335'). Overrides --gv2-accent. */
		accent?: string;
		/** Custom header left snippet. Replaces default sheet menu button. */
		headerLeft?: Snippet;
		/** Custom header right snippet. */
		headerRight?: Snippet;
		/** ActionSheet menu items for the header sheet menu. Default: empty. */
		menuActions?: Array<{ label: string; onclick: () => void; destructive?: boolean }>;
		/** Initial tab on mount. Default: 'vibes'. */
		initialTab?: SuperAppTab;
		/** Tab subset to display. Default: all 5 tabs. */
		tabs?: SuperAppTab[];
		/** Skip dark theme setup. Default: false (dark theme applied). */
		skipDarkTheme?: boolean;
		/** Show splash screen on app start. Default: true. */
		showSplash?: boolean;
		/** Extra CSS class on AppShell. */
		class?: string;
		/** Page content — rendered inside Vibes tab by default. */
		children: Snippet;
	}

	let {
		appName = 'etzhayyim',
		accent,
		headerLeft,
		headerRight,
		menuActions = [],
		initialTab = 'vibes',
		tabs,
		skipDarkTheme = false,
		showSplash = true,
		class: className,
		children,
	}: Props = $props();

	const SPLASH_SEEN_KEY = 'yoro-splash-seen-v1';
	function getSplashSeenInSession(): boolean {
		if (typeof window === 'undefined') return false;
		try {
			return window.sessionStorage.getItem(SPLASH_SEEN_KEY) === '1';
		} catch {
			return false;
		}
	}
	function markSplashSeenInSession(): void {
		if (typeof window === 'undefined') return;
		try {
			window.sessionStorage.setItem(SPLASH_SEEN_KEY, '1');
		} catch {
			// ignore storage failures (private mode / quota)
		}
	}

	let menuOpen = $state(false);
	let splashDone = $state(!showSplash || getSplashSeenInSession());
	let appReady = $state(false);

	onMount(() => {
		// Signal that app is ready (splash can dismiss)
		requestAnimationFrame(() => { appReady = true; });
	});

	// Dynamic mood-driven color: blend mood color into accent and border
	const moodMeta = $derived(MOOD_META[$vibesTuning.mood]);
	const moodEnergy = $derived($vibesTuning.energy);
	const moodDynamicStyle = $derived([
		`--gv2-accent: ${accent || moodMeta.color}`,
		`--gv2-accent-rgb: ${hexToRgb(accent || moodMeta.color)}`,
		`--tuner-mood-color: ${moodMeta.color}`,
		`--tuner-mood-glow: ${moodMeta.color}${Math.round(moodEnergy * 0.4 + 8).toString(16).padStart(2, '0')}`,
		`--tuner-energy: ${moodEnergy}`,
	].join('; '));

	function hexToRgb(hex: string): string {
		const h = hex.replace('#', '');
		return `${parseInt(h.substring(0, 2), 16)}, ${parseInt(h.substring(2, 4), 16)}, ${parseInt(h.substring(4, 6), 16)}`;
	}

	// Tab transition direction tracking for depth/slide SE
	let prevTab = $state<string>('');
	$effect(() => {
		const tab = $currentTab;
		if (prevTab && prevTab !== tab) {
			const tabs = ['vibes', 'search', 'talk', 'apps', 'profile'];
			const fromIdx = tabs.indexOf(prevTab);
			const toIdx = tabs.indexOf(tab);
			if (toIdx > fromIdx) {
				playNavForward();
			} else {
				playNavBack();
			}
		}
		prevTab = tab;
	});
</script>


{#if isEmbed}
	<!-- Embed mode: content only, no chrome -->
	<div
		class="min-h-screen bg-[var(--gv2-bg-primary,#0a0a0a)] text-[var(--gv2-text-primary,#fff)] {className ?? ''}"
		style={moodDynamicStyle}
	>
		{@render children()}
	</div>
{:else}
<AppShell
	sidebarOpen={false}
	class="bg-[var(--gv2-bg-primary,#0a0a0a)] text-[var(--gv2-text-primary,#fff)] {className ?? ''} transition-all duration-700"
	style={moodDynamicStyle}
>
	{#snippet header()}
		<Header
			appName={appName}
			showStandardActions={false}
			showTuner={false}
			showAppLauncher={false}
			showCredits={false}
			class="!bg-[var(--gv2-bg-primary,#141414)]/86 material-blur border-b border-[var(--gv2-border,#2f2f2f)] transition-shadow duration-700"
			style="box-shadow: 0 1px 16px var(--tuner-mood-glow, transparent)"
		>
			{#snippet left()}
				{#if headerLeft}
					{@render headerLeft()}
				{:else if menuActions.length > 0}
					<!-- Sheet menu button -->
					<button
						type="button"
						class="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-xl border border-[var(--gv2-border,#2f2f2f)] bg-transparent text-[var(--gv2-text-primary,#fff)] touch-manipulation active:opacity-80"
						onclick={() => menuOpen = true}
						aria-label="Menu"
					>
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
							<line x1="3" y1="6" x2="21" y2="6" />
							<line x1="3" y1="12" x2="21" y2="12" />
							<line x1="3" y1="18" x2="21" y2="18" />
						</svg>
					</button>
				{/if}
			{/snippet}
			{#snippet right()}
				{#if headerRight}
					{@render headerRight()}
				{/if}
			{/snippet}
		</Header>
	{/snippet}
	{#snippet bottomBar()}
		<SuperAppTabBar {tabs} />
	{/snippet}
	<main class="flex-1 min-h-0 overflow-y-auto relative">
		<AmbientBackground class="z-0" />
		<div class="relative z-10">
			{@render children()}
		</div>
	</main>
</AppShell>

{#if menuActions.length > 0}
	<ActionSheet bind:open={menuOpen} actions={menuActions} cancelLabel="Cancel" />
{/if}

{#if showSplash && !splashDone}
	<SplashScreen
		{appName}
		accent={accent || moodMeta.color}
		ready={appReady}
		ondismiss={() => {
			splashDone = true;
			markSplashSeenInSession();
		}}
	/>
{/if}
{/if}
