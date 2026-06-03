<!--
  /tasks/inbox — LangGraph HITL interrupt inbox.
  Polls LangGraph Server for interrupted threads and lets the user allow/deny tool calls.
-->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { fade, fly, slide } from 'svelte/transition';
	import { Skeleton } from '@etzhayyim/design-system';

	const STORAGE_KEY = 'etzhayyim:langgraph-server-url';
	const DEFAULT_SERVER = 'http://127.0.0.1:2024';
	const POLL_MS = 2500;

	interface InterruptedThread {
		thread_id: string;
		created_at: string;
		updated_at: string;
		interrupt: {
			tool_name: string;
			args: Record<string, unknown>;
		} | null;
		resolving: boolean;
	}

	let serverUrl = $state(DEFAULT_SERVER);
	let threads = $state<InterruptedThread[]>([]);
	let loading = $state(true);
	let error = $state('');
	let editingUrl = $state(false);
	let urlInput = $state(DEFAULT_SERVER);
	let pollTimer: ReturnType<typeof setInterval> | null = null;
	let streamingId = $state<string | null>(null);
	let streamLog = $state<string[]>([]);

	function loadServerUrl() {
		try {
			serverUrl = localStorage.getItem(STORAGE_KEY) ?? DEFAULT_SERVER;
			urlInput = serverUrl;
		} catch { /* ignore */ }
	}

	function saveServerUrl() {
		try {
			localStorage.setItem(STORAGE_KEY, urlInput.trim() || DEFAULT_SERVER);
			serverUrl = urlInput.trim() || DEFAULT_SERVER;
		} catch { /* ignore */ }
		editingUrl = false;
		void poll();
	}

	async function fetchInterruptedThreads(): Promise<InterruptedThread[]> {
		const res = await fetch(`${serverUrl}/threads/search`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ status: 'interrupted', limit: 20 }),
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const list: Array<{ thread_id: string; created_at: string; updated_at: string }> = await res.json();

		// Fetch state for each thread to get interrupt value
		const results = await Promise.all(
			list.map(async (t) => {
				try {
					const sr = await fetch(`${serverUrl}/threads/${t.thread_id}/state`);
					if (!sr.ok) return { ...t, interrupt: null, resolving: false };
					const state = await sr.json();
					const iv = state?.interrupts?.[0];
					const interruptValue = iv?.value ?? null;
					return {
						thread_id: t.thread_id,
						created_at: t.created_at,
						updated_at: t.updated_at,
						interrupt: interruptValue
							? {
								tool_name: typeof interruptValue === 'object' ? (interruptValue as Record<string, unknown>).tool_name as string ?? '?' : '?',
								args: typeof interruptValue === 'object' ? (interruptValue as Record<string, unknown>).args as Record<string, unknown> ?? {} : {},
							}
							: null,
						resolving: false,
					};
				} catch {
					return { thread_id: t.thread_id, created_at: t.created_at, updated_at: t.updated_at, interrupt: null, resolving: false };
				}
			})
		);
		return results;
	}

	async function poll() {
		try {
			const fresh = await fetchInterruptedThreads();
			// Preserve resolving state for threads already in the list
			const resolvingIds = new Set(threads.filter((t) => t.resolving).map((t) => t.thread_id));
			threads = fresh.map((t) => ({ ...t, resolving: resolvingIds.has(t.thread_id) }));
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function decide(thread: InterruptedThread, decision: 'allow' | 'deny') {
		thread.resolving = true;
		streamingId = thread.thread_id;
		streamLog = [`→ Sending "${decision}" to thread ${thread.thread_id.slice(0, 8)}...`];

		try {
			const res = await fetch(`${serverUrl}/threads/${thread.thread_id}/runs/stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					command: { resume: decision },
					stream_mode: ['messages', 'updates'],
				}),
			});

			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const reader = res.body?.getReader();
			if (!reader) throw new Error('No response body');

			const decoder = new TextDecoder();
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				const text = decoder.decode(value, { stream: true });
				for (const line of text.split('\n')) {
					if (!line.startsWith('data: ')) continue;
					try {
						const data = JSON.parse(line.slice(6));
						const ev = data?.event ?? '';
						if (ev === 'messages/partial') {
							for (const msg of data?.data ?? []) {
								const chunk = msg?.content ?? '';
								if (chunk && msg?.type?.includes('AI')) {
									streamLog = [...streamLog, chunk];
								}
							}
						}
					} catch { /* ignore parse errors */ }
				}
			}
			streamLog = [...streamLog, `✓ Done`];
		} catch (e) {
			streamLog = [...streamLog, `✗ ${e instanceof Error ? e.message : String(e)}`];
		} finally {
			thread.resolving = false;
			// Remove resolved thread from list immediately
			threads = threads.filter((t) => t.thread_id !== thread.thread_id);
			// Poll to refresh
			setTimeout(() => void poll(), 500);
		}
	}

	function formatTime(ts: string): string {
		if (!ts) return '';
		const d = new Date(ts);
		const diff = Date.now() - d.getTime();
		if (diff < 60000) return `${Math.floor(diff / 1000)}秒前`;
		if (diff < 3600000) return `${Math.floor(diff / 60000)}分前`;
		return d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
	}

	function formatArgs(args: Record<string, unknown>): string {
		return Object.entries(args)
			.map(([k, v]) => `${k}: ${typeof v === 'string' && v.length > 80 ? v.slice(0, 80) + '…' : v}`)
			.join('\n');
	}

	onMount(() => {
		loadServerUrl();
		void poll();
		pollTimer = setInterval(() => void poll(), POLL_MS);
	});

	onDestroy(() => {
		if (pollTimer) clearInterval(pollTimer);
	});
</script>

<svelte:head><title>Task Inbox — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center justify-between border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<div class="flex items-center gap-2">
			<button
				type="button"
				class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
				onclick={() => void goto('/')}
				aria-label="Back">
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6" /></svg>
			</button>
			<!-- Robot icon -->
			<svg class="h-4.5 w-4.5 text-[#F59E0B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<rect x="3" y="11" width="18" height="10" rx="2" />
				<path d="M9 11V7a3 3 0 0 1 6 0v4" />
				<path d="M12 3v2" />
				<circle cx="9" cy="16" r="1" fill="currentColor" />
				<circle cx="15" cy="16" r="1" fill="currentColor" />
			</svg>
			<span class="text-[17px] font-bold text-gv2-text-primary">タスクインボックス</span>
		</div>

		<div class="flex items-center gap-2">
			<!-- Poll indicator -->
			{#if !error}
				<div class="h-2 w-2 animate-pulse rounded-full bg-[#58CC02]"></div>
			{/if}
			<!-- Server URL edit button -->
			<button
				type="button"
				class="flex h-8 items-center gap-1 rounded-full border border-gv2-border/40 px-2.5 text-[11px] text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover font-mono"
				onclick={() => { editingUrl = true; urlInput = serverUrl; }}
				title="LangGraph Server URL">
				{serverUrl.replace('http://', '')}
			</button>
		</div>
	</div>

	<!-- URL edit sheet -->
	{#if editingUrl}
		<div class="border-b border-gv2-border/30 bg-gv2-bg-card/80 px-4 py-3" transition:slide={{ duration: 200 }}>
			<p class="mb-2 text-[12px] text-gv2-text-muted font-medium">LangGraph Server URL</p>
			<div class="flex gap-2">
				<input
					type="url"
					class="flex-1 rounded-xl border border-gv2-border/40 bg-gv2-bg-primary px-3 py-2 text-[13px] font-mono text-gv2-text-primary outline-none focus:border-[#F59E0B]/60"
					bind:value={urlInput}
					placeholder="http://127.0.0.1:2024"
					onkeydown={(e) => { if (e.key === 'Enter') saveServerUrl(); if (e.key === 'Escape') editingUrl = false; }} />
				<button
					type="button"
					class="rounded-xl bg-[#F59E0B] px-3 py-2 text-[13px] font-semibold text-white touch-manipulation active:opacity-80"
					onclick={saveServerUrl}>保存</button>
				<button
					type="button"
					class="rounded-xl border border-gv2-border/40 px-3 py-2 text-[13px] text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
					onclick={() => editingUrl = false}>キャンセル</button>
			</div>
		</div>
	{/if}

	<!-- Stream log -->
	{#if streamingId && streamLog.length > 0}
		<div class="border-b border-gv2-border/30 bg-gv2-bg-card/60 px-4 py-3 max-h-[160px] overflow-y-auto" transition:slide={{ duration: 200 }}>
			<div class="flex items-center justify-between mb-2">
				<p class="text-[11px] font-medium text-[#F59E0B] uppercase tracking-wide">AI Response</p>
				<button type="button" class="text-[11px] text-gv2-text-muted touch-manipulation" onclick={() => { streamingId = null; streamLog = []; }}>閉じる</button>
			</div>
			<div class="space-y-0.5">
				{#each streamLog as line, i (i)}
					<p class="text-[12px] font-mono text-gv2-text-primary/80 whitespace-pre-wrap">{line}</p>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Error banner -->
	{#if error}
		<div class="flex items-center gap-2 border-b border-red-500/20 bg-red-500/10 px-4 py-2.5" transition:fade>
			<svg class="h-4 w-4 shrink-0 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="m15 9-6 6M9 9l6 6" /></svg>
			<p class="flex-1 text-[12px] text-red-400">{error}</p>
			<button type="button" class="text-[11px] text-red-400/70 touch-manipulation" onclick={() => void poll()}>再試行</button>
		</div>
	{/if}

	<!-- Content -->
	<div class="flex-1 overflow-y-auto scrollbar-none">
		{#if loading}
			<div class="space-y-3 p-4">
				{#each Array(3) as _}
					<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-3">
						<Skeleton class="!h-5 !w-1/3" />
						<Skeleton class="!h-4 !w-2/3" />
						<Skeleton class="!h-4 !w-full" />
					</div>
				{/each}
			</div>
		{:else if threads.length === 0}
			<div class="flex flex-col items-center justify-center gap-4 p-8 mt-8" in:fade>
				<div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F59E0B]/10">
					<svg class="h-8 w-8 text-[#F59E0B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<rect x="3" y="11" width="18" height="10" rx="2" />
						<path d="M9 11V7a3 3 0 0 1 6 0v4" />
						<path d="M12 3v2" />
						<circle cx="9" cy="16" r="1" fill="currentColor" />
						<circle cx="15" cy="16" r="1" fill="currentColor" />
					</svg>
				</div>
				<div class="text-center">
					<p class="text-[16px] font-semibold text-gv2-text-primary">承認待ちタスクなし</p>
					<p class="mt-1 text-[13px] text-gv2-text-muted">Terminal Agent がツールを実行する際、<br>ここに承認リクエストが表示されます</p>
				</div>
				<div class="mt-2 rounded-xl border border-gv2-border/30 bg-gv2-bg-card/50 px-4 py-3 max-w-xs w-full">
					<p class="text-[11px] text-gv2-text-muted font-medium mb-1">接続先</p>
					<p class="text-[12px] font-mono text-gv2-text-primary/70">{serverUrl}</p>
					<p class="mt-1.5 text-[10px] text-gv2-text-muted/60">2.5秒ごとにポーリング中</p>
				</div>
			</div>
		{:else}
			<div class="p-3 space-y-3">
				<p class="px-1 text-[12px] text-gv2-text-muted">{threads.length}件の承認待ちタスク</p>
				{#each threads as thread (thread.thread_id)}
					<div class="rounded-2xl border border-[#F59E0B]/20 bg-gv2-bg-card overflow-hidden" in:fly={{ y: 10, duration: 200 }}>
						<!-- Tool header -->
						<div class="flex items-center gap-3 border-b border-gv2-border/20 bg-[#F59E0B]/5 px-4 py-3">
							<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#F59E0B]/15">
								{#if thread.interrupt?.tool_name === 'bash'}
									<svg class="h-4.5 w-4.5 text-[#F59E0B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5" /><line x1="12" y1="19" x2="20" y2="19" /></svg>
								{:else if thread.interrupt?.tool_name === 'write_file'}
									<svg class="h-4.5 w-4.5 text-[#F59E0B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="12" y1="18" x2="12" y2="12" /><line x1="9" y1="15" x2="15" y2="15" /></svg>
								{:else}
									<svg class="h-4.5 w-4.5 text-[#F59E0B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14" /></svg>
								{/if}
							</div>
							<div class="min-w-0 flex-1">
								<p class="text-[14px] font-semibold text-gv2-text-primary">
									{thread.interrupt?.tool_name ?? '不明なツール'}
								</p>
								<p class="text-[11px] text-gv2-text-muted/60 font-mono truncate">
									{thread.thread_id.slice(0, 16)}… · {formatTime(thread.updated_at)}
								</p>
							</div>
						</div>

						<!-- Args -->
						{#if thread.interrupt?.args && Object.keys(thread.interrupt.args).length > 0}
							<div class="px-4 py-3 border-b border-gv2-border/10">
								<p class="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-gv2-text-muted/60">引数</p>
								<pre class="text-[12px] text-gv2-text-primary/80 whitespace-pre-wrap break-all font-mono leading-relaxed">{formatArgs(thread.interrupt.args)}</pre>
							</div>
						{/if}

						<!-- Actions -->
						<div class="flex gap-2 p-3">
							{#if thread.resolving}
								<div class="flex flex-1 items-center justify-center gap-2 py-2">
									<div class="h-4 w-4 animate-spin rounded-full border-2 border-[#F59E0B]/30 border-t-[#F59E0B]"></div>
									<span class="text-[13px] text-gv2-text-muted">処理中...</span>
								</div>
							{:else}
								<button
									type="button"
									class="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-[#58CC02] px-4 py-2.5 text-[14px] font-semibold text-white shadow-[0_2px_0_rgba(0,0,0,0.12)] active:shadow-none active:translate-y-[2px] touch-manipulation"
									onclick={() => void decide(thread, 'allow')}>
									<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12" /></svg>
									許可
								</button>
								<button
									type="button"
									class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-[14px] font-semibold text-red-400 active:bg-red-500/20 touch-manipulation"
									onclick={() => void decide(thread, 'deny')}>
									<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
									拒否
								</button>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
