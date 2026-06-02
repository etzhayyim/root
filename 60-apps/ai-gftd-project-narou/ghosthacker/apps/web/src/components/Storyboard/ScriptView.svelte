<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Panel, PanelData } from '$lib/gen/proto/storyboard_pb';
	import { PanelDataSchema, DialogueSchema } from '$lib/gen/proto/storyboard_pb';
	import { create } from '@bufbuild/protobuf';

	let { panels = [] } = $props<{
		panels: Panel[];
		episodeId?: string;
		storyboardPath?: string;
	}>();

	const dispatch = createEventDispatcher();

	// Group panels by page
	let pagesMap = $derived(panels.reduce((acc: Record<number, Panel[]>, panel: Panel) => {
		const pageNum = panel.pageNumber;
		if (!acc[pageNum]) {
			acc[pageNum] = [];
		}
		acc[pageNum].push(panel);
		return acc;
	}, {} as Record<number, Panel[]>));

	let pageNumbers = $derived(Object.keys(pagesMap)
		.map(Number)
		.sort((a, b) => a - b));

	// Editing state
	let editingPanelId = $state<string | null>(null);
	let editBuffer = $state<PanelData | null>(null);

	function startEditing(panel: Panel) {
		editingPanelId = `${panel.pageNumber}-${panel.panel}`;
		editBuffer = create(PanelDataSchema, panel.data ?? {});
		dispatch('panelSelect', panel);
		dispatch('contextAdd', { type: 'panel', data: panel });
	}

	function saveAndStopEditing(panel: Panel) {
		if (editBuffer) {
			dispatch('update', {
				pageNumber: panel.pageNumber,
				panel: panel.panel,
				data: editBuffer
			});
		}
		editingPanelId = null;
		editBuffer = null;
	}

	function handleBufferUpdate(field: string, value: any) {
		if (!editBuffer) return;
		(editBuffer as any)[field] = value;
	}

	function handleDialogueBufferUpdate(index: number, field: string, value: any) {
		if (!editBuffer?.dialogue) return;
		const newDialogues = [...editBuffer.dialogue];
		const currentDialogue = newDialogues[index];
		if (!currentDialogue) return;

		const dialogueInit: any = {
			speaker: currentDialogue.speaker,
			text: currentDialogue.text,
			delivery: currentDialogue.delivery,
			subtext: currentDialogue.subtext,
			emotion: currentDialogue.emotion,
			pauseBeforeMs: currentDialogue.pauseBeforeMs,
			pauseAfterMs: currentDialogue.pauseAfterMs,
			mangaLayout: currentDialogue.mangaLayout,
		};
		dialogueInit[field] = value;

		newDialogues[index] = create(DialogueSchema, dialogueInit);
		editBuffer.dialogue = newDialogues;
	}

	function getAvatarUrl(speaker: string) {
		if (!speaker || speaker === 'Narration' || speaker === 'NewsHacker') return '';
		const id = speaker.replace('character:', '');
		const baseUrl = typeof window !== 'undefined' 
			? (window.location.port === '1421' ? 'http://localhost:8081' : window.location.origin)
			: 'http://localhost:8081';
		return `${baseUrl}/images/characters/${id}.png`;
	}
</script>

