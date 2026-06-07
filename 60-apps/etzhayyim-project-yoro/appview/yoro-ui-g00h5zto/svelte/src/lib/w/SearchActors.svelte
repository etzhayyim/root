<script lang="ts">
	import { searchActors, searchPosts, followUser, createProjectConvo } from '$lib/atproto-agent';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { fade } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { playTap, haptic } from '@etzhayyim/design-system/audio';
	import { RichText } from './index.js';
	import type { PostView, AuthorProfile } from '$lib/atproto-agent';

	type SearchTab = 'actors' | 'posts' | 'people';

	interface Props {
		onSelectActor?: (did: string) => void;
		onSelectPost?: (uri: string) => void;
		/** @deprecated Use onSelectActor */
		onSelectMessage?: (convoId: string, rkey: string) => void;
		/** @deprecated Use onSelectActor */
		onSelectConvo?: (convoId: string) => void;
		onSelectPerson?: (did: string) => void;
		onSelectPage?: (url: string) => void;
	}

	let { onSelectActor, onSelectPost, onSelectPerson, onSelectMessage, onSelectConvo, onSelectPage }: Props = $props();

	let query = $state('');
	let tab = $state<SearchTab>('actors');
	let actorResults = $state<AuthorProfile[]>([]);
	let postResults = $state<PostView[]>([]);
	let loading = $state(false);
	let loadingMore = $state(false);
	let cursor = $state('');
	let hasMore = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;
	let sentinelEl: HTMLDivElement | undefined;
	let observer: IntersectionObserver | undefined;

	const tabs: { key: SearchTab; label: string }[] = [
		{ key: 'actors', label: 'Actors' },
		{ key: 'posts', label: 'Posts' },
		{ key: 'people', label: 'People' },
	];

	function handleInput() {
		if (debounceTimer) clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => void doSearch(), 300);
	}

	async function doSearch() {
		const q = query.trim();
		if (!q && tab !== 'actors') { actorResults = []; postResults = []; cursor = ''; hasMore = false; return; }
		loading = true;
		cursor = '';
		hasMore = false;
		try {
			if (tab === 'actors' || tab === 'people') {
				const result = await searchActors(q, { limit: 25 });
				const res = result as any;
				actorResults = Array.isArray(res) ? res : (res?.actors ?? []);
				cursor = res?.cursor ?? '';
				hasMore = !!cursor;
			} else if (tab === 'posts') {
				const result = await searchPosts(q, { limit: 25 });
				postResults = Array.isArray(result) ? result : (result as any)?.posts ?? [];
			}
		} catch (e) {
			console.warn('search failed', e);
		} finally {
			loading = false;
		}
	}

	async function loadMore() {
		if (loadingMore || !hasMore || !cursor) return;
		if (tab !== 'actors' && tab !== 'people') return;
		loadingMore = true;
		try {
			const q = query.trim();
			const result = await searchActors(q, { limit: 25, cursor });
			const res = result as any;
			const newActors: AuthorProfile[] = Array.isArray(res) ? res : (res?.actors ?? []);
			actorResults = [...actorResults, ...newActors];
			cursor = res?.cursor ?? '';
			hasMore = !!cursor;
		} catch (e) {
			console.warn('loadMore failed', e);
		} finally {
			loadingMore = false;
		}
	}

	onMount(() => {
		if (tab === 'actors') void doSearch();

		observer = new IntersectionObserver((entries) => {
			if (entries[0]?.isIntersecting) void loadMore();
		}, { threshold: 0.1 });

		return () => observer?.disconnect();
	});

	$effect(() => {
		if (sentinelEl && observer) {
			observer.observe(sentinelEl);
			return () => { if (sentinelEl) observer?.unobserve(sentinelEl); };
		}
	});

	let followedDids = $state(new Set<string>());
	let dmBusyDid = $state('');

	async function handleFollowActor(e: Event, did: string) {
		e.stopPropagation();
		if (followedDids.has(did)) return;
		try {
			await followUser(did);
			followedDids = new Set([...followedDids, did]);
		} catch (err) {
			console.warn('search: follow failed', err);
		}
	}

	async function handleDMActor(e: Event, did: string) {
		e.stopPropagation();
		if (dmBusyDid) return;
		dmBusyDid = did;
		try {
			const result = await createProjectConvo(did);
			if (result?.convo?.convoId) {
				await goto(`/projects/${encodeURIComponent(result.convo.convoId)}`, { keepFocus: true, noScroll: true });
			}
		} catch (err) {
			console.warn('search: DM failed', err);
		} finally {
			dmBusyDid = '';
		}
	}

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return '';
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}m`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h`;
		return `${Math.floor(hrs / 24)}d`;
	}
