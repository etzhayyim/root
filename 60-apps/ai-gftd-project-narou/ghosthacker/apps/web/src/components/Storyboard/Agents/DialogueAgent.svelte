<script lang="ts">
	import { storyboardClient } from '$lib/client/storyboard-client';
	import { createEventDispatcher } from 'svelte';

	let { selectedEpisode, storyboardPath, pageNumber, panelIndex, panelData } = $props<{
		selectedEpisode: string;
		storyboardPath: string;
		pageNumber: number;
		panelIndex: number;
		panelData: any;
	}>();

	const dispatch = createEventDispatcher();

	let loading = $state(false);
	let message = $state('');
	let style = $state('cinematic drama, Japanese');
	let maxLines = $state(2);

	async function generateDialogue() {
		if (!selectedEpisode) return;
		loading = true;
		message = 'Generating dialogue...';
		try {
			const res = await storyboardClient.generateDialogue({
				filePath: storyboardPath,
				episodeId: selectedEpisode,
				pageNumber: pageNumber,
				panel: panelIndex,
				panelData: panelData,
				style: style,
				maxLines: maxLines
			});
			
			if (res.success && res.dialogue.length > 0) {
				message = `Generated ${res.dialogue.length} lines.`;
				// Dispatch event to update the panel in the parent
				dispatch('generated', {
					dialogue: res.dialogue
				});
			} else {
				message = res.message || 'Failed to generate dialogue.';
			}
		} catch (err) {
			message = `Error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			loading = false;
		}
	}
</script>

<div class="agent-panel dialogue-agent">
	<h3>Dialogue Agent</h3>
	<p class="description">Generate dialogue with acting/directing metadata.</p>
	
	<div class="selection-info">
		Selected: Page {pageNumber}, Panel {panelIndex}
	</div>

	<div class="input-group">
		<label for="dialogue-style">Style:</label>
		<input id="dialogue-style" type="text" bind:value={style} placeholder="Style (e.g. cinematic drama)" />
	</div>

	<div class="input-group">
		<label for="max-lines">Max Lines:</label>
		<input id="max-lines" type="number" bind:value={maxLines} min="1" max="10" />
	</div>

	<button onclick={generateDialogue} disabled={loading || !selectedEpisode}>
		{loading ? 'Generating...' : 'Generate Dialogue'}
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

	.input-group {
		margin-bottom: 0.75rem;
	}

	.input-group label {
		display: block;
		font-size: 0.8rem;
		color: #555;
		margin-bottom: 0.25rem;
	}

	.input-group input {
		width: 100%;
		padding: 0.4rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.9rem;
	}

	button {
		width: 100%;
		padding: 0.6rem;
		background: #e74c3c;
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
		background: #fff5f5;
		border-radius: 4px;
	}

	.status-message.error {
		background: #fee;
		color: #c00;
	}
</style>
