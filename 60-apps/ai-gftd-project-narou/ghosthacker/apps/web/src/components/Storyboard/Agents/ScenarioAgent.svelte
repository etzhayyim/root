<script lang="ts">
	import { storyboardClient } from '$lib/client/storyboard-client';

	let { storyboardPath } = $props<{
		selectedEpisode: string;
		storyboardPath: string;
	}>();

	let prompt = $state('');
	let loading = $state(false);
	let message = $state('');

	async function generateScenario() {
		if (!prompt) return;
		loading = true;
		message = 'Starting scenario generation...';
		try {
			const res = await storyboardClient.generateScenario({
				filePath: storyboardPath,
				prompt: prompt
			});
			message = res.message;
		} catch (err) {
			message = `Error: ${err instanceof Error ? err.message : String(err)}`;
		} finally {
			loading = false;
		}
	}
</script>

<div class="agent-panel scenario-agent">
	<h3>Scenario Writer LLM</h3>
	<p class="description">High-level plot, beats, and narrative structure.</p>
	
	<div class="input-group">
		<textarea 
			bind:value={prompt} 
			placeholder="Enter plot idea or scenario prompt..."
			disabled={loading}
		></textarea>
		<button onclick={generateScenario} disabled={loading || !prompt}>
			{loading ? 'Generating...' : 'Generate Scenario'}
		</button>
	</div>

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

	textarea {
		width: 100%;
		height: 80px;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		margin-bottom: 0.5rem;
		resize: vertical;
	}

	button {
		width: 100%;
		padding: 0.6rem;
		background: #4a90e2;
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
		background: #f0f7ff;
		border-radius: 4px;
	}

	.status-message.error {
		background: #fee;
		color: #c00;
	}
</style>
