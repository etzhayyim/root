<script lang="ts">
	import type { Panel, PanelData } from '$lib/gen/proto/storyboard_pb';
	import MangaPanel from './MangaPanel.svelte';
	import { createEventDispatcher } from 'svelte';

	interface PanelLayoutInfo {
		x: number;
		y: number;
		width: number;
		height: number;
		zIndex?: number;
		panelIndex?: number;
	}

	let { panels = [], pageNumber = 1, episodeId = '', storyboardPath = '' } = $props<{
		panels: Panel[];
		pageNumber: number;
		episodeId?: string;
		storyboardPath?: string;
	}>();

	const dispatch = createEventDispatcher();

	// Derived states
	let sortedPanels = $derived([...panels].sort((a, b) => a.panel - b.panel));
	let storedLayout = $derived(panels[0]?.data?.mangaLayout);
	
	// Generate fallback layout based on panel count if no stored layout
	let pageLayout = $derived(storedLayout?.panels?.length > 0 ? storedLayout : generateDefaultLayout(sortedPanels.length));
	
	/**
	 * Generate Jump manga-style default layout based on panel count
	 * Japanese manga reading order: RIGHT to LEFT, TOP to BOTTOM
	 * All layouts include small gaps between panels for authentic manga look
	 */
	function generateDefaultLayout(panelCount: number): { panels: PanelLayoutInfo[] } {
		const layouts: Record<number, PanelLayoutInfo[]> = {
			1: [{ x: 0, y: 0, width: 100, height: 100 }],
			2: [
				{ x: 0, y: 0, width: 100, height: 58 },
				{ x: 0, y: 59, width: 100, height: 41 }
			],
			3: [
				{ x: 0, y: 0, width: 100, height: 44 },
				// Row 2: P2 on RIGHT, P3 on LEFT (right-to-left reading)
				{ x: 46, y: 45, width: 54, height: 55 },
				{ x: 0, y: 45, width: 45, height: 55 }
			],
			4: [
				{ x: 0, y: 0, width: 100, height: 49 },
				// Row 2: P2 RIGHT, P3 CENTER, P4 LEFT (right-to-left reading)
				{ x: 68, y: 50, width: 32, height: 50 },
				{ x: 34, y: 50, width: 33, height: 50 },
				{ x: 0, y: 50, width: 33, height: 50 }
			],
			5: [
				{ x: 0, y: 0, width: 100, height: 40 },
				// Row 2: P2 RIGHT, P3 LEFT
				{ x: 51, y: 41, width: 49, height: 29 },
				{ x: 0, y: 41, width: 50, height: 29 },
				// Row 3: P4 RIGHT, P5 LEFT
				{ x: 41, y: 71, width: 59, height: 29 },
				{ x: 0, y: 71, width: 40, height: 29 }
			],
			6: [
				{ x: 0, y: 0, width: 100, height: 36 },
				// Row 2: P2 RIGHT, P3 LEFT
				{ x: 51, y: 37, width: 49, height: 31 },
				{ x: 0, y: 37, width: 50, height: 31 },
				// Row 3: P4 RIGHT, P5 CENTER, P6 LEFT
				{ x: 68, y: 69, width: 32, height: 31 },
				{ x: 33, y: 69, width: 34, height: 31 },
				{ x: 0, y: 69, width: 32, height: 31 }
			],
			7: [
				{ x: 0, y: 0, width: 100, height: 33 },
				// Row 2: P2 RIGHT, P3 CENTER, P4 LEFT (right-to-left reading)
				{ x: 70, y: 34, width: 30, height: 24 },
				{ x: 40, y: 34, width: 29, height: 24 },
				{ x: 0, y: 34, width: 39, height: 24 },
				// Row 3: P5 RIGHT, P6 LEFT
				{ x: 51, y: 59, width: 49, height: 20 },
				{ x: 0, y: 59, width: 50, height: 20 },
				{ x: 0, y: 80, width: 100, height: 20 }
			],
			8: [
				// Row 1: P1 LEFT (big), P2 RIGHT-TOP, P3 RIGHT-BOTTOM
				{ x: 0, y: 0, width: 59, height: 29 },
				{ x: 60, y: 0, width: 40, height: 14 },
				{ x: 60, y: 15, width: 40, height: 14 },
				// Row 2: P4 RIGHT, P5 LEFT
				{ x: 51, y: 30, width: 49, height: 24 },
				{ x: 0, y: 30, width: 50, height: 24 },
				// Row 3: P6 RIGHT, P7 CENTER, P8 LEFT
				{ x: 68, y: 55, width: 32, height: 22 },
				{ x: 33, y: 55, width: 34, height: 22 },
				{ x: 0, y: 55, width: 32, height: 22 }
			],
			9: [
				{ x: 0, y: 0, width: 100, height: 28 },
				// Row 2: P2 RIGHT, P3 CENTER, P4 LEFT
				{ x: 68, y: 29, width: 32, height: 22 },
				{ x: 33, y: 29, width: 34, height: 22 },
				{ x: 0, y: 29, width: 32, height: 22 },
				// Row 3: P5 RIGHT, P6 LEFT
				{ x: 51, y: 52, width: 49, height: 23 },
				{ x: 0, y: 52, width: 50, height: 23 },
				// Row 4: P7 RIGHT, P8 CENTER, P9 LEFT
				{ x: 68, y: 76, width: 32, height: 24 },
				{ x: 33, y: 76, width: 34, height: 24 },
				{ x: 0, y: 76, width: 32, height: 24 }
			]
		};
		
		// Get the appropriate layout or fallback to grid
		const layoutPanels = layouts[panelCount];
		if (layoutPanels) {
			return { panels: layoutPanels.map((p, i) => ({ ...p, zIndex: i, panelIndex: i + 1 })) };
		}
		
		// Fallback: generate a reasonable grid for any panel count
		const cols = panelCount <= 4 ? 2 : 3;
		const rows = Math.ceil(panelCount / cols);
		const panelWidth = 100 / cols;
		const panelHeight = 100 / rows;
		
		const gridPanels: PanelLayoutInfo[] = [];
		for (let i = 0; i < panelCount; i++) {
			const row = Math.floor(i / cols);
			const col = i % cols;
			gridPanels.push({
				x: col * panelWidth,
				y: row * panelHeight,
				width: panelWidth,
				height: panelHeight,
				zIndex: i,
				panelIndex: i + 1
			});
		}
		return { panels: gridPanels };
	}

	function handleUpdate(panelNumber: number, data: PanelData) {
		dispatch('update', {
			pageNumber,
			panel: panelNumber,
			data
		});
	}

	function handlePanelResize(panelIndex: number, delta: { x: number, y: number, w: number, h: number }) {
		if (!pageLayout) return;

		const newPanels = pageLayout.panels.map((p: any, i: number) => {
			if (i === panelIndex) {
				return {
					...p,
					x: Math.max(0, Math.min(100, p.x + delta.x)),
					y: Math.max(0, Math.min(100, p.y + delta.y)),
					width: Math.max(5, Math.min(100, p.width + delta.w)),
					height: Math.max(5, Math.min(100, p.height + delta.h))
				};
			}
			return p;
		});

		// Update only the first panel of the page with the new layout
		const firstPanel = panels[0];
		if (!firstPanel) return;

		const updatedData = {
			...firstPanel.data,
			mangaLayout: {
				...pageLayout,
				panels: newPanels
			}
		};
		handleUpdate(firstPanel.panel, updatedData as any);
	}
