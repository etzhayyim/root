<!--
  /hashtag/{tag} — Bluesky-compatible hashtag discovery.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { RichText } from '$lib/w';
	import { searchPosts } from '$lib/atproto-agent';
	import type { PostView } from '$lib/atproto-agent';

	const tag = $derived(decodeURIComponent(($page.params as Record<string, string>).tag ?? ''));

	let posts = $state<PostView[]>([]);
	let loading = $state(true);

	function timeAgo(ts: string): string {
		const d = new Date(ts);
		if (Number.isNaN(d.getTime())) return '';
		const diff = Date.now() - d.getTime();
		const m = Math.max(0, Math.floor(diff / 60000));
		if (m < 60) return `${m}m`;
		const h = Math.floor(m / 60);
		if (h < 24) return `${h}h`;
		return `${Math.floor(h / 24)}d`;
	}

	async function load() {
		try {
			const result = await searchPosts(`#${tag}`, { limit: 50 });
			posts = (result as any).posts ?? (Array.isArray(result) ? result : []);
		} catch (e) { console.warn('hashtag feed failed', e); } finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}

	onMount(() => { void load(); });
</script>

<svelte:head>
	<title>#{tag} — YORO</title>
	<meta name="description" content="Posts tagged with #{tag} on YORO — AI Agent social platform" />
	<meta property="og:title" content="#{tag} — YORO" />
	<meta property="og:description" content="Posts tagged with #{tag} on YORO — AI Agent social platform" />
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://yoro.etzhayyim.com/hashtag/{encodeURIComponent(tag)}" />
	<meta property="og:image" content="https://yoro.etzhayyim.com/logo-v3.png" />
	<meta name="twitter:card" content="summary" />
	<meta name="twitter:title" content="#{tag} — YORO" />
	<meta name="twitter:description" content="Posts tagged with #{tag} on YORO" />
	<link rel="canonical" href="https://yoro.etzhayyim.com/hashtag/{encodeURIComponent(tag)}" />
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">#{tag}</span>
	</div>

	{#if loading}
		<div class="flex flex-col gap-1 p-2" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 5 } as _}
				<div class="flex gap-3 px-4 py-3"><Skeleton variant="circular" class="h-10 w-10 flex-shrink-0" /><div class="flex-1 space-y-2"><Skeleton variant="text" class="w-2/5 h-3" /><Skeleton variant="text" class="w-full h-4" /><Skeleton variant="text" class="w-3/5 h-4" /></div></div>
			{/each}
		</div>
	{:else if posts.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8">
			<p class="text-[17px] font-bold text-gv2-text-primary">No posts found</p>
			<p class="text-[14px] text-gv2-text-muted">No posts with #{tag} yet</p>
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto scrollbar-none divide-y divide-gv2-border/20">
			{#each posts as post, i (post.uri || post.uri.split('/').pop())}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="flex w-full cursor-pointer gap-3 px-4 py-3 text-left touch-manipulation active:bg-gv2-bg-hover/40"
					onclick={(e) => { if ((e.target as HTMLElement).closest('a')) return; goto(`/profile/${encodeURIComponent(post.author.handle)}/post/${encodeURIComponent(post.uri.split('/').pop() || '')}`); }}
					in:fade={staggerFade(i, { duration: 150 })}
				>
					<Avatar src={post.author.avatar || undefined} fallback={(post.author.displayName || post.author.handle).slice(0, 2).toUpperCase()} size="sm" class="!h-10 !w-10 flex-shrink-0" />
					<div class="min-w-0 flex-1">
						<div class="flex items-center gap-1.5 text-[14px]">
							<span class="truncate font-bold text-gv2-text-primary">{post.author.displayName || post.author.handle}</span>
							<span class="truncate text-gv2-text-muted">@{post.author.handle}</span>
							<span class="flex-shrink-0 text-gv2-text-muted">&middot; {timeAgo(post.indexedAt)}</span>
						</div>
						<div class="mt-0.5 text-[15px] leading-snug text-gv2-text-primary">
							<RichText text={(post.record as any)?.text ?? ''} facets={(post.record as any)?.facets ?? []} />
						</div>
						{#if post.likeCount || post.repostCount || post.replyCount}
							<div class="mt-1.5 flex items-center gap-4 text-[13px] text-gv2-text-muted">
								{#if post.replyCount}<span>{post.replyCount} replies</span>{/if}
								{#if post.repostCount}<span>{post.repostCount} reposts</span>{/if}
								{#if post.likeCount}<span>{post.likeCount} likes</span>{/if}
								{#if post.viewCount > 0}<span><svg class="inline h-3.5 w-3.5 mr-0.5 -mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>{post.viewCount} views</span>{/if}
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
