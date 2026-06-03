<!--
  /embed/post/[handle]/[rkey] — Lightweight iframe-embeddable post view.
  Renders a single post card for oEmbed / external site embedding.
  No header, no nav, no auth — minimal chrome.
-->
<script lang="ts">
	import { Avatar } from '@etzhayyim/design-system';
	import { RichText } from '$lib/w';

	const { data } = $props();
	const post = data.post;
	const handle = data.handle;
	const rkey = data.rkey;
	const profileUrl = `https://yoro.etzhayyim.com/profile/${handle}`;
	const postUrl = `${profileUrl}/post/${rkey}`;

	function timeAgo(ts: string): string {
		if (!ts) return '';
		const d = new Date(ts);
		if (Number.isNaN(d.getTime())) return '';
		const diff = Date.now() - d.getTime();
		const m = Math.floor(diff / 60000);
		if (m < 60) return `${m}m`;
		const h = Math.floor(m / 60);
		if (h < 24) return `${h}h`;
		return `${Math.floor(h / 24)}d`;
	}
</script>

<svelte:head>
	<title>{post?.author?.displayName ?? handle} on YORO</title>
	<style>
		html, body { margin: 0; padding: 0; background: #0a0a0a; color: #fff; font-family: -apple-system, system-ui, sans-serif; }
	</style>
</svelte:head>

{#if post}
	<div style="max-width: 550px; margin: 0 auto; padding: 16px;">
		<a href={postUrl} target="_blank" rel="noopener" style="text-decoration: none; color: inherit; display: block;">
			<!-- Author -->
			<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
				<Avatar src={post.author.avatar} fallback={post.author.displayName?.slice(0, 2) ?? '?'} size="sm" />
				<div>
					<div style="font-size: 14px; font-weight: 700; color: #fff;">{post.author.displayName}</div>
					<div style="font-size: 12px; color: #777;">@{post.author.handle} · {timeAgo(post.indexedAt)}</div>
				</div>
			</div>

			<!-- Text -->
			{#if post.text}
				<p style="font-size: 15px; line-height: 1.5; margin: 0 0 12px; white-space: pre-wrap; word-break: break-word;">{post.text}</p>
			{/if}

			<!-- Embed images -->
			{#if post.embed?.images}
				<div style="display: flex; gap: 4px; border-radius: 12px; overflow: hidden; margin-bottom: 12px;">
					{#each post.embed.images.slice(0, 4) as img}
						<img src={img.thumb || img.fullsize} alt={img.alt || ''} style="flex: 1; min-width: 0; max-height: 200px; object-fit: cover;" />
					{/each}
				</div>
			{/if}

			<!-- Stats -->
			<div style="display: flex; gap: 16px; font-size: 12px; color: #777; padding-top: 8px; border-top: 1px solid #2f2f2f;">
				<span>{post.replyCount} replies</span>
				<span>{post.repostCount} reposts</span>
				<span>{post.likeCount} likes</span>
				{#if post.viewCount > 0}<span><svg style="display:inline;vertical-align:-2px;margin-right:2px" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/></svg>{post.viewCount} views</span>{/if}
			</div>

			<!-- Branding -->
			<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #2f2f2f; font-size: 11px; color: #555;">
				Read on <span style="color: #3b82f6; font-weight: 600;">YORO</span>
			</div>
		</a>
	</div>
{:else}
	<div style="padding: 32px; text-align: center; color: #777; font-size: 14px;">
		Post not found · <a href="https://yoro.etzhayyim.com/profile/{handle}" style="color: #3b82f6;">View profile</a>
	</div>
{/if}
