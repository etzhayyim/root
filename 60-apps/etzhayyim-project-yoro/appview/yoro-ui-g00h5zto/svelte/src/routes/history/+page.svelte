<!--
  /history — Browsing history (Twitter-style access/view history).
  Data stored in Cypher graph via PDS (com.etzhayyim.apps.yoro.browsingHistory).
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { fade } from 'svelte/transition';
	import { getHistory, loadHistory, isHistoryLoaded, isHistoryLoading, removeEntry, clearHistory, type HistoryEntry } from '$lib/history.svelte';

	let filterType = $state<'all' | 'profile' | 'post' | 'search'>('all');
	let showClearConfirm = $state(false);

	const entries = $derived(
		filterType === 'all' ? getHistory() : getHistory().filter((e) => e.type === filterType)
	);

	$effect(() => {
		if (browser && !isHistoryLoaded() && !isHistoryLoading()) {
			void loadHistory();
		}
	});

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return '';
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}分前`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}時間前`;
		const days = Math.floor(hrs / 24);
		if (days < 7) return `${days}日前`;
		return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
	}

	function typeIcon(type: HistoryEntry['type']): string {
		switch (type) {
			case 'profile': return 'profile';
			case 'post': return 'post';
			case 'search': return 'search';
			default: return 'post';
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}

	function handleClearAll() {
		clearHistory();
		showClearConfirm = false;
	}
</script>

<svelte:head>
	<title>閲覧履歴 — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Header -->
	<div class="sticky top-0 z-10 flex items-center gap-3 border-b border-gv2-border/50 bg-gv2-bg-primary/80 px-4 py-3 material-blur">
		<button
			type="button"
			class="rounded-full p-1.5 touch-manipulation active:bg-gv2-bg-hover"
			onclick={goBack}
			aria-label="戻る"
		>
			<svg class="h-5 w-5 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<h1 class="flex-1 text-[17px] font-bold text-gv2-text-primary">閲覧履歴</h1>
		{#if getHistory().length > 0}
			<button
				type="button"
				class="rounded-full px-3 py-1.5 text-[13px] font-medium text-red-500 touch-manipulation active:bg-red-500/10"
				onclick={() => { showClearConfirm = true; }}
			>
				すべて削除
			</button>
		{/if}
	</div>

	<!-- Filter tabs -->
	<div class="flex overflow-x-auto scrollbar-none border-b border-gv2-border/50 bg-gv2-bg-primary">
		{#each [
			{ id: 'all' as const, label: 'すべて' },
			{ id: 'profile' as const, label: 'プロフィール' },
			{ id: 'post' as const, label: '投稿' },
			{ id: 'search' as const, label: '検索' },
		] as tab}
			{@const isActive = filterType === tab.id}
			<button
				type="button"
				class="relative shrink-0 px-4 py-3 text-center text-[14px] font-semibold touch-manipulation transition-colors {isActive
					? 'text-gv2-text-primary'
					: 'text-gv2-text-muted active:text-gv2-text-secondary'}"
				onclick={() => { filterType = tab.id; }}
			>
				{tab.label}
				{#if isActive}
					<div class="absolute bottom-0 left-1/2 h-[3px] w-12 -translate-x-1/2 rounded-full bg-[#1185FE]"></div>
				{/if}
			</button>
		{/each}
	</div>

	<!-- Content -->
	{#if isHistoryLoading() && !isHistoryLoaded()}
		<div class="flex flex-col">
			{#each { length: 6 } as _}
				<div class="flex items-center gap-3 border-b border-gv2-border/20 px-4 py-3">
					<Skeleton variant="circular" class="h-[42px] w-[42px] flex-shrink-0" />
					<div class="flex-1 space-y-2">
						<Skeleton variant="text" class="h-4 w-3/5" />
						<Skeleton variant="text" class="h-3 w-2/5" />
					</div>
				</div>
			{/each}
		</div>
	{:else if entries.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-4 p-8" in:fade={{ duration: 300 }}>
			<div class="flex h-16 w-16 items-center justify-center rounded-full bg-gv2-bg-hover">
				<svg class="h-8 w-8 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
			</div>
			<div class="text-center">
				<h2 class="text-[17px] font-bold text-gv2-text-primary">閲覧履歴がありません</h2>
				<p class="mt-1 text-[14px] text-gv2-text-muted">プロフィールや投稿を閲覧すると、ここに表示されます</p>
			</div>
		</div>
	{:else}
		<div class="divide-y divide-gv2-border/20 overflow-y-auto">
			{#each entries as entry (entry.path + entry.visitedAt)}
				<div
					role="button"
					tabindex="0"
					class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation transition-colors active:bg-gv2-bg-hover/40 cursor-pointer"
					onclick={() => void goto(entry.path)}
					onkeydown={(e) => { if (e.key === 'Enter') void goto(entry.path); }}
				>
					<!-- Avatar / Type icon -->
					{#if entry.avatar}
						<Avatar
							src={entry.avatar}
							fallback={entry.title.slice(0, 2).toUpperCase()}
							size="md"
							class="!h-[42px] !w-[42px] flex-shrink-0"
						/>
					{:else}
						<div class="flex h-[42px] w-[42px] flex-shrink-0 items-center justify-center rounded-full bg-gv2-bg-hover">
							{#if entry.type === 'profile'}
								<svg class="h-5 w-5 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4" /><path d="M20 21a8 8 0 1 0-16 0" /></svg>
							{:else if entry.type === 'search'}
								<svg class="h-5 w-5 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
							{:else}
								<svg class="h-5 w-5 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
							{/if}
						</div>
					{/if}

					<!-- Content -->
					<div class="min-w-0 flex-1">
						<div class="flex items-baseline gap-1">
							<span class="truncate text-[15px] font-semibold text-gv2-text-primary">{entry.title}</span>
							<span class="flex-shrink-0 text-[13px] text-gv2-text-muted">· {timeAgo(entry.visitedAt)}</span>
						</div>
						{#if entry.handle}
							<div class="truncate text-[13px] text-gv2-text-muted">@{entry.handle}</div>
						{/if}
					</div>

					<!-- Delete button -->
					<button
						type="button"
						class="flex-shrink-0 rounded-full p-2 touch-manipulation active:bg-red-500/10"
						onclick={(e) => { e.stopPropagation(); removeEntry(entry.path); }}
						aria-label="削除"
					>
						<svg class="h-4 w-4 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Clear all confirmation modal -->
{#if showClearConfirm}
	<button
		type="button"
		class="fixed inset-0 z-[200] bg-black/50"
		onclick={() => { showClearConfirm = false; }}
		aria-label="閉じる"
		transition:fade={{ duration: 200 }}
	></button>
	<div
		class="fixed left-1/2 top-1/2 z-[201] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-gv2-bg-primary p-6 shadow-2xl"
		transition:fade={{ duration: 200 }}
	>
		<h3 class="text-[17px] font-bold text-gv2-text-primary">閲覧履歴を削除</h3>
		<p class="mt-2 text-[14px] text-gv2-text-muted">すべての閲覧履歴を削除しますか？この操作は取り消せません。</p>
		<div class="mt-4 flex gap-3">
			<button
				type="button"
				class="flex-1 rounded-full border border-gv2-border py-2.5 text-[14px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
				onclick={() => { showClearConfirm = false; }}
			>
				キャンセル
			</button>
			<button
				type="button"
				class="flex-1 rounded-full bg-red-500 py-2.5 text-[14px] font-semibold text-white touch-manipulation active:opacity-80"
				onclick={handleClearAll}
			>
				削除
			</button>
		</div>
	</div>
{/if}
