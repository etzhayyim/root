<script lang="ts">
	import { storyboardClient } from '$lib/client/storyboard-client';

	let { selectedEpisode, storyboardPath, pageNumber, panelIndex } = $props<{
		selectedEpisode: string;
		storyboardPath: string;
		pageNumber: number;
		panelIndex: number;
	}>();

	let loading = $state(false);
	let message = $state('');

	async function generateCinematic() {
		if (!selectedEpisode) return;
		loading = true;
		message = 'Generating cinematic sketch...';
		try {
			const res = await storyboardClient.generateCinematicSketch({
				filePath: storyboardPath,
				episodeId: selectedEpisode,
				pageNumber: pageNumber,
				panel: panelIndex
			});
			message = res.message;
		} catch (err) {
			message = `Error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			loading = false;
		}
	}
</script>

<div class="agent-panel cinematic-agent">
	<h3>Cinematic Sketch LLM</h3>
	<p class="description">Visual composition, camera work, and image prompts.</p>
	
	<div class="selection-info">
		Selected: Page {pageNumber}, Panel {panelIndex}
	</div>

	<button onclick={generateCinematic} disabled={loading || !selectedEpisode}>
		{loading ? 'Generating...' : 'Generate Cinematic Sketch'}
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
		margin-bottom: 0.5rem;
	}

	.selection-info {
		font-size: 0.8rem;
		color: #888;
		margin-bottom: 1rem;
		font-style: italic;
	}

	button {
		width: 100%;
		padding: 0.6rem;
		background: #e67e22;
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
		background: #fff5eb;
		border-radius: 4px;
	}

	.status-message.error {
		background: #fee;
		color: #c00;
	}
</style>
