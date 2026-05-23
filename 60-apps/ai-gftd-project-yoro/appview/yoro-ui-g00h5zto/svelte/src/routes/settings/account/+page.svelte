<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Skeleton } from '@etzhayyim/design-system';
	import { getSession } from '$lib/atproto-agent';
	import { getSessionToken } from '$lib/auth';

	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }

	let handle = $state('');
	let email = $state('');
	let loading = $state(true);

	onMount(async () => {
		try {
			const token = await getSessionToken().catch(() => null);
			if (!token) return;
			const session = await getSession();
			handle = (session as any)?.handle ?? '';
			email = (session as any)?.email ?? '';
		} catch (e) { console.warn('account session load failed', e); } finally { loading = false; }
	});
</script>

<svelte:head><title>Account — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Account</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		{#if loading}
			<div class="space-y-3"><Skeleton variant="text" class="w-1/2 h-4" /><Skeleton variant="text" class="w-2/3 h-4" /></div>
		{:else}
			<div class="space-y-1">
				<div class="flex min-h-[44px] items-center justify-between rounded-lg px-3 py-2">
					<span class="text-[14px] text-gv2-text-muted">Handle</span>
					<span class="text-[15px] text-gv2-text-primary">@{handle || 'Not set'}</span>
				</div>
				<div class="flex min-h-[44px] items-center justify-between rounded-lg px-3 py-2">
					<span class="text-[14px] text-gv2-text-muted">Email</span>
					<span class="text-[15px] text-gv2-text-primary">{email || 'Not set'}</span>
				</div>
				<button type="button" class="flex min-h-[44px] w-full items-center rounded-lg px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => goto('/settings/app-passwords')}>
					<span class="text-[15px] text-gv2-text-primary">App passwords</span>
					<svg class="ml-auto h-4 w-4 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 5l7 7-7 7" /></svg>
				</button>
			</div>
			<div class="mt-8 border-t border-gv2-border/20 pt-4">
				<button type="button" class="min-h-[44px] w-full rounded-lg px-3 py-2 text-left text-[15px] text-red-500 touch-manipulation active:bg-red-500/10">Delete account</button>
			</div>
		{/if}
	</div>
</div>
