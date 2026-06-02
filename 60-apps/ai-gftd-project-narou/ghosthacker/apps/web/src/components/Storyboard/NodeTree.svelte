<script lang="ts">
	import type { Panel } from '$lib/gen/proto/storyboard_pb';

	let { panels = [], selectedId = '', onSelect, onContextAdd } = $props<{
		panels: Panel[];
		selectedId: string;
		onSelect?: (panel: Panel) => void;
		onContextAdd?: (type: string, data: any) => void;
	}>();

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

	function handleDragStart(e: DragEvent, type: string, data: any) {
		if (e.dataTransfer) {
			e.dataTransfer.setData('application/json', JSON.stringify({ type, ...data }));
			e.dataTransfer.effectAllowed = 'copy';
		}
	}
</script>

<div class="node-tree">
	<div class="tree-header">STORY STRUCTURE</div>
	<div class="tree-content">
		<div class="episode-node">
			<div 
				class="node-label episode" 
				draggable="true"
				ondragstart={(e) => handleDragStart(e, 'episode', { id: selectedId })}
				onclick={() => onContextAdd?.('episode', { id: selectedId })}
			>
				📁 {selectedId || 'No Selection'}
			</div>
			
			<div class="children">
				{#each pageNumbers as pageNum}
					<div class="page-node">
						<div 
							class="node-label page"
							draggable="true"
							ondragstart={(e) => handleDragStart(e, 'page', { episodeId: selectedId, pageNumber: pageNum })}
							onclick={() => onContextAdd?.('page', { episodeId: selectedId, pageNumber: pageNum })}
						>
							📄 Page {pageNum}
						</div>
						<div class="children">
							{#each pagesMap[pageNum] as panel}
								<div 
									class="node-label panel"
									draggable="true"
									ondragstart={(e) => handleDragStart(e, 'panel', { 
										episodeId: selectedId, 
										pageNumber: pageNum, 
										panel: panel.panel,
										data: panel.data 
									})}
									onclick={() => {
										onSelect?.(panel);
										onContextAdd?.('panel', { 
											episodeId: selectedId, 
											pageNumber: pageNum, 
											panel: panel.panel,
											data: panel.data 
										});
									}}
								>
									🎞️ Panel {panel.panel}
									{#if panel.data?.characters && panel.data.characters.length > 0}
										<span class="node-meta">({panel.data.characters.length} chars)</span>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>

<style>
	.node-tree {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: #252526;
		color: #ccc;
		font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
		font-size: 0.85rem;
	}

	.tree-header {
		padding: 0.75rem 1rem;
		font-size: 0.7rem;
		font-weight: bold;
		color: #888;
		letter-spacing: 0.1em;
		background: #2d2d2d;
		border-bottom: 1px solid #333;
	}

	.tree-content {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem 0;
	}

	.node-label {
		padding: 0.25rem 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.node-label:hover {
		background: #37373d;
		color: #fff;
	}

	.node-label.episode { font-weight: bold; color: #e0e0e0; }
	.node-label.page { color: #d4d4d4; }
	.node-label.panel { color: #b5cea8; padding-left: 2rem; }

	.children {
		display: flex;
		flex-direction: column;
	}

	.page-node > .children {
		padding-left: 1rem;
	}

	.node-meta {
		font-size: 0.7rem;
		color: #666;
		margin-left: auto;
	}

	:global(.dragging) {
		opacity: 0.5;
	}
</style>
