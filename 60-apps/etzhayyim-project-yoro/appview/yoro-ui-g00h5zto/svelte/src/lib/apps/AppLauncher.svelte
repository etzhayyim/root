<script lang="ts">
	import { onMount } from 'svelte';
	import type { GfAppLink } from './types';
	import { apps as defaultApps } from './apps';
	import { Input } from '@etzhayyim/design-system';
	import { isSignedIn } from '../auth/stores.js';
	import {
		installedApps,
		installedAppsLoading,
		fetchInstalledApps,
		installedToAppLinks
	} from './installed-apps.js';

	const {
		apps = defaultApps,
		buttonClass = ''
	} = $props<{
		apps?: GfAppLink[];
		buttonClass?: string;
	}>();

	let open = $state(false);
	let query = $state('');
	let rootEl: HTMLDivElement | undefined = $state();

	const categoryOrder: Array<GfAppLink['category']> = ['Services', 'Systems', 'Orgs'];
	const keyword = $derived(query.trim().toLowerCase());

	const myApps = $derived(installedToAppLinks($installedApps));
	const filteredMyApps = $derived(
		keyword
			? myApps.filter((app) => {
				const token = `${app.shortName || ''} ${app.name} ${app.description || ''}`.toLowerCase();
				return token.includes(keyword);
			})
			: myApps
	);

	const visibleApps = $derived(
		apps.filter((app: GfAppLink) => {
			if (!keyword) return true;
			const token = `${app.shortName || ''} ${app.name} ${app.description || ''} ${app.href}`.toLowerCase();
			return token.includes(keyword);
		})
	);

	const sectionApps = $derived(
		Object.fromEntries(
			categoryOrder.map((category) => [
				category,
				visibleApps.filter((app: GfAppLink) => app.category === category)
			])
		) as Record<GfAppLink['category'], GfAppLink[]>
	);

	function toggle() {
		open = !open;
		if (!open) query = '';
	}

	function close() {
		open = false;
		query = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') close();
	}

	function handleDocumentClick(e: MouseEvent) {
		if (rootEl && !rootEl.contains(e.target as Node)) {
			close();
		}
	}

	$effect(() => {
		if (!open) return;
		document.addEventListener('click', handleDocumentClick);
		return () => {
			document.removeEventListener('click', handleDocumentClick);
		};
	});

	onMount(() => {
		// Fetch installed apps when user is signed in
		if ($isSignedIn) {
			fetchInstalledApps();
		}
	});

	// Re-fetch when sign-in state changes
	$effect(() => {
		if ($isSignedIn) {
			fetchInstalledApps();
		}
	});
</script>

<svelte:window onkeydown={open ? handleKeydown : undefined} />