<div class="script-view">
	<div class="screenplay-page">
		{#each pageNumbers as pageNum}
			<div class="page-break-marker">PAGE {pageNum}</div>
			
			{#each pagesMap[pageNum] as panel, i (panel.panel + '-' + i)}
				{@const isEditing = editingPanelId === `${panel.pageNumber}-${panel.panel}`}
				
				<div 
					class="script-block" 
					class:editing={isEditing}
					onclick={() => !isEditing && startEditing(panel)}
					role="button"
					tabindex="0"
					onkeydown={(e) => e.key === 'Enter' && startEditing(panel)}
				>
					<!-- Scene Heading (using environment) -->
					<div class="scene-heading">
						{panel.data?.environment?.toUpperCase() || 'INT. LOCATION - DAY'}
					</div>

					{#if isEditing && editBuffer}
						<div class="edit-form">
							<textarea 
								class="action-input"
								value={editBuffer.visualNote ?? ''} 
								oninput={(e) => handleBufferUpdate('visualNote', e.currentTarget.value)}
								placeholder="Action lines..."
							></textarea>
							
							<div class="dialogue-editor">
								{#each editBuffer.dialogue ?? [] as d, i}
									<div class="dialogue-edit-row">
										<input 
											class="speaker-input"
											value={d.speaker} 
											oninput={(e) => handleDialogueBufferUpdate(i, 'speaker', e.currentTarget.value)}
										/>
										<textarea 
											class="text-input"
											value={d.text} 
											oninput={(e) => handleDialogueBufferUpdate(i, 'text', e.currentTarget.value)}
										></textarea>
									</div>
								{/each}
							</div>
							<button class="done-btn" onclick={() => saveAndStopEditing(panel)}>Done</button>
						</div>
					{:else}
						<!-- Action Lines -->
						<div class="action-line">
							{panel.data?.visualNote || '---'}
						</div>

						<!-- Dialogues -->
						<div class="dialogue-container">
							{#each panel.data?.dialogue ?? [] as d}
								<div class="dialogue-block">
									<div class="character-name">
										{#if getAvatarUrl(d.speaker)}
											<img src={getAvatarUrl(d.speaker)} alt={d.speaker} class="mini-avatar" onerror={(e) => (e.currentTarget as HTMLImageElement).style.display='none'} />
										{/if}
										{d.speaker.toUpperCase()}
									</div>
									{#if d.delivery}
										<div class="parenthetical">({d.delivery})</div>
									{/if}
									<div class="dialogue-text">
										{d.text}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		{/each}
	</div>
</div>

<style>
	.script-view {
		flex: 1;
		overflow-y: auto;
		background: #f0f0f0;
		padding: 2rem;
		font-family: 'Courier Prime', 'Courier New', Courier, monospace;
	}

	.screenplay-page {
		max-width: 800px;
		margin: 0 auto;
		background: white;
		padding: 4rem 6rem;
		box-shadow: 0 0 15px rgba(0,0,0,0.1);
		min-height: 100vh;
		color: black;
	}

	.page-break-marker {
		text-align: center;
		font-size: 0.7rem;
		color: #ccc;
		border-bottom: 1px dashed #eee;
		margin: 2rem 0;
		padding-bottom: 0.5rem;
	}

	.script-block {
		margin-bottom: 2rem;
		padding: 1rem;
		border-radius: 4px;
		transition: background 0.2s;
	}

	.script-block:hover:not(.editing) {
		background: #f9f9f9;
		cursor: pointer;
	}

	.script-block.editing {
		outline: 2px solid #4a90e2;
		background: #fff;
	}

	.scene-heading {
		font-weight: bold;
		text-transform: uppercase;
		margin-bottom: 1rem;
		letter-spacing: 0.05em;
	}

	.action-line {
		margin-bottom: 1.5rem;
		line-height: 1.2;
		white-space: pre-wrap;
	}

	.dialogue-container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.dialogue-block {
		width: 70%;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
	}

	.character-name {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
		font-weight: bold;
		position: relative;
	}

	.mini-avatar {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		object-fit: cover;
		border: 2px solid #eee;
		background: #f9f9f9;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}

	.parenthetical {
		font-size: 0.9rem;
		margin-bottom: 0.2rem;
		font-style: normal;
	}

	.dialogue-text {
		line-height: 1.2;
		text-align: left;
		width: 100%;
	}

	/* Edit Form */
	.edit-form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.action-input {
		width: 100%;
		min-height: 100px;
		border: 1px solid #ddd;
		padding: 0.5rem;
		font-family: inherit;
	}

	.dialogue-edit-row {
		margin-bottom: 1rem;
		border-left: 3px solid #eee;
		padding-left: 1rem;
	}

	.speaker-input {
		font-weight: bold;
		text-transform: uppercase;
		border: none;
		border-bottom: 1px solid #eee;
		margin-bottom: 0.5rem;
	}

	.text-input {
		width: 100%;
		border: 1px solid #eee;
		padding: 0.4rem;
		font-family: inherit;
	}

	.done-btn {
		align-self: flex-end;
		padding: 0.4rem 1.5rem;
		background: #333;
		color: white;
		border: none;
		cursor: pointer;
	}
</style>
