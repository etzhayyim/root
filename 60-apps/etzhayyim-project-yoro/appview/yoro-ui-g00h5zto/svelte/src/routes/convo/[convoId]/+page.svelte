<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { useActivityFeed } from '$lib/provider/activity-feed.svelte.js';

	const convoId = $derived($page.params.convoId);
	const isAgentActivity = $derived(convoId === 'agent-activity');
	const activity = useActivityFeed();

	onMount(() => {
		if (isAgentActivity) {
			activity.startPolling();
			return () => activity.stopPolling();
		}
		void goto(`/projects/${convoId}`, { replaceState: true });
	});
</script>

{#if isAgentActivity}
<div class="flex flex-col h-full bg-gv2-bg-primary">
	<!-- Header -->
	<div class="flex items-center gap-3 px-4 py-3 border-b border-gv2-border/30">
		<button onclick={() => goto('/convo')} class="text-gv2-accent text-[14px]">&larr;</button>
		<div class="w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 to-blue-500 flex items-center justify-center text-white text-[14px] font-bold">A</div>
		<div>
			<h1 class="text-[15px] font-bold text-gv2-text-primary">Agent Activity</h1>
			<p class="text-[12px] text-gv2-text-muted">{activity.entries.length} events</p>
		</div>
	</div>

	<!-- Chat-style activity feed -->
	<div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
		{#if activity.loading && activity.entries.length === 0}
			<div class="flex items-center gap-2 text-[13px] text-gv2-text-muted py-8 justify-center">
				<div class="w-4 h-4 border-2 border-gv2-accent/40 border-t-gv2-accent rounded-full animate-spin"></div>
				Loading agent activity...
			</div>
		{:else if activity.entries.length === 0}
			<p class="text-[13px] text-gv2-text-muted text-center py-8">No agent activity yet.</p>
		{:else}
			{#each activity.entries as entry (entry.id)}
				<div class="flex gap-2 items-start">
					<img
						src={entry.actorAvatar}
						alt={entry.actorName}
						class="w-8 h-8 rounded-full bg-gv2-bg-secondary shrink-0 mt-0.5"
					/>
					<div class="flex-1 min-w-0">
						<div class="flex items-baseline gap-1.5">
							<span class="text-[13px] font-semibold text-gv2-text-primary truncate">{entry.actorName}</span>
							<span class="text-[11px] text-gv2-text-muted shrink-0">{new Date(entry.timestamp).toLocaleTimeString()}</span>
						</div>
						<div class="rounded-2xl bg-gv2-bg-secondary/60 px-3 py-2 mt-0.5 max-w-[85%]">
							<p class="text-[13px] text-gv2-text-primary">{entry.summary}</p>
							{#if entry.detail}
								<p class="text-[12px] text-gv2-text-muted mt-1">{entry.detail}</p>
							{/if}
						</div>
						<span class="text-[10px] text-gv2-text-muted mt-0.5 inline-block px-1.5 py-0.5 rounded bg-gv2-bg-secondary/40">{entry.type}</span>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>
{:else}
<p>Redirecting...</p>
{/if}