</script>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<div class="border-b border-gv2-border/40 px-4 py-3">
		<input
			class="w-full rounded-2xl bg-gv2-bg-card px-4 py-3 text-[15px] text-gv2-text-primary placeholder-gv2-text-muted/50 outline-none focus:ring-2 focus:ring-[var(--gv2-accent,#1185FE)]/40"
			placeholder="Search actors, posts..."
			bind:value={query}
			oninput={handleInput}
		/>
		<div class="mt-2 flex gap-2 overflow-x-auto scrollbar-none">
			{#each tabs as t (t.key)}
				<button
					type="button"
					class="whitespace-nowrap rounded-full px-3 py-1 text-[13px] font-bold touch-manipulation {tab === t.key ? 'bg-[var(--gv2-accent,#1185FE)] text-white' : 'bg-gv2-bg-card text-gv2-text-muted'}"
					onclick={() => { tab = t.key; void doSearch(); }}
				>{t.label}</button>
			{/each}
		</div>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none">
		{#if loading}
			<div class="p-4 space-y-3" in:fade={staggerFade(0, { duration: 200 })}>
				{#each { length: 5 } as _}
					<div class="flex items-center gap-3">
						<Skeleton variant="circular" class="h-11 w-11" />
						<div class="flex-1 space-y-2">
							<Skeleton variant="text" class="h-4 w-2/5" />
							<Skeleton variant="text" class="h-3 w-4/5" />
						</div>
					</div>
				{/each}
			</div>
		{:else if (tab === 'actors' || tab === 'people') && actorResults.length > 0}
			<div class="divide-y divide-gv2-border/20">
				{#each actorResults as actor (actor.did)}
					<div
						class="flex w-full items-center gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40 cursor-pointer"
						role="button"
						tabindex="0"
						onclick={() => { playTap(); haptic('light'); (onSelectActor ?? onSelectPerson)?.(actor.did); }}
						onkeydown={(e) => { if (e.key === 'Enter') { playTap(); haptic('light'); (onSelectActor ?? onSelectPerson)?.(actor.did); } }}
					>
						<Avatar
							src={actor.avatar}
							fallback={(actor.displayName || actor.handle || '?').slice(0, 2).toUpperCase()}
							size="md"
							class="!h-11 !w-11 flex-shrink-0"
						/>
						<div class="min-w-0 flex-1">
							<div class="flex items-center gap-1.5">
								<span class="truncate text-[15px] font-bold text-gv2-text-primary">{actor.displayName || actor.handle}</span>
							</div>
							<div class="text-[14px] text-gv2-text-muted truncate">@{actor.handle}</div>
							{#if actor.description}
								<p class="mt-0.5 text-[13px] text-gv2-text-secondary line-clamp-2">{actor.description}</p>
							{/if}
						</div>
						<div class="flex flex-shrink-0 items-center gap-1.5">
							<button
								type="button"
								class="rounded-full px-3 py-1 text-[12px] font-semibold touch-manipulation active:opacity-80 {followedDids.has(actor.did) ? 'bg-gv2-bg-hover text-gv2-text-muted' : 'bg-[#1185FE] text-white'}"
								onclick={(e) => handleFollowActor(e, actor.did)}
							>{followedDids.has(actor.did) ? 'Following' : 'Follow'}</button>
							<button
								type="button"
								class="rounded-full px-3 py-1 text-[12px] font-semibold bg-gv2-bg-card text-gv2-text-primary touch-manipulation active:opacity-80"
								onclick={(e) => handleDMActor(e, actor.did)}
								disabled={dmBusyDid === actor.did}
							>{dmBusyDid === actor.did ? '...' : 'DM'}</button>
						</div>
					</div>
				{/each}

				<!-- Infinite scroll sentinel -->
				{#if hasMore}
					<div bind:this={sentinelEl} class="py-4 flex justify-center">
						{#if loadingMore}
							<div class="flex items-center gap-3 px-4">
								<Skeleton variant="circular" class="h-9 w-9" />
								<div class="flex-1 space-y-2 w-40">
									<Skeleton variant="text" class="h-4 w-3/5" />
									<Skeleton variant="text" class="h-3 w-full" />
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{:else if tab === 'posts' && postResults.length > 0}
			<div class="divide-y divide-gv2-border/20">
				{#each postResults as post (post.uri)}
					<button
						type="button"
						class="flex w-full gap-2.5 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40"
						onclick={() => { playTap(); haptic('light'); onSelectPost?.(post.uri); }}
					>
						<Avatar
							src={post.author.avatar}
							fallback={(post.author.displayName ?? '?').slice(0, 2).toUpperCase()}
							size="md"
							class="!h-10 !w-10 flex-shrink-0"
						/>
						<div class="min-w-0 flex-1">
							<div class="flex items-baseline gap-1">
								<span class="truncate text-[14px] font-bold text-gv2-text-primary">{post.author.displayName}</span>
								<span class="text-[13px] text-gv2-text-muted">@{post.author.handle}</span>
								<span class="text-[13px] text-gv2-text-muted">· {timeAgo(post.indexedAt)}</span>
							</div>
							<div class="mt-0.5 text-[14px] text-gv2-text-primary line-clamp-3">
								<RichText text={(post.record as any)?.text ?? ''} facets={(post.record as any)?.facets ?? []} />
							</div>
						</div>
					</button>
				{/each}
			</div>
		{:else if query.trim()}
			<div class="flex flex-col items-center justify-center py-20 text-center">
				<p class="text-[15px] text-gv2-text-muted">No results</p>
			</div>
		{:else if tab !== 'actors'}
			<div class="flex flex-col items-center justify-center py-20 text-center">
				<p class="text-[15px] text-gv2-text-muted">Search for actors or posts</p>
			</div>
		{:else}
			<div class="flex flex-col items-center justify-center py-20 text-center">
				<p class="text-[15px] text-gv2-text-muted">No actors available</p>
			</div>
		{/if}
	</div>
</div>
