<script lang="ts">
	import type { Panel } from '$lib/gen/proto/storyboard_pb';

	let { panels = [], episodeId = '' } = $props<{
		panels: Panel[];
		episodeId?: string;
		storyboardPath?: string;
	}>();

	function getAvatarUrl(speaker: string) {
		if (!speaker || speaker === 'Narration' || speaker === 'NewsHacker') return '';
		const id = speaker;
		const baseUrl = typeof window !== 'undefined' 
			? (window.location.port === '1421' ? 'http://localhost:8081' : window.location.origin)
			: 'http://localhost:8081';
		return `${baseUrl}/images/characters/${id}.png`;
	}
</script>

<div class="shooting-view">
	<div class="shooting-container">
		<header class="shooting-header">
			<h1>SHOOTING SCRIPT: {episodeId}</h1>
		</header>

		<table class="shooting-table">
			<thead>
				<tr>
					<th class="col-num">#</th>
					<th class="col-shot">SHOT / CAMERA</th>
					<th class="col-action">ACTION / VISUAL</th>
					<th class="col-dialogue">DIALOGUE / SOUND</th>
				</tr>
			</thead>
			<tbody>
				{#each panels as panel}
					<tr class="panel-row">
						<td class="col-num">
							<div class="panel-id">P{panel.pageNumber}-{panel.panel}</div>
							{#if panel.cutNumber}
								<div class="cut-id">CUT {panel.cutNumber}</div>
							{/if}
						</td>
						<td class="col-shot">
							<div class="shot-type">{panel.data?.shot || '---'}</div>
							<div class="camera-dir">{panel.data?.cameraDirection || ''}</div>
							{#if panel.data?.durationSeconds}
								<div class="duration">{panel.data.durationSeconds}s</div>
							{/if}
						</td>
						<td class="col-action">
							<div class="visual-note">{panel.data?.visualNote || '---'}</div>
							{#if panel.data?.environment}
								<div class="env-tag">ENV: {panel.data.environment}</div>
							{/if}
						</td>
						<td class="col-dialogue">
							{#each panel.data?.dialogue ?? [] as d}
								<div class="dialogue-line">
									<div class="speaker">
										{#if getAvatarUrl(d.speaker)}
											<img src={getAvatarUrl(d.speaker)} alt={d.speaker} class="mini-avatar" />
										{/if}
										{d.speaker}:
									</div>
									<div class="text">「{d.text}」</div>
									{#if d.delivery}
										<div class="delivery">({d.delivery})</div>
									{/if}
								</div>
							{/each}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<style>
	.shooting-view {
		flex: 1;
		overflow-y: auto;
		background: #fff;
		padding: 2rem;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
	}

	.shooting-container {
		max-width: 1200px;
		margin: 0 auto;
	}

	.shooting-header {
		border-bottom: 3px solid #000;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
	}

	.shooting-header h1 {
		font-size: 1.5rem;
		font-weight: 900;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.shooting-table {
		width: 100%;
		border-collapse: collapse;
	}

	.shooting-table th {
		background: #f0f0f0;
		text-align: left;
		padding: 0.75rem;
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		border: 1px solid #ddd;
	}

	.panel-row {
		border-bottom: 1px solid #eee;
	}

	.panel-row:hover {
		background: #f9f9f9;
	}

	.panel-row td {
		padding: 1rem;
		vertical-align: top;
		border: 1px solid #eee;
	}

	.col-num { width: 80px; }
	.col-shot { width: 200px; }
	.col-action { width: 400px; }
	.col-dialogue { flex: 1; }

	.panel-id { font-weight: bold; font-size: 0.8rem; }
	.cut-id { font-size: 0.7rem; color: #888; }

	.shot-type { font-weight: bold; text-transform: uppercase; font-size: 0.9rem; }
	.camera-dir { font-size: 0.8rem; color: #e67e22; font-style: italic; }
	.duration { font-size: 0.75rem; color: #666; margin-top: 0.25rem; }

	.visual-note { font-size: 0.9rem; line-height: 1.5; }
	.env-tag { font-size: 0.7rem; color: #888; margin-top: 0.5rem; }

	.dialogue-line { margin-bottom: 1rem; }
	.speaker { 
		font-weight: bold; 
		font-size: 0.8rem; 
		display: flex; 
		align-items: center; 
		gap: 0.4rem;
		margin-bottom: 0.2rem;
	}
	.mini-avatar { width: 18px; height: 18px; border-radius: 50%; }
	.text { font-size: 0.9rem; line-height: 1.4; }
	.delivery { font-size: 0.75rem; color: #2ecc71; font-style: italic; }
</style>
