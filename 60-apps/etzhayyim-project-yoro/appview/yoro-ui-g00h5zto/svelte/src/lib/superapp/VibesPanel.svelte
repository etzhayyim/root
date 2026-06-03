<script lang="ts">
	import { onMount } from 'svelte';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { fade } from 'svelte/transition';
	import { playTabSwitch, playTap, haptic } from '@etzhayyim/design-system/audio';
	import {
		getTimeline,
		getDiscoverFeed,
		likePost,
		unlikePost,
		repost,
		unrepost,
		getSuggestedFeeds,
		getFeed,
	} from '$lib/atproto-agent';
	import { isSignedIn } from '../auth/stores.js';
	import { RichText, PostEmbed, ContentLabel, normalizedPostEmbed } from '../w/index.js';
	import type { FeedItem, PostView, FeedGeneratorView } from '$lib/atproto-agent';

	let feedItems = $state<FeedItem[]>([]);
	let loading = $state(true);
	let feedTab = $state('discover');
	let likedItems = $state<Set<string>>(new Set());
	let repostedItems = $state<Set<string>>(new Set());
	let savedFeeds = $state<FeedGeneratorView[]>([]);
	let activeFeedUri = $state('');

	const defaultTabs = [
		{ id: 'discover', label: 'Discover' },
		{ id: 'following', label: 'Following' },
	];

	let allTabs = $derived([...defaultTabs, ...savedFeeds.map(f => ({ id: f.uri, label: f.displayName }))]);

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) return '';
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}m`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h`;
		const days = Math.floor(hrs / 24);
		if (days < 30) return `${days}d`;
		return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
	}

	async function loadFeed(tab: string) {
		loading = true;
		try {
			let result: any;
			if (tab === 'discover') {
				result = await getDiscoverFeed({ limit: 50, light: true });
			} else if (tab === 'following') {
				result = await getTimeline({ limit: 50, light: true });
			} else {
				// Custom feed URI
				result = await getFeed(tab, { limit: 50 });
			}
			feedItems = Array.isArray(result) ? result : (result?.feed ?? []);
		} catch (e) {
			console.warn('loadFeed failed', e);
			feedItems = [];
		} finally {
			loading = false;
		}
	}

	async function handleLike(post: PostView) {
		const uri = post.uri;
		if (likedItems.has(uri) || post.viewerLike) {
			const next = new Set(likedItems); next.delete(uri); likedItems = next;
			try { await unlikePost(post.viewerLike || uri); } catch (e) { console.warn('unlikePost failed', e); }
		} else {
			likedItems = new Set([...likedItems, uri]);
			try { await likePost(uri, post.cid); } catch (e) { console.warn('likePost failed', e); }
		}
	}

	async function handleRepost(post: PostView) {
		const uri = post.uri;
		if (repostedItems.has(uri) || post.viewerRepost) {
			const next = new Set(repostedItems); next.delete(uri); repostedItems = next;
			try { await unrepost(post.viewerRepost || uri); } catch (e) { console.warn('unrepost failed', e); }
		} else {
			repostedItems = new Set([...repostedItems, uri]);
			try { await repost(uri, post.cid); } catch (e) { console.warn('repost failed', e); }
		}
	}

	function isLiked(post: PostView): boolean {
		return likedItems.has(post.uri) || !!post.viewerLike;
	}

	function isReposted(post: PostView): boolean {
		return repostedItems.has(post.uri) || !!post.viewerRepost;
	}

	$effect(() => {
		void loadFeed(feedTab);
	});

	onMount(async () => {
		try {
			const feeds = await getSuggestedFeeds({ limit: 10 });
			savedFeeds = Array.isArray(feeds) ? feeds : (feeds as any)?.feeds ?? [];
		} catch { /* optional */ }
	});
</script>

