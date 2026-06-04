<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { spring } from 'svelte/motion';
	import { fade, fly } from 'svelte/transition';
	import { isSignedIn, clerkUser, displayName as clerkDisplayName } from '$lib/auth';
	import { playClick } from '$lib/sound';
	import { playTap } from '@etzhayyim/design-system/audio';
	import { PostComposer } from '$lib/w';
	import { createProjectConvo, followUser, searchActors, atProcedure } from '$lib/atproto-agent';
	import type { AuthorProfile } from '$lib/atproto-agent';
	import { useProviderWorker } from '$lib/provider';
	import { Avatar } from '@etzhayyim/design-system';
	import { getSessionToken } from '$lib/auth';

	const OPS_DID = 'did:web:ops.etzhayyim.com';

	const worker = useProviderWorker();
	const fabScale = spring(1, { stiffness: 0.3, damping: 0.6 });

	let showComposePost = $state(false);
	let showCreditGate = $state(false);
	let showModeSelector = $state(false);
	let showAgentPicker = $state(false);
	let composePlaceholder = $state("What's happening?");
	let agentConnecting = $state(false);
	let errorMessage = $state('');

	// Agent picker state
	let agentQuery = $state('');
	let agentResults = $state<AuthorProfile[]>([]);
	let agentSearching = $state(false);
	let agentInputRef: HTMLInputElement | undefined = $state();
	let searchTimeout: ReturnType<typeof setTimeout> | undefined;

	type ComposeMode = 'agent' | 'post' | 'ask';

	const CREDIT_COST_POST = 1.0;

	const isConvoRoute = $derived($page.url.pathname.startsWith('/projects'));
	const creditBalance = $derived(worker.workerStats.totalEarned);

	/** Create a new project and navigate to its chat. */
	async function createNewProject() {
		agentConnecting = true;
		errorMessage = '';
		try {
			const token = await getSessionToken();
			if (!token) { errorMessage = 'ログインが必要です'; return; }
			const now = new Date();
			const name = `Project ${now.toLocaleDateString('ja-JP')} ${now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}`;
			const res = await atProcedure<Record<string, unknown>>('com.etzhayyim.projector.newProjectConvo', { name }, { bearerToken: token });
			const parsed = (typeof res === 'string' ? JSON.parse(res) : res) as Record<string, unknown>;
			const convoId = (parsed?.convoId as string) || '';
			if (convoId) {
				localStorage.setItem('yoro:project-convo-id', convoId);
				await goto(`/projects/${encodeURIComponent(convoId)}`);
			} else {
				errorMessage = 'プロジェクト作成に失敗しました';
			}
		} catch (e: any) {
			errorMessage = e?.message ?? 'プロジェクト作成に失敗しました';
			console.warn('createNewProject failed', e);
		} finally {
			agentConnecting = false;
		}
	}

	function openModeSelector() {
		errorMessage = '';
		if (isConvoRoute) {
			// On /projects page, create a new project directly
			void createNewProject();
		} else {
			showModeSelector = true;
		}
	}

	function selectMode(mode: ComposeMode) {
		showModeSelector = false;
		if (mode === 'agent') {
			openAgentPicker();
		} else if (mode === 'ask') {
			composePlaceholder = 'Ask anything...';
			openComposePost();
		} else {
			composePlaceholder = "What's happening?";
			openComposePost();
		}
	}

	function openAgentPicker() {
		showAgentPicker = true;
		agentQuery = '';
		agentResults = [];
		// Load suggested agents
		void fetchAgents('etzhayyim');
		requestAnimationFrame(() => agentInputRef?.focus());
	}

	async function fetchAgents(q: string) {
		if (!q.trim()) {
			agentResults = [];
			return;
		}
		agentSearching = true;
		try {
			const result = await searchActors(q, { limit: 20 });
			agentResults = result?.actors ?? [];
		} catch (e) {
			console.warn('searchActors failed', e);
			agentResults = [];
		} finally {
			agentSearching = false;
		}
	}

	function handleAgentSearch(q: string) {
		agentQuery = q;
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => void fetchAgents(q || 'etzhayyim'), 300);
	}

	async function selectAgent(actor: AuthorProfile) {
		const did = actor.did;
		if (!did) return;
		showAgentPicker = false;
		await startAgentConvo(did, actor.displayName ?? '');
	}

	async function startAgentConvo(did: string = OPS_DID, name: string = '') {
		agentConnecting = true;
		errorMessage = '';
		playTap();
		try {
			await followUser(did).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/components/OpsFAB.svelte: suppressed async error", error); });
			const result = await createProjectConvo(did);
			const convoId = result?.convo?.convoId;
			if (convoId) {
				await goto(`/projects/${convoId}`);
			} else {
				errorMessage = `DM 作成に失敗しました${name ? ` (${name})` : ''}`;
				console.warn('Failed to create agent convo', result);
			}
		} catch (e: any) {
			errorMessage = e?.message ?? 'Agent 接続に失敗しました';
			console.warn('startAgentConvo failed', e);
		} finally {
			agentConnecting = false;
		}
	}

	function openComposePost() {
		const isHumanMode = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('mode') === 'human';
		if (isHumanMode && creditBalance < CREDIT_COST_POST) {
			showCreditGate = true;
			return;
		}
		showComposePost = true;
	}
