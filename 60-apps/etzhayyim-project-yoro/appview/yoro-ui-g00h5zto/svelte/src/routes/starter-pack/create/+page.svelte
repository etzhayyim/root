<script lang="ts">
	import { goto } from '$app/navigation';
	import { Avatar } from '@etzhayyim/design-system';
	import { searchActors } from '$lib/atproto-agent';

	function goBack() { if (history.length > 1) history.back(); else void goto('/'); }

	let name = $state('');
	let description = $state('');
	let searchQuery = $state('');
	let searchResults = $state<Array<{ did: string; handle: string; displayName?: string; avatar?: string }>>([]);
	let selectedUsers = $state<Array<{ did: string; handle: string; displayName?: string; avatar?: string }>>([]);
	let searching = $state(false);

	async function doSearch() {
		const q = searchQuery.trim();
		if (!q) { searchResults = []; return; }
		searching = true;
		try {
			const result = await searchActors(q, { limit: 10 });
			searchResults = Array.isArray(result) ? result : (result as any).actors ?? [];
		} catch (e) { console.warn('starter pack search failed', e); } finally { searching = false; }
	}

	function addUser(u: typeof selectedUsers[0]) {
		if (!selectedUsers.find(s => s.did === u.did)) {
			selectedUsers = [...selectedUsers, u];
		}
		searchQuery = '';
		searchResults = [];
	}

	function removeUser(did: string) {
		selectedUsers = selectedUsers.filter(u => u.did !== did);
	}
</script>

<svelte:head><title>Create Starter Pack — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="flex-1 text-[17px] font-bold text-gv2-text-primary">Create Starter Pack</span>
		<button type="button" class="min-h-[36px] rounded-full bg-[#1185FE] px-4 py-1.5 text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-50" disabled={!name.trim() || selectedUsers.length === 0}>Create</button>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-4">
		<input type="text" bind:value={name} placeholder="Pack name" class="mb-3 min-h-[44px] w-full rounded-lg border border-gv2-border/40 bg-gv2-bg-primary px-3 py-2 text-[15px] text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/50" />
		<textarea bind:value={description} placeholder="Description (optional)" rows="2" class="mb-4 min-h-[60px] w-full rounded-lg border border-gv2-border/40 bg-gv2-bg-primary px-3 py-2 text-[15px] text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/50 resize-none"></textarea>

		<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Add people</h4>
		<form class="mb-3" onsubmit={(e) => { e.preventDefault(); void doSearch(); }}>
			<input type="search" bind:value={searchQuery} placeholder="Search users" class="min-h-[44px] w-full rounded-lg border border-gv2-border/40 bg-gv2-bg-primary px-3 py-2 text-[15px] text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/50" />
		</form>

		{#if searchResults.length > 0}
			<div class="mb-4 divide-y divide-gv2-border/20 rounded-lg border border-gv2-border/40">
				{#each searchResults as u (u.did)}
					<button type="button" class="flex w-full items-center gap-3 px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => addUser(u)}>
						<Avatar src={u.avatar || undefined} fallback={(u.displayName || u.handle || '?').slice(0, 2).toUpperCase()} size="sm" class="!h-8 !w-8" />
						<div class="min-w-0 flex-1">
							<span class="block truncate text-[14px] font-bold text-gv2-text-primary">{u.displayName || u.handle}</span>
							<span class="block truncate text-[12px] text-gv2-text-muted">@{u.handle}</span>
						</div>
					</button>
				{/each}
			</div>
		{/if}

		{#if selectedUsers.length > 0}
			<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">Selected ({selectedUsers.length})</h4>
			<div class="space-y-1">
				{#each selectedUsers as u (u.did)}
					<div class="flex items-center gap-3 rounded-lg px-3 py-2">
						<Avatar src={u.avatar || undefined} fallback={(u.displayName || u.handle || '?').slice(0, 2).toUpperCase()} size="sm" class="!h-8 !w-8" />
						<span class="flex-1 truncate text-[14px] font-medium text-gv2-text-primary">{u.displayName || u.handle}</span>
						<button type="button" class="text-[13px] text-red-500 touch-manipulation active:opacity-70" onclick={() => removeUser(u.did)}>Remove</button>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
