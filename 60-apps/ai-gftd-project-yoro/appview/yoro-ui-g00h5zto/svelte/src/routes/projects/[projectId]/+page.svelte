<!--
  /projects/{projectId} — Project chat with slash commands, MCP, members, image gen.
  Data persisted in yata graph (PDS KV). LLM via Murakumo.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount, onDestroy, tick } from 'svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { atQuery, atProcedure, getCurrentDID, searchActors, uploadBlob } from '$lib/atproto-agent';
	import { getSessionToken } from '$lib/auth';
	import { useGraphRAG } from '$lib/provider/graph-rag.svelte.js';
	import { useLocalLLM } from '$lib/provider/local-llm.svelte.js';
	import {
		BROWSER_TOOLS,
		buildAgentSystemPrompt,
		parseToolCalls,
		executeToolCalls,
		formatToolResultsAsMessage,
		type ToolResult,
	} from '$lib/provider/agent-executor.svelte.js';
	import { RichText, PostEmbed } from '$lib/w';

	const graphRAG = useGraphRAG();
	const localLLM = useLocalLLM();

	interface ChatAttachment {
		type: 'image' | 'video' | 'file';
		name: string;
		mimeType: string;
		size: number;
		url?: string;
		ref?: string;
		previewUrl?: string;
	}

	interface ChatMessage {
		id: string;
		role: 'user' | 'assistant' | 'system' | 'tool';
		body: string;
		timestamp: string;
		status?: 'sending' | 'sent' | 'error';
		toolName?: string;
		sender?: string;
		imageB64?: string;
		thinking?: string;
		attachments?: ChatAttachment[];
		embed?: any;
	}

	interface SlashCommand { name: string; description: string; usage: string }
	interface ProjectMember { did: string; displayName?: string; role: string; addedAt: string }
	interface QuickAction {
		id: string;
		label: string;
		prompt: string;
	}

	const SLASH_COMMANDS: SlashCommand[] = [
		{ name: '/task', description: 'タスクを追加', usage: '/task タイトル' },
		{ name: '/done', description: 'タスクを完了', usage: '/done ID' },
		{ name: '/status', description: '進捗確認', usage: '/status' },
		{ name: '/mcp', description: 'MCP ツール一覧', usage: '/mcp' },
		{ name: '/invite', description: 'メンバー招待', usage: '/invite DID' },
		{ name: '/members', description: 'メンバー一覧', usage: '/members' },
		{ name: '/image', description: '画像生成', usage: '/image プロンプト' },
		{ name: '/knowledge', description: 'domain knowledge に質問', usage: '/knowledge 質問' },
		{ name: '/think', description: '深い推論 (qwq-32b)', usage: '/think 質問' },
		{ name: '/new', description: '新しいプロジェクト', usage: '/new' },
	];

	const convoId = $derived(decodeURIComponent(($page.params as Record<string, string>).projectId ?? ''));
	let selfDid = $state('');
	let messages = $state<ChatMessage[]>([]);
	let chatLoading = $state(false);
	let loadingLabel = $state('');
	let scrollContainer: HTMLDivElement | undefined = $state();
	let autoScroll = $state(true);
	let members = $state<ProjectMember[]>([]);

	let projectEmail = $state('');
	let projectName = $state('');
	let projectDid = $state('');
	let parentProjectConvoId = $state('');
	let parentProjectName = $state('');
	let emailCopied = $state(false);
	let showSubProjects = $state(false);
	let subProjects = $state<Array<{ convoId: string; name: string; did?: string; email?: string; kind?: string; childCount?: number }>>([]);
	let subProjectsLoading = $state(false);
	let creatingSubProject = $state(false);
	let isMemberOrOwner = $state(false);
	let accessChecked = $state(false);

	let composerText = $state('');
	let composerRef: HTMLTextAreaElement | undefined = $state();
	let showSlashMenu = $state(false);
	let slashFilter = $state('');
	let sending = $state(false);
	let showMemberPanel = $state(false);
	let inviteQuery = $state('');
	let inviteResults = $state<Array<{ did: string; displayName?: string; avatar?: string }>>([]);
	let inviteSearchTimeout: ReturnType<typeof setTimeout> | undefined;

	/** Pending file attachments (pre-upload previews). */
	let pendingFiles = $state<Array<{ file: File; previewUrl: string; uploading: boolean; error?: string }>>([]);
	let fileInputRef: HTMLInputElement | undefined = $state();
	const MAX_ATTACHMENTS = 4;
	const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

	const filteredCommands = $derived(
		slashFilter ? SLASH_COMMANDS.filter((c) => c.name.startsWith(`/${slashFilter}`)) : SLASH_COMMANDS,
	);

	/** DID → member lookup for message sender resolution. */
	const memberLookup = $derived(new Map(members.map((m) => [m.did, m])));

	/** Context-aware quick actions shown as tap-only chips. */
	const contextQuickActions = $derived(buildContextQuickActions(messages, projectName || 'このプロジェクト'));

	/** Member-scoped quick actions shown per participant. */
	const memberQuickActions = $derived(
		members
			.filter((m) => m.did !== selfDid)
			.map((member) => ({ member, actions: buildMemberQuickActions(member) }))
			.filter((row) => row.actions.length > 0),
	);

	/** Resolve sender display name from DID. */
	function senderName(msg: ChatMessage): string {
		if (msg.role === 'user') {
			if (msg.sender && msg.sender !== selfDid) {
				const m = memberLookup.get(msg.sender);
				return m?.displayName ?? shortDid(msg.sender);
			}
			return 'あなた';
		}
		if (msg.sender) {
			const m = memberLookup.get(msg.sender);
			if (m) return m.displayName ?? shortDid(msg.sender);
		}
		return 'yoro';
	}

	/** Truncate DID for display. */
	function shortDid(did: string): string {
		if (!did) return '';
		if (did.startsWith('did:web:')) return did.replace('did:web:', '');
		if (did.length > 30) return did.slice(0, 20) + '…' + did.slice(-8);
		return did;
	}

	function memberName(member: ProjectMember): string {
		return member.displayName?.trim() || shortDid(member.did);
	}

	function uniqActions(actions: QuickAction[]): QuickAction[] {
		const seen = new Set<string>();
		const out: QuickAction[] = [];
		for (const action of actions) {
			if (seen.has(action.label)) continue;
			seen.add(action.label);
			out.push(action);
		}
		return out.slice(0, 5);
	}

	function buildContextQuickActions(allMessages: ChatMessage[], projectLabel: string): QuickAction[] {
		const latest = [...allMessages].reverse().find((m) => m.role !== 'system');
		const latestText = (latest?.body ?? '').toLowerCase();
		const base: QuickAction[] = [
			{
				id: 'ctx-next',
				label: '次の一手',
				prompt: `${projectLabel} の現状から、次にやるべき作業を優先度順で3つだけ提案して。`,
			},
			{
				id: 'ctx-summary',
				label: '要点まとめ',
				prompt: `ここまでの会話を3行で要約して。決定事項と未決事項を分けて。`,
			},
			{
				id: 'ctx-task',
				label: 'タスク化',
				prompt: `ここまでの会話を TODO に変換して。各項目に「担当・期限・完了条件」をつけて。`,
			},
		];

		if (latestText.includes('エラー') || latestText.includes('失敗') || latestText.includes('error')) {
			base.push({
				id: 'ctx-debug',
				label: '原因切り分け',
				prompt: '直近の失敗について、原因候補を3つに絞って、確認手順を順番に出して。',
			});
		}
		if (latestText.includes('/image') || latestText.includes('画像')) {
			base.push({
				id: 'ctx-image',
				label: '画像プロンプト改善',
				prompt: '直近の画像生成結果を改善するために、具体的な改善プロンプトを3案出して。',
			});
		}
		if (latestText.includes('/think') || latestText.includes('推論')) {
			base.push({
				id: 'ctx-think',
				label: '前提確認',
				prompt: '結論の前提条件を洗い出して、危ない前提を3つ指摘して。',
			});
		}
		return uniqActions(base);
	}

	function buildMemberQuickActions(member: ProjectMember): QuickAction[] {
		const name = memberName(member);
		const isAdmin = member.role === 'owner' || member.role === 'admin';
		const actions: QuickAction[] = [
			{
				id: `m-${member.did}-assign`,
				label: '担当依頼',
				prompt: `${name} (${member.did}) に依頼する次の作業を1件作って。依頼文は120文字以内で。`,
			},
			{
				id: `m-${member.did}-review`,
				label: 'レビュー依頼',
				prompt: `${name} (${member.did}) 向けに、今の文脈でレビュー依頼メッセージを作成して。`,
			},
		];
		if (isAdmin) {
			actions.push({
				id: `m-${member.did}-decision`,
				label: '意思決定確認',
				prompt: `${name} (${member.did}) に確認すべき意思決定事項を2点に絞って提案して。`,
			});
		}
		return actions.slice(0, 3);
	}

	const OPS_TIMEOUT_MS = 5000;

	/** Track previous convoId to detect navigation between projects. */
	let prevConvoId = $state('');

	/**
	 * Phase 3 BPMN reply consumer (ADR-2604271600).
	 *
	 * When the PDS Worker has `PROJECTOR_USE_BPMN=1` set, sendProjectMessage
	 * returns 202 Accepted immediately and the actual reply is appended to
	 * vertex_projector_message by the L7 LangServer `projector.persist.message`
	 * primitive. Subscribe to /sse/projects/{convoId} so the reply renders
	 * as soon as it lands instead of waiting for the next poll/load.
	 *
	 * Falls back gracefully when SSE is unavailable: the existing
	 * sendMessage() path either gets a synchronous reply (legacy CF Worker
	 * path) or the user can refresh and loadChat() will pick it up.
	 */
	let projectorSse: EventSource | null = null;
	const seenSseRkeys = new Set<string>();
	let sseRetryTimer: ReturnType<typeof setTimeout> | null = null;

	function disconnectProjectorSse(): void {
		if (sseRetryTimer) {
			clearTimeout(sseRetryTimer);
			sseRetryTimer = null;
		}
		if (projectorSse) {
			try { projectorSse.close(); } catch { /* ignore */ }
			projectorSse = null;
		}
	}

	function connectProjectorSse(): void {
		disconnectProjectorSse();
		if (!convoId) return;
		// `EventSource` is browser-only; SSR build skips this branch.
		if (typeof EventSource === 'undefined') return;

		const since = Date.now() - 5000;
		const url = `/sse/projects/${encodeURIComponent(convoId)}?since=${since}`;
		try {
			const es = new EventSource(url);
			projectorSse = es;
			es.addEventListener('message', (ev: MessageEvent) => {
				try {
					const data = JSON.parse(ev.data) as {
						uri?: string;
						rkey?: string;
						ts_ms?: number;
						record?: { text?: string; convoId?: string };
					};
					const rkey = data.rkey || data.uri || '';
					if (!rkey || seenSseRkeys.has(rkey)) return;
					seenSseRkeys.add(rkey);
					const body = data.record?.text || '';
					if (!body) return;
					if (data.record?.convoId && data.record.convoId !== convoId) return;
					messages = [
						...messages,
						{
							id: `bpmn-${rkey}`,
							role: 'assistant',
							body,
							timestamp: new Date(data.ts_ms ?? Date.now()).toISOString(),
							sender: 'projector-bpmn',
						},
					];
					void tick().then(scrollToBottom);
				} catch (e) {
					console.warn('[projector-sse] parse failed:', e);
				}
			});
			es.addEventListener('error', () => {
				// Browser auto-reconnects on transient failures, but if the
				// stream closes after the 90s server budget we re-open it
				// ourselves. Cap retry to avoid hammering on hard failures.
				if (sseRetryTimer) return;
				sseRetryTimer = setTimeout(() => {
					sseRetryTimer = null;
					if (convoId) connectProjectorSse();
				}, 3000);
			});
		} catch (e) {
			console.warn('[projector-sse] connect failed:', e);
		}
	}

	/** Initialize project chat: load messages, check membership, show welcome if empty. */
	async function initProjectChat() {
		// Reset state for new project
		messages = [];
		members = [];
		chatLoading = false;
		projectEmail = '';
		projectName = '';
		projectDid = '';
		parentProjectConvoId = '';
		parentProjectName = '';
		isMemberOrOwner = false;
		accessChecked = false;
		subProjects = [];
		showSubProjects = false;
		showMemberPanel = false;
		sending = false;

		try { localStorage.setItem('yoro:project-convo-id', convoId); } catch { /* ignore */ }
		seenSseRkeys.clear();
		await loadChat();
		void checkMembership();
		connectProjectorSse();
		if (messages.length === 0) {
			messages = [{
				id: 'welcome', role: 'assistant' as const,
				body: `こんにちは! **yoro** です\n\nこのプロジェクトの AI アシスタントだよ。何でも聞いてね!\n\n**できること:**\n\`/task\` タスク管理\n\`/think\` 深い推論\n\`/image\` 画像生成\n\`/research\` Web 調査\n\`/mcp\` ツール一覧\n\`/new\` サブプロジェクト作成\n\nまたは、普通に話しかけてくれれば OK! グラフデータの検索や分析、要約、翻訳もブラウザ内でできるよ。`,
				timestamp: new Date().toISOString(),
			}];
		}
		await tick();
		scrollToBottom();
	}

	onMount(async () => {
		try { selfDid = (await getCurrentDID()) ?? ''; } catch { selfDid = ''; }
		prevConvoId = convoId;
		await initProjectChat();
	});

	onDestroy(() => {
		disconnectProjectorSse();
	});

	/**
	 * Re-initialize when convoId changes (client-side navigation between projects).
	 * SvelteKit reuses the component, so onMount does not re-fire.
	 */
	$effect(() => {
		const currentId = convoId;
		if (currentId && prevConvoId && currentId !== prevConvoId) {
			prevConvoId = currentId;
			void initProjectChat();
		}
	});

	/** XRPC with session token. LLM-invoking endpoints get 30s timeout. */
	async function atProcedureWithSession<T = Record<string, unknown>>(nsid: string, body?: unknown, opts?: { timeout?: number }): Promise<T> {
		const token = await getSessionToken();
		if (!token) throw new Error('ログインセッションが見つかりま���ん。再ログインしてください。');
		return atProcedure<T>(nsid, body, { bearerToken: token, timeout: opts?.timeout });
	}

	/** Long timeout for LLM-invoking PDS calls (server-side inference can take 15-25s). */
	const LLM_TIMEOUT_MS = 30_000;

	async function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
		let timer: ReturnType<typeof setTimeout> | undefined;
		try {
			return await Promise.race([
				promise,
				new Promise<T>((_, reject) => {
					timer = setTimeout(() => reject(new Error(`${label} timeout (${ms}ms)`)), ms);
				}),
			]);
		} finally {
			if (timer) clearTimeout(timer);
		}
	}

	async function createProjectConvo(name: string): Promise<string> {
		const payload: Record<string, unknown> = { name };

		try {
			const res = await withTimeout(
				atProcedureWithSession('com.etzhayyim.apps.ops.newProjectConvo', payload),
				OPS_TIMEOUT_MS,
				'ops.newProjectConvo',
			);
			const parsed = (typeof res === 'string' ? JSON.parse(res) : res) as Record<string, unknown>;
			const convo = (parsed?.convoId as string) || (parsed?.convo_id as string);
			if (convo) return convo;
		} catch (e) {
			console.warn('ops.newProjectConvo failed:', e);
		}

		const legacyRes = await atProcedureWithSession('com.etzhayyim.projector.newProjectConvo', payload);
		const legacy = (typeof legacyRes === 'string' ? JSON.parse(legacyRes) : legacyRes) as Record<string, unknown>;
		const convo = (legacy?.convoId as string) || (legacy?.convo_id as string);
		if (!convo) throw new Error('newProjectConvo returned no convoId');
		return convo;
	}

	function buildUniqueProjectName(): string {
		const now = new Date();
		const datePart = now.toLocaleDateString('ja-JP');
		const timePart = now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
		const rand = Math.random().toString(36).slice(2, 6);
		return `Project ${datePart} ${timePart} ${rand}`;
	}

	async function loadChat() {
		try {
			const res = await atProcedureWithSession('com.etzhayyim.projector.loadProjectChat', { convoId });
			const data = res as Record<string, unknown>;
			const loaded = (data?.messages ?? []) as ChatMessage[];
			const loadedMembers = (data?.members ?? []) as ProjectMember[];
			if (loaded.length > 0) messages = loaded;
			if (loadedMembers.length > 0) members = loadedMembers;
		} catch (e) { console.warn('loadProjectChat failed:', e); }
		// Load project metadata (email, name, DID)
		try {
			const meta = await atProcedureWithSession<Record<string, unknown>>('com.etzhayyim.projector.getProjectConvo', { convoId });
			const proj = (typeof meta === 'string' ? JSON.parse(meta) : meta) as Record<string, unknown>;
			const project = (proj?.project ?? {}) as Record<string, unknown>;
			projectEmail = (project?.email as string) || '';
			projectName = (project?.name as string) || '';
			projectDid = (project?.did as string) || '';
			// Extract parent project info
			const parentUri = (project?.parentProjectUri as string) || '';
			if (parentUri) {
				const parentId = parentUri.split('/').pop() || '';
				parentProjectConvoId = parentId;
				parentProjectName = (project?.parentProjectName as string) || '';
				// If no parent name in response, fetch it
				if (!parentProjectName && parentId) {
					atProcedureWithSession<Record<string, unknown>>('com.etzhayyim.projector.getProjectConvo', { convoId: parentId })
						.then(r => { const p = (typeof r === 'string' ? JSON.parse(r) : r) as Record<string, unknown>; const pp = (p?.project ?? {}) as Record<string, unknown>; parentProjectName = (pp?.name as string) || parentId.slice(0, 8); })
						.catch((error) => {
							console.warn('[silent-fail] projects/[projectId]/+page.svelte: parent project fetch failed', error);
							parentProjectName = parentId.slice(0, 8);
						});
				}
			}
		} catch (e) { console.warn('getProjectConvo failed:', e); }
	}

	/** Copy project email to clipboard. */
	async function copyEmail() {
		if (!projectEmail) return;
		try {
			await navigator.clipboard.writeText(projectEmail);
			emailCopied = true;
			setTimeout(() => { emailCopied = false; }, 2000);
		} catch { /* fallback: select text */ }
	}

	/** Load sub-projects (children of current project). */
	async function loadSubProjects() {
		subProjectsLoading = true;
		try {
			const parentUri = `at://${selfDid}/com.etzhayyim.projector/${convoId}`;
			const res = await atProcedureWithSession<{ convos: typeof subProjects }>('com.etzhayyim.projector.listProjectConvos', { parentUri, limit: 50 });
			const data = typeof res === 'string' ? JSON.parse(res) : res;
			subProjects = (data?.convos ?? []) as typeof subProjects;
		} catch (e) { console.warn('loadSubProjects failed:', e); subProjects = []; }
		finally { subProjectsLoading = false; }
	}

	/** Create a sub-project under current project. */
	async function createSubProject() {
		if (creatingSubProject) return;
		creatingSubProject = true;
		try {
			const now = new Date();
			const name = `Sub ${now.toLocaleDateString('ja-JP')} ${now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}`;
			const parentUri = `at://${selfDid}/com.etzhayyim.projector/${convoId}`;
			const res = await atProcedureWithSession<Record<string, unknown>>('com.etzhayyim.projector.newProjectConvo', { name, parentProjectUri: parentUri });
			const parsed = (typeof res === 'string' ? JSON.parse(res) : res) as Record<string, unknown>;
			const newConvoId = (parsed?.convoId as string) || '';
			if (newConvoId) {
				await loadSubProjects();
			}
		} catch (e) {
			messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: `サブプロジェクト作成に失敗: ${errorMessage(e)}`, timestamp: new Date().toISOString() }];
		} finally { creatingSubProject = false; }
	}

	/** Check if current user is owner/member of this project. */
	async function checkMembership() {
		try {
			const meta = await atProcedureWithSession<Record<string, unknown>>('com.etzhayyim.projector.getProjectConvo', { convoId });
			const proj = (typeof meta === 'string' ? JSON.parse(meta) : meta) as Record<string, unknown>;
			const project = (proj?.project ?? {}) as Record<string, unknown>;
			const membersList = (project?.members ?? proj?.members ?? []) as Array<{ did: string }>;
			const createdBy = (project?.createdBy as string) || '';
			isMemberOrOwner = createdBy === selfDid || membersList.some(m => m.did === selfDid);
		} catch { isMemberOrOwner = false; }
		accessChecked = true;
	}

	// ── Composer ──
	function handleComposerInput() {
		if (composerRef) { composerRef.style.height = 'auto'; composerRef.style.height = Math.min(composerRef.scrollHeight, 120) + 'px'; }
		const t = composerText;
		if (t === '/') { showSlashMenu = true; slashFilter = ''; }
		else if (t.startsWith('/') && !t.includes(' ')) { showSlashMenu = true; slashFilter = t.slice(1); }
		else { showSlashMenu = false; }
	}

	function selectSlashCommand(cmd: SlashCommand) {
		composerText = cmd.name + ' ';
		showSlashMenu = false;
		composerRef?.focus();
	}

	function handleKeydown(e: KeyboardEvent) {
		// Tab: autocomplete slash command
		if (e.key === 'Tab' && showSlashMenu && filteredCommands.length > 0) {
			e.preventDefault();
			selectSlashCommand(filteredCommands[0]);
			return;
		}
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			if (showSlashMenu && filteredCommands.length > 0) selectSlashCommand(filteredCommands[0]);
			else void handleSend(composerText);
		}
		if (e.key === 'Escape') showSlashMenu = false;
	}

	function shouldUseKnowledgeAnswer(text: string): boolean {
		const q = text.toLowerCase();
		if (q.startsWith('/knowledge ')) return true;
		return /ぽこあ|ポコピア|pokopia|夢島|ゆめしま|フワンテ|あたたかい風の棲家|pokemon pokopia/i.test(text);
	}

	function knowledgeQuestion(text: string): string {
		return text.trim().replace(/^\/knowledge\s+/i, '').trim();
	}

	function knowledgePayload(question: string): Record<string, unknown> {
		const isPokopia = /ぽこあ|ポコピア|pokopia|夢島|ゆめしま|フワンテ|あたたかい風の棲家|pokemon/i.test(question);
		return {
			question,
			domain: isPokopia ? 'media_gamers' : '',
			game_slug: isPokopia ? 'pokemon-pokopia' : '',
			lang: 'ja',
			topK: 6,
			tier: 'fast',
		};
	}

	function extractKnowledgeAnswer(payload: unknown): string {
		const data = payload as Record<string, unknown>;
		const variables = (data.variables && typeof data.variables === 'object') ? data.variables as Record<string, unknown> : data;
		const error = String(variables.error ?? data.error ?? '').trim();
		const errorKind = String(variables.errorKind ?? data.errorKind ?? '').trim();
		if (error) return `Domain knowledge 回答エラー: ${errorKind ? `${errorKind}: ` : ''}${error}`;
		const answer = String(variables.answer ?? '').trim();
		const citations = Array.isArray(variables.citations) ? variables.citations.map(String).filter(Boolean) : [];
		const contexts = Array.isArray(variables.contexts) ? variables.contexts as Array<Record<string, unknown>> : [];
		const imageUrl = citations.find((url) => /\.(png|jpg|jpeg|webp)(\?|$)/i.test(url))
			?? contexts.map((c) => String(c.chunk_text ?? '')).find((s) => /^.*https?:\/\/\S+\.(png|jpg|jpeg|webp).*$/i.test(s))?.match(/https?:\/\/\S+/)?.[0];
		const sourceText = citations.length ? `\n\nSources:\n${citations.slice(0, 6).map((url) => `- ${url}`).join('\n')}` : '';
		const imageText = imageUrl ? `\n\n画像: ${imageUrl}` : '';
		return `${answer || '該当する domain knowledge から回答を作れませんでした。'}${imageText}${sourceText}`.trim();
	}

	async function handleKnowledgeAnswer(text: string, msgId: string): Promise<boolean> {
		const question = knowledgeQuestion(text);
		if (!question) return false;
		loadingLabel = 'Domain knowledge を検索中...';
		const res = await fetch('https://llm.etzhayyim.com/xrpc/com.etzhayyim.apps.llm.answerWithKnowledge?stream=1&timeoutMs=240000', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
			body: JSON.stringify(knowledgePayload(question)),
		});
		if (!res.ok || !res.body) throw new Error(`knowledge request failed: ${res.status}`);

		const reader = res.body.getReader();
		const decoder = new TextDecoder();
		let buffer = '';
		let completed: unknown = null;
		while (true) {
			const { value, done } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const parts = buffer.split('\n\n');
			buffer = parts.pop() ?? '';
			for (const part of parts) {
				const event = part.split('\n').find((line) => line.startsWith('event:'))?.slice(6).trim();
				const dataLine = part.split('\n').find((line) => line.startsWith('data:'))?.slice(5).trim();
				if (event === 'heartbeat') loadingLabel = 'Domain knowledge 回答を待機中...';
				if ((event === 'complete' || event === 'error') && dataLine) {
					completed = JSON.parse(dataLine);
				}
			}
		}
		if (!completed) throw new Error('knowledge response ended without complete event');
		messages = messages.map((m) => (m.id === msgId ? { ...m, status: 'sent' as const } : m));
		messages = [...messages, { id: `knowledge-${Date.now()}`, role: 'assistant', body: extractKnowledgeAnswer(completed), timestamp: new Date().toISOString(), sender: 'llm.etzhayyim.com' }];
		return true;
	}

	// ── Send ──
	async function handleSend(text: string) {
		// If files are pending, use upload flow
		if (pendingFiles.length > 0) { await uploadAndSend(); return; }
		if (!text.trim() || sending) return;
		sending = true;
		composerText = '';
		showSlashMenu = false;
		if (composerRef) composerRef.style.height = 'auto';

		// Local commands
		if (text.trim() === '/new') {
			chatLoading = true;
			loadingLabel = '新しいプロジェクトを作成中...';
			try {
				const newConvoId = await createProjectConvo(buildUniqueProjectName());
				try { localStorage.setItem('yoro:project-convo-id', newConvoId); } catch { /* ignore */ }
				void goto(`/projects/${encodeURIComponent(newConvoId)}`, { replaceState: true });
			} catch (e) {
				messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: `新規プロジェクト作成に失敗: ${errorMessage(e)}`, timestamp: new Date().toISOString() }];
			} finally {
				chatLoading = false;
				loadingLabel = '';
				sending = false;
			}
			return;
		}
		if (text.trim() === '/members') { showMemberPanel = !showMemberPanel; sending = false; return; }
		if (text.trim().startsWith('/invite ')) { await handleInviteDirect(text.trim().slice(8).trim()); sending = false; return; }
		if (text.trim() === '/mcp') { await handleMcpList(); sending = false; return; }
		if (text.trim().startsWith('/image ')) { await handleImageGen(text.trim().slice(7).trim()); sending = false; return; }
		if (text.trim().startsWith('/think ')) { await handleThink(text.trim().slice(7).trim()); sending = false; return; }

		const msgId = `msg-${Date.now()}`;
		messages = [...messages, { id: msgId, role: 'user', body: text, timestamp: new Date().toISOString(), status: 'sending' }];
		await tick();
		scrollToBottom();
		chatLoading = true;

		if (shouldUseKnowledgeAnswer(text)) {
			try {
				if (await handleKnowledgeAnswer(text, msgId)) {
					atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', { convoId, text: text.trim() }).catch((e) => console.warn('[knowledge] PDS persist failed:', e));
					chatLoading = false; loadingLabel = ''; sending = false;
					await tick(); scrollToBottom();
					return;
				}
			} catch (e) {
				console.warn('[knowledge] answerWithKnowledge failed:', e);
				messages = messages.map((m) => (m.id === msgId ? { ...m, status: 'error' as const } : m));
				messages = [...messages, {
					id: `err-${Date.now()}`,
					role: 'system',
					body: `Domain knowledge 回答エラー: ${errorMessage(e)}`,
					timestamp: new Date().toISOString(),
				}];
				chatLoading = false; loadingLabel = ''; sending = false;
				await tick(); scrollToBottom();
				return;
			}
		}

		// ── Browser-side Agentic Execution (Tool Calling Loop) ──
		// Priority: Local LLM with tool calling → GraphRAG → PDS fallback
		if (localLLM.isReady) {
			loadingLabel = 'Agent 推論中 (browser)...';
			const systemPrompt = buildAgentSystemPrompt(projectName || 'Project');
			const history = messages
				.filter((m) => m.role === 'user' || m.role === 'assistant' || m.role === 'tool')
				.slice(-12)
				.map((m) => ({ role: (m.role === 'tool' ? 'assistant' : m.role) as 'user' | 'assistant' | 'system', content: m.body }));

			let llmReply = await localLLM.chatCompletion(
				[{ role: 'system', content: systemPrompt }, ...history, { role: 'user', content: text.trim() }],
				{ maxTokens: 512, temperature: 0.6 },
			);

			if (llmReply) {
				messages = messages.map((m) => (m.id === msgId ? { ...m, status: 'sent' as const } : m));
				let toolIterations = 0;
				let accumulatedToolContext = '';

				while (toolIterations < 3) {
					const toolCalls = parseToolCalls(llmReply ?? '');
					if (toolCalls.length === 0) break;
					toolIterations++;
					loadingLabel = `ツール実行中 (${toolCalls.map(c => c.name).join(', ')})...`;
					await tick(); scrollToBottom();

					const toolResults = await executeToolCalls(toolCalls);
					for (const result of toolResults) {
						messages = [...messages, {
							id: `tool-${Date.now()}-${result.tool}`, role: 'tool' as const,
							body: formatToolResultsAsMessage([result]), toolName: result.tool,
							timestamp: new Date().toISOString(),
						}];
					}
					await tick(); scrollToBottom();

					const toolContext = toolResults.map((r) => `[Tool: ${r.tool}, ${r.executedIn}, ${r.durationMs.toFixed(0)}ms]\n${JSON.stringify(r.data).slice(0, 1500)}`).join('\n\n');
					accumulatedToolContext += '\n' + toolContext;

					loadingLabel = 'ツール結果を分析中...';
					llmReply = await localLLM.chatCompletion([
						{ role: 'system', content: systemPrompt }, ...history,
						{ role: 'user', content: text.trim() },
						{ role: 'assistant', content: `Tool results:\n${accumulatedToolContext}` },
						{ role: 'user', content: 'Based on the tool results, provide a concise answer. Call another tool if needed, otherwise give the final answer without tool calls.' },
					], { maxTokens: 512, temperature: 0.5 });
				}

				const cleanReply = (llmReply ?? '').replace(/\[TOOL_CALL:.*?\]/g, '').trim();
				if (cleanReply) {
					messages = [...messages, { id: `local-${Date.now()}`, role: 'assistant', body: cleanReply, timestamp: new Date().toISOString() }];
				}
				chatLoading = false; loadingLabel = ''; sending = false;
				atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', { convoId, text: text.trim() }).catch((e) => console.warn('[agent-executor] PDS persist failed:', e));
				await tick(); scrollToBottom();
				return;
			}
		}

		// GraphRAG fallback (DuckDB context + LLM, without tool calling)
		if (graphRAG.isLLMReady) {
			loadingLabel = 'GraphRAG 推論中...';
			const history = messages.filter((m) => m.role === 'user' || m.role === 'assistant').slice(-10).map((m) => ({ role: m.role as 'user' | 'assistant', content: m.body }));
			const localReply = await graphRAG.query(history, text.trim(), `You are the AI agent for project "${projectName || 'Untitled'}". Respond concisely in the same language as the user.`);
			if (localReply) {
				messages = messages.map((m) => (m.id === msgId ? { ...m, status: 'sent' as const } : m));
				messages = [...messages, { id: `local-${Date.now()}`, role: 'assistant', body: localReply, timestamp: new Date().toISOString() }];
				chatLoading = false; loadingLabel = ''; sending = false;
				atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', { convoId, text: text.trim() }).catch((e) => console.warn('[graphrag] PDS persist failed:', e));
				await tick(); scrollToBottom();
				return;
			}
		}

		// PDS server-side LLM fallback (Murakumo + MCP tool calling)
		loadingLabel = 'Agent 推論中 (server)...';
		try {
			const res = await atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', { convoId, text: text.trim() }, { timeout: LLM_TIMEOUT_MS });
			const data = res as Record<string, unknown>;
			messages = messages.map((m) => (m.id === msgId ? { ...m, status: 'sent' as const } : m));
			let replyText = (data?.reply as string) ?? '';
			if (replyText) {
				if (replyText.includes('</think>')) replyText = replyText.replace(/<think>[\s\S]*?<\/think>\s*/g, '').trim();
				messages = [...messages, { id: `reply-${Date.now()}`, role: 'assistant', body: replyText, timestamp: new Date().toISOString() }];
			}
		} catch (e) {
			messages = messages.map((m) => (m.id === msgId ? { ...m, status: 'error' as const } : m));
			const errMsg = errorMessage(e);
			const isTimeout = errMsg.includes('timed out') || errMsg.includes('timeout');
			messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: isTimeout ? 'サーバーの応答に時間がかかっています。もう一度お試しください。' : `送信に失敗: ${errMsg}`, timestamp: new Date().toISOString() }];
		} finally { chatLoading = false; loadingLabel = ''; sending = false; }
		await tick(); scrollToBottom();
	}

	async function handleImageGen(prompt: string) {
		if (!prompt) return;
		messages = [...messages, { id: `msg-${Date.now()}`, role: 'user', body: `/image ${prompt}`, timestamp: new Date().toISOString() }];
		chatLoading = true;
		loadingLabel = '画像を生成中...';
		await tick();
		scrollToBottom();
		try {
			const res = await atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', {
				convoId,
				text: `/image ${prompt}`,
			}, { timeout: LLM_TIMEOUT_MS });
			const data = res as Record<string, unknown>;
			const reply = (data?.reply as string) ?? '';
			const imageB64 = (data?.imageB64 as string) ?? '';
			if (reply || imageB64) {
				messages = [...messages, {
					id: `img-${Date.now()}`,
					role: 'assistant',
					body: reply || '画像を生成しました',
					timestamp: new Date().toISOString(),
					...(imageB64 ? { imageB64 } : {}),
				}];
			} else {
				messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: '画像生成結果が返りませんでした', timestamp: new Date().toISOString() }];
			}
		} catch (e) {
			messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: `画像生成エラー: ${errorMessage(e)}`, timestamp: new Date().toISOString() }];
		} finally {
			chatLoading = false;
			loadingLabel = '';
		}
		await tick();
		scrollToBottom();
	}

	/** Deep reasoning via qwq-32b — shows thinking process + conclusion separately. */
	async function handleThink(prompt: string) {
		if (!prompt) return;
		messages = [...messages, { id: `msg-${Date.now()}`, role: 'user', body: `/think ${prompt}`, timestamp: new Date().toISOString() }];
		chatLoading = true;
		loadingLabel = '推論中 (qwq-32b)...';
		await tick();
		scrollToBottom();
		try {
			const res = await atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', {
				convoId, text: `/think ${prompt}`,
			}, { timeout: LLM_TIMEOUT_MS });
			const data = res as Record<string, unknown>;
			const thinking = (data?.thinking as string) ?? '';
			const reply = (data?.reply as string) ?? '';
			if (thinking || reply) {
				messages = [...messages, {
					id: `think-${Date.now()}`, role: 'assistant',
					body: reply || '推論結果なし',
					timestamp: new Date().toISOString(),
					thinking: thinking || undefined,
				}];
			}
		} catch (e) {
			messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: `推論エラー: ${errorMessage(e)}`, timestamp: new Date().toISOString() }];
		} finally {
			chatLoading = false;
			loadingLabel = '';
		}
		await tick();
		scrollToBottom();
	}

	async function handleMcpList() {
		chatLoading = true;
		try {
			const res = await fetch('/api/mcp', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} }) });
			const data = await res.json() as { result?: { tools?: Array<{ name: string; description?: string }> } };
			const tools = data?.result?.tools ?? [];
			if (tools.length > 0) {
				messages = [...messages, { id: `mcp-${Date.now()}`, role: 'assistant', body: `**MCP ツール (${tools.length}件)**\n\n${tools.map(t => `\`${t.name}\` — ${t.description ?? ''}`).join('\n')}`, timestamp: new Date().toISOString() }];
			} else { messages = [...messages, { id: `sys-${Date.now()}`, role: 'system', body: 'MCP ツールが見つかりません', timestamp: new Date().toISOString() }]; }
		} catch (e) { messages = [...messages, { id: `sys-${Date.now()}`, role: 'system', body: `MCP 失敗: ${errorMessage(e)}`, timestamp: new Date().toISOString() }]; }
		finally { chatLoading = false; }
		await tick(); scrollToBottom();
	}

	async function handleInviteDirect(target: string) {
		if (!target) return;
		chatLoading = true;
		try {
			await atProcedureWithSession('com.etzhayyim.projector.addConvoMember', { convoId: convoId, memberDid: target, role: 'member' });
			let displayName = target;
			try { const r = await searchActors(target, { limit: 1 }); displayName = (r?.actors ?? [])[0]?.displayName ?? target; } catch { /* ok */ }
			members = [...members, { did: target, displayName, role: 'member', addedAt: new Date().toISOString() }];
			messages = [...messages, { id: `inv-${Date.now()}`, role: 'system', body: `${displayName} を招待しました`, timestamp: new Date().toISOString() }];
		} catch (e) { messages = [...messages, { id: `sys-${Date.now()}`, role: 'system', body: `招待失敗: ${errorMessage(e)}`, timestamp: new Date().toISOString() }]; }
		finally { chatLoading = false; }
		await tick(); scrollToBottom();
	}

	function handleInviteSearch(query: string) {
		clearTimeout(inviteSearchTimeout);
		if (!query.trim()) { inviteResults = []; return; }
		inviteSearchTimeout = setTimeout(async () => {
			try { const r = await searchActors(query.trim(), { limit: 8 }); inviteResults = (r?.actors ?? []).filter((a: {did:string}) => !members.some(m => m.did === a.did)); } catch { inviteResults = []; }
		}, 250);
	}

	/** Open file picker. */
	function openFilePicker() {
		fileInputRef?.click();
	}

	/** Handle files selected from picker. */
	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const files = Array.from(input.files ?? []);
		input.value = '';
		for (const file of files) {
			if (pendingFiles.length >= MAX_ATTACHMENTS) break;
			if (file.size > MAX_FILE_SIZE) {
				messages = [...messages, { id: `sys-${Date.now()}`, role: 'system', body: `${file.name} は 50MB を超えています`, timestamp: new Date().toISOString() }];
				continue;
			}
			const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : '';
			pendingFiles = [...pendingFiles, { file, previewUrl, uploading: false }];
		}
	}

	/** Remove a pending file. */
	function removePendingFile(idx: number) {
		const removed = pendingFiles[idx];
		if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl);
		pendingFiles = pendingFiles.filter((_, i) => i !== idx);
	}

	/** Upload pending files and send as message. */
	async function uploadAndSend() {
		if (pendingFiles.length === 0 && !composerText.trim()) return;
		sending = true;
		const text = composerText.trim();
		composerText = '';
		showSlashMenu = false;
		if (composerRef) composerRef.style.height = 'auto';

		const attachments: ChatAttachment[] = [];
		const filesToUpload = [...pendingFiles];
		pendingFiles = [];

		// Show user message immediately with local previews
		const msgId = `msg-${Date.now()}`;
		const localAttachments: ChatAttachment[] = filesToUpload.map(f => ({
			type: f.file.type.startsWith('image/') ? 'image' as const : f.file.type.startsWith('video/') ? 'video' as const : 'file' as const,
			name: f.file.name,
			mimeType: f.file.type || 'application/octet-stream',
			size: f.file.size,
			previewUrl: f.previewUrl || undefined,
		}));
		messages = [...messages, {
			id: msgId, role: 'user',
			body: text || (filesToUpload.length === 1 ? filesToUpload[0].file.name : `${filesToUpload.length} files`),
			timestamp: new Date().toISOString(),
			status: 'sending',
			attachments: localAttachments,
		}];
		await tick();
		scrollToBottom();

		// Upload files
		chatLoading = true;
		loadingLabel = 'ファイルをアップロード中...';
		if (filesToUpload.length > 0) {
			const currentDid = await getCurrentDID();
			if (!currentDid) {
				throw new Error('ログインが必要です。再ログインしてください。');
			}
		}
		for (const pf of filesToUpload) {
			try {
				const result = await uploadBlob(pf.file);
				attachments.push({
					type: pf.file.type.startsWith('image/') ? 'image' : pf.file.type.startsWith('video/') ? 'video' : 'file',
					name: pf.file.name,
					mimeType: pf.file.type || 'application/octet-stream',
					size: pf.file.size,
					ref: result.blob.ref,
					url: pf.previewUrl || undefined,
				});
			} catch (e) {
				console.warn('uploadBlob failed:', e);
				messages = [...messages, { id: `sys-${Date.now()}`, role: 'system', body: `${pf.file.name} のアップロードに失敗: ${errorMessage(e)}`, timestamp: new Date().toISOString() }];
			}
		}

		// Build embed for AT Protocol (images / external)
		let embed: Record<string, unknown> | undefined;
		const imageAttachments = attachments.filter(a => a.type === 'image');
		if (imageAttachments.length > 0) {
			embed = {
				$type: 'app.bsky.embed.images',
				images: imageAttachments.map(a => ({ alt: a.name, image: { ref: a.ref, mimeType: a.mimeType, size: a.size } })),
			};
		}

		// Update message with uploaded refs
		messages = messages.map(m => m.id === msgId ? { ...m, status: 'sent' as const, attachments, embed } : m);

		// Send to PDS
		loadingLabel = '応答中...';
		try {
			const payload: Record<string, unknown> = { convoId, text: text || `[ファイル: ${attachments.map(a => a.name).join(', ')}]` };
			if (embed) payload.embed = embed;
			if (attachments.length > 0) payload.attachments = attachments;
			const res = await atProcedureWithSession('com.etzhayyim.projector.sendProjectMessage', payload, { timeout: LLM_TIMEOUT_MS });
			const data = res as Record<string, unknown>;
			const replyText = ((data?.reply as string) ?? '').replace(/<think>[\s\S]*?<\/think>\s*/g, '').trim();
			if (replyText) {
				messages = [...messages, { id: `reply-${Date.now()}`, role: 'assistant', body: replyText, timestamp: new Date().toISOString() }];
			}
		} catch (e) {
			messages = messages.map(m => m.id === msgId ? { ...m, status: 'error' as const } : m);
			messages = [...messages, { id: `err-${Date.now()}`, role: 'system', body: `送信失敗: ${errorMessage(e)}`, timestamp: new Date().toISOString() }];
		} finally {
			chatLoading = false;
			loadingLabel = '';
			sending = false;
		}
		await tick();
		scrollToBottom();
	}

	/** Handle paste events for images. */
	function handlePaste(e: ClipboardEvent) {
		const items = Array.from(e.clipboardData?.items ?? []);
		const imageItems = items.filter(item => item.type.startsWith('image/'));
		if (imageItems.length === 0) return;
		e.preventDefault();
		for (const item of imageItems) {
			if (pendingFiles.length >= MAX_ATTACHMENTS) break;
			const file = item.getAsFile();
			if (!file) continue;
			const previewUrl = URL.createObjectURL(file);
			pendingFiles = [...pendingFiles, { file, previewUrl, uploading: false }];
		}
	}

	/** Handle drag-and-drop files. */
	function handleDrop(e: DragEvent) {
		e.preventDefault();
		const files = Array.from(e.dataTransfer?.files ?? []);
		for (const file of files) {
			if (pendingFiles.length >= MAX_ATTACHMENTS) break;
			if (file.size > MAX_FILE_SIZE) continue;
			const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : '';
			pendingFiles = [...pendingFiles, { file, previewUrl, uploading: false }];
		}
	}

	/** Format file size for display. */
	function formatSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function scrollToBottom() { if (scrollContainer && autoScroll) scrollContainer.scrollTop = scrollContainer.scrollHeight; }
	function handleScroll() { if (scrollContainer) autoScroll = scrollContainer.scrollHeight - scrollContainer.scrollTop - scrollContainer.clientHeight < 80; }
	function formatTime(ts: string): string { return ts ? new Date(ts).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }) : ''; }
	function sendQuickAction(prompt: string) {
		if (!prompt || sending || chatLoading) return;
		void handleSend(prompt);
	}
	function errorMessage(error: unknown, fallback = '不明なエラー'): string {
		if (error instanceof Error && error.message.trim()) return error.message;
		if (typeof error === 'string' && error.trim()) return error;
		if (error && typeof error === 'object') {
			const value = error as Record<string, unknown>;
			const direct = value.message ?? value.detail ?? value.error_description;
			if (typeof direct === 'string' && direct.trim()) return direct;
			if (typeof value.error === 'string' && value.error.trim()) return value.error;
			if (value.error && typeof value.error === 'object') {
				const nested = (value.error as Record<string, unknown>).message;
				if (typeof nested === 'string' && nested.trim()) return nested;
			}
			try {
				const serialized = JSON.stringify(error);
				if (serialized && serialized !== '{}') return serialized;
			} catch {
				// ignore serialization errors
			}
		}
		return fallback;
	}

	function stripToolCallMarkers(body: string): string {
		if (!body) return '';
		return body
			.replace(/\[TOOL_CALL:[\s\S]*?\]/g, '')
			replace(/\n{3,}/g, '\n\n')
			.trim();
	}

	function renderBody(body: string): string {
		const clean = stripToolCallMarkers(body);
		const escaped = clean.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
			.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
			.replace(/`([^`]+)`/g,'<code class="rounded bg-black/10 dark:bg-white/10 px-1 py-0.5 text-[13px] font-mono">$1</code>')
			.replace(/\n/g,'<br/>');
		return escaped.replace(/https?:\/\/[^\s<]+/g, (url) => {
			const cleanUrl = url.replace(/[),.。]+$/g, '');
			const suffix = url.slice(cleanUrl.length);
			const link = `<a href="${cleanUrl}" target="_blank" rel="noreferrer" class="underline decoration-current/30 underline-offset-2 break-all">${cleanUrl}</a>`;
			if (/\.(png|jpe?g|webp|gif)(\?.*)?$/i.test(cleanUrl)) {
				return `${link}<br/><img src="${cleanUrl}" alt="Referenced image" loading="lazy" class="mt-2 max-h-[260px] max-w-full rounded-lg border border-gv2-border/20 object-contain" />${suffix}`;
			}
			return `${link}${suffix}`;
		});
	}
