<script lang="ts">
	import type { GfAppLink } from './types';

	const {
		title = 'etzhayyim Apps',
		showSearch = false,
		apps = []
	} = $props<{
		title?: string;
		showSearch?: boolean;
		apps?: GfAppLink[];
	}>();

	const categoryOrder: Array<GfAppLink['category']> = ['Orgs', 'Services', 'Systems'];
	let query = $state('');
	const keyword = $derived(query.trim().toLowerCase());
	const visibleApps = $derived(
		apps.filter((app: GfAppLink) => {
			if (!keyword) return true;
			const token = `${app.name} ${app.description || ''}`.toLowerCase();
			return token.includes(keyword);
		})
	);

	const sectionApps = $derived(
		Object.fromEntries(
			categoryOrder.map((category) => [
				category,
				visibleApps.filter((app: GfAppLink) => app.category === category),
			])
		) as Record<'Orgs' | 'Services' | 'Systems', GfAppLink[]>
	);
</script>

<div class="flex h-full flex-col p-3.5 text-[var(--gv2-text-primary,#fff)]">
	<header class="mb-2.5 flex items-center justify-between">
		<div class="text-[11px] font-bold uppercase tracking-[0.07em] text-[var(--gv2-text-muted,#8b8b8b)]">{title}</div>
	</header>

	{#if showSearch}
		<div class="mb-2.5">
			<input
				class="h-[34px] w-full rounded-lg border border-[var(--gv2-border,#333)] bg-[var(--gv2-bg-hover,#2a2a2a)] px-2.5 text-[var(--gv2-text-primary,#fff)] outline-none focus:border-[var(--gv2-accent,#d4a574)]"
				bind:value={query}
				placeholder="Search apps..."
				aria-label="Search apps"
			/>
		</div>
	{/if}

	<div class="flex flex-col gap-3.5">
		{#each categoryOrder as category}
			{#if sectionApps[category]?.length}
				<section>
					<h3 class="mb-2 text-[10px] font-bold uppercase tracking-[0.07em] text-[var(--gv2-text-muted,#8b8b8b)]">{category}</h3>
					<div class="grid grid-cols-2 gap-2.5">
						{#each sectionApps[category] as app}
							<a
								href={app.href}
								class="grid grid-cols-[28px_1fr] items-start gap-2.5 rounded-[14px] border border-[var(--gv2-border,#333)] bg-[var(--gv2-bg-sidebar,#1f1f1f)] p-2.5 text-inherit no-underline transition hover:-translate-y-px hover:border-[color-mix(in_oklab,var(--gv2-accent,#d4a574)_45%,var(--gv2-border,#333))] hover:shadow-[0_6px_16px_rgba(0,0,0,0.24)]"
								target={app.external ? '_blank' : undefined}
								rel={app.external ? 'noopener noreferrer' : undefined}
							>
								<div class="inline-flex size-7 items-center justify-center rounded-[7px] bg-[var(--gv2-bg-hover,#2a2a2a)] text-base" aria-hidden="true">{app.icon}</div>
								<div>
									<div class="text-xs font-semibold leading-[1.35] text-[var(--gv2-text-primary,#fff)]">{app.name}</div>
									{#if app.description}
										<p class="mt-[3px] text-[10px] leading-[1.4] text-[var(--gv2-text-muted,#777)]">{app.description}</p>
									{/if}
								</div>
							</a>
						{/each}
					</div>
				</section>
			{/if}
		{/each}
	</div>

	{#if visibleApps.length === 0}
		<p class="px-1 py-6 text-center text-xs text-[var(--gv2-text-muted,#777)]">No apps found.</p>
	{/if}
</div>