</script>

<div class="manga-page">
	<div class="manga-page-content">
		{#each sortedPanels as panel, i (panel.panel + '-' + i)}
			{@const layout = pageLayout?.panels?.[i]}
			{#if layout}
				<div 
					class="layout-wrapper"
					class:emphasis={layout.emphasis}
					style="
						position: absolute;
						left: {layout.x}%;
						top: {layout.y}%;
						width: {layout.width}%;
						height: {layout.height}%;
						z-index: {layout.zIndex || i};
					"
				>
					<MangaPanel
						{panel}
						{episodeId}
						{storyboardPath}
						on:update={(e) => handleUpdate(panel.panel, e.detail)}
					/>
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="resize-handle" onmousedown={(e) => {
						const startX = e.clientX;
						const startY = e.clientY;
						const onMouseMove = (moveEvent: MouseEvent) => {
							const dx = ((moveEvent.clientX - startX) / 600) * 100;
							const dy = ((moveEvent.clientY - startY) / 848) * 100;
							handlePanelResize(i, { x: 0, y: 0, w: dx, h: dy });
						};
						const onMouseUp = () => {
							window.removeEventListener('mousemove', onMouseMove);
							window.removeEventListener('mouseup', onMouseUp);
						};
						window.addEventListener('mousemove', onMouseMove);
						window.addEventListener('mouseup', onMouseUp);
					}}></div>
				</div>
			{/if}
		{/each}
	</div>
	<div class="page-footer">
		{pageNumber}
	</div>
</div>

<style>
	.manga-page {
		width: 600px;
		min-height: 848px;
		background: #fff;
		box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
		padding: 40px;
		position: relative;
		display: flex;
		flex-direction: column;
	}

	.manga-page-content {
		position: relative;
		flex: 1;
		min-height: 768px;
	}

	.layout-wrapper {
		border: 1px solid transparent;
		transition: border-color 0.2s, box-shadow 0.2s;
		padding: 2px;
		box-sizing: border-box;
	}

	.layout-wrapper:hover {
		border-color: #007bff;
	}

	/* Jump manga style: emphasis panels get subtle highlight */
	.layout-wrapper.emphasis {
		z-index: 100 !important;
	}

	.resize-handle {
		position: absolute;
		right: 0;
		bottom: 0;
		width: 15px;
		height: 15px;
		background: rgba(0, 123, 255, 0.5);
		cursor: nwse-resize;
		display: none;
		border-radius: 2px;
	}

	.layout-wrapper:hover .resize-handle {
		display: block;
	}

	.page-footer {
		text-align: center;
		padding-top: 20px;
		color: #888;
		font-size: 0.8rem;
	}
</style>
