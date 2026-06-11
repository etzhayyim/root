<script lang="ts">
	import { onMount } from 'svelte';
	import { appsStore, loadAppsFromRegistry } from '../apps/appsStore.js';
	import type { GfAppLink } from '../apps/index.js';
	import { spring } from 'svelte/motion';
	import { playTap, playSelect, haptic } from '@etzhayyim/design-system/audio';
	import { goto } from '$app/navigation';

	onMount(() => { loadAppsFromRegistry(); });

	let searchQuery = $state('');
	let pressedIndex = $state(-1);

	const pressScale = spring(1, { stiffness: 0.35, damping: 0.55 });

	// Installed apps (pinned at top for quick access)
	const INSTALLED_IDS = ['news', 'search', 'maps', 'shinshi', 'manga', 'games', 'drive', 'calendar'];
	let installedApps = $derived(INSTALLED_IDS.map(id => $appsStore.find(a => a.id === id)).filter((a): a is GfAppLink => !!a));

	const categoryOrder = ['Security', 'Integrations', 'Productivity', 'Media', 'AI', 'Business', 'System'];
	const categoryEmoji: Record<string, string> = {
		Security: '🛡', Integrations: '🔗', Productivity: '⚡', Media: '🎮', AI: '🤖', Business: '💼', System: '⚙️'
	};
	const categoryMap: Record<string, string[]> = {
		Security: ['kiyome', 'harai'],
		Integrations: ['gmail', 'outlook'],
		Productivity: ['drive', 'organizer', 'sheets', 'docs', 'calendar', 'mailer', 'forms', 'contacts', 'vault'],
		Media: ['news', 'manga', 'anime', 'games', 'shinshi', 'music', 'douga', 'videos', 'yomikikase', 'oshikatsu', 'narou'],
		AI: ['search', 'generator', 'swe', 'awai', 'crawler', 'aima', 'robot', 'translate', 'images'],
		Business: ['cowork', 'shigotoba', 'commodity', 'budget', 'tsukuru', 'fleamarket', 'okaimono', 'marketer', 'wire', 'lawfirm', 'lawyer', 'ekyc', 'shomeisyashin', 'global', 'briefing'],
		System: ['performers', 'os', 'analytics', 'ops', 'sre', 'hub', 'scheduler', 'po', 'gov', 'resources', 'completer']
	};

	function getAppCategory(app: GfAppLink): string {
		for (const [cat, ids] of Object.entries(categoryMap)) {
			if (ids.includes(app.id)) return cat;
		}
		if (app.category === 'Systems') return 'System';
		return 'Business';
	}

	let categorizedApps = $derived.by(() => {
		const allApps = $appsStore.filter((a) => a.id !== 'etzhayyim');
		const filtered = searchQuery.trim()
			? allApps.filter((a) =>
				a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(a.shortName ?? '').toLowerCase().includes(searchQuery.toLowerCase()) ||
				(a.description ?? '').toLowerCase().includes(searchQuery.toLowerCase())
			)
			: allApps;
		const groups: Record<string, GfAppLink[]> = {};
		for (const app of filtered) {
			const cat = getAppCategory(app);
			if (!groups[cat]) groups[cat] = [];
			groups[cat].push(app);
		}
		return categoryOrder.filter((cat) => groups[cat]?.length).map((cat) => ({ name: cat, apps: groups[cat] }));
	});

	function globalIndex(catIdx: number, appIdx: number): number {
		let idx = installedApps.length; // offset by installed count
		for (let c = 0; c < catIdx; c++) {
			idx += categorizedApps[c]?.apps.length ?? 0;
		}
		return idx + appIdx;
	}

	async function handleOpenApp(app: GfAppLink, gIdx: number) {
		playSelect();
		haptic('medium');
		pressedIndex = gIdx;
		pressScale.set(0.88);
		setTimeout(() => pressScale.set(1.06), 80);
		setTimeout(() => pressScale.set(1), 260);

		// Path-based actor DIDs (e.g. "smishing.etzhayyim.com:actor:kiyome") contain ".etzhayyim.com"
		// but don't end with it — use includes() so they route correctly.
		const host = app.name.includes('.etzhayyim.com') ? app.name : `${app.id}.etzhayyim.com`;
		await goto(`/profile/did:web:${host}`);
	}
</script>

