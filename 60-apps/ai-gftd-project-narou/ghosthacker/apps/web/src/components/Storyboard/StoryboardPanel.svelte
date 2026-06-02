<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Panel, Dialogue, GeneratedImage } from '$lib/gen/proto/storyboard_pb';
	import { PanelDataSchema, DialogueSchema, GeneratedImageSchema } from '$lib/gen/proto/storyboard_pb';
	import { create } from '@bufbuild/protobuf';
	import { generatePanelDialogue, submitGenerationJob, cancelGenerationJob, storyboardClient } from '$lib/client/storyboard-client';
	import { getJobForPanel } from '$lib/stores/job-store.svelte';

	export let panel: Panel;
	export let episodeId: string = '';
	export let storyboardPath: string = '';

	const dispatch = createEventDispatcher();

	let editing = false;
	let cutNumber = panel.cutNumber || '';
	let visualNote = panel.data?.visualNote ?? '';
	let cameraDirection = panel.data?.cameraDirection ?? '';
	let durationSeconds = panel.data?.durationSeconds ?? 0;
	let dialogues: Dialogue[] = panel.data?.dialogue ?? [];
	let characters = panel.data?.characters ?? [];
	let environment = panel.data?.environment ?? '';
	let shot = panel.data?.shot ?? '';
	let runwayPrompt = panel.data?.runwayPrompt ?? '';
	let generatedImages: GeneratedImage[] = panel.data?.generatedImages ?? [];
	let currentImageIndex = panel.data?.currentImageIndex ?? (generatedImages.length > 0 ? generatedImages.length - 1 : -1);
	let generatingImage = false;
	let imageError = '';
	let selectedModel = 'local'; // 'openrouter' or 'local'
	let activeJobId = '';
	let generatingDialogue = false;
	let dialogueError = '';
	let generatingCinematic = false;
	let cinematicError = '';

	// Reactive: update when panel prop changes (important for initial data load)
	$: if (panel.data?.generatedImages) {
		generatedImages = panel.data.generatedImages;
		currentImageIndex = panel.data.currentImageIndex ?? (generatedImages.length > 0 ? generatedImages.length - 1 : -1);
	}

	// Computed: current image URL (convert relative path to full URL)
	$: currentImageUrl = currentImageIndex >= 0 && currentImageIndex < generatedImages.length 
		? (() => {
			const url = generatedImages[currentImageIndex]?.imageUrl ?? '';
			if (!url) return '';
			// If it's already a full URL (data URL or http), return as is
			if (url.startsWith('http') || url.startsWith('data:')) {
				return url;
			}
			// Otherwise, prepend backend base URL
			const baseUrl = typeof window !== 'undefined' 
				? (window.location.port === '1421' ? 'http://localhost:8081' : window.location.origin)
				: 'http://localhost:8081';
			return baseUrl + url;
		})()
		: '';

	function startEdit() {
		editing = true;
	}

	function saveEdit() {
		console.log('[StoryboardPanel] saveEdit: saving data', {
			generatedImages: generatedImages.map(img => ({
				imageUrl: img.imageUrl,
				imagePrompt: img.imagePrompt,
				generatedAt: img.generatedAt?.toString(),
				model: img.model
			})),
			currentImageIndex,
			panelNumber: panel.panel,
			pageNumber: panel.pageNumber,
			generatedImagesCount: generatedImages.length
		});
		
		// Ensure all GeneratedImage objects are properly created with schema
		const serializedImages = generatedImages.map((img, idx) => {
			// If already a GeneratedImage type, use as is, otherwise create from schema
			if (img && typeof img === 'object' && 'imageUrl' in img) {
				const serialized = create(GeneratedImageSchema, {
					imageUrl: img.imageUrl || '',
					imagePrompt: img.imagePrompt || '',
					generatedAt: typeof img.generatedAt === 'bigint' ? img.generatedAt : BigInt(img.generatedAt || Date.now()),
					model: img.model || 'google/gemini-3-pro-image-preview'
				});
				console.log(`[StoryboardPanel] saveEdit: serialized image ${idx}`, {
					imageUrl: serialized.imageUrl,
					imagePrompt: serialized.imagePrompt,
					generatedAt: serialized.generatedAt?.toString(),
					model: serialized.model
				});
				return serialized;
			}
			console.warn(`[StoryboardPanel] saveEdit: image ${idx} is not a valid GeneratedImage`, img);
			return img;
		});
		
		const updatedData = create(PanelDataSchema, {
			characters: characters,
			dialogue: dialogues,
			environment: environment,
			visualNote: visualNote,
			cameraDirection: cameraDirection,
			durationSeconds: durationSeconds,
			cutNumber: cutNumber,
			shot: shot,
			runwayPrompt: runwayPrompt,
			generatedImages: serializedImages,
			currentImageIndex: currentImageIndex,
		});

		console.log('[StoryboardPanel] saveEdit: created PanelData', {
			generatedImagesCount: updatedData.generatedImages?.length || 0,
			currentImageIndex: updatedData.currentImageIndex,
			generatedImages: updatedData.generatedImages?.map(img => ({
				imageUrl: img.imageUrl,
				imagePrompt: img.imagePrompt?.substring(0, 50) + '...',
				generatedAt: img.generatedAt?.toString(),
				model: img.model
			}))
		});
		dispatch('update', updatedData);
		editing = false;
	}

	function cancelEdit() {
		editing = false;
		// Reset to original values
		cutNumber = panel.cutNumber ?? '';
		visualNote = panel.data?.visualNote ?? '';
		cameraDirection = panel.data?.cameraDirection ?? '';
		durationSeconds = panel.data?.durationSeconds ?? 0;
		dialogues = panel.data?.dialogue ?? [];
		characters = panel.data?.characters ?? [];
		environment = panel.data?.environment ?? '';
		shot = panel.data?.shot ?? '';
		runwayPrompt = panel.data?.runwayPrompt ?? '';
		generatedImages = panel.data?.generatedImages ?? [];
		currentImageIndex = panel.data?.currentImageIndex ?? (generatedImages.length > 0 ? generatedImages.length - 1 : -1);
		imageError = '';
		dialogueError = '';
	}

	async function handleGenerateDialogue() {
		if (generatingDialogue || !episodeId) return;

		generatingDialogue = true;
		dialogueError = '';

		try {
			const panelData = create(PanelDataSchema, {
				characters: characters,
				dialogue: dialogues,
				environment: environment,
				visualNote: visualNote,
				cameraDirection: cameraDirection,
				durationSeconds: durationSeconds,
				cutNumber: cutNumber,
				shot: shot,
				runwayPrompt: runwayPrompt,
			});

			const result = await generatePanelDialogue(storyboardPath, episodeId, panel.pageNumber, panel.panel, panelData, {
				// "dialogue に対して生成" を優先、短いドラマ調
				maxLines: dialogues.length > 0 ? dialogues.length : 0,
				style: 'cinematic drama, Japanese, short lines, actor-friendly delivery',
				strictKnownFacts: true,
			});

			if (result.success && result.dialogue) {
				// Replace dialogue lines with generated ones (keep schema)
				dialogues = result.dialogue.map((d) =>
					create(DialogueSchema, {
						speaker: d.speaker ?? '',
						text: d.text ?? '',
						delivery: d.delivery ?? '',
						subtext: d.subtext ?? '',
						emotion: d.emotion ?? '',
						pauseBeforeMs: d.pauseBeforeMs ?? 0,
						pauseAfterMs: d.pauseAfterMs ?? 0,
					})
				);
				// Auto-save after generation
				saveEdit();
			} else {
				dialogueError = result.message || 'Failed to generate dialogue';
			}
		} catch (err) {
			dialogueError = err instanceof Error ? err.message : 'Unknown error';
			console.error('[StoryboardPanel] Error generating dialogue:', err);
		} finally {
			generatingDialogue = false;
		}
	}

	function getAvatarUrl(speaker: string) {
		if (!speaker || speaker === 'Narration' || speaker === 'NewsHacker') return '';
		
		// Map speaker names to IDs if necessary
		const id = speaker;
		const baseUrl = typeof window !== 'undefined' 
			? (window.location.port === '1421' ? 'http://localhost:8081' : window.location.origin)
			: 'http://localhost:8081';
		return `${baseUrl}/images/characters/${id}.png`;
	}

	async function handleGenerateImage() {
		if (generatingImage || !episodeId) return;

		generatingImage = true;
		imageError = '';

		try {
			const panelData = create(PanelDataSchema, {
				characters: characters,
				dialogue: dialogues,
				environment: environment,
				visualNote: visualNote,
				cameraDirection: cameraDirection,
				durationSeconds: durationSeconds,
				cutNumber: cutNumber,
				shot: shot,
				runwayPrompt: runwayPrompt,
			});

			console.log('[StoryboardPanel] Submitting generation job');

			const result = await submitGenerationJob(
				storyboardPath,
				episodeId,
				panel.pageNumber,
				panel.panel,
				panelData,
				selectedModel
			);

			if (result.success && result.jobId) {
				activeJobId = result.jobId;
				// Progress will be updated via StreamUpdates -> job-store
				// generatingImage stays true until job completes
			} else {
				imageError = result.message || 'Failed to submit job';
				generatingImage = false;
			}
		} catch (err) {
			imageError = err instanceof Error ? err.message : 'Unknown error';
			console.error('[StoryboardPanel] Error submitting generation job:', err);
			generatingImage = false;
		}
	}

	async function handleCancelGeneration() {
		if (!activeJobId) return;
		try {
			await cancelGenerationJob(activeJobId);
		} catch (err) {
			console.error('[StoryboardPanel] Error cancelling job:', err);
		}
		generatingImage = false;
		activeJobId = '';
	}

	function formatEta(ms: number): string {
		const seconds = Math.ceil(ms / 1000);
		const minutes = Math.floor(seconds / 60);
		const secs = seconds % 60;
		if (minutes > 0) return `${minutes}:${secs.toString().padStart(2, '0')}`;
		return `${secs}s`;
	}

	// Watch for job completion from store
	$: {
		const job = getJobForPanel(episodeId, panel.pageNumber, panel.panel);
		if (!job && activeJobId && generatingImage) {
			// Job was removed from store (completed/failed/cancelled)
			generatingImage = false;
			activeJobId = '';
		}
	}

	async function handleGenerateCinematic() {
		if (generatingCinematic || !episodeId) return;
		generatingCinematic = true;
		cinematicError = '';
		try {
			const res = await storyboardClient.generateCinematicSketch({
				filePath: storyboardPath,
				episodeId: episodeId,
				pageNumber: panel.pageNumber,
				panel: panel.panel
			});
			if (!res.success) {
				cinematicError = res.message;
			}
		} catch (err) {
			cinematicError = err instanceof Error ? err.message : String(err);
		} finally {
			generatingCinematic = false;
		}
	}

	function navigateImage(direction: 'prev' | 'next') {
		if (generatedImages.length === 0) return;

		if (direction === 'prev') {
			currentImageIndex = currentImageIndex > 0 ? currentImageIndex - 1 : generatedImages.length - 1;
		} else {
			currentImageIndex = currentImageIndex < generatedImages.length - 1 ? currentImageIndex + 1 : 0;
		}
		saveEdit();
	}

	function addDialogue() {
		const newDialogue = create(DialogueSchema, { speaker: '', text: '' });
		dialogues = [...dialogues, newDialogue];
	}

	function removeDialogue(index: number) {
		dialogues = dialogues.filter((_, i) => i !== index);
	}