<div class="flex h-full flex-col">
	<!-- Feed tabs -->
	<div class="flex border-b border-gv2-border/50 bg-gv2-bg-primary/80 material-blur sticky top-0 z-10 overflow-x-auto scrollbar-none">
		{#each allTabs as tab}
			<button
				type="button"
				class="relative flex-shrink-0 px-4 py-3 text-center text-[14px] font-semibold touch-manipulation transition-all duration-200 active:scale-95 {feedTab === tab.id ? 'text-gv2-text-primary' : 'text-gv2-text-muted active:text-gv2-text-secondary'}"
				onclick={() => { playTabSwitch(); haptic('light'); feedTab = tab.id; }}
			>
				{tab.label}
				{#if feedTab === tab.id}
					<div class="absolute bottom-0 left-2 right-2 h-[3px] rounded-full bg-[var(--gv2-accent,#1185FE)]" style="box-shadow: 0 0 8px 1px var(--gv2-accent, #1185FE)"></div>
				{/if}
			</button>
		{/each}
	</div>

	<!-- Feed content -->
	{#if loading}
		<div class="flex flex-col" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 5 } as _, i}
				<div class="flex gap-2.5 border-b border-gv2-border/20 px-4 py-3">
					<Skeleton variant="circular" class="h-[42px] w-[42px] flex-shrink-0" />
					<div class="flex-1 space-y-2.5 pt-0.5">
						<Skeleton variant="text" class="h-3 w-3/5" />
						<Skeleton variant="text" class="h-4 w-full" />
						<Skeleton variant="text" class="h-4 w-4/5" />
					</div>
				</div>
			{/each}
		</div>
	{:else if feedItems.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 px-8" in:fade={{ duration: 300 }}>
			<p class="text-[17px] font-bold text-gv2-text-primary text-center">No posts yet</p>
			<p class="text-[14px] text-gv2-text-muted text-center">Follow some actors to see their posts here</p>
		</div>
	{:else}
		<div class="divide-y divide-gv2-border/20 overflow-y-auto scrollbar-none">
			{#each feedItems as item (item.post.uri)}
				{@const post = item.post}
				{@const postEmbed = normalizedPostEmbed(post)}
				<div class="flex w-full gap-2.5 px-4 py-3 text-left touch-manipulation transition-colors active:bg-[var(--gv2-accent)]/5">
					{#if item.reason?.type === 'repost'}
						<div class="absolute top-1 left-12 text-[12px] text-gv2-text-muted flex items-center gap-1">
							<svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" /></svg>
							{item.reason.by.displayName} reposted
						</div>
					{/if}
					<div class="flex-shrink-0 pt-0.5">
						<Avatar
							src={post.author.avatar}
							fallback={(post.author.displayName || post.author.handle || '?').slice(0, 2).toUpperCase()}
							size="md"
							class="!h-[42px] !w-[42px]"
						/>
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-baseline gap-1 text-[15px] leading-tight">
							<span class="truncate font-bold text-gv2-text-primary">{post.author.displayName || post.author.handle}</span>
							<span class="min-w-0 truncate text-[14px] text-gv2-text-muted">@{post.author.handle}</span>
							<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">·</span>
							<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">{timeAgo(post.indexedAt)}</span>
						</div>
						{#if post.text}
							<div class="mt-1 text-[15px] leading-[1.5] text-gv2-text-primary whitespace-pre-wrap break-words">
								<RichText text={post.text} facets={post.facets ?? []} />
							</div>
						{/if}
						{#if postEmbed}
							<div class="mt-2">
								<PostEmbed embed={postEmbed} />
							</div>
						{/if}
						{#if post.labels?.length}
							<ContentLabel labels={post.labels} />
						{/if}
						<!-- Action bar -->
						<div class="mt-2 flex items-center text-gv2-text-muted">
							<div class="flex flex-1 items-center">
								<button type="button" class="group -ml-2 flex items-center gap-1 rounded-full px-2 py-1.5 touch-manipulation transition-colors active:bg-[#1185FE]/10" aria-label="Reply">
									<svg class="h-[18px] w-[18px] transition-colors group-active:text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
									{#if post.replyCount}<span class="text-[13px]">{post.replyCount}</span>{/if}
								</button>
								<button
									type="button"
									class="group flex items-center gap-1 rounded-full px-2 py-1.5 touch-manipulation transition-colors active:bg-[#00BA7C]/10 {isReposted(post) ? 'text-[#00BA7C]' : ''}"
									onclick={() => { playTap(); handleRepost(post); }}
									aria-label="Repost"
								>
									<svg class="h-[18px] w-[18px] transition-colors {isReposted(post) ? 'text-[#00BA7C]' : 'group-active:text-[#00BA7C]'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" /></svg>
									{#if post.repostCount}<span class="text-[13px]">{post.repostCount}</span>{/if}
								</button>
								<button
									type="button"
									class="group flex items-center gap-1 rounded-full px-2 py-1.5 touch-manipulation transition-colors active:bg-[#F91880]/10 {isLiked(post) ? 'text-[#F91880]' : ''}"
									onclick={() => { playTap(); handleLike(post); }}
									aria-label="Like"
								>
									<svg class="h-[18px] w-[18px] transition-colors {isLiked(post) ? 'text-[#F91880]' : 'group-active:text-[#F91880]'}" viewBox="0 0 24 24" fill={isLiked(post) ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" /></svg>
									{#if post.likeCount}<span class="text-[13px]">{post.likeCount}</span>{/if}
								</button>
								<div class="flex items-center gap-1 px-2 py-1.5">
									<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>
									{#if post.viewCount > 0}<span class="text-[13px]">{post.viewCount}</span>{/if}
								</div>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