</script>

<svelte:head><title>Project — YORO</title></svelte:head>

<div class="fixed inset-0 flex flex-col bg-gv2-bg-primary z-[60]">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center justify-between border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<div class="flex items-center gap-2">
			<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover" onclick={() => void goto('/projects')} aria-label="Back">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6" /></svg>
			</button>
			<svg class="h-4.5 w-4.5 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 20h.01" /><path d="M7 20v-4" /><path d="M12 20v-8" /><path d="M17 20V8" /><path d="M22 4v16" /></svg>
			<div class="min-w-0">
				{#if parentProjectConvoId}
					<div class="flex items-center gap-1 -mb-0.5">
						<button type="button" class="truncate text-[11px] text-gv2-text-muted/70 hover:text-[#1185FE] transition-colors touch-manipulation font-medium" onclick={() => void goto(`/projects/${encodeURIComponent(parentProjectConvoId)}`)}>
							{parentProjectName || '親プロジェクト'}
						</button>
						<svg class="h-3 w-3 shrink-0 text-gv2-text-muted/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6" /></svg>
					</div>
				{/if}
				<div class="flex items-center gap-1.5">
					{#if projectDid}
						<button type="button" class="truncate text-[17px] font-bold text-gv2-text-primary hover:text-[#1185FE] transition-colors touch-manipulation" onclick={() => void goto(`/profile/${encodeURIComponent(projectDid)}`)}>
							{projectName || 'Project'}
						</button>
					{:else}
						<span class="text-[17px] font-bold text-gv2-text-primary">{projectName || 'Project'}</span>
					{/if}
					{#if projectDid}
						<button type="button" class="text-[11px] text-gv2-text-muted/50 font-mono hover:text-[#1185FE] transition-colors touch-manipulation" onclick={() => void goto(`/profile/${encodeURIComponent(projectDid)}`)}>
							{convoId.slice(0, 8)}
						</button>
					{:else}
						<span class="text-[11px] text-gv2-text-muted/50 font-mono">{convoId.slice(0, 8)}</span>
					{/if}
					<!-- Member-only visibility badge -->
					<span class="flex items-center gap-0.5 rounded-full bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-medium text-amber-500">
						<svg class="h-2.5 w-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
						member only
					</span>
				</div>
				{#if projectEmail}
					<button type="button" class="flex items-center gap-1 mt-0.5 group touch-manipulation" onclick={copyEmail} title="メールをコピー">
						<svg class="h-3 w-3 shrink-0 text-[#F91880]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6" /></svg>
						<span class="truncate text-[11px] text-gv2-text-muted/70 font-mono group-hover:text-gv2-text-primary transition-colors">{projectEmail}</span>
						{#if emailCopied}
							<span class="text-[10px] text-emerald-500 font-medium" in:fade={{ duration: 150 }}>copied!</span>
						{:else}
							<svg class="h-3 w-3 shrink-0 text-gv2-text-muted/40 group-hover:text-[#1185FE] transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
						{/if}
					</button>
				{/if}
			</div>
		</div>
		<button type="button"
			class="flex h-9 items-center gap-1 rounded-full px-2.5 text-[12px] font-medium touch-manipulation transition-colors {showMemberPanel ? 'bg-[#1185FE] text-white' : 'bg-gv2-bg-card text-gv2-text-secondary active:bg-gv2-bg-hover'}"
			onclick={() => { showMemberPanel = !showMemberPanel; }}>
			<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /></svg>
			{members.length || ''}
		</button>
	</div>

	<!-- Member panel -->
	{#if showMemberPanel}
		<div class="border-b border-gv2-border/20 bg-gv2-bg-card/30 max-h-[40vh] overflow-y-auto" transition:slide={{ duration: 200 }}>
			<div class="px-4 pt-3 pb-2">
				<div class="flex items-center gap-2 rounded-xl bg-gv2-bg-primary px-3 py-1.5">
					<input type="text" bind:value={inviteQuery} class="flex-1 bg-transparent text-[14px] text-gv2-text-primary placeholder-gv2-text-muted/50 focus:outline-none" placeholder="DID or handle で招待..."
						oninput={(e) => handleInviteSearch((e.target as HTMLInputElement).value)}
						onkeydown={(e) => { if (e.key === 'Enter' && inviteQuery.trim()) { void handleInviteDirect(inviteQuery.trim()); inviteQuery = ''; } }} />
				</div>
				{#if inviteResults.length > 0}
					<div class="mt-1 rounded-xl bg-gv2-bg-primary divide-y divide-gv2-border/10 max-h-[120px] overflow-y-auto">
						{#each inviteResults as actor (actor.did)}
							<button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left touch-manipulation active:bg-gv2-bg-hover" onclick={() => { void handleInviteDirect(actor.did); inviteQuery=''; inviteResults=[]; }}>
								<Avatar src={actor.avatar} fallback={actor.displayName ?? '?'} size="sm" class="!h-7 !w-7" />
								<span class="truncate text-[13px] text-gv2-text-primary">{actor.displayName ?? actor.did}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
			{#if members.length > 0}
				<div class="divide-y divide-gv2-border/10">
					{#each members as member (member.did)}
						<div class="flex items-center gap-2.5 px-4 py-2">
							<Avatar fallback={member.displayName ?? '?'} size="sm" class="!h-7 !w-7" />
							<p class="truncate text-[13px] text-gv2-text-primary">{member.displayName ?? member.did}</p>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Members strip -->
	{#if members.length > 0}
		<div class="flex items-center gap-1.5 border-b border-gv2-border/10 px-4 py-1.5 overflow-x-auto scrollbar-none">
			<span class="text-[11px] text-gv2-text-muted/60 shrink-0">参加者</span>
			{#each members as member (member.did)}
				<button
					class="flex items-center gap-1 rounded-full bg-gv2-bg-card/60 px-2 py-0.5 text-[11px] text-gv2-text-secondary hover:bg-gv2-bg-card transition-colors shrink-0"
					title={member.did}
					onclick={() => goto(`/profile/${member.did}`)}
				>
					<span class="h-4 w-4 rounded-full bg-gv2-accent/20 text-[9px] font-bold flex items-center justify-center text-gv2-accent">{member.displayName?.slice(0, 1) ?? '?'}</span>
					<span class="max-w-[100px] truncate">{member.displayName ?? shortDid(member.did)}</span>
					<span class="text-[9px] text-gv2-text-muted/40">{member.role === 'owner' ? '👑' : ''}</span>
				</button>
			{/each}
			<span class="text-[10px] text-gv2-text-muted/40 shrink-0">{members.length}人</span>
		</div>
	{/if}

	<!-- Quick action chips: context + per-member -->
	{#if contextQuickActions.length > 0 || memberQuickActions.length > 0}
		<div class="border-b border-gv2-border/10 bg-gv2-bg-card/20 px-3 py-2">
			{#if contextQuickActions.length > 0}
				<div class="mb-2">
					<p class="mb-1 text-[11px] font-medium text-gv2-text-muted/70">文脈の選択肢</p>
					<div class="flex flex-wrap gap-1.5">
						{#each contextQuickActions as action (action.id)}
							<button
								type="button"
								class="rounded-full border border-[#1185FE]/30 bg-[#1185FE]/10 px-2.5 py-1 text-[11px] font-medium text-[#1185FE] touch-manipulation active:opacity-70 disabled:opacity-50"
								disabled={sending || chatLoading}
								onclick={() => sendQuickAction(action.prompt)}
								title={action.prompt}
							>
								{action.label}
							</button>
						{/each}
					</div>
				</div>
			{/if}

			{#if memberQuickActions.length > 0}
				<div class="space-y-1.5">
					{#each memberQuickActions as row (row.member.did)}
						<div>
							<p class="mb-1 text-[11px] font-medium text-gv2-text-muted/70">{memberName(row.member)} の選択肢</p>
							<div class="flex flex-wrap gap-1.5">
								{#each row.actions as action (action.id)}
									<button
										type="button"
										class="rounded-full border border-gv2-border/40 bg-gv2-bg-primary px-2.5 py-1 text-[11px] font-medium text-gv2-text-secondary touch-manipulation active:bg-gv2-bg-hover disabled:opacity-50"
										disabled={sending || chatLoading}
										onclick={() => sendQuickAction(action.prompt)}
										title={action.prompt}
									>
										{action.label}
									</button>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Chat -->
	<div bind:this={scrollContainer} onscroll={handleScroll} class="flex-1 overflow-y-auto scrollbar-none px-4 py-3">
		{#each messages as msg, i (msg.id)}
			{@const isUser = msg.role === 'user'}
			{@const isSystem = msg.role === 'system'}
			{@const prevMsg = i > 0 ? messages[i - 1] : null}
			{@const sameRole = prevMsg?.role === msg.role}

			{#if isSystem}
				<div class="my-2 flex justify-center" in:fade={{ duration: 200 }}>
					<span class="rounded-full bg-gv2-bg-card px-3 py-1 text-[12px] text-gv2-text-muted">{msg.body}</span>
				</div>
			{:else}
				<div class="flex {isUser ? 'justify-end' : 'justify-start'} {sameRole ? 'mt-1' : 'mt-4'}" in:fly={{ y: 10, duration: 200 }}>
					<div class="flex max-w-[85%] gap-2 {isUser ? 'flex-row-reverse' : ''}">
						{#if !sameRole}
							{@const senderMember = msg.sender ? memberLookup.get(msg.sender) : undefined}
							<div class="flex-shrink-0 mt-1">
								{#if isUser && (!msg.sender || msg.sender === selfDid)}
									<Avatar fallback="You" size="sm" class="!h-7 !w-7" />
								{:else if senderMember}
									<Avatar fallback={senderMember.displayName?.slice(0, 2) ?? '??'} size="sm" class="!h-7 !w-7" />
								{:else}
									<div class="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-[#FFD93D] to-[#FF6B6B]" title="yoro">
										<span class="text-[13px] leading-none select-none">Y</span>
									</div>
								{/if}
							</div>
						{:else}<div class="w-7 flex-shrink-0"></div>{/if}
						<div>
							{#if !sameRole}
								<div class="mb-0.5 flex items-baseline gap-2 {isUser ? 'justify-end' : ''}">
									<span class="text-[12px] font-semibold {isUser ? 'text-[#1185FE]' : 'text-gv2-text-primary'}">{senderName(msg)}</span>
									{#if msg.sender && msg.sender !== selfDid}
										<span class="text-[10px] text-gv2-text-muted/60 truncate max-w-[120px]" title={msg.sender}>{shortDid(msg.sender)}</span>
									{/if}
									<span class="text-[10px] text-gv2-text-muted">{formatTime(msg.timestamp)}</span>
								</div>
							{/if}
							<div class="rounded-2xl px-3.5 py-2 text-[14px] leading-relaxed {isUser ? 'bg-[#1185FE] text-white rounded-tr-md' : 'bg-gv2-bg-card text-gv2-text-primary rounded-tl-md'}">
								{#if msg.thinking}
									<!-- Thinking process (collapsible) -->
									<details class="mb-2">
										<summary class="cursor-pointer text-[12px] font-medium text-gv2-text-muted/70 hover:text-gv2-text-muted flex items-center gap-1">
											<svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
											思考過程を表示
										</summary>
										<div class="mt-1.5 rounded-lg bg-black/5 dark:bg-white/5 px-3 py-2 text-[12px] leading-relaxed text-gv2-text-muted whitespace-pre-wrap max-h-[300px] overflow-y-auto">
											{msg.thinking}
										</div>
									</details>
									<div class="border-t border-gv2-border/10 pt-1.5">
										{@html renderBody(msg.body)}
									</div>
								{:else}
									{@html renderBody(msg.body)}
								{/if}
								{#if msg.imageB64}
									<img src="data:image/png;base64,{msg.imageB64}" alt="Generated" class="mt-2 rounded-xl max-w-full max-h-[400px] object-contain" />
								{/if}
								{#if msg.attachments?.length}
									<div class="mt-2 flex flex-wrap gap-2">
										{#each msg.attachments as att, ai (ai)}
											{#if att.type === 'image'}
												<img src={att.previewUrl || att.url || ''} alt={att.name}
													class="rounded-lg max-w-[200px] max-h-[200px] object-cover cursor-pointer border border-gv2-border/20"
													onclick={() => att.previewUrl && window.open(att.previewUrl, '_blank')} />
											{:else}
												<div class="flex items-center gap-2 rounded-lg border border-gv2-border/20 bg-gv2-bg-primary/50 px-3 py-2 text-[13px]">
													<svg class="h-4 w-4 shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
													<div class="min-w-0">
														<p class="truncate font-medium {isUser ? 'text-white/90' : 'text-gv2-text-primary'}">{att.name}</p>
														<p class="text-[11px] {isUser ? 'text-white/60' : 'text-gv2-text-muted'}">{formatSize(att.size)}</p>
													</div>
												</div>
											{/if}
										{/each}
									</div>
								{/if}
								{#if msg.embed}
									<div class="mt-2">
										<PostEmbed embed={msg.embed} />
									</div>
								{/if}
							</div>
							{#if msg.status === 'sending'}<div class="mt-0.5 {isUser ? 'text-right' : ''}"><span class="text-[10px] text-gv2-text-muted/50">送信中...</span></div>{/if}
							{#if msg.status === 'error'}<div class="mt-0.5 {isUser ? 'text-right' : ''}"><span class="text-[10px] text-red-400">送信失敗</span></div>{/if}
						</div>
					</div>
				</div>
			{/if}
		{/each}
		{#if chatLoading}
			<div class="mt-3 flex items-start gap-2" in:fade={{ duration: 150 }}>
				<div class="flex h-7 w-7 items-center justify-center rounded-full bg-[#1185FE]">
					<svg class="h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M2 20h.01" /><path d="M7 20v-4" /><path d="M12 20v-8" /><path d="M17 20V8" /><path d="M22 4v16" /></svg>
				</div>
				<div class="rounded-2xl rounded-tl-md bg-gv2-bg-card px-4 py-3">
					{#if loadingLabel}
						<span class="text-[13px] text-gv2-text-muted">{loadingLabel}</span>
					{/if}
					<div class="flex gap-1 {loadingLabel ? 'mt-1' : ''}">
						<div class="h-2 w-2 animate-bounce rounded-full bg-gv2-text-muted/40" style="animation-delay:0ms"></div>
						<div class="h-2 w-2 animate-bounce rounded-full bg-gv2-text-muted/40" style="animation-delay:150ms"></div>
						<div class="h-2 w-2 animate-bounce rounded-full bg-gv2-text-muted/40" style="animation-delay:300ms"></div>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Sub-projects section (project in project) -->
	<div class="border-t border-gv2-border/20">
		<button type="button"
			class="flex w-full items-center justify-between px-4 py-2 text-left touch-manipulation active:bg-gv2-bg-hover/40"
			onclick={() => { showSubProjects = !showSubProjects; if (showSubProjects && subProjects.length === 0) void loadSubProjects(); }}>
			<div class="flex items-center gap-2">
				<svg class="h-4 w-4 text-[#58CC02]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
				<span class="text-[13px] font-semibold text-gv2-text-primary">サブプロジェクト</span>
				{#if subProjects.length > 0}
					<span class="min-w-[18px] h-[18px] px-1 rounded-full bg-[#58CC02]/10 text-[#58CC02] text-[10px] font-bold flex items-center justify-center">{subProjects.length}</span>
				{/if}
			</div>
			<svg class="h-4 w-4 text-gv2-text-muted/50 transition-transform {showSubProjects ? 'rotate-180' : ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9" /></svg>
		</button>

		{#if showSubProjects}
			<div class="px-4 pb-3" transition:slide={{ duration: 150 }}>
				{#if subProjectsLoading}
					<div class="flex items-center gap-2 py-3 text-[12px] text-gv2-text-muted">
						<div class="h-4 w-4 animate-spin rounded-full border-2 border-gv2-text-muted/20 border-t-gv2-text-muted"></div>
						読み込み中...
					</div>
				{:else}
					<!-- Sub-project list -->
					{#if subProjects.length > 0}
						<div class="space-y-1 mb-2">
							{#each subProjects as sub (sub.convoId)}
								<button type="button"
									class="flex w-full items-center gap-2.5 rounded-xl bg-gv2-bg-card/50 px-3 py-2.5 text-left touch-manipulation active:bg-gv2-bg-hover transition-colors"
									in:fly={{ y: 6, duration: 150 }}
									onclick={() => void goto(`/projects/${encodeURIComponent(sub.convoId)}`)}>
									<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#58CC02]/10">
										<svg class="h-4 w-4 text-[#58CC02]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 20h.01M7 20v-4M12 20v-8M17 20V8M22 4v16" /></svg>
									</div>
									<div class="min-w-0 flex-1">
										<p class="truncate text-[13px] font-medium text-gv2-text-primary">{sub.name}</p>
										{#if sub.did}
											<p class="truncate text-[10px] text-gv2-text-muted/60 font-mono">{sub.did}</p>
										{/if}
									</div>
									{#if (sub.childCount ?? 0) > 0}
										<span class="text-[10px] text-gv2-text-muted/50">{sub.childCount} sub</span>
									{/if}
									<svg class="h-3.5 w-3.5 shrink-0 text-gv2-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6" /></svg>
								</button>
							{/each}
						</div>
					{/if}

					<!-- Create sub-project button -->
					<button type="button"
						class="flex w-full items-center justify-center gap-1.5 rounded-xl border-2 border-dashed border-gv2-border/30 py-2.5 text-[13px] font-medium text-gv2-text-muted touch-manipulation active:border-[#58CC02]/40 active:text-[#58CC02] transition-colors disabled:opacity-50"
						disabled={creatingSubProject}
						onclick={() => void createSubProject()}>
						{#if creatingSubProject}
							<div class="h-4 w-4 animate-spin rounded-full border-2 border-gv2-text-muted/20 border-t-[#58CC02]"></div>
							作成中...
						{:else}
							<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14" /></svg>
							サブプロジェクトを追加
						{/if}
					</button>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Slash menu -->
	{#if showSlashMenu && filteredCommands.length > 0}
		<div class="border-t border-gv2-border/20 bg-gv2-bg-primary" transition:slide={{ duration: 100 }}>
			<div class="max-h-[200px] overflow-y-auto divide-y divide-gv2-border/10">
				{#each filteredCommands as cmd (cmd.name)}
					<button type="button" class="flex w-full items-center gap-3 px-4 py-2.5 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => selectSlashCommand(cmd)}>
						<code class="rounded bg-[#1185FE]/10 px-2 py-0.5 text-[13px] font-mono font-semibold text-[#1185FE]">{cmd.name}</code>
						<span class="text-[13px] text-gv2-text-secondary">{cmd.description}</span>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Composer -->
	<div class="border-t border-gv2-border/40 bg-gv2-bg-primary px-3 pb-[max(env(safe-area-inset-bottom),10px)] pt-2"
		ondragover={(e) => e.preventDefault()} ondrop={handleDrop}>
		<!-- Hidden file input -->
		<input bind:this={fileInputRef} type="file" multiple accept="image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.pptx,.csv,.txt,.json,.zip"
			class="hidden" onchange={handleFileSelect} />

		<!-- Pending file previews -->
		{#if pendingFiles.length > 0}
			<div class="mb-2 flex gap-2 overflow-x-auto scrollbar-none pb-1">
				{#each pendingFiles as pf, pi (pi)}
					<div class="relative shrink-0">
						{#if pf.previewUrl}
							<img src={pf.previewUrl} alt={pf.file.name} class="h-16 w-16 rounded-lg object-cover border border-gv2-border/30" />
						{:else}
							<div class="flex h-16 w-16 flex-col items-center justify-center rounded-lg border border-gv2-border/30 bg-gv2-bg-card px-1">
								<svg class="h-5 w-5 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
								<span class="mt-0.5 max-w-full truncate text-[9px] text-gv2-text-muted">{pf.file.name.split('.').pop()?.toUpperCase()}</span>
							</div>
						{/if}
						<button type="button" class="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-white shadow-sm touch-manipulation"
							onclick={() => removePendingFile(pi)} aria-label="Remove">
							<svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
						</button>
						{#if pf.uploading}
							<div class="absolute inset-0 flex items-center justify-center rounded-lg bg-black/40">
								<div class="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
							</div>
						{/if}
					</div>
				{/each}
				{#if pendingFiles.length < MAX_ATTACHMENTS}
					<button type="button" class="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg border-2 border-dashed border-gv2-border/30 text-gv2-text-muted/40 touch-manipulation active:border-[#1185FE]/40 active:text-[#1185FE]/60"
						onclick={openFilePicker} aria-label="Add file">
						<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
					</button>
				{/if}
			</div>
		{/if}

		<div class="flex items-end gap-2">
			<!-- Attach button -->
			<button type="button"
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gv2-bg-card text-gv2-text-muted touch-manipulation active:text-[#1185FE] active:bg-[#1185FE]/10 transition-colors"
				onclick={openFilePicker} aria-label="ファイルを添付">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
			</button>
			<textarea bind:this={composerRef} bind:value={composerText}
				class="block max-h-[120px] min-h-[44px] min-w-0 flex-1 resize-none rounded-[22px] bg-gv2-bg-card px-4 py-3 text-[15px] leading-tight text-gv2-text-primary placeholder-gv2-text-muted/50 shadow-sm focus:outline-none focus:ring-2 focus:ring-[#1185FE]/40"
				rows="1" placeholder="メッセージ or / でコマンド..."
				oninput={handleComposerInput} onkeydown={handleKeydown} onpaste={handlePaste}></textarea>
			<button type="button"
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all duration-75 touch-manipulation {composerText.trim() || pendingFiles.length > 0 ? 'bg-[#1185FE] text-white shadow-[0_3px_0_rgba(0,0,0,0.2)] active:shadow-none active:translate-y-[3px]' : 'bg-gv2-bg-card text-gv2-text-muted/30'}"
				onclick={() => void handleSend(composerText)} disabled={!composerText.trim() && pendingFiles.length === 0} aria-label="Send">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
			</button>
		</div>
	</div>
</div>
