<script lang="ts">
	import { storyboardClient } from '$lib/client/storyboard-client';

	let { selectedEpisode, storyboardPath } = $props<{
		selectedEpisode: string;
		storyboardPath: string;
	}>();

	let loading = $state(false);
	let message = $state('');

	async function refineCharacters() {
		if (!selectedEpisode) return;
		loading = true;
		message = 'Refining characters...';
		try {
			const res = await storyboardClient.refineCharacters({
				filePath: storyboardPath,
				episodeId: selectedEpisode,
				characterIds: [] // Backend can extract from episode if empty
			});
			message = res.message;
		} catch (err) {
			message = `Error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			loading = false;
		}
	}
</script>

<div class="agent-panel character-agent">
	<h3>Character LLM</h3>
	<p class="description">Character consistency, emotional state, and motives.</p>
	
	<button onclick={refineCharacters} disabled={loading || !selectedEpisode}>
		{loading ? 'Refining...' : 'Refine Character Consistency'}
	</button>

	{#if message}
		<div class="status-message" class:error={message.startsWith('Error')}>
			{message}
		</div>
	{/if}
</div>

<style>
	.agent-panel {
		padding: 1rem;
		background: #fff;
		border: 1px solid #ddd;
		border-radius: 8px;
		margin-bottom: 1rem;
	}

	h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
		color: #333;
	}

	.description {
		font-size: 0.85rem;
		color: #666;
		margin-bottom: 1rem;
	}

	button {
		width: 100%;
		padding: 0.6rem;
		background: #9b59b6;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-weight: 600;
	}

	button:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.status-message {
		margin-top: 0.5rem;
		font-size: 0.85rem;
		padding: 0.5rem;
		background: #f5f0f9;
		border-radius: 4px;
	}

	.status-message.error {
		background: #fee;
		color: #c00;
	}
</style>