<div class="relative inline-flex items-center" bind:this={rootEl}>
	<button
		class={`inline-flex size-9 items-center justify-center rounded-lg bg-transparent text-[var(--gv2-text-primary,#1a1a1a)] hover:bg-[var(--gv2-bg-hover,#f0f0f0)] ${buttonClass}`}
		onclick={toggle}
		aria-haspopup="menu"
		aria-expanded={open}
		aria-label="Open app launcher"
	>
		<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
			<circle cx="5" cy="5" r="2.2" />
			<circle cx="12" cy="5" r="2.2" />
			<circle cx="19" cy="5" r="2.2" />
			<circle cx="5" cy="12" r="2.2" />
			<circle cx="12" cy="12" r="2.2" />
			<circle cx="19" cy="12" r="2.2" />
			<circle cx="5" cy="19" r="2.2" />
			<circle cx="12" cy="19" r="2.2" />
			<circle cx="19" cy="19" r="2.2" />
		</svg>
	</button>

	{#if open}
		<div
			class="fixed left-3 top-[calc(var(--gv2-header-height,56px)+4px)] z-[1000] flex w-[min(88vw,340px)] max-h-[min(72vh,620px)] max-w-[min(90vw,360px)] flex-col overflow-hidden rounded-xl border border-[var(--gv2-border,#e6e6e6)] bg-[var(--gv2-bg-primary,#ffffff)] shadow-[0_4px_24px_rgba(0,0,0,0.12)] md:w-80"
			role="menu"
			aria-label="App Launcher"
		>
			<header class="flex shrink-0 items-center gap-2 border-b border-[var(--gv2-border,#e6e6e6)] px-3.5 py-3">
				<Input
					bind:value={query}
					placeholder="Search apps..."
					aria-label="Search apps"
					blockSize="sm"
					class="flex-1"
				/>
				<button class="inline-flex size-9 shrink-0 items-center justify-center rounded-lg text-[var(--gv2-text-muted,#767676)] hover:bg-[var(--gv2-bg-hover,#f0f0f0)] hover:text-[var(--gv2-text-primary,#1a1a1a)]" onclick={close} aria-label="Close">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18" />
						<line x1="6" y1="6" x2="18" y2="18" />
					</svg>
				</button>
			</header>

			<div class="flex-1 overflow-y-auto p-3.5">
				<!-- My Apps (installed) -->
				{#if filteredMyApps.length > 0}
					<section class="mb-4">
						<h3 class="mb-2.5 text-[11px] font-bold uppercase tracking-[0.07em] text-[var(--gv2-accent,#06c755)]">My Apps</h3>
						<div class="grid grid-cols-2 gap-1.5">
							{#each filteredMyApps as app (app.id)}
								<a
									href={app.href}
									class="flex flex-col items-center gap-1 rounded-xl px-1 py-2.5 text-inherit no-underline hover:bg-[var(--gv2-bg-hover,#f0f0f0)]"
									onclick={close}
								>
									<span class="flex size-11 items-center justify-center rounded-[10px] bg-[var(--gv2-accent,#06c755)]/10 text-2xl md:size-10 md:text-[22px]" aria-hidden="true">{app.icon}</span>
									<span class="max-w-[72px] overflow-hidden text-ellipsis whitespace-nowrap text-center text-[11px] font-medium leading-[1.3] text-[var(--gv2-text-primary,#1a1a1a)]">{app.shortName || app.name}</span>
								</a>
							{/each}
						</div>
					</section>
				{:else if $isSignedIn && $installedAppsLoading}
					<section class="mb-4">
						<h3 class="mb-2.5 text-[11px] font-bold uppercase tracking-[0.07em] text-[var(--gv2-accent,#06c755)]">My Apps</h3>
						<p class="text-[12px] text-[var(--gv2-text-muted,#767676)] px-1">Loading...</p>
					</section>
				{/if}

				<!-- All Apps (catalog) -->
				{#each categoryOrder as category}
					{#if sectionApps[category]?.length}
						<section class="mb-4 last:mb-0">
							<h3 class="mb-2.5 text-[11px] font-bold uppercase tracking-[0.07em] text-[var(--gv2-text-muted,#767676)]">{category}</h3>
							<div class="grid grid-cols-2 gap-1.5">
								{#each sectionApps[category] as app (app.id)}
									<a
										href={app.href}
										class="flex flex-col items-center gap-1 rounded-xl px-1 py-2.5 text-inherit no-underline hover:bg-[var(--gv2-bg-hover,#f0f0f0)]"
										target={app.external ? '_blank' : undefined}
										rel={app.external ? 'noopener noreferrer' : undefined}
										onclick={close}
									>
										<span class="flex size-11 items-center justify-center rounded-[10px] bg-[var(--gv2-bg-hover,#f0f0f0)] text-2xl md:size-10 md:text-[22px]" aria-hidden="true">{app.icon}</span>
										<span class="max-w-[72px] overflow-hidden text-ellipsis whitespace-nowrap text-center text-[11px] font-medium leading-[1.3] text-[var(--gv2-text-primary,#1a1a1a)]">{app.shortName || app.name}</span>
									</a>
								{/each}
							</div>
						</section>
					{/if}
				{/each}

				{#if visibleApps.length === 0 && filteredMyApps.length === 0}
					<p class="px-1 py-8 text-center text-[13px] text-[var(--gv2-text-muted,#767676)]">No apps found.</p>
				{/if}
			</div>
		</div>
	{/if}
</div>
