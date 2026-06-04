<!--
  /convo/projects — Project list + recursive tree navigation.
  Root projects at top level. Tap to open sub-projects (channels/threads).
  Each project has DID + auto-generated email. Non-members see 404.
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, tick } from 'svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { isSignedIn } from '$lib/auth/stores.js';
	import { getSessionToken } from '$lib/auth';
	import { atQuery, atProcedure, getCurrentDID, searchActors } from '$lib/atproto-agent';

	// ── Types ──
	interface ProjectConvo {
		convoId: string;
		name: string;
		description?: string;
		kind?: string;
		depth?: number;
		email?: string;
		did?: string;
		parentProjectUri?: string;
		memberCount?: number;
		lastActivity?: string;
		childCount?: number;
		status?: string;
	}

	interface TreeNode {
		convoId: string;
		name: string;
		kind: string;
		depth: number;
		parentProjectUri: string;
		email: string;
		childCount: number;
	}

	/** Unread notification count per project convoId. */
	interface UnreadCount {
		convoId: string;
		unreadCount: number;
	}

	// ── State ──
	let selfDid = $state('');
	let projects = $state<ProjectConvo[]>([]);
	let treeNodes = $state<TreeNode[]>([]);
	let loading = $state(true);
	let error = $state('');
	let currentParentUri = $state('');
	let breadcrumb = $state<Array<{ convoId: string; name: string }>>([]);
	let creating = $state(false);
	let unreadCounts = $state<Map<string, number>>(new Map());
	let showNotifPanel = $state(false);
	let projectNotifications = $state<any[]>([]);

	const KIND_LABELS: Record<string, { label: string; icon: string; color: string }> = {
		general: { label: 'プロジェクト', icon: 'M2 20h.01M7 20v-4M12 20v-8M17 20V8M22 4v16', color: '#1185FE' },
		channel: { label: 'チャンネル', icon: 'M4 9h16M4 15h16M10 3L8 21M16 3l-2 18', color: '#58CC02' },
		thread: { label: 'スレッド', icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', color: '#F59E0B' },
		'email-inbox': { label: 'メール受信', icon: 'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6', color: '#F91880' },
	};

	/** Extract human-readable message from arbitrary thrown value (Error / XRPC error obj / string). */
	function extractErrorMessage(e: unknown): string {
		if (!e) return '不明なエラー';
		if (typeof e === 'string') return e;
		if (e instanceof Error) return e.message;
		if (typeof e === 'object') {
			const o = e as Record<string, unknown>;
			if (typeof o.message === 'string') return o.message;
			if (typeof o.error === 'string') return o.error;
			if (o.error && typeof o.error === 'object') {
				const inner = o.error as Record<string, unknown>;
				if (typeof inner.message === 'string') return inner.message;
			}
			try { return JSON.stringify(e); } catch { /* ignore */ }
		}
		return String(e);
	}

	/** XRPC call with session token. */
	async function atProcedureWithSession<T = Record<string, unknown>>(nsid: string, body?: unknown, opts?: { timeout?: number }): Promise<T> {
		const token = await getSessionToken();
		if (!token) throw new Error('ログインセッションが見つかりません。再ログインしてください。');
		return atProcedure<T>(nsid, body, { bearerToken: token, timeout: opts?.timeout ?? 20_000 });
	}

	/** Load root projects or children of a parent. */
	async function loadProjects(parentUri?: string) {
		loading = true;
		error = '';
		try {
			const payload: Record<string, unknown> = { limit: 50 };
			if (parentUri) payload.parentUri = parentUri;
			const res = await atProcedureWithSession<{ convos: ProjectConvo[]; total: number }>('com.etzhayyim.projector.listProjectConvos', payload);
			const data = typeof res === 'string' ? JSON.parse(res) : res;
			projects = (data?.convos ?? []) as ProjectConvo[];
		} catch (e) {
			console.warn('loadProjects failed:', e);
			const msg = extractErrorMessage(e);
			error = (msg.includes('timed out') || msg.includes('timeout')) ? 'サーバーの応答に時間がかかっています。再試行してください。' : msg;
			projects = [];
		} finally {
			loading = false;
		}
	}

	/** Load full tree for a project (for sidebar/tree view). */
	async function loadTree(convoId: string) {
		try {
			const res = await atProcedureWithSession<{ tree: TreeNode[] }>('com.etzhayyim.projector.listProjectTree', { convoId, maxDepth: 5 });
			const data = typeof res === 'string' ? JSON.parse(res) : res;
			treeNodes = (data?.tree ?? []) as TreeNode[];
		} catch (e) {
			console.warn('loadTree failed:', e);
			treeNodes = [];
		}
	}

	/** Navigate into a sub-project. */
	function navigateInto(project: ProjectConvo) {
		breadcrumb = [...breadcrumb, { convoId: project.convoId, name: project.name }];
		currentParentUri = `at://${selfDid}/com.etzhayyim.projector/${project.convoId}`;
		void loadProjects(currentParentUri);
		void loadTree(project.convoId);
	}

	/** Navigate back in breadcrumb. */
	function navigateBack(index: number) {
		if (index < 0) {
			breadcrumb = [];
			currentParentUri = '';
			treeNodes = [];
			void loadProjects();
		} else {
			const target = breadcrumb[index];
			breadcrumb = breadcrumb.slice(0, index + 1);
			currentParentUri = `at://${selfDid}/com.etzhayyim.projector/${target.convoId}`;
			void loadProjects(currentParentUri);
			void loadTree(target.convoId);
		}
	}

	/** Open project chat page. */
	function openChat(convoId: string) {
		localStorage.setItem('yoro:project-convo-id', convoId);
		void goto(`/projects/${encodeURIComponent(convoId)}`);
	}

	/** Instantly create a new project and navigate to chat. */
	async function handleCreateAndOpen() {
		if (creating) return;
		creating = true;
		try {
			const now = new Date();
			const name = `Project ${now.toLocaleDateString('ja-JP')} ${now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}`;
			const payload: Record<string, unknown> = { name };
			if (currentParentUri) payload.parentProjectUri = currentParentUri;

			const res = await atProcedureWithSession<Record<string, unknown>>('com.etzhayyim.projector.newProjectConvo', payload);
			const parsed = (typeof res === 'string' ? JSON.parse(res) : res) as Record<string, unknown>;
			const convoId = (parsed?.convoId as string) || '';
			if (convoId) {
				localStorage.setItem('yoro:project-convo-id', convoId);
				void goto(`/projects/${encodeURIComponent(convoId)}`);
			} else {
				console.warn('newProjectConvo returned no convoId');
			}
		} catch (e) {
			error = extractErrorMessage(e);
			console.warn('create project failed:', e);
		} finally {
			creating = false;
		}
	}

	// ── Helpers ──
	function formatTime(ts: string): string {
		if (!ts) return '';
		const d = new Date(ts);
		const now = new Date();
		const diff = now.getTime() - d.getTime();
		if (diff < 3600000) return `${Math.floor(diff / 60000)}分前`;
		if (diff < 86400000) return `${Math.floor(diff / 3600000)}時間前`;
		return d.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
	}

	function getKind(kind?: string) {
		return KIND_LABELS[kind || 'general'] || KIND_LABELS.general;
	}

	/** Load unread notification counts per project. */
	async function loadUnreadCounts() {
		try {
			const res = await atProcedureWithSession<{ counts: UnreadCount[] }>('com.etzhayyim.projector.getProjectUnreadCounts', {});
			const data = typeof res === 'string' ? JSON.parse(res) : res;
			const map = new Map<string, number>();
			for (const c of data?.counts ?? []) {
				if (c.unreadCount > 0) map.set(c.convoId, c.unreadCount);
			}
			unreadCounts = map;
		} catch (e) {
			console.warn('loadUnreadCounts failed:', e);
		}
	}

	/** Load cross-project notifications for the notification panel. */
	async function loadProjectNotifications() {
		try {
			const res = await atProcedureWithSession<{ notifications: any[]; unreadCount: number }>('com.etzhayyim.projector.listProjectNotifications', { limit: 30 });
			const data = typeof res === 'string' ? JSON.parse(res) : res;
			projectNotifications = data?.notifications ?? [];
		} catch (e) {
			console.warn('loadProjectNotifications failed:', e);
			projectNotifications = [];
		}
	}

	/** Toggle notification panel and load notifications. */
	function toggleNotifPanel() {
		showNotifPanel = !showNotifPanel;
		if (showNotifPanel && projectNotifications.length === 0) {
			void loadProjectNotifications();
		}
	}

	/** Total unread count across all projects. */
	const totalUnread = $derived(
		Array.from(unreadCounts.values()).reduce((sum, c) => sum + c, 0)
	);

	// ── Lifecycle ──
	onMount(async () => {
		try {
			selfDid = (await getCurrentDID()) ?? '';
		} catch { selfDid = ''; }
		await Promise.all([loadProjects(), loadUnreadCounts()]);
	});
</script>

<svelte:head><title>Projects — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center justify-between border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<div class="flex items-center gap-2">
			<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover" onclick={() => void goto('/projects')} aria-label="Back">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6" /></svg>
			</button>
			<svg class="h-4.5 w-4.5 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 20h.01" /><path d="M7 20v-4" /><path d="M12 20v-8" /><path d="M17 20V8" /><path d="M22 4v16" /></svg>
			<span class="text-[17px] font-bold text-gv2-text-primary">Projects</span>
		</div>
		<div class="flex items-center gap-2">
			<!-- Notification bell -->
			<button type="button"
				class="relative flex h-9 w-9 items-center justify-center rounded-full touch-manipulation active:bg-gv2-bg-hover {showNotifPanel ? 'text-[#1185FE]' : 'text-gv2-text-muted'}"
				onclick={toggleNotifPanel}
				aria-label="通知">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 01-3.46 0" />
				</svg>
				{#if totalUnread > 0}
					<span class="absolute -top-0.5 -right-0.5 min-w-[16px] h-[16px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center leading-none">{totalUnread > 99 ? '99+' : totalUnread}</span>
				{/if}
			</button>
			<!-- New project button -->
			<button type="button"
				class="flex h-9 items-center gap-1.5 rounded-full bg-[#1185FE] px-3 text-[13px] font-semibold text-white touch-manipulation active:opacity-80 disabled:opacity-50"
				disabled={creating}
				onclick={() => void handleCreateAndOpen()}>
				{#if creating}
					<div class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
				{:else}
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14" /></svg>
				{/if}
				{creating ? '作成中...' : '新規'}
			</button>
		</div>
	</div>

	<!-- Notification panel (slide-down) -->
	{#if showNotifPanel}
		<div class="border-b border-gv2-border/30 bg-gv2-bg-card/80 max-h-[280px] overflow-y-auto" transition:slide={{ duration: 200 }}>
			{#if projectNotifications.length === 0}
				<div class="flex items-center justify-center gap-2 py-6 text-[13px] text-gv2-text-muted">
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" /></svg>
					プロジェクト通知はありません
				</div>
			{:else}
				{#each projectNotifications as notif (notif.eventId)}
					<button type="button"
						class="flex w-full items-center gap-3 px-4 py-2.5 text-left touch-manipulation active:bg-gv2-bg-hover/40 border-b border-gv2-border/10 last:border-b-0"
						onclick={() => { if (notif.convoId) openChat(notif.convoId); showNotifPanel = false; }}>
						<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#1185FE]/10">
							{#if notif.activity === 'convo:message'}
								<svg class="h-4 w-4 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
							{:else if notif.activity === 'convo:addMember'}
								<svg class="h-4 w-4 text-[#58CC02]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg>
							{:else}
								<svg class="h-4 w-4 text-[#F59E0B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 20h.01M7 20v-4M12 20v-8M17 20V8M22 4v16" /></svg>
							{/if}
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-[13px] text-gv2-text-primary truncate">{notif.summary}</p>
							<p class="text-[11px] text-gv2-text-muted">{formatTime(notif.timestamp)}</p>
						</div>
					</button>
				{/each}
			{/if}
		</div>
	{/if}

	<!-- Breadcrumb -->
	{#if breadcrumb.length > 0}
		<div class="flex items-center gap-1 border-b border-gv2-border/20 px-4 py-2 overflow-x-auto scrollbar-none" transition:slide={{ duration: 150 }}>
			<button type="button" class="shrink-0 text-[12px] text-[#1185FE] font-medium touch-manipulation" onclick={() => navigateBack(-1)}>
				All Projects
			</button>
			{#each breadcrumb as crumb, i (crumb.convoId)}
				<svg class="h-3 w-3 shrink-0 text-gv2-text-muted/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6" /></svg>
				<button type="button"
					class="shrink-0 text-[12px] font-medium touch-manipulation truncate max-w-[120px] {i === breadcrumb.length - 1 ? 'text-gv2-text-primary' : 'text-[#1185FE]'}"
					onclick={() => navigateBack(i)}>
					{crumb.name}
				</button>
			{/each}
		</div>
	{/if}

	<!-- Tree sidebar (when inside a project) -->
	{#if treeNodes.length > 1}
		<div class="border-b border-gv2-border/20 bg-gv2-bg-card/30 px-3 py-2 max-h-[160px] overflow-y-auto" transition:slide={{ duration: 200 }}>
			{#each treeNodes as node (node.convoId)}
				{@const k = getKind(node.kind)}
				<button type="button"
					class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left touch-manipulation active:bg-gv2-bg-hover/40"
					style="padding-left: {12 + node.depth * 16}px"
					onclick={() => {
						if (node.childCount > 0) {
							const proj: ProjectConvo = { convoId: node.convoId, name: node.name, kind: node.kind };
							navigateInto(proj);
						} else {
							openChat(node.convoId);
						}
					}}>
					<svg class="h-3.5 w-3.5 shrink-0" style="color: {k.color}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="{k.icon}" /></svg>
					<span class="text-[12px] text-gv2-text-primary truncate">{node.name}</span>
					{#if node.childCount > 0}
						<span class="ml-auto text-[10px] text-gv2-text-muted/50">{node.childCount}</span>
					{/if}
				</button>
			{/each}
		</div>
	{/if}

	<!-- Project list -->
	<div class="flex-1 overflow-y-auto scrollbar-none">
		{#if loading}
			<div class="space-y-3 p-4">
				{#each Array(5) as _}
					<div class="flex items-center gap-3 rounded-2xl bg-gv2-bg-card p-4">
						<Skeleton class="!h-10 !w-10 !rounded-xl" />
						<div class="flex-1 space-y-2">
							<Skeleton class="!h-4 !w-2/3" />
							<Skeleton class="!h-3 !w-1/3" />
						</div>
					</div>
				{/each}
			</div>
		{:else if error}
			<div class="flex flex-col items-center justify-center gap-3 p-8">
				<svg class="h-12 w-12 text-gv2-text-muted/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10" /><path d="m15 9-6 6M9 9l6 6" /></svg>
				<p class="text-[14px] text-gv2-text-muted">{error}</p>
				<button type="button" class="rounded-full bg-[#1185FE] px-4 py-2 text-[13px] font-semibold text-white" onclick={() => void loadProjects(currentParentUri || undefined)}>再試行</button>
			</div>
		{:else if projects.length === 0}
			<div class="flex flex-col items-center justify-center gap-4 p-8">
				<div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#1185FE]/10">
					<svg class="h-8 w-8 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 20h.01M7 20v-4M12 20v-8M17 20V8M22 4v16" /></svg>
				</div>
				<div class="text-center">
					<p class="text-[16px] font-semibold text-gv2-text-primary">
						{currentParentUri ? 'サブプロジェクトなし' : 'プロジェクトなし'}
					</p>
					<p class="mt-1 text-[13px] text-gv2-text-muted">
						{currentParentUri ? 'チャンネルやスレッドを作成しましょう' : '最初のプロジェクトを作成しましょう'}
					</p>
				</div>
				<button type="button" class="rounded-full bg-[#1185FE] px-5 py-2.5 text-[14px] font-semibold text-white shadow-[0_3px_0_rgba(0,0,0,0.15)] active:shadow-none active:translate-y-[3px] touch-manipulation"
					onclick={() => void handleCreateAndOpen()}>
					<svg class="mr-1.5 -ml-0.5 inline h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14" /></svg>
					{currentParentUri ? 'サブプロジェクト作成' : 'プロジェクト作成'}
				</button>
			</div>
		{:else}
			<div class="divide-y divide-gv2-border/10">
				{#each projects as project (project.convoId)}
					{@const k = getKind(project.kind)}
					<!-- div role=button (not <button>): the row contains nested action
					     buttons, and button-in-button is invalid HTML (Svelte 5 SSR
					     node_invalid_placement_ssr). -->
					<div role="button" tabindex="0"
						class="flex w-full items-center gap-3 px-4 py-3.5 text-left touch-manipulation active:bg-gv2-bg-hover/40 transition-colors cursor-pointer"
						in:fly={{ y: 8, duration: 200 }}
						onclick={() => openChat(project.convoId)}
						onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openChat(project.convoId); } }}>
						<!-- Kind icon -->
						<div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl" style="background: {k.color}15">
							<svg class="h-5 w-5" style="color: {k.color}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="{k.icon}" /></svg>
						</div>
						<!-- Info -->
						<div class="min-w-0 flex-1">
							<div class="flex items-center gap-2">
								{#if project.did}
									<button type="button" class="truncate text-[15px] font-semibold text-gv2-text-primary hover:text-[#1185FE] transition-colors" onclick={(e) => { e.stopPropagation(); void goto(`/profile/${encodeURIComponent(project.did!)}`); }}>
										{project.name}
									</button>
								{:else}
									<span class="truncate text-[15px] font-semibold text-gv2-text-primary">{project.name}</span>
								{/if}
								{#if unreadCounts.get(project.convoId)}
									<span class="min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center leading-none">{unreadCounts.get(project.convoId)}</span>
								{/if}
								{#if project.status === 'archived'}
									<span class="rounded-full bg-gv2-text-muted/10 px-1.5 py-0.5 text-[10px] text-gv2-text-muted">archived</span>
								{/if}
							</div>
							<div class="mt-0.5 flex items-center gap-2">
								<span class="text-[11px] font-medium" style="color: {k.color}">{k.label}</span>
								{#if project.email}
									<span class="truncate text-[11px] text-gv2-text-muted/60 font-mono">{project.email}</span>
								{/if}
							</div>
							{#if project.description}
								<p class="mt-0.5 truncate text-[12px] text-gv2-text-muted/70">{project.description}</p>
							{/if}
						</div>
						<!-- Right side: child indicator or time -->
						<div class="flex shrink-0 flex-col items-end gap-1">
							{#if project.lastActivity}
								<span class="text-[10px] text-gv2-text-muted/50">{formatTime(project.lastActivity)}</span>
							{/if}
							{#if (project.childCount ?? 0) > 0}
								<button type="button"
									class="flex items-center gap-0.5 rounded-full bg-gv2-bg-card px-2 py-0.5 text-[10px] text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
									onclick={(e) => { e.stopPropagation(); navigateInto(project); }}>
									<span>{project.childCount}</span>
									<svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6" /></svg>
								</button>
							{/if}
							{#if project.memberCount}
								<span class="text-[10px] text-gv2-text-muted/40">{project.memberCount} members</span>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

</div>
