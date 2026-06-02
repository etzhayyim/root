<script lang="ts">
	import { storyboardClient } from '$lib/client/storyboard-client';

	let { selectedEpisode, storyboardPath } = $props<{
		selectedEpisode: string;
		storyboardPath: string;
	}>();

	let loading = $state(false);
	let message = $state('');

	async function generateEpisode() {
		if (!selectedEpisode) return;
		loading = true;
		message = 'Starting episode generation...';
		try {
			const res = await storyboardClient.generateEpisode({
				filePath: storyboardPath,
				episodeId: selectedEpisode
			});
			message = res.message;
		} catch (err) {
			message = `Error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			loading = false;
		}
	}
</script>

<div class="agent-panel episode-agent">
	<h3>Episode LLM</h3>
	<p class="description">Detailed scene breakdown, dialogue, and pacing.</p>
	
	<button onclick={generateEpisode} disabled={loading || !selectedEpisode}>
		{loading ? 'Generating...' : 'Generate Episode Content'}
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
		background: #2ecc71;
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
		background: #f0fff4;
		border-radius: 4px;
	}

	.status-message.error {
		background: #fee;
		color: #c00;
	}
</style>