<div class="flex flex-col gap-5 p-4 pb-20 max-w-[600px] mx-auto">
	<!-- Search bar -->
	<div class="relative">
		<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--gv2-text-muted);" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
		</svg>
		<input
			type="text"
			placeholder="Search apps..."
			bind:value={searchQuery}
			class="w-full pl-10 pr-4 py-2.5 rounded-2xl text-[15px] min-h-[44px] transition-all duration-200"
			style="background: var(--gv2-bg-input); color: var(--gv2-text-primary); border: 1px solid var(--gv2-border);"
		/>
	</div>

	<!-- Installed Apps (quick launch) -->
	{#if !searchQuery.trim() && installedApps.length > 0}
		<div>
			<div class="flex items-center gap-2 mb-3">
				<span class="text-base">📌</span>
				<h3 class="text-[13px] font-bold uppercase tracking-wider" style="color: var(--gv2-text-muted);">Installed</h3>
			</div>
			<div class="flex gap-3 overflow-x-auto scrollbar-none pb-1">
				{#each installedApps as app, i}
					<button
						class="group flex flex-col items-center gap-1.5 min-w-[72px] p-2.5 rounded-2xl touch-manipulation relative overflow-hidden card-float focus-glow installed-app-enter"
						style="animation-delay: {i * 40}ms; {pressedIndex === i ? `transform: scale(${$pressScale})` : ''}"
						onclick={() => handleOpenApp(app, i)}
						title={app.description}
					>
						<div class="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 group-active:opacity-100 transition-opacity duration-200" style="background: radial-gradient(circle at center, var(--gv2-accent, #2563eb)10, transparent 70%)"></div>
						<div class="relative w-14 h-14 rounded-2xl grid place-items-center group-active:scale-90 transition-all duration-150" style="background: var(--gv2-bg-card); border: 1px solid var(--gv2-border); box-shadow: 0 2px 8px rgba(0,0,0,0.1)">
							<span class="text-[28px]">{app.icon}</span>
						</div>
						<span class="relative text-[11px] leading-tight text-center line-clamp-1 transition-colors duration-200" style="color: var(--gv2-text-secondary);">{app.shortName || app.name}</span>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- All Apps by category -->
	{#each categorizedApps as category, catIdx}
		<div class="app-cat-enter" style="animation-delay: {(catIdx + 1) * 60}ms">
			<div class="flex items-center gap-2 mb-3">
				<span class="text-base">{categoryEmoji[category.name] ?? '📦'}</span>
				<h3 class="text-[13px] font-bold uppercase tracking-wider" style="color: var(--gv2-text-muted);">{category.name}</h3>
				<div class="flex-1 h-px" style="background: var(--gv2-border);"></div>
				<span class="text-[11px]" style="color: var(--gv2-text-muted); opacity: 0.5;">{category.apps.length}</span>
			</div>

			<div class="grid grid-cols-4 gap-2.5">
				{#each category.apps as app, appIdx}
					{@const gIdx = globalIndex(catIdx, appIdx)}
					<button
						class="group flex flex-col items-center gap-1.5 p-2.5 rounded-2xl touch-manipulation min-h-[44px] relative overflow-hidden card-float focus-glow app-tile-enter"
						style="animation-delay: {Math.min(gIdx * 25, 500)}ms; {pressedIndex === gIdx ? `transform: scale(${$pressScale})` : ''}"
						onclick={() => handleOpenApp(app, gIdx)}
						title={app.description}
					>
						<div class="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 group-active:opacity-100 transition-opacity duration-200" style="background: radial-gradient(circle at center, var(--gv2-accent, #2563eb)08, transparent 70%)"></div>
						<div class="relative w-12 h-12 rounded-xl grid place-items-center transition-all duration-200 group-active:scale-90" style="background: var(--gv2-bg-card); border: 1px solid var(--gv2-border);">
							<span class="text-2xl">{app.icon}</span>
						</div>
						<span class="relative text-[11px] leading-tight text-center line-clamp-1 transition-colors duration-200" style="color: var(--gv2-text-secondary);">{app.shortName || app.name}</span>
					</button>
				{/each}
			</div>
		</div>
	{/each}

	{#if categorizedApps.length === 0}
		<div class="flex flex-col items-center justify-center min-h-[200px] gap-3 py-16">
			<span class="text-4xl">🔍</span>
			<p class="text-[14px]" style="color: var(--gv2-text-muted);">No apps found</p>
		</div>
	{/if}
</div>

<style>
	.app-cat-enter {
		animation: cat-fade-in 0.3s ease-out both;
	}
	.app-tile-enter {
		animation: tile-pop-in 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
	}
	.installed-app-enter {
		animation: tile-pop-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
	}
	@keyframes cat-fade-in {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: translateY(0); }
	}
	@keyframes tile-pop-in {
		from { opacity: 0; transform: scale(0.7); }
		to { opacity: 1; transform: scale(1); }
	}
	@media (prefers-reduced-motion: reduce) {
		.app-cat-enter, .app-tile-enter, .installed-app-enter { animation: none; }
	}
</style>
