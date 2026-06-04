<!--
  /settings/app-passwords — App passwords management.
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { listAppPasswords, createAppPassword, revokeAppPassword } from '$lib/atproto-agent';

	let passwords = $state<Array<{ name: string; createdAt: string }>>([]);
	let loading = $state(true);
	let newName = $state('');
	let creating = $state(false);
	let createdPassword = $state('');

	async function load() {
		loading = true;
		try {
			const result = await listAppPasswords();
			passwords = Array.isArray(result) ? result : (result as any).passwords ?? [];
		} catch (e) { console.warn('list app passwords failed', e); } finally {
			loading = false;
		}
	}

	async function handleCreate() {
		const name = newName.trim();
		if (!name || creating) return;
		creating = true;
		try {
			const result = await createAppPassword(name);
			createdPassword = (result as any)?.password ?? '';
			newName = '';
			await load();
		} catch (e) { console.warn('create app password failed', e); } finally {
			creating = false;
		}
	}

	async function handleRevoke(name: string) {
		try {
			await revokeAppPassword(name);
			await load();
		} catch (e) { console.warn('revoke app password failed', e); }
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/settings');
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>App Passwords — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">App Passwords</span>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none">
		<div class="px-4 py-4">
			<p class="mb-4 text-[13px] text-gv2-text-muted">App passwords allow third-party apps to access your account without giving them your main password.</p>

			{#if createdPassword}
				<div class="mb-4 rounded-lg border border-[#00BA7C]/40 bg-[#00BA7C]/10 p-3">
					<p class="text-[13px] font-bold text-gv2-text-primary">New app password created:</p>
					<p class="mt-1 font-mono text-[15px] text-gv2-text-primary">{createdPassword}</p>
					<p class="mt-1 text-[12px] text-gv2-text-muted">Copy this password now. You won't be able to see it again.</p>
				</div>
			{/if}

			<form class="mb-4 flex gap-2" onsubmit={(e) => { e.preventDefault(); void handleCreate(); }}>
				<input type="text" bind:value={newName} placeholder="App name" class="min-h-[44px] flex-1 rounded-lg border border-gv2-border/40 bg-gv2-bg-primary px-3 py-2 text-[15px] text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/50" />
				<button type="submit" class="min-h-[44px] rounded-lg bg-[#1185FE] px-4 text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-50" disabled={creating || !newName.trim()}>Add</button>
			</form>
		</div>

		{#if loading}
			<div class="px-4" in:fade={staggerFade(0, { duration: 300 })}>
				{#each { length: 3 } as _}
					<div class="flex items-center gap-3 py-3"><Skeleton variant="text" class="w-1/3 h-4" /><Skeleton variant="text" class="w-1/4 h-3" /></div>
				{/each}
			</div>
		{:else}
			<div class="divide-y divide-gv2-border/20">
				{#each passwords as pw, i (pw.name)}
					<div class="flex items-center justify-between px-4 py-3" in:fade={staggerFade(i, { duration: 150 })}>
						<div>
							<span class="block text-[15px] font-medium text-gv2-text-primary">{pw.name}</span>
							<span class="block text-[12px] text-gv2-text-muted">Created {new Date(pw.createdAt).toLocaleDateString()}</span>
						</div>
						<button type="button" class="min-h-[36px] rounded-lg bg-red-500/10 px-3 text-[13px] font-bold text-red-500 touch-manipulation active:bg-red-500/20" onclick={() => void handleRevoke(pw.name)}>Revoke</button>
					</div>
				{/each}
				{#if passwords.length === 0}
					<div class="py-8 text-center text-[14px] text-gv2-text-muted">No app passwords</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
