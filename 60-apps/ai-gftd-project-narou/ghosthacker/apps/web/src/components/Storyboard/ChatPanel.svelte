<script lang="ts">
	import { storyboardClient } from '$lib/client/storyboard-client';
	import { onMount } from 'svelte';
	import { marked } from 'marked';

	let { selectedEpisode, storyboardPath, onApplyPatches } = $props<{
		selectedEpisode: string;
		storyboardPath: string;
		onApplyPatches?: (patches: any[]) => void;
	}>();

	type Message = { 
		role: 'user' | 'assistant' | 'system' | 'debug' | 'error', 
		content: string, 
		context?: any, 
		agent?: string, 
		patches?: any[], 
		contextScope?: any, 
		context_json?: string, 
		resolvedIds?: string[] 
	};
	type ChatSession = { id: string, title: string, messages: Message[], timestamp: number };

	let sessions = $state<ChatSession[]>([]);
	let currentSessionId = $state<string>(Math.random().toString(36).substring(2, 15));
	let messages = $state<Message[]>([]);
	let showHistory = $state(false);

	onMount(async () => {
		await loadAllSessions();
	});

	async function loadAllSessions() {
		try {
			const res = await storyboardClient.getChatSessions({});
			if (res.sessions) {
				sessions = res.sessions.map(s => ({
					id: s.id,
					title: s.title,
					messages: s.messages.map(m => {
						let context = undefined;
						if (m.contextJson) {
							try {
								context = JSON.parse(m.contextJson);
							} catch (e) {
								console.error('Failed to parse context JSON from history:', e);
							}
						}
						return {
							role: m.role as any,
							agent: m.agentMode,
							content: m.content,
							context: context,
							'context_json': m.contextJson,
							resolvedIds: m.resolvedIds,
							patches: m.patches,
							contextScope: m.contextScope
						};
					}),
					timestamp: Number(s.timestamp)
				}));
				
				// Load the most recent session if messages are empty
				if (sessions.length > 0 && messages.length === 0) {
					const firstSession = sessions[0];
					if (firstSession) {
						loadSession(firstSession.id);
					}
				}
			}
		} catch (err) {
			console.error('Failed to load chat sessions:', err);
		}
	}

	async function saveCurrentSession() {
		const session = sessions.find(s => s.id === currentSessionId);
		if (!session) return;

		try {
			await storyboardClient.saveChatSession({
				session: {
					id: session.id,
					title: session.title,
					timestamp: BigInt(session.timestamp),
					messages: messages.map(m => ({
						role: m.role,
						agentMode: m.agent ?? '',
						content: m.content,
						contextJson: m.context ? JSON.stringify(m.context) : (m.context_json ?? ''),
						resolvedIds: m.resolvedIds ?? [],
						patches: m.patches ?? [],
						contextScope: m.contextScope
					}))
				}
			});
		} catch (err) {
			console.error('Failed to save chat session:', err);
		}
	}

	let inputValue = $state('');
	let loading = $state(false);
	let dropContext = $state<any[]>([]);
	let currentAgentMode = $state<'general' | 'scenario' | 'episode' | 'character' | 'cinematic' | 'dialogue' | 'orchestration' | 'environment' | 'prop' | 'ghost'>('general');
	let isAutoPilot = $state(false);
	let activeWorkflowId = $state<string | null>(null);
	let metrics = $state<any | null>(null);

	async function runAnalysis() {
		if (!selectedEpisode) return;
		try {
			const res = await storyboardClient.analyzeStructure({
				filePath: storyboardPath,
				episodeId: selectedEpisode
			});
			if (res.success) {
				metrics = res.metrics;
			}
		} catch (err) {
			console.error('Failed to run analysis:', err);
		}
	}

	// Initialize with first session
	$effect(() => {
		if (sessions.length === 0) {
			const initialSession: ChatSession = {
				id: currentSessionId,
				title: 'New Conversation',
				messages: [],
				timestamp: Date.now()
			};
			sessions = [initialSession];
		}
	});

	// Sync current messages with sessions
	$effect(() => {
		const session = sessions.find(s => s.id === currentSessionId);
		if (session && messages.length > 0) {
			session.messages = messages;
			const firstMsg = messages[0];
			if (firstMsg && (session.title === 'New Conversation' || session.title === '')) {
				session.title = firstMsg.content.substring(0, 30) + (firstMsg.content.length > 30 ? '...' : '');
				saveCurrentSession();
			}
		}
	});

	async function createNewSession() {
		const newId = Math.random().toString(36).substring(2, 15);
		const newSession: ChatSession = {
			id: newId,
			title: 'New Conversation',
			messages: [],
			timestamp: Date.now()
		};
		sessions = [newSession, ...sessions];
		currentSessionId = newId;
		messages = [];
		currentAgentMode = 'general';
		isAutoPilot = false;
		showHistory = false;
		await saveCurrentSession();
	}

	function loadSession(id: string) {
		const session = sessions.find(s => s.id === id);
		if (session) {
			currentSessionId = id;
			messages = session.messages.map(m => {
				let context = undefined;
				if (m.context_json) {
					try {
						context = JSON.parse(m.context_json);
					} catch (e) {
						console.error('Failed to parse context JSON:', e);
					}
				}
				const msg: Message = {
					role: m.role as any,
					content: m.content,
					agent: m.agent ?? 'general',
					context: context || m.context,
					patches: m.patches ?? [],
					contextScope: m.contextScope,
					resolvedIds: m.resolvedIds ?? []
				};
				return msg;
			});
			showHistory = false;
			console.log('[ ] Loaded session:', id, 'messages:', messages.length);
		}
	}

	// Expose a method to trigger agent commands from outside
	export function triggerAgent(agent: typeof currentAgentMode, initialPrompt?: string) {
		currentAgentMode = agent;
		if (initialPrompt) {
			inputValue = initialPrompt;
		}
		// Focus the textarea
		const textarea = document.querySelector('.chat-input-area textarea') as HTMLTextAreaElement;
		if (textarea) textarea.focus();
	}

	// Expose a method to add messages from outside (e.g. from stream)
	export async function addMessage(msg: { role: 'user' | 'assistant', content: string, agent?: string }) {
		messages = [...messages, msg];
		await saveCurrentSession();
	}

	// Expose a method to add context items programmatically
	export function addContext(type: string, data: any) {
		const item = { type, ...data };
		if (!dropContext.find(existing => JSON.stringify(existing) === JSON.stringify(item))) {
			dropContext = [...dropContext, item];
			console.log('[ ] Context added programmatically:', item);
		}
	}

	async function sendMessage() {
		if (!inputValue && dropContext.length === 0) return;

		const userMessage = inputValue;
		const currentContext = [...dropContext];
		const agentMode = currentAgentMode;

		// Check for avatar generation command
		if (userMessage.startsWith('/avatar ')) {
			const charId = userMessage.replace('/avatar ', '').trim();
			if (charId) {
				messages = [...messages, { role: 'user', content: userMessage, context: currentContext, agent: agentMode }];
				inputValue = '';
				loading = true;
				try {
					const res = await storyboardClient.generatePanelImage({
						filePath: storyboardPath,
						episodeId: selectedEpisode || 'system',
						pageNumber: 0,
						panel: 0,
						panelData: {
							visualNote: `CHARACTER_AVATAR:${charId}`,
							characters: [charId.startsWith('character:') ? charId : `character:${charId}`]
						}
					});
					if (res.success) {
						messages = [...messages, { role: 'assistant', content: `Avatar for ${charId} generated and saved. Please refresh to see it.` }];
					} else {
						messages = [...messages, { role: 'assistant', content: `Failed to generate avatar: ${res.message}` }];
					}
				} catch (err) {
					messages = [...messages, { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : String(err)}` }];
				} finally {
					loading = false;
					await saveCurrentSession();
				}
				return;
			}
		}
		
		messages = [...messages, { role: 'user', content: userMessage, context: currentContext, agent: agentMode }];
		inputValue = '';
		dropContext = [];
		loading = true;

		await saveCurrentSession();

		console.log('[ ] Sending message to AI...', { userMessage, contextCount: currentContext.length, agentMode });

		try {
			const res = await storyboardClient.interactWithAI({
				filePath: storyboardPath,
				episodeId: selectedEpisode,
				message: userMessage,
				agentMode: agentMode,
				history: messages.slice(0, -1).map(m => ({
					role: m.role,
					agentMode: m.agent ?? '',
					content: m.content,
					contextJson: m.context ? JSON.stringify(m.context) : (m.context_json ?? ''),
					resolvedIds: m.resolvedIds ?? [],
					patches: m.patches ?? [],
					contextScope: m.contextScope
				})),
				context: currentContext.map(ctx => ({
					type: ctx.type,
					id: String(ctx.id || ''),
					pageNumber: Number(ctx.pageNumber || 0),
					panel: Number(ctx.panel || 0),
					jsonContent: ctx.data ? JSON.stringify(ctx.data) : (ctx.type === 'page' ? '{"info": "page context"}' : '')
				}))
			});

			console.log('[ ] AI Response received:', res);

			if (res.success) {
				messages = [...messages, { 
					role: 'assistant', 
					content: res.aiResponse,
					patches: res.patches,
					contextScope: res.contextScope,
					resolvedIds: res.resolvedIds
				}];
				
				if (res.patches && res.patches.length > 0) {
					console.log('[ ] AI suggested patches:', res.patches);
				}
				
				// Keep context persistent for the session (don't clear it here)
				// dropContext = []; // Removed clearing
				
				await saveCurrentSession();
			} else {
				messages = [...messages, { role: 'assistant', content: `AI Error: ${res.message}` }];
			}
		} catch (err) {
			console.error('[ ] RPC Error:', err);
			messages = [...messages, { role: 'assistant', content: `Connection Error: ${err instanceof Error ? err.message : String(err)}` }];
		} finally {
			loading = false;
		}
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		const data = e.dataTransfer?.getData('application/json');
		if (data) {
			try {
				const parsed = JSON.parse(data);
				console.log('[ ] Node dropped:', parsed);
				if (!dropContext.find(item => JSON.stringify(item) === JSON.stringify(parsed))) {
					dropContext = [...dropContext, parsed];
				}
			} catch (err) {
				console.error('[ ] Failed to parse dropped data:', err);
			}
		}
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
	}

	function removeContext(index: number) {
		dropContext = dropContext.filter((_, i) => i !== index);
	}

	function applyPatches(patches: any[]) {
		if (onApplyPatches) {
			onApplyPatches(patches);
		}
	}

	async function startAutoPilot() {
		if (!selectedEpisode) return;
		isAutoPilot = true;
		const goal = inputValue || "Advance the story naturally";
		inputValue = '';
		
		messages = [...messages, { 
			role: 'user', 
			content: `[AUTO-PILOT START] Goal: ${goal}`,
			context: [...dropContext]
		}];

		await saveCurrentSession();

		try {
			const res = await storyboardClient.startAutonomousGeneration({
				filePath: storyboardPath,
				episodeId: selectedEpisode,
				goal: goal,
				initialContext: dropContext.map(ctx => ({
					type: ctx.type,
					id: String(ctx.id || ''),
					pageNumber: Number(ctx.pageNumber || 0),
					panel: Number(ctx.panel || 0),
					jsonContent: ctx.data ? JSON.stringify(ctx.data) : ''
				}))
			});

			if (res.success) {
				activeWorkflowId = res.workflowId;
				messages = [...messages, { 
					role: 'assistant', 
					content: `Autonomous generation started. Workflow ID: ${res.workflowId}. Agents are now collaborating...` 
				}];
				
				// No longer simulating, real updates will come via the stream
			} else {
				messages = [...messages, { role: 'assistant', content: `Failed to start Auto-Pilot: ${res.message}` }];
				isAutoPilot = false;
			}
		} catch (err) {
			messages = [...messages, { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : String(err)}` }];
			isAutoPilot = false;
		}
	}

	async function stopAutoPilot() {
		if (!activeWorkflowId) return;
		try {
			const res = await storyboardClient.terminateAutonomousGeneration({
				workflowId: activeWorkflowId,
				reason: "User terminated from UI"
			});
			if (res.success) {
				isAutoPilot = false;
				activeWorkflowId = null;
			}
		} catch (err) {
			console.error('Failed to terminate workflow:', err);
		}
	}

	function triggerOrchestrationPattern(pattern: 'polish' | 'consistency' | 'visuals' | 'master') {
		currentAgentMode = 'orchestration';
		let goal = "";
		switch (pattern) {
			case 'polish':
				goal = "今のストーリーの完成度を評価して、ブラッシュアップ案を提示・適用してください。";
				break;
			case 'consistency':
				goal = "設定やキャラクターの性格に矛盾がないかを評価し、修正が必要な箇所を特定・修正してください。";
				break;
			case 'visuals':
				goal = "シネマティックスケッチが生成されていないパネルを特定し、ARIA Cinematic Baseに基づいて生成してください。";
				break;
			case 'master':
				goal = "エピソード全体の構成、台詞、演出を統合的に評価し、完成度を極限まで高めるための協調オーケストレーションを開始してください。";
				break;
		}
		inputValue = goal;
		startAutoPilot();
	}
</script>

<div class="chat-panel">
	<div class="chat-header">
		<div class="header-top">
			<div class="header-left">
				<span>AI STORY ASSISTANT</span>
				<button class="history-toggle" onclick={() => showHistory = !showHistory} title="Conversation History">
					{showHistory ? '✕' : '📜'}
				</button>
			</div>
			<div class="header-actions">
				<button class="new-chat-btn" onclick={createNewSession} title="Start New Conversation">+</button>
				{#if isAutoPilot}
					<button 
						class="autopilot-btn active" 
						onclick={stopAutoPilot}
					>
						STOP ORCHESTRATION
					</button>
				{:else}
					<button 
						class="autopilot-btn" 
						onclick={startAutoPilot}
						disabled={!selectedEpisode}
					>
						START AUTO-PILOT
					</button>
				{/if}
			</div>
		</div>
		{#if showHistory}
			<div class="history-list">
				{#each sessions as session}
					<button 
						class="history-item" 
						class:active={session.id === currentSessionId}
						onclick={() => loadSession(session.id)}
					>
						<span class="history-title">{session.title}</span>
						<span class="history-date">{new Date(session.timestamp).toLocaleTimeString()}</span>
					</button>
				{/each}
			</div>
		{/if}
		<div class="orchestration-quick-actions">
			<button class="quick-action-btn master-btn" onclick={() => triggerOrchestrationPattern('master')} disabled={isAutoPilot}>👑 Episode Master</button>
			<button class="quick-action-btn" onclick={() => triggerOrchestrationPattern('polish')} disabled={isAutoPilot}>✨ Polish</button>
			<button class="quick-action-btn" onclick={() => triggerOrchestrationPattern('consistency')} disabled={isAutoPilot}>🔍 Consistency</button>
			<button class="quick-action-btn" onclick={() => triggerOrchestrationPattern('visuals')} disabled={isAutoPilot}>🎨 Visuals</button>
			<button class="quick-action-btn metrics-btn" onclick={runAnalysis} disabled={isAutoPilot}>📊 Metrics</button>
		</div>
		{#if metrics}
			<div class="metrics-dashboard">
				<div class="metric-item">
					<span class="m-label">Reading Units:</span>
					<span class="m-value" class:warn={metrics.readingUnits < 600 || metrics.readingUnits > 1500}>{metrics.readingUnits}</span>
				</div>
				<div class="metric-item">
					<span class="m-label">Dialogue Ratio:</span>
					<span class="m-value">{Math.round(metrics.dialogueRatio * 100)}%</span>
				</div>
				<div class="metric-item">
					<span class="m-label">Beats:</span>
					<span class="m-value">{metrics.beatCount}</span>
				</div>
				{#if metrics.validationErrors?.length > 0}
					<div class="validation-errors">
						{#each metrics.validationErrors as err}
							<div class="v-err">⚠️ {err}</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
		<div class="agent-mode-selector">
			<button 
				class="mode-btn general" 
				class:active={currentAgentMode === 'general'} 
				onclick={() => currentAgentMode = 'general'}
			>General</button>
			<button 
				class="mode-btn scenario" 
				class:active={currentAgentMode === 'scenario'} 
				onclick={() => currentAgentMode = 'scenario'}
			>Scenario</button>
			<button 
				class="mode-btn episode" 
				class:active={currentAgentMode === 'episode'} 
				onclick={() => currentAgentMode = 'episode'}
			>Episode</button>
			<button 
				class="mode-btn character" 
				class:active={currentAgentMode === 'character'} 
				onclick={() => currentAgentMode = 'character'}
			>Character</button>
			<button 
				class="mode-btn cinematic" 
				class:active={currentAgentMode === 'cinematic'} 
				onclick={() => currentAgentMode = 'cinematic'}
			>Cinematic</button>
			<button 
				class="mode-btn dialogue" 
				class:active={currentAgentMode === 'dialogue'} 
				onclick={() => currentAgentMode = 'dialogue'}
			>Dialogue</button>
			<button 
				class="mode-btn orchestration" 
				class:active={currentAgentMode === 'orchestration'} 
				onclick={() => currentAgentMode = 'orchestration'}
			>Orchestrate</button>
			<button 
				class="mode-btn environment" 
				class:active={currentAgentMode === 'environment'} 
				onclick={() => currentAgentMode = 'environment'}
			>Env</button>
			<button 
				class="mode-btn prop" 
				class:active={currentAgentMode === 'prop'} 
				onclick={() => currentAgentMode = 'prop'}
			>Prop</button>
			<button 
				class="mode-btn ghost" 
				class:active={currentAgentMode === 'ghost'} 
				onclick={() => currentAgentMode = 'ghost'}
			>Ghost</button>
		</div>
	</div>
	
	<div class="chat-messages">
		{#if messages.length === 0}
			<div class="empty-state">
				<p>Drag nodes (Episodes, Pages, Panels) from the left tree here to add them to context.</p>
				<p>Then ask me to rewrite dialogue, suggest visual notes, or update the story structure.</p>
			</div>
		{/if}
		{#each messages as msg}
			<div class="message" class:user={msg.role === 'user'} class:debug={msg.role === 'debug'} class:error={msg.role === 'error'} class:system={msg.role === 'system'}>
				{#if msg.agent && msg.agent !== 'general'}
					<span class="message-agent-tag" class:scenario={msg.agent === 'scenario'} class:episode={msg.agent === 'episode'} class:character={msg.agent === 'character'} class:cinematic={msg.agent === 'cinematic'} class:dialogue={msg.agent === 'dialogue'} class:reviewer={msg.agent === 'reviewer'}>
						{msg.agent.toUpperCase()}
					</span>
				{/if}
				{#if msg.context && msg.context.length > 0}
					<div class="message-context">
						{#each msg.context as ctx}
							<span class="context-tag">{ctx.type}: {ctx.panel ?? ctx.pageNumber ?? ctx.id}</span>
						{/each}
					</div>
				{/if}
				<div class="message-content">
					{#if msg.role === 'debug'}
						<pre>{msg.content}</pre>
					{:else}
						{@html marked.parse(msg.content)}
					{/if}
				</div>
				{#if msg.contextScope}
					<div class="context-scope-display">
						<span class="scope-label">LOADED CONTEXT:</span>
						{#if msg.contextScope.episodes?.length > 0}
							<span class="scope-item">📁 {msg.contextScope.episodes.join(', ')}</span>
						{/if}
						{#if msg.contextScope.pages?.length > 0}
							<span class="scope-item">📄 Pages: {msg.contextScope.pages.join(', ')}</span>
						{/if}
						{#if msg.contextScope.panels?.length > 0}
							<span class="scope-item">🎞️ Panels: {msg.contextScope.panels.join(', ')}</span>
						{/if}
						{#if msg.contextScope.characters?.length > 0}
							<span class="scope-item">👤 {msg.contextScope.characters.join(', ')}</span>
						{/if}
					</div>
				{/if}
				{#if msg.resolvedIds && msg.resolvedIds.length > 0}
					<div class="resolved-ids-display">
						<span class="scope-label">AUTO-RESOLVED LORE:</span>
						<div class="resolved-tags">
							{#each msg.resolvedIds as id}
								<span class="resolved-tag">🔍 {id}</span>
							{/each}
						</div>
					</div>
				{/if}
				{#if msg.patches && msg.patches.length > 0}
					<div class="patch-actions">
						<button class="apply-btn" onclick={() => applyPatches(msg.patches!)}>
							Apply {msg.patches.length} Changes
						</button>
					</div>
				{/if}
			</div>
		{/each}
		{#if loading}
			<div class="message assistant loading">
				<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
			</div>
		{/if}
	</div>

	<div 
		class="chat-input-area"
		ondrop={handleDrop}
		ondragover={handleDragOver}
	>
		{#if dropContext.length > 0}
			<div class="drop-context-preview">
				<div class="context-header">
					<span>ACTIVE CONTEXT ({dropContext.length})</span>
					<button class="clear-context-btn" onclick={() => dropContext = []}>Clear All</button>
				</div>
				<div class="context-tags-scroll">
					{#each dropContext as ctx, i}
						<span class="context-tag">
							{ctx.type}: {ctx.panel ?? ctx.pageNumber ?? ctx.id}
							<button onclick={() => removeContext(i)}>×</button>
						</span>
					{/each}
				</div>
			</div>
		{/if}
		
		<div class="input-wrapper">
			<textarea 
				bind:value={inputValue} 
				placeholder="Ask AI to edit... (Drop nodes here, or use /avatar CharacterID)"
				onkeydown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
			></textarea>
			<button class="send-btn" onclick={sendMessage} disabled={loading || (!inputValue && dropContext.length === 0)}>
				{loading ? '...' : 'Send'}
			</button>
		</div>
	</div>
</div>

<style>
	.chat-panel {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: #1e1e1e;
		color: #d4d4d4;
		font-family: 'Segoe UI', sans-serif;
	}

	.chat-header {
		padding: 0.5rem 1rem;
		font-size: 0.7rem;
		font-weight: bold;
		color: #aaa;
		letter-spacing: 0.1em;
		background: #252526;
		border-bottom: 1px solid #333;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.header-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	.history-toggle, .new-chat-btn {
		background: #333;
		color: #aaa;
		border: 1px solid #444;
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 0.7rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.history-toggle:hover, .new-chat-btn:hover {
		background: #444;
		color: white;
	}

	.new-chat-btn {
		font-weight: bold;
		font-size: 0.9rem;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.history-list {
		margin-top: 0.5rem;
		display: flex;
		flex-direction: column;
		gap: 2px;
		max-height: 200px;
		overflow-y: auto;
		background: #1e1e1e;
		border: 1px solid #333;
		border-radius: 4px;
	}

	.history-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		background: transparent;
		border: none;
		color: #888;
		cursor: pointer;
		text-align: left;
		font-size: 0.7rem;
	}

	.history-item:hover {
		background: #2d2d2d;
		color: #ccc;
	}

	.history-item.active {
		background: #37373d;
		color: #fff;
		border-left: 2px solid #007acc;
	}

	.history-title {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.history-date {
		font-size: 0.6rem;
		opacity: 0.5;
		margin-left: 0.5rem;
	}

	.autopilot-btn {
		background: #333;
		color: #aaa;
		border: 1px solid #444;
		padding: 2px 8px;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
	}

	.autopilot-btn:hover:not(:disabled) {
		background: #444;
		color: white;
	}

	.autopilot-btn.active {
		background: #e74c3c;
		color: white;
		border-color: transparent;
		animation: pulse 2s infinite;
	}

	.orchestration-quick-actions {
		display: flex;
		gap: 0.4rem;
		margin-bottom: 0.25rem;
	}

	.quick-action-btn {
		flex: 1;
		background: #2d2d2d;
		color: #ccc;
		border: 1px solid #444;
		padding: 4px 2px;
		border-radius: 4px;
		font-size: 0.55rem;
		cursor: pointer;
		transition: all 0.2s;
		white-space: nowrap;
	}

	.quick-action-btn:hover:not(:disabled) {
		background: #3d3d3d;
		color: white;
		border-color: #666;
	}

	.quick-action-btn.master-btn {
		background: #f39c12;
		color: #000;
		border-color: #e67e22;
	}

	.quick-action-btn.master-btn:hover:not(:disabled) {
		background: #e67e22;
	}

	.quick-action-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.metrics-dashboard {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: #2d2d2d;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		border: 1px solid #444;
	}

	.metric-item {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
	}

	.m-label { color: #888; }
	.m-value { color: #2ecc71; font-weight: bold; }
	.m-value.warn { color: #e74c3c; }

	.validation-errors {
		margin-top: 0.25rem;
		padding-top: 0.25rem;
		border-top: 1px solid #444;
	}

	.v-err {
		color: #f1c40f;
		font-size: 0.6rem;
		margin-bottom: 2px;
	}

	@keyframes pulse {
		0% { opacity: 1; }
		50% { opacity: 0.7; }
		100% { opacity: 1; }
	}

	.agent-mode-selector {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		width: 100%;
	}

	.mode-btn {
		padding: 2px 6px;
		border-radius: 3px;
		font-size: 0.6rem;
		background: #333;
		color: #888;
		border: 1px solid #444;
		cursor: pointer;
		transition: all 0.2s;
	}

	.mode-btn:hover {
		background: #444;
		color: #ccc;
	}

	.mode-btn.active {
		color: white;
		border-color: transparent;
	}

	.mode-btn.active.general { background: #555; }
	.mode-btn.active.scenario { background: #4a90e2; }
	.mode-btn.active.episode { background: #2ecc71; }
	.mode-btn.active.character { background: #9b59b6; }
	.mode-btn.active.cinematic { background: #e67e22; }
	.mode-btn.active.dialogue { background: #e74c3c; }
	.mode-btn.active.orchestration { background: #f1c40f; color: #000; }
	.mode-btn.active.environment { background: #16a085; }
	.mode-btn.active.prop { background: #7f8c8d; }
	.mode-btn.active.ghost { background: #8e44ad; }

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.empty-state {
		text-align: center;
		color: #666;
		font-size: 0.85rem;
		margin-top: 3rem;
		padding: 0 1rem;
		line-height: 1.5;
	}

	.message {
		padding: 0.8rem 1rem;
		border-radius: 8px;
		max-width: 90%;
		font-size: 0.9rem;
		line-height: 1.5;
		position: relative;
	}

	.message.user {
		align-self: flex-end;
		background: #007acc;
		color: white;
		border-bottom-right-radius: 2px;
	}

	.message.assistant {
		align-self: flex-start;
		background: #2d2d2d;
		border: 1px solid #444;
		border-bottom-left-radius: 2px;
	}

	.message.debug {
		align-self: flex-start;
		background: #1a1a1a;
		border: 1px dashed #333;
		color: #888;
		font-family: 'Courier New', monospace;
		font-size: 0.75rem;
		opacity: 0.8;
	}

	.message.error {
		align-self: center;
		background: #3a1a1a;
		border: 1px solid #633;
		color: #f88;
		font-weight: bold;
	}

	.message.system {
		align-self: center;
		background: transparent;
		border: 1px solid #333;
		color: #666;
		font-size: 0.75rem;
		font-style: italic;
	}

	.message-agent-tag {
		font-size: 0.55rem;
		font-weight: bold;
		padding: 1px 4px;
		border-radius: 3px;
		margin-bottom: 0.25rem;
		display: inline-block;
		color: white;
	}

	.message-agent-tag.scenario { background: #4a90e2; }
	.message-agent-tag.episode { background: #2ecc71; }
	.message-agent-tag.character { background: #9b59b6; }
	.message-agent-tag.cinematic { background: #e67e22; }
	.message-agent-tag.dialogue { background: #e74c3c; }
	.message-agent-tag.reviewer { background: #34495e; }
	.message-agent-tag.environment { background: #16a085; }
	.message-agent-tag.prop { background: #7f8c8d; }
	.message-agent-tag.ghost { background: #8e44ad; }
	.message-agent-tag.evaluation { background: #27ae60; }

	.message-context {
		margin-bottom: 0.5rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.3rem;
	}

	.context-tag {
		font-size: 0.65rem;
		background: rgba(255,255,255,0.1);
		padding: 2px 8px;
		border-radius: 10px;
		color: #bbb;
		display: flex;
		align-items: center;
		gap: 4px;
		border: 1px solid rgba(255,255,255,0.05);
	}

	.context-tag button {
		background: none;
		border: none;
		color: #ff5f56;
		cursor: pointer;
		padding: 0;
		font-size: 0.9rem;
		line-height: 1;
	}

	.message-content {
		word-break: break-word;
	}

	.message-content :global(p) { margin: 0 0 0.5rem 0; }
	.message-content :global(p:last-child) { margin-bottom: 0; }
	.message-content :global(h1), .message-content :global(h2), .message-content :global(h3) { 
		margin: 1rem 0 0.5rem 0; 
		font-size: 1rem;
		color: #fff;
	}
	.message-content :global(ul), .message-content :global(ol) {
		margin: 0.5rem 0;
		padding-left: 1.25rem;
	}
	.message-content :global(code) {
		background: rgba(255,255,255,0.1);
		padding: 2px 4px;
		border-radius: 3px;
		font-family: 'Courier New', monospace;
	}
	.message-content :global(pre) {
		background: #000;
		padding: 0.75rem;
		border-radius: 4px;
		overflow-x: auto;
		margin: 0.5rem 0;
	}
	.message-content :global(pre code) {
		background: transparent;
		padding: 0;
	}

	.message-content pre {
		margin: 0;
		white-space: pre-wrap;
		font-size: 0.7rem;
	}

	.context-scope-display {
		margin-top: 0.75rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.2);
		border-radius: 4px;
		font-size: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		border-left: 3px solid #f1c40f;
	}

	.resolved-ids-display {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.1);
		border-radius: 4px;
		font-size: 0.7rem;
		border-left: 3px solid #3498db;
	}

	.resolved-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		margin-top: 0.25rem;
	}

	.resolved-tag {
		background: rgba(52, 152, 219, 0.2);
		color: #3498db;
		padding: 1px 6px;
		border-radius: 10px;
		font-size: 0.6rem;
	}

	.scope-label {
		font-weight: bold;
		color: #f1c40f;
		font-size: 0.65rem;
		margin-bottom: 0.25rem;
	}

	.scope-item {
		color: #aaa;
	}

	.patch-actions {
		margin-top: 0.75rem;
		display: flex;
		justify-content: flex-end;
	}

	.apply-btn {
		background: #2ecc71;
		color: white;
		border: none;
		border-radius: 4px;
		padding: 4px 12px;
		font-size: 0.75rem;
		font-weight: bold;
		cursor: pointer;
		transition: background 0.2s;
	}

	.apply-btn:hover {
		background: #27ae60;
	}

	.chat-input-area {
		padding: 1rem;
		background: #252526;
		border-top: 1px solid #333;
	}

	.drop-context-preview {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		margin-bottom: 0.75rem;
		padding: 0.5rem;
		background: #1e1e1e;
		border: 1px dashed #555;
		border-radius: 6px;
		min-height: 2.5rem;
	}

	.context-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.6rem;
		font-weight: bold;
		color: #888;
		margin-bottom: 0.25rem;
	}

	.clear-context-btn {
		background: none;
		border: none;
		color: #555;
		cursor: pointer;
		text-decoration: underline;
	}

	.clear-context-btn:hover { color: #888; }

	.context-tags-scroll {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.input-wrapper {
		display: flex;
		gap: 0.75rem;
		align-items: flex-end;
	}

	textarea {
		flex: 1;
		background: #3c3c3c;
		color: white;
		border: 1px solid #555;
		border-radius: 4px;
		padding: 0.6rem;
		font-size: 0.9rem;
		resize: none;
		height: 80px;
		outline: none;
	}

	textarea:focus {
		border-color: #007acc;
	}

	.send-btn {
		background: #007acc;
		color: white;
		border: none;
		border-radius: 6px;
		padding: 0.6rem 1.2rem;
		cursor: pointer;
		font-weight: bold;
		height: 40px;
		transition: background 0.2s;
	}

	.send-btn:hover:not(:disabled) {
		background: #0062a3;
	}

	.send-btn:disabled {
		background: #444;
		color: #888;
		cursor: not-allowed;
	}

	.loading .dot {
		animation: blink 1.4s infinite both;
		font-size: 1.5rem;
		line-height: 0;
	}

	.loading .dot:nth-child(2) { animation-delay: 0.2s; }
	.loading .dot:nth-child(3) { animation-delay: 0.4s; }

	@keyframes blink {
		0% { opacity: .2; }
		20% { opacity: 1; }
		100% { opacity: .2; }
	}
</style>