</script>

<div class="storyboard-panel-row">
	<!-- カット列 -->
	<div class="col-cut">
		{#if editing}
			<input
				type="text"
				bind:value={cutNumber}
				placeholder="76"
				class="cut-input"
			/>
		{:else}
			<div class="cut-number" onclick={startEdit} onkeydown={(e) => e.key === 'Enter' && startEdit()} role="button" tabindex="0">
				{cutNumber || panel.panel}
			</div>
		{/if}
	</div>

	<!-- 画列（元の画） -->
	<div class="col-picture">
		<div class="picture-frame">
			{#if editing}
				<div class="cinematic-generation-controls">
					<button
						type="button"
						onclick={handleGenerateCinematic}
						disabled={generatingCinematic}
						class="generate-cinematic-btn"
						title="Generate cinematic sketch and visual prompts"
					>
						{generatingCinematic ? '...' : 'Sketch AI'}
					</button>
					{#if cinematicError}
						<div class="cinematic-error">{cinematicError}</div>
					{/if}
				</div>
				<textarea
					bind:value={visualNote}
					placeholder="Visual description..."
					class="visual-note-input"
				></textarea>
				{#if cameraDirection}
					<div class="camera-note">{cameraDirection}</div>
				{/if}
				<input
					type="text"
					bind:value={cameraDirection}
					placeholder="Camera direction (e.g., Followカメラ)"
					class="camera-input"
				/>
			{:else}
				<div class="visual-placeholder">
					{#if visualNote}
						<div class="visual-note">{visualNote}</div>
					{:else}
						<div class="placeholder-text">画</div>
					{/if}
					{#if cameraDirection}
						<div class="camera-note">{cameraDirection}</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	<!-- 画列（生成画像） -->
	<div class="col-picture-generated">
		<div class="picture-frame">
			{#if editing}
				<div class="image-generation-controls">
					<select bind:value={selectedModel} class="model-select" disabled={generatingImage}>
						<option value="openrouter">SeedReam 4.5 (API)</option>
						<option value="local">AnimagineXL 4.0 (Local)</option>
					</select>
					{#if generatingImage && activeJobId}
						{@const job = getJobForPanel(episodeId, panel.pageNumber, panel.panel)}
						<div class="generation-progress">
							<div class="progress-bar-container">
								<div class="progress-bar-fill" style="width: {job && job.totalSteps > 0 ? (job.currentStep / job.totalSteps) * 100 : 0}%"></div>
							</div>
							<div class="progress-info">
								<span class="progress-step">{job?.currentStep ?? 0}/{job?.totalSteps ?? 28}</span>
								{#if job && job.etaMs > 0}
									<span class="progress-eta">{formatEta(job.etaMs)}</span>
								{/if}
							</div>
							<button type="button" onclick={handleCancelGeneration} class="cancel-btn">Cancel</button>
						</div>
					{:else}
						<button
							type="button"
							onclick={handleGenerateImage}
							disabled={generatingImage}
							class="generate-btn"
						>
							{generatingImage ? 'Submitting...' : 'Generate'}
						</button>
					{/if}
					{#if imageError}
						<div class="image-error">{imageError}</div>
					{/if}
				</div>
			{/if}
			{#if currentImageUrl}
				<div class="generated-image-container">
					{#if generatedImages.length > 1}
						<button
							type="button"
							onclick={() => navigateImage('prev')}
							class="image-nav-btn image-nav-prev"
							title="Previous image"
						>
							←
						</button>
					{/if}
					<img src={currentImageUrl} alt="Generated image" class="generated-image" />
					{#if generatedImages.length > 1}
						<button
							type="button"
							onclick={() => navigateImage('next')}
							class="image-nav-btn image-nav-next"
							title="Next image"
						>
							→
						</button>
						<div class="image-counter">
							{currentImageIndex + 1} / {generatedImages.length}
						</div>
					{/if}
				</div>
			{:else}
				<div class="visual-placeholder">
					<div class="placeholder-text">生成画</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- 内容列 -->
	<div class="col-content">
		{#if editing}
			<div class="content-editor">
				<div class="characters-section">
					<label>Characters:</label>
					<input
						type="text"
						value={characters.join(', ')}
						oninput={(e) => {
							characters = (e.currentTarget as HTMLInputElement).value
								.split(',')
								.map((s) => s.trim())
								.filter((s) => s);
						}}
						placeholder="character:Ren, character:Nei"
					/>
				</div>
				<div class="environment-section">
					<label>Environment:</label>
					<input
						type="text"
						bind:value={environment}
						placeholder="env:ren-office"
					/>
				</div>
				<div class="shot-section">
					<label>Shot Type:</label>
					<input
						type="text"
						bind:value={shot}
						placeholder="Close-up, Wide Shot, etc."
					/>
				</div>
				<div class="prompt-section">
					<label>Runway Prompt:</label>
					<textarea
						bind:value={runwayPrompt}
						placeholder="Runway base prompt..."
						class="prompt-input"
					></textarea>
				</div>
				<div class="dialogue-section">
					<label>Dialogue:</label>
					<div class="dialogue-generation-controls">
						<button
							type="button"
							onclick={() => dispatch('agentTrigger', { agent: 'dialogue' })}
							class="generate-dialogue-btn"
							title="Open Dialogue Agent"
						>
							Dialogue AI
						</button>
						<button
							type="button"
							onclick={handleGenerateDialogue}
							disabled={generatingDialogue}
							class="generate-dialogue-btn-legacy"
						>
							{generatingDialogue ? 'Generating...' : 'Quick Gen'}
						</button>
						{#if dialogueError}
							<div class="dialogue-error">{dialogueError}</div>
						{/if}
					</div>
					{#each dialogues as dialogue, index}
						<div class="dialogue-item">
							<input
								type="text"
								bind:value={dialogue.speaker}
								placeholder="Speaker"
							/>
							<input
								type="text"
								bind:value={dialogue.text}
								placeholder="Text"
							/>
							<button
								type="button"
								onclick={() => removeDialogue(index)}
								class="remove-btn"
							>
								×
							</button>
						</div>
					{/each}
					<button type="button" onclick={addDialogue} class="add-btn">
						+ Add Dialogue
					</button>
				</div>
				<div class="actions">
					<button onclick={saveEdit} class="save-btn">Save</button>
					<button onclick={cancelEdit} class="cancel-btn">Cancel</button>
				</div>
			</div>
		{:else}
			<div class="content-display" ondblclick={startEdit} role="button" tabindex="0">
				{#if characters.length > 0}
					<div class="characters">
						Characters: {characters.join(', ')}
					</div>
				{/if}
				{#if environment}
					<div class="environment">Env: {environment}</div>
				{/if}
				{#if shot}
					<div class="shot">Shot: {shot}</div>
				{/if}
				{#if runwayPrompt}
					<div class="runway-prompt">Prompt: {runwayPrompt}</div>
				{/if}
				{#if dialogues.length > 0}
					<div class="dialogue">
						{#each dialogues as dialogue}
							<div class="dialogue-line">
								<div class="speaker-info">
									{#if getAvatarUrl(dialogue.speaker)}
										<img src={getAvatarUrl(dialogue.speaker)} alt={dialogue.speaker} class="speaker-avatar" onerror={(e) => (e.currentTarget as HTMLImageElement).style.display='none'} />
									{/if}
									<strong>{dialogue.speaker}:</strong>
								</div>
								<div class="dialogue-text-content">
									{dialogue.text}
								</div>
							</div>
						{/each}
					</div>
				{/if}
				{#if visualNote}
					<div class="visual-note-text">{visualNote}</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- 秒列 -->
	<div class="col-seconds">
		{#if editing}
			<input
				type="number"
				bind:value={durationSeconds}
				step="0.1"
				min="0"
				class="duration-input"
			/>
		{:else}
			<div class="duration" onclick={startEdit} onkeydown={(e) => e.key === 'Enter' && startEdit()} role="button" tabindex="0">
				{durationSeconds > 0 ? durationSeconds.toFixed(1) : '-'}
			</div>
		{/if}
	</div>
</div>

<style>
	.storyboard-panel-row {
		display: grid;
		grid-template-columns: 80px 1fr 1fr 400px 60px;
		border-bottom: 1px solid #e0e0e0;
		min-height: 200px;
	}

	.storyboard-panel-row:hover {
		background: #fafafa;
	}

	.col-cut,
	.col-picture,
	.col-picture-generated,
	.col-content,
	.col-seconds {
		padding: 1rem;
		border-right: 1px solid #e0e0e0;
		display: flex;
		align-items: flex-start;
	}

	.col-cut:last-child,
	.col-picture:last-child,
	.col-picture-generated:last-child,
	.col-content:last-child,
	.col-seconds:last-child {
		border-right: none;
	}

	/* カット列 */
	.cut-number {
		font-size: 1.2rem;
		font-weight: 600;
		color: #333;
		cursor: pointer;
		text-align: center;
		width: 100%;
	}

	.cut-input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 1rem;
		text-align: center;
	}

	/* 画列 */
	.picture-frame {
		width: 100%;
		min-height: 150px;
		border: 2px solid #ccc;
		border-radius: 4px;
		background: #f9f9f9;
		position: relative;
		padding: 0.5rem;
	}

	.visual-placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.placeholder-text {
		font-size: 3rem;
		color: #ccc;
		font-weight: 300;
	}

	.visual-note {
		font-size: 0.85rem;
		color: #555;
		line-height: 1.4;
		margin-bottom: 0.5rem;
	}

	.visual-note-input {
		width: 100%;
		min-height: 100px;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.85rem;
		resize: vertical;
		font-family: inherit;
	}

	.camera-note {
		font-size: 0.75rem;
		color: #888;
		font-style: italic;
		margin-top: 0.5rem;
		padding: 0.25rem 0.5rem;
		background: #fff3cd;
		border-radius: 3px;
	}

	.camera-input {
		width: 100%;
		margin-top: 0.5rem;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	/* 生成画像列 */
	.col-picture-generated {
		position: relative;
	}

	.generated-image {
		width: 100%;
		height: auto;
		border-radius: 4px;
		object-fit: contain;
		max-height: 300px;
	}

	.image-generation-controls {
		width: 100%;
		margin-bottom: 0.5rem;
		display: flex;
		gap: 0.25rem;
	}

	.model-select {
		flex: 1;
		padding: 0.5rem 0.25rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.75rem;
		background: white;
	}

	.generate-btn {
		flex: 0 0 auto;
		padding: 0.5rem;
		background: #4caf50;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.generate-btn:hover:not(:disabled) {
		background: #45a049;
	}

	.generate-btn:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.generation-progress {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		width: 100%;
	}

	.progress-bar-container {
		width: 100%;
		height: 6px;
		background: #e0e0e0;
		border-radius: 3px;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		background: #4caf50;
		border-radius: 3px;
		transition: width 0.5s ease;
	}

	.progress-info {
		display: flex;
		justify-content: space-between;
		font-size: 0.7rem;
		color: #666;
	}

	.progress-step {
		font-weight: 600;
	}

	.progress-eta {
		color: #999;
	}

	.cancel-btn {
		padding: 0.25rem 0.5rem;
		background: #f44336;
		color: white;
		border: none;
		border-radius: 3px;
		cursor: pointer;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.cancel-btn:hover {
		background: #d32f2f;
	}

	.image-error {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: #fee;
		color: #c00;
		border: 1px solid #fcc;
		border-radius: 4px;
		font-size: 0.75rem;
	}

	.generated-image-container {
		position: relative;
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.generated-image {
		width: 100%;
		height: auto;
		border-radius: 4px;
		object-fit: contain;
		max-height: 300px;
	}

	.image-nav-btn {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		background: rgba(0, 0, 0, 0.6);
		color: white;
		border: none;
		border-radius: 50%;
		width: 32px;
		height: 32px;
		cursor: pointer;
		font-size: 1.2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10;
		transition: background 0.2s;
	}

	.image-nav-btn:hover {
		background: rgba(0, 0, 0, 0.8);
	}

	.image-nav-prev {
		left: 8px;
	}

	.image-nav-next {
		right: 8px;
	}

	.image-counter {
		position: absolute;
		bottom: 8px;
		right: 8px;
		background: rgba(0, 0, 0, 0.6);
		color: white;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 0.75rem;
		z-index: 10;
	}

	/* 内容列 */
	.content-display {
		width: 100%;
		cursor: pointer;
		font-size: 0.9rem;
		line-height: 1.6;
	}

	.content-display:hover {
		background: #f0f0f0;
		padding: 0.5rem;
		border-radius: 4px;
	}

	.characters {
		font-weight: 600;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.environment {
		font-size: 0.85rem;
		color: #777;
		margin-bottom: 0.5rem;
	}

	.shot {
		font-size: 0.85rem;
		font-weight: 600;
		color: #444;
		margin-bottom: 0.5rem;
	}

	.runway-prompt {
		font-size: 0.8rem;
		color: #666;
		background: #f0f0f0;
		padding: 0.5rem;
		border-radius: 4px;
		margin-top: 0.5rem;
		word-break: break-all;
	}

	.dialogue {
		margin-top: 0.5rem;
	}

	.dialogue-line {
		margin-bottom: 0.5rem;
		padding-left: 1rem;
		border-left: 2px solid #ddd;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.speaker-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.speaker-avatar {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		object-fit: cover;
		border: 1px solid #ddd;
		background: #eee;
	}

	.dialogue-text-content {
		padding-left: 0;
	}

	.dialogue-line strong {
		color: #333;
	}

	.visual-note-text {
		margin-top: 0.5rem;
		font-size: 0.85rem;
		color: #666;
		font-style: italic;
	}

	.content-editor {
		width: 100%;
	}

	.content-editor label {
		display: block;
		font-weight: 600;
		margin-top: 0.75rem;
		margin-bottom: 0.25rem;
		font-size: 0.85rem;
		color: #555;
	}

	.content-editor input[type='text'],
	.content-editor textarea {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
		font-family: inherit;
	}

	.content-editor textarea {
		min-height: 80px;
		resize: vertical;
	}

	.dialogue-item {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
		align-items: center;
	}

	.dialogue-item input {
		flex: 1;
	}

	.remove-btn {
		padding: 0.25rem 0.5rem;
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 4px;
		cursor: pointer;
		color: #c00;
	}

	.add-btn {
		padding: 0.5rem 1rem;
		background: #e8f5e9;
		border: 1px solid #c8e6c9;
		border-radius: 4px;
		cursor: pointer;
		color: #2e7d32;
		font-size: 0.85rem;
		margin-top: 0.5rem;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.save-btn,
	.cancel-btn {
		padding: 0.5rem 1rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.save-btn {
		background: #4caf50;
		color: white;
		border-color: #4caf50;
	}

	.cancel-btn {
		background: #fff;
		color: #666;
	}

	/* 秒列 */
	.duration {
		text-align: center;
		font-size: 1rem;
		color: #666;
		cursor: pointer;
		width: 100%;
	}

	.duration-input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-size: 1rem;
		text-align: center;
	}

	.dialogue-generation-controls {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.generate-dialogue-btn {
		width: 100%;
		padding: 0.5rem;
		background: #e74c3c;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.85rem;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.generate-dialogue-btn:hover {
		background: #c0392b;
	}

	.generate-dialogue-btn-legacy {
		width: 100%;
		padding: 0.4rem;
		background: #1976d2;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.generate-dialogue-btn-legacy:hover:not(:disabled) {
		background: #1565c0;
	}

	.generate-dialogue-btn-legacy:disabled {
		background: #ccc;
		cursor: not-allowed;
	}

	.cinematic-generation-controls {
		position: absolute;
		top: 5px;
		right: 5px;
		z-index: 5;
	}

	.generate-cinematic-btn {
		padding: 0.25rem 0.5rem;
		background: #e67e22;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.generate-cinematic-btn:hover:not(:disabled) {
		background: #d35400;
	}

	.cinematic-error {
		position: absolute;
		top: 100%;
		right: 0;
		background: #fee;
		color: #c00;
		font-size: 0.6rem;
		padding: 2px 4px;
		border-radius: 2px;
		white-space: nowrap;
	}

	.dialogue-error {
		padding: 0.5rem;
		background: #fee;
		color: #c00;
		border: 1px solid #fcc;
		border-radius: 4px;
		font-size: 0.75rem;
	}
</style>
