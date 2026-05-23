<script lang="ts">
	import { page } from '$app/stores';
	import { Badge } from '@etzhayyim/design-system';
	import { tenantLabel, plan, theme, signOut, adminKey } from '$lib/stores';

	const NAV = [
		{ href: '/studio', label: 'Home', icon: '⌂' },
		{ href: '/studio/cypher', label: 'Cypher', icon: 'ƛ' },
		{ href: '/studio/storage', label: 'Storage', icon: '🗄' },
		{ href: '/studio/billing', label: 'Billing', icon: '¥' },
	];

	const ADMIN_NAV = [{ href: '/studio/admin/outbox', label: 'Outbox review', icon: '✉︎' }];

	function active(href: string): boolean {
		const path = $page.url.pathname;
		if (href === '/studio') return path === '/studio' || path === '/studio/';
		return path.startsWith(href);
	}

	function toggleTheme() {
		theme.update((t) => (t === 'dark' ? 'light' : 'dark'));
	}
</script>

<aside
	class="hidden w-60 shrink-0 flex-col border-r border-gftd-border bg-gftd-card/40 md:flex"
>
	<div class="flex items-center gap-2 px-5 py-5">
		<span class="text-2xl">🟦</span>
		<a href="/studio" class="text-lg font-semibold text-gftd-text">yatabase</a>
		<Badge type="secondary">Studio</Badge>
	</div>

	<nav class="flex-1 px-3">
		<ul class="space-y-1">
			{#each NAV as item}
				<li>
					<a
						href={item.href}
						class={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition
							${
								active(item.href)
									? 'bg-gftd-accent/15 text-gftd-text font-medium'
									: 'text-gftd-secondary hover:bg-white/5 hover:text-gftd-text'
							}`}
						aria-current={active(item.href) ? 'page' : undefined}
					>
						<span class="w-5 text-center text-base opacity-70">{item.icon}</span>
						{item.label}
					</a>
				</li>
			{/each}
		</ul>

		{#if $adminKey}
			<p class="mt-6 px-3 text-xs font-medium uppercase tracking-wider text-gftd-muted">
				Admin
			</p>
			<ul class="mt-2 space-y-1">
				{#each ADMIN_NAV as item}
					<li>
						<a
							href={item.href}
							class={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition
								${
									active(item.href)
										? 'bg-amber-500/15 text-gftd-text font-medium'
										: 'text-gftd-secondary hover:bg-white/5 hover:text-gftd-text'
								}`}
							aria-current={active(item.href) ? 'page' : undefined}
						>
							<span class="w-5 text-center text-base opacity-70">{item.icon}</span>
							{item.label}
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</nav>

	<div class="border-t border-gftd-border p-4 text-xs">
		<div class="flex items-center justify-between gap-2">
			<div class="min-w-0">
				<div class="truncate text-gftd-text">{$tenantLabel || '—'}</div>
				<div class="truncate text-gftd-muted">{$plan?.plan ?? 'free'} plan</div>
			</div>
			<button
				class="rounded-md border border-gftd-border px-2 py-1 text-gftd-secondary hover:bg-white/5"
				onclick={toggleTheme}
				type="button"
				aria-label="Toggle theme"
			>
				{$theme === 'dark' ? '☾' : '☼'}
			</button>
		</div>
		{#if $tenantLabel}
			<button
				class="mt-3 w-full rounded-md border border-gftd-border px-2 py-1 text-gftd-secondary hover:bg-white/5"
				type="button"
				onclick={() => signOut()}>Sign out</button
			>
		{/if}
	</div>
</aside>
