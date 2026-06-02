<script lang="ts">
	import { onMount } from 'svelte';
	import { getEpisodes, getEpisodePanels, getArcs, getArcPanels, storyboardClient, streamUpdates, exportPdf, listProjects, switchProject } from '$lib/client/storyboard-client';
	import StoryboardPage from './StoryboardPage.svelte';
	import MangaEditor from './MangaEditor.svelte';
	import ScriptView from './ScriptView.svelte';
	import ShootingView from './ShootingView.svelte';
	import NodeTree from './NodeTree.svelte';
	import from './ .svelte';
	import ImageGenStatus from './ImageGenStatus.svelte';
	// import { exportToPdf, type ExportMode } from '$lib/pdf-export';
	import type { PanelData, Panel } from '$lib/gen/proto/storyboard_pb';
	import { updateJob, removeJob } from '$lib/stores/job-store.svelte';

	let projects: Array<{ id: string; name: string; hasStoryboard: boolean }> = $state([]);
	let activeProject = $state('');
	let episodes: Array<{ id: string; title: string; totalPages: number }> = $state([]);
	let arcs: Array<{ id: string; title: string; description: string; episodeIds: string[] }> = $state([]);
	let selectedEpisode = $state('');
	let selectedArc = $state('');
	let editMode = $state<'episode' | 'arc'>('episode');
	let panels: Panel[] = $state([]);
	let loading = $state(false);
	let error = $state('');
	let selectedPage = $state(1);
	let selectedPanelIndex = $state(1);
	let selectedPanelData = $state<PanelData | undefined>(undefined);
	let viewMode = $state<'storyboard' | 'manga' | 'script' | 'shooting'>('storyboard');
	
	// Chat Panel reference
	let chatPanel = $state<any>(undefined);

	function openChatWithAgent(agent: any, prompt?: string) {
		if (chatPanel) {
			chatPanel.triggerAgent(agent, prompt);
		}
	}

	function addContextToChat(type: string, data: any) {
		if (chatPanel) {
			chatPanel.addContext(type, data);
		}
	}
	
	// Resizable split view state
	let storyboardWidthPercent = $state(50);
	let isResizing = $state(false);

	function startResizing(e: MouseEvent) {
		isResizing = true;
		e.preventDefault();
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isResizing) return;
		
		const container = document.querySelector('.editor-content');
		if (!container) return;
		
		const containerRect = container.getBoundingClientRect();
		// Adjust for agent sidebar if it's open
		const sidebar = document.querySelector('.agent-sidebar');
		const sidebarWidth = sidebar ? sidebar.getBoundingClientRect().width : 0;
		
		const relativeX = e.clientX - containerRect.left - sidebarWidth;
		const totalWidth = containerRect.width - sidebarWidth;
		
		const newPercent = (relativeX / totalWidth) * 100;
		// Constrain between 20% and 80%
		storyboardWidthPercent = Math.max(20, Math.min(80, newPercent));
	}

	function stopResizing() {
		isResizing = false;
	}

	// Remove unused variables found by svelte-check
	// let selectedPanelIndex = $state(1);
	// let selectedPanelData = $state<PanelData | undefined>(undefined);
	// let storyboardWidthPercent = $state(50);
	// let isResizing = $state(false);

	$effect(() => {
		console.log('StoryboardEditor state:', { 
			selectedPanelIndex, 
			selectedPanelData, 
			storyboardWidthPercent, 
			isResizing,
			startResizing,
			handleMouseMove,
			stopResizing
		});
	});
	
	const sessionId = Math.random().toString(36).substring(2, 15);

	const storyboardPath = '';

	async function loadProjects() {
		try {
			const response = await listProjects();
			const mapped = (response.projects ?? []).map((p) => ({
				id: p.id ?? '',
				name: p.name ?? '',
				hasStoryboard: p.hasStoryboard ?? false }));
			if (mapped.length > 0) {
				projects = mapped;
				activeProject = response.activeProject ?? '';
			} else {
				projects = [];
				activeProject = '';
			}
		} catch (err) {
			console.error('[StoryboardEditor] loadProjects error:', err);
			projects = [];
			activeProject = '';
		}
	}

	async function handleProjectSwitch(projectId: string) {
		if (projectId === activeProject) return;
		try {
			loading = true;
			error = '';
			await switchProject(projectId);
			activeProject = projectId;
			// Reset state and reload
			episodes = [];
			arcs = [];
			panels = [];
			selectedEpisode = '';
			selectedArc = '';
			selectedPage = 1;
			await Promise.all([loadEpisodes(), loadArcs()]);
		} catch (err) {
			console.error('[StoryboardEditor] handleProjectSwitch error:', err);
			error = `Failed to switch project: ${err}`;
		} finally {
			loading = false;
		}
	}

	// Load initial data - use $effect for reliable initialization
	let initialized = false;
	$effect(() => {
		if (initialized) return;
		initialized = true;
		console.log('[StoryboardEditor] init: loading projects, episodes and arcs, sessionId:', sessionId);
		(async () => {
			try {
				await loadProjects();
				await Promise.all([loadEpisodes(), loadArcs()]);
			} catch (err) {
				console.error('[StoryboardEditor] init: error loading initial data', err);
			}
		})();
	});

	$effect(() => {
		const currentId = editMode === 'episode' ? selectedEpisode : selectedArc;
		if (!currentId) return;

		console.log('[StoryboardEditor] Effect: setting up stream for', currentId);
		let unsubscribe: (() => void) | undefined;
		
		// Use a small timeout to avoid rapid re-connections during state transitions
		const timer = setTimeout(() => {
			unsubscribe = streamUpdates(
				storyboardPath,
				sessionId,
				(update) => {
					console.log('[StoryboardEditor] Stream update received:', update);
					const isRelevant = editMode === 'episode' 
						? update.episodeId === selectedEpisode 
						: arcs.find(a => a.id === selectedArc)?.episodeIds.includes(update.episodeId);

					if (update.updateType === 'panel_updated' && isRelevant) {
						// Update panel in local state
						panels = panels.map(p => {
							if (p.pageNumber === update.pageNumber && p.panel === update.panel) {
								// Use the panel's data directly from the update
								const newPanel = { ...p };
								if (update.panelData) {
									newPanel.data = update.panelData;
								}
								return newPanel;
							}
							return p;
						});
					} else if (update.updateType === 'chat_message') {
						// Forward to chat panel
						if (chatPanel && update.chatMessage) {
							chatPanel.addMessage({
								role: update.chatMessage.role,
								agent: update.chatMessage.agentMode,
								content: update.chatMessage.content
							});
						}
					} else if (update.updateType?.startsWith('job_')) {
						// Job progress/completion events
						if (update.jobId) {
							if (update.jobStatus === 'completed' || update.jobStatus === 'failed' || update.jobStatus === 'cancelled') {
								updateJob(update.jobId, {
									status: update.jobStatus,
									imageUrl: update.jobImageUrl || '',
									error: update.jobError || '' });
								// Reload panels to get the updated image
								if (update.jobStatus === 'completed' && isRelevant) {
									loadPanels();
								}
								// Remove from store after a brief delay
								setTimeout(() => removeJob(update.jobId!), 3000);
							} else {
								updateJob(update.jobId, {
									jobId: update.jobId,
									episodeId: update.episodeId,
									pageNumber: update.pageNumber,
									panel: update.panel,
									status: update.jobStatus || 'running',
									currentStep: update.jobCurrentStep,
									totalSteps: update.jobTotalSteps,
									etaMs: update.jobEtaMs });
							}
						}
					}
				},
				(err) => {
					console.error('[StoryboardEditor] Stream error:', err);
				}
			);
		}, 100);

		return () => {
			console.log('[StoryboardEditor] Effect cleanup: unsubscribing stream');
			clearTimeout(timer);
			if (unsubscribe) unsubscribe();
		};
	});

	async function loadEpisodes() {
		try {
			console.log('[StoryboardEditor] loadEpisodes: starting', { storyboardPath });
			loading = true;
			error = '';
			
			// Use type-safe wrapper with runtime validation
			const episodesList = await getEpisodes(storyboardPath);
			console.log('[StoryboardEditor] loadEpisodes: episodes received', episodesList);
			
			episodes = episodesList.map((e) => ({
				id: e.id ?? '',
				title: e.title ?? '',
				totalPages: e.totalPages ?? 0 }));
			
			if (episodes.length > 0 && !selectedEpisode && editMode === 'episode') {
				const firstEpisode = episodes[0];
				if (firstEpisode) {
					selectedEpisode = firstEpisode.id;
					await loadPanels();
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load episodes';
			console.error('[StoryboardEditor] Failed to load episodes:', err);
			episodes = [];
		} finally {
			loading = false;
		}
	}

	async function loadArcs() {
		try {
			console.log('[StoryboardEditor] loadArcs: starting', { storyboardPath });
			loading = true;
			error = '';
			
			const arcsList = await getArcs(storyboardPath);
			console.log('[StoryboardEditor] loadArcs: arcs received', arcsList);
			
			arcs = arcsList.map((a) => ({
				id: a.id ?? '',
				title: a.title ?? '',
				description: a.description ?? '',
				episodeIds: a.episodeIds ?? [] }));
			
			if (arcs.length > 0 && !selectedArc && editMode === 'arc') {
				const firstArc = arcs[0];
				if (firstArc) {
					selectedArc = firstArc.id;
					await loadArcPanelsData();
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load arcs';
			console.error('[StoryboardEditor] Failed to load arcs:', err);
			arcs = [];
		} finally {
			loading = false;
		}
	}

	async function loadPanels() {
		if (!selectedEpisode) return;
		try {
			loading = true;
			error = '';
			const panelsList = await getEpisodePanels(storyboardPath, selectedEpisode, 0);
			panels = panelsList;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load panels';
			panels = [];
		} finally {
			loading = false;
		}
	}

	async function loadArcPanelsData() {
		if (!selectedArc) return;
		try {
			loading = true;
			error = '';
			const panelsList = await getArcPanels(storyboardPath, selectedArc);
			panels = panelsList;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load arc panels';
			panels = [];
		} finally {
			loading = false;
		}
	}

	async function handlePanelUpdate(
		pageNumber: number,
		panel: number,
		data: PanelData
	) {
		const episodeId = editMode === 'episode' ? selectedEpisode : (data as any).gh_episodeId || selectedEpisode;
		if (!episodeId) return;
		
		// Optimistic local update
		panels = panels.map(p => {
			if (p.pageNumber === pageNumber && p.panel === panel) {
				return { ...p, data };
			}
			return p;
		});

		try {
			await storyboardClient.updatePanel({
				filePath: storyboardPath,
				episodeId: episodeId,
				pageNumber,
				panel,
				panelData: data,
				sessionId: sessionId
			});
			// No need to reload everything if we updated local state correctly
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update panel';
			console.error('Failed to update panel:', err);
			if (editMode === 'episode') {
				await loadPanels();
			} else {
				await loadArcPanelsData();
			}
		}
	}

	function handleApplyPatches(patches: any[]) {
		console.log('[StoryboardEditor] Applying patches:', patches);
		// For now, we handle simple panel data updates
		// In a real implementation, this would be more complex
		for (const patch of patches) {
			// Example path: /gh:episodes/0/gh:pages/0/gh:panels/0/dialogue/0/text
			// This is a placeholder for a real JSON-LD patch application
			console.log('[StoryboardEditor] Patch logic pending for:', patch.path);
		}
		alert(`AI suggested ${patches.length} changes. Patch application logic is being developed.`);
	}

	let lastContextId = $state<string | null>(null);

	// Only load panels when an episode or arc is selected
	$effect(() => {
		const currentId = editMode === 'episode' ? selectedEpisode : selectedArc;
		if (!currentId || currentId.trim() === '') return;

		if (currentId !== lastContextId) {
			console.log('[StoryboardEditor] Effect: selection changed, loading panels for', currentId);
			lastContextId = currentId;
			
			if (editMode === 'episode') {
				loadPanels();
				addContextToChat('episode', { id: currentId });
			} else {
				loadArcPanelsData();
				addContextToChat('arc', { id: currentId });
			}
		}
	});

	// Handle initial selection
	$effect(() => {
		if (editMode === 'episode' && !selectedEpisode && episodes.length > 0) {
			const firstEpisode = episodes[0];
			if (firstEpisode) {
				selectedEpisode = firstEpisode.id;
			}
		} else if (editMode === 'arc' && !selectedArc && arcs.length > 0) {
			const firstArc = arcs[0];
			if (firstArc) {
				selectedArc = firstArc.id;
			}
		}
	});

	// PDF Export state
	let isExporting = $state(false);

	async function handleExportPdf() {
		if (isExporting || panels.length === 0) return;
		
		isExporting = true;
		try {
			const currentId = editMode === 'episode' ? selectedEpisode : selectedArc;
			const episodeId = editMode === 'episode' ? currentId : '';
			const arcId = editMode === 'arc' ? currentId : '';
			
			const response = await exportPdf(
				storyboardPath,
				episodeId,
				arcId,
				viewMode
			);

			if (response.pdfContent) {
				// Download the PDF
				const blob = new Blob([response.pdfContent], { type: 'application/pdf' });
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = response.filename || `storyboard_${currentId}.pdf`;
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
				document.body.removeChild(a);
			}
		} catch (err) {
			console.error('PDF export failed:', err);
			error = err instanceof Error ? err.message : 'PDF export failed';
		} finally {
			isExporting = false;
		}
	}
</script>

<div class="storyboard-editor">
	<header class="editor-header">
		<div class="project-selector">
			<select
				value={activeProject}
				onchange={(e) => {
					const newProject = e.currentTarget.value;
					if (newProject !== activeProject) handleProjectSwitch(newProject);
				}}
				disabled={loading || projects.length === 0}
			>
				{#if projects.length === 0}
					<option value="" disabled>Loading projects...</option>
				{:else}
					{#each projects as project}
						<option value={project.id} selected={project.id === activeProject}>{project.name}{project.hasStoryboard ? '' : ' (no storyboard)'}</option>
					{/each}
				{/if}
			</select>
		</div>

		<div class="edit-mode-selector">
			<button
				class:active={editMode === 'episode'}
				onclick={() => editMode = 'episode'}
			>By Episode</button>
			<button
				class:active={editMode === 'arc'}
				onclick={() => editMode = 'arc'}
			>By Arc</button>
		</div>

		<div class="selection-controls">
			{#if editMode === 'episode'}
				<div class="episode-selector">
					<label for="episode-select">Episode:</label>
					<select
						id="episode-select"
						bind:value={selectedEpisode}
					>
						{#if episodes.length === 0}
							<option value="" disabled>No episodes available</option>
						{:else}
							{#each episodes as episode}
								<option value={episode.id}>{episode.title}</option>
							{/each}
						{/if}
					</select>
				</div>
			{:else}
				<div class="arc-selector">
					<label for="arc-select">Arc:</label>
					<select
						id="arc-select"
						bind:value={selectedArc}
					>
						{#if arcs.length === 0}
							<option value="" disabled>No arcs available</option>
						{:else}
							{#each arcs as arc}
								<option value={arc.id}>{arc.title}</option>
							{/each}
						{/if}
					</select>
				</div>
			{/if}
		</div>

		<div class="view-switcher">
			<button 
				class:active={viewMode === 'storyboard'} 
				onclick={() => viewMode = 'storyboard'}
			>Storyboard</button>
			<button 
				class:active={viewMode === 'manga'} 
				onclick={() => viewMode = 'manga'}
			>Manga</button>
			<button 
				class:active={viewMode === 'script'} 
				onclick={() => viewMode = 'script'}
			>Script</button>
			<button 
				class:active={viewMode === 'shooting'} 
				onclick={() => viewMode = 'shooting'}
			>Shooting</button>
		</div>

		<div class="episode-info">
			{#if selectedEpisode && episodes.length > 0}
				{@const episode = episodes.find((e) => e.id === selectedEpisode)}
				{#if episode}
					<span class="total-pages">{episode.totalPages} pages</span>
				{/if}
			{/if}
		</div>

		<div class="header-right-group">
			<ImageGenStatus />
			<div class="export-controls">
				<button
					class="export-btn"
					onclick={handleExportPdf}
					disabled={isExporting || panels.length === 0}
					title={`Export ${viewMode} as PDF`}
				>
					{#if isExporting}
						<span class="spinner"></span>
						Exporting...
					{:else}
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
							<polyline points="14 2 14 8 20 8"></polyline>
							<line x1="12" y1="18" x2="12" y2="12"></line>
							<line x1="9" y1="15" x2="15" y2="15"></line>
						</svg>
						PDF ({viewMode})
					{/if}
				</button>
			</div>
		</div>
	</header>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	{#if loading}
		<div class="loading">Loading...</div>
	{:else if panels.length > 0}
		<div 
			class="editor-content" 
		>
			<aside class="left-sidebar">
				<NodeTree 
					{panels} 
					selectedId={editMode === 'episode' ? selectedEpisode : selectedArc} 
					onSelect={(panel) => {
						selectedPanelIndex = panel.panel;
						selectedPanelData = panel.data;
						addContextToChat('panel', panel);
					}}
					onContextAdd={(type, data) => addContextToChat(type, data)}
				/>
			</aside>

			<main class="main-content">
				<div class="active-view">
					{#if viewMode === 'storyboard'}
						<StoryboardPage
							{panels}
							episodeId={editMode === 'episode' ? selectedEpisode : selectedArc}
							storyboardPath={storyboardPath}
							on:update={({ detail }) =>
								handlePanelUpdate(detail.pageNumber, detail.panel, detail.data)}
							on:pageChange={({ detail }) => {
								selectedPage = detail;
							}}
							on:panelSelect={({ detail }) => {
								selectedPanelIndex = detail.panel;
								selectedPanelData = detail.data;
								addContextToChat('panel', detail);
							}}
							on:contextAdd={({ detail }) => {
								addContextToChat(detail.type, detail.data);
							}}
					on:agentTrigger={({ detail }) => {
						openChatWithAgent(detail.agent);
					}}
						/>
					{:else if viewMode === 'manga'}
						<MangaEditor
							{panels}
							episodeId={editMode === 'episode' ? selectedEpisode : selectedArc}
							{storyboardPath}
							bind:selectedPage
							on:update={({ detail }) =>
								handlePanelUpdate(detail.pageNumber, detail.panel, detail.data)}
							on:panelSelect={({ detail }) => {
								selectedPanelIndex = detail.panel;
								selectedPanelData = detail.data;
								addContextToChat('panel', detail);
							}}
							on:contextAdd={({ detail }) => {
								addContextToChat(detail.type, detail.data);
							}}
						/>
					{:else if viewMode === 'script'}
						<ScriptView 
							{panels} 
							episodeId={editMode === 'episode' ? selectedEpisode : selectedArc} 
							{storyboardPath}
							on:update={({ detail }) =>
								handlePanelUpdate(detail.pageNumber, detail.panel, detail.data)}
							on:panelSelect={({ detail }) => {
								selectedPanelIndex = detail.panel;
								selectedPanelData = detail.data;
								addContextToChat('panel', detail);
							}}
							on:contextAdd={({ detail }) => {
								addContextToChat(detail.type, detail.data);
							}}
						/>
					{:else if viewMode === 'shooting'}
						<ShootingView 
							{panels} 
							episodeId={editMode === 'episode' ? selectedEpisode : selectedArc} 
							{storyboardPath}
						/>
					{/if}
				</div>
			</main>

			<aside class="right-sidebar">
				< bind:this={chatPanel} 
					selectedEpisode={editMode === 'episode' ? selectedEpisode : selectedArc} 
					{storyboardPath} 
					onApplyPatches={handleApplyPatches}
				/>
			</aside>
		</div>
	{:else if episodes.length === 0 && !loading}
		<div class="empty-state">
			<p>No episodes available. Check console for details.</p>
			<button onclick={loadEpisodes}>Retry</button>
		</div>
	{/if}
</div>

<style>
	.storyboard-editor {
		display: flex;
		flex-direction: column;
		height: 100vh;
		background: #f5f5f0;
		font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
	}

	.editor-content {
		display: flex;
		flex: 1;
		overflow: hidden;
		position: relative;
		background: #1e1e1e;
	}

	.left-sidebar {
		width: 260px;
		flex-shrink: 0;
		border-right: 1px solid #333;
		display: flex;
		flex-direction: column;
	}

	.right-sidebar {
		width: 350px;
		flex-shrink: 0;
		border-left: 1px solid #333;
		display: flex;
		flex-direction: column;
	}

	.main-content {
		flex: 1;
		display: flex;
		position: relative;
		overflow: hidden;
		background: #fff;
	}

	.active-view {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.storyboard-view {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		border-right: 1px solid #ddd;
	}

	.manga-view {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.editor-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 1.5rem;
		background: #fff;
		border-bottom: 2px solid #ddd;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		gap: 1rem;
	}

	.edit-mode-selector {
		display: flex;
		background: #f0f0f0;
		padding: 3px;
		border-radius: 6px;
	}

	.edit-mode-selector button {
		padding: 0.3rem 0.8rem;
		border: none;
		background: transparent;
		border-radius: 4px;
		font-size: 0.8rem;
		font-weight: 600;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
	}

	.edit-mode-selector button.active {
		background: #fff;
		color: #4a90e2;
		box-shadow: 0 1px 3px rgba(0,0,0,0.1);
	}

	.project-selector {
		flex-shrink: 0;
	}

	.project-selector select {
		padding: 0.4rem 0.6rem;
		border: 2px solid #4a90e2;
		border-radius: 6px;
		font-size: 0.85rem;
		font-weight: 600;
		background: #e8f0fe;
		color: #1a56db;
		cursor: pointer;
		min-width: 160px;
	}

	.project-selector select:hover {
		background: #d0e2fd;
	}

	.project-selector select:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.selection-controls {
		display: flex;
		align-items: center;
		flex: 1;
	}

	.episode-selector, .arc-selector {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.episode-selector label, .arc-selector label {
		font-weight: 600;
		font-size: 0.9rem;
	}

	.episode-selector select, .arc-selector select {
		padding: 0.4rem 0.8rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.9rem;
		min-width: 150px;
	}

	.view-switcher {
		display: flex;
		background: #eee;
		padding: 3px;
		border-radius: 6px;
		margin: 0 1rem;
	}

	.view-switcher button {
		padding: 0.4rem 1rem;
		border: none;
		background: transparent;
		border-radius: 4px;
		font-size: 0.85rem;
		font-weight: 600;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
	}

	.view-switcher button.active {
		background: #fff;
		color: #4a90e2;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}

	.debug-info {
		margin-left: 0.5rem;
		color: #f90;
		font-size: 1.2rem;
		cursor: help;
	}

	.episode-info {
		display: flex;
		align-items: center;
		gap: 1rem;
		color: #666;
		font-size: 0.9rem;
	}

	.total-pages {
		font-weight: 500;
	}

	.error {
		padding: 1rem;
		background: #fee;
		color: #c00;
		border: 1px solid #fcc;
		margin: 1rem;
		border-radius: 4px;
	}

	.loading {
		padding: 2rem;
		text-align: center;
		color: #666;
	}

	.empty-state {
		padding: 2rem;
		text-align: center;
		color: #666;
	}

	.empty-state button {
		margin-top: 1rem;
		padding: 0.5rem 1rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		background: #fff;
		cursor: pointer;
	}

	.empty-state button:hover {
		background: #f5f5f5;
	}

	.header-right-group {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.export-controls {
		display: flex;
		align-items: center;
	}

	.export-btn {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.4rem 0.8rem;
		border: 1px solid #4a90e2;
		border-radius: 4px;
		background: #4a90e2;
		color: white;
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.export-btn:hover:not(:disabled) {
		background: #357abd;
		border-color: #357abd;
	}

	.export-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.export-btn svg {
		flex-shrink: 0;
	}

	.spinner {
		display: inline-block;
		width: 14px;
		height: 14px;
		border: 2px solid #ffffff;
		border-radius: 50%;
		border-top-color: transparent;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