</script>

{#if $isSignedIn && !isConvoRoute}
	<button
		type="button"
		class="fixed bottom-24 right-4 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[#1185FE] text-white shadow-lg tap-target-44 touch-manipulation safe-area-bottom"
		style="transform: scale({$fabScale})"
		onpointerdown={() => fabScale.set(0.85)}
		onpointerup={() => fabScale.set(1)}
		onpointerleave={() => fabScale.set(1)}
		onclick={() => {
			playClick();
			fabScale.set(0.85);
			setTimeout(() => fabScale.set(1.1), 80);
			setTimeout(() => { fabScale.set(1); openModeSelector(); }, 180);
		}}
		aria-label="作成"
		in:fade={{ duration: 200, delay: 300 }}
	>
		{#if isConvoRoute}
			<!-- Message icon on convo pages -->
			<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
		{:else}
			<!-- Plus icon on other pages -->
			<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14" /><path d="M5 12h14" /></svg>
		{/if}
	</button>
{/if}

<!-- Error toast -->
{#if errorMessage}
	<div
		class="fixed bottom-40 left-1/2 z-[80] -translate-x-1/2 rounded-2xl bg-red-500/90 px-5 py-3 text-[14px] font-semibold text-white shadow-lg"
		transition:fly={{ y: 20, duration: 200 }}
	>
		{errorMessage}
		<button type="button" class="ml-3 text-white/70 hover:text-white" onclick={() => { errorMessage = ''; }}>✕</button>
	</div>
{/if}

<!-- Connecting overlay -->
{#if agentConnecting}
	<div class="fixed inset-0 z-[75] flex items-center justify-center bg-black/40" transition:fade={{ duration: 150 }}>
		<div class="flex flex-col items-center gap-3 rounded-3xl bg-[var(--gv2-bg-primary,#1a1a1a)] p-8 shadow-2xl">
			<div class="h-8 w-8 rounded-full border-3 border-[#58CC02] border-t-transparent animate-spin"></div>
			<span class="text-[14px] font-semibold text-[var(--gv2-text-primary,#fff)]">Agent に接続中...</span>
		</div>
	</div>
{/if}

<!-- Agent Picker Bottom Sheet -->
{#if showAgentPicker}
	<button
		type="button"
		class="fixed inset-0 z-[70] bg-black/60"
		onclick={() => { showAgentPicker = false; }}
		aria-label="閉じる"
		transition:fade={{ duration: 150 }}
	></button>
	<div
		class="fixed inset-x-0 bottom-0 z-[71] w-full max-w-[600px] mx-auto rounded-t-3xl bg-[var(--gv2-bg-primary,#1a1a1a)] pb-safe-bottom shadow-2xl"
		style="max-height: 80vh;"
		transition:fly={{ y: 300, duration: 250 }}
	>
		<div class="flex justify-center pt-3 pb-1">
			<div class="h-1 w-10 rounded-full bg-[var(--gv2-border,#2f2f2f)]"></div>
		</div>

		<!-- Search input -->
		<div class="px-4 pt-2 pb-3">
			<h2 class="text-[17px] font-bold text-[var(--gv2-text-primary,#fff)] mb-3">Agent を選択</h2>
			<div class="flex items-center gap-2 rounded-xl bg-[var(--gv2-bg-card,#222)] px-4 py-1">
				<svg class="h-4 w-4 shrink-0 text-[var(--gv2-text-muted,#777)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
				<input
					bind:this={agentInputRef}
					type="text"
					value={agentQuery}
					oninput={(e) => handleAgentSearch(e.currentTarget.value)}
					class="flex-1 bg-transparent py-2.5 text-[15px] text-[var(--gv2-text-primary,#fff)] placeholder-[var(--gv2-text-muted,#555)]/50 focus:outline-none"
					placeholder="Agent を検索..."
				/>
				{#if agentSearching}
					<div class="h-4 w-4 rounded-full border-2 border-[#1185FE] border-t-transparent animate-spin shrink-0"></div>
				{/if}
			</div>
		</div>

		<!-- Quick action: Ops Project Agent -->
		<div class="px-4 pb-2">
			<button
				type="button"
				class="flex w-full items-center gap-3 rounded-2xl bg-[#58CC02]/10 border border-[#58CC02]/30 px-4 py-3 text-left touch-manipulation active:bg-[#58CC02]/20 transition-colors"
				onclick={() => { showAgentPicker = false; void startAgentConvo(OPS_DID, 'Ops PM'); }}
			>
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#58CC02] text-[14px] font-bold text-white">PM</div>
				<div class="flex-1 min-w-0">
					<div class="flex items-center gap-2">
						<span class="text-[14px] font-bold text-[#58CC02]">Ops Project Manager</span>
						<span class="rounded-full bg-[#58CC02]/20 px-2 py-0.5 text-[10px] font-bold text-[#58CC02] uppercase tracking-wider">new project</span>
					</div>
					<p class="text-[12px] text-[var(--gv2-text-muted,#777)] mt-0.5">プロジェクトを作成してタスクを管理</p>
				</div>
				<svg class="h-5 w-5 shrink-0 text-[var(--gv2-text-muted,#555)]" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4l6 6-6 6" /></svg>
			</button>
		</div>

		<!-- Agent results -->
		<div class="flex-1 overflow-y-auto px-4 pb-6 space-y-1" style="max-height: calc(80vh - 200px);">
			{#if agentResults.length === 0 && !agentSearching && agentQuery}
				<p class="py-4 text-center text-[14px] text-[var(--gv2-text-muted,#777)]">Agent が見つかりません</p>
			{/if}
			{#each agentResults as actor (actor.did)}
				<button
					type="button"
					class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left touch-manipulation active:bg-[var(--gv2-bg-hover,#2a2a2a)] transition-colors"
					onclick={() => void selectAgent(actor)}
				>
					<Avatar
						src={actor.avatar}
						fallback={actor.displayName ?? '?'}
						size="sm"
						class="!h-10 !w-10 shrink-0"
					/>
					<div class="flex-1 min-w-0">
						<span class="block truncate text-[14px] font-semibold text-[var(--gv2-text-primary,#fff)]">{actor.displayName ?? actor.handle ?? actor.did}</span>
						{#if actor.description}
							<p class="truncate text-[12px] text-[var(--gv2-text-muted,#777)] mt-0.5">{actor.description}</p>
						{/if}
					</div>
					<svg class="h-4 w-4 shrink-0 text-[var(--gv2-text-muted,#555)]" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4l6 6-6 6" /></svg>
				</button>
			{/each}
		</div>
	</div>
{/if}

<!-- Mode Selector Bottom Sheet (non-convo pages only) -->
{#if showModeSelector}
	<button
		type="button"
		class="fixed inset-0 z-[70] bg-black/60"
		onclick={() => { showModeSelector = false; }}
		aria-label="閉じる"
		transition:fade={{ duration: 150 }}
	></button>
	<div
		class="fixed inset-x-0 bottom-0 z-[71] w-full max-w-[600px] mx-auto rounded-t-3xl bg-[var(--gv2-bg-primary,#1a1a1a)] pb-safe-bottom shadow-2xl"
		transition:fly={{ y: 300, duration: 250 }}
	>
		<div class="flex justify-center pt-3 pb-1">
			<div class="h-1 w-10 rounded-full bg-[var(--gv2-border,#2f2f2f)]"></div>
		</div>
		<div class="px-4 pt-2 pb-6 space-y-2">
			<!-- Agent Mode (default, highlighted) -->
			<button
				type="button"
				class="flex w-full items-center gap-4 rounded-2xl bg-[#58CC02]/10 border border-[#58CC02]/30 px-4 py-4 text-left touch-manipulation active:bg-[#58CC02]/20 transition-colors"
				onclick={() => selectMode('agent')}
			>
				<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#58CC02]">
					<svg class="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 2a4 4 0 014 4v1a4 4 0 01-8 0V6a4 4 0 014-4z" />
						<path d="M6 10h12" />
						<rect x="8" y="14" width="8" height="6" rx="1" />
						<path d="M10 14v6M14 14v6" />
					</svg>
				</div>
				<div class="flex-1 min-w-0">
					<div class="flex items-center gap-2">
						<span class="text-[15px] font-bold text-[#58CC02]">Agent</span>
						<span class="rounded-full bg-[#58CC02]/20 px-2 py-0.5 text-[10px] font-bold text-[#58CC02] uppercase tracking-wider">default</span>
					</div>
					<p class="text-[13px] text-[var(--gv2-text-muted,#777)] mt-0.5">AI Agent を選んで DM で対話する</p>
				</div>
				<svg class="h-5 w-5 shrink-0 text-[var(--gv2-text-muted,#555)]" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4l6 6-6 6" /></svg>
			</button>

			<!-- Post Mode -->
			<button
				type="button"
				class="flex w-full items-center gap-4 rounded-2xl bg-[var(--gv2-bg-card,#222)] px-4 py-4 text-left touch-manipulation active:bg-[var(--gv2-bg-hover,#2a2a2a)] transition-colors"
				onclick={() => selectMode('post')}
			>
				<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#1185FE]">
					<svg class="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 20h9" />
						<path d="M16.5 3.5a2.121 2.121 0 113 3L7 19l-4 1 1-4L16.5 3.5z" />
					</svg>
				</div>
				<div class="flex-1 min-w-0">
					<span class="text-[15px] font-bold text-[var(--gv2-text-primary,#fff)]">Post</span>
					<p class="text-[13px] text-[var(--gv2-text-muted,#777)] mt-0.5">タイムラインに投稿する</p>
				</div>
				<svg class="h-5 w-5 shrink-0 text-[var(--gv2-text-muted,#555)]" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4l6 6-6 6" /></svg>
			</button>

			<!-- Ask Mode -->
			<button
				type="button"
				class="flex w-full items-center gap-4 rounded-2xl bg-[var(--gv2-bg-card,#222)] px-4 py-4 text-left touch-manipulation active:bg-[var(--gv2-bg-hover,#2a2a2a)] transition-colors"
				onclick={() => selectMode('ask')}
			>
				<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#F59E0B]">
					<svg class="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10" />
						<path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
				</div>
				<div class="flex-1 min-w-0">
					<span class="text-[15px] font-bold text-[var(--gv2-text-primary,#fff)]">Ask</span>
					<p class="text-[13px] text-[var(--gv2-text-muted,#777)] mt-0.5">質問を投稿してコミュニティに聞く</p>
				</div>
				<svg class="h-5 w-5 shrink-0 text-[var(--gv2-text-muted,#555)]" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 4l6 6-6 6" /></svg>
			</button>
		</div>
	</div>
{/if}

<PostComposer
	bind:open={showComposePost}
	placeholder={composePlaceholder}
	avatarSrc={$clerkUser?.imageUrl || undefined}
	avatarFallback={($clerkDisplayName || 'U').slice(0, 2).toUpperCase()}
	onPosted={(post) => {
		if (post?.uri) {
			const parts = post.uri.replace('at://', '').split('/');
			const did = parts[0];
			const rkey = parts[2];
			if (did && rkey) goto(`/profile/${encodeURIComponent(did)}/post/${encodeURIComponent(rkey)}`);
		}
	}}
/>

{#if showCreditGate}
	<button
		type="button"
		class="fixed inset-0 z-[70] bg-black/60"
		onclick={() => { showCreditGate = false; }}
		aria-label="閉じる"
		transition:fade={{ duration: 200 }}
	></button>
	<div class="fixed left-1/2 top-1/2 z-[71] w-[90vw] max-w-[360px] -translate-x-1/2 -translate-y-1/2 rounded-3xl bg-gv2-bg-primary p-6 shadow-2xl">
		<div class="flex flex-col items-center gap-4 text-center">
			<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#FFD700]/20 text-[32px]">💰</div>
			<h3 class="text-[20px] font-black text-gv2-text-primary">クレジット不足</h3>
			<p class="text-[14px] text-gv2-text-muted leading-relaxed">
				投稿には {CREDIT_COST_POST} クレジットが必要です。<br/>
				現在の残高: <span class="font-bold text-gv2-text-primary">{creditBalance.toFixed(2)}</span> credits
			</p>
			<div class="w-full rounded-2xl bg-gv2-bg-card/60 p-4">
				<p class="text-[13px] font-bold text-gv2-text-primary mb-2">Murakumo (推論タスク):</p>
				<div class="space-y-1 text-[12px] text-gv2-text-muted">
					<div class="flex justify-between"><span>推論タスク (8B)</span><span class="font-bold text-[#58CC02]">+¥0.1</span></div>
					<div class="flex justify-between"><span>推論タスク (70B)</span><span class="font-bold text-[#58CC02]">+¥0.5</span></div>
					<div class="flex justify-between"><span>蒸留タスク</span><span class="font-bold text-[#58CC02]">+¥5</span></div>
					<div class="flex justify-between"><span>GPU 提供 (1分)</span><span class="font-bold text-[#58CC02]">+¥0.3</span></div>
				</div>
				<p class="text-[13px] font-bold text-gv2-text-primary mt-3 mb-2">hc.etzhayyim.com (人間タスク):</p>
				<div class="space-y-1 text-[12px] text-gv2-text-muted">
					<div class="flex justify-between"><span>翻訳タスク</span><span class="font-bold text-[#58CC02]">+¥3</span></div>
					<div class="flex justify-between"><span>コードレビュー</span><span class="font-bold text-[#58CC02]">+¥5</span></div>
					<div class="flex justify-between"><span>マイクロタスク</span><span class="font-bold text-[#58CC02]">+¥2</span></div>
					<div class="flex justify-between"><span>モデレーション</span><span class="font-bold text-[#58CC02]">+¥1</span></div>
				</div>
			</div>
			<div class="flex w-full gap-2">
				<a href="https://murakumo.etzhayyim.com" class="flex-1 rounded-2xl bg-[#FFD700] py-3 text-center text-[14px] font-black text-gray-900 no-underline shadow-[0_4px_0_#B8960F] touch-manipulation active:shadow-none active:translate-y-[4px] transition-all duration-75">Murakumo</a>
				<a href="https://hc.etzhayyim.com" class="flex-1 rounded-2xl bg-[#58CC02] py-3 text-center text-[14px] font-black text-white no-underline shadow-[0_4px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[4px] transition-all duration-75">HC タスク</a>
			</div>
			<button type="button" class="text-[14px] font-semibold text-gv2-text-muted" onclick={() => { showCreditGate = false; }}>閉じる</button>
		</div>
	</div>
{/if}
