<script lang="ts">
	/**
	 * PostComposer — Bluesky-style compose modal.
	 *
	 * Design reference: https://github.com/bluesky-social/social-app
	 * Top bar: Cancel | Post button
	 * Body: Avatar + textarea + embeds
	 * Bottom toolbar: Image / Video / Threadgate / Content warning / Character count
	 */
	import { tick } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { Avatar, Chip } from '@etzhayyim/design-system';
	import { playTap, playSuccess } from '@etzhayyim/design-system/audio';
	import { createPost, detectFacets, resolveFacetMentions, uploadBlob, uploadVideo, getVideoJobStatus, setThreadgate, searchActorsTypeahead, atQuery, getCurrentDID } from '$lib/atproto-agent';
	import { getSessionToken } from '$lib/auth/passkey';
	import type { PostView, AuthorProfile, ThreadgateRule } from '$lib/atproto-agent';

	interface QuoteRef {
		uri: string;
		cid: string;
		text?: string;
		author?: { displayName: string; handle: string };
	}

	interface LinkCard {
		uri: string;
		title: string;
		description: string;
		thumb?: string;
	}

	interface Props {
		open?: boolean;
		replyTo?: { root: { uri: string; cid: string }; parent: { uri: string; cid: string } };
		quotePost?: QuoteRef;
		onPost?: (post: PostView) => void;
		onPosted?: (post?: PostView) => void;
		onCancel?: () => void;
		placeholder?: string;
		avatarSrc?: string;
		avatarFallback?: string;
	}

	let { open = $bindable(true), replyTo, quotePost, onPost, onPosted, onCancel, placeholder = "What's happening?", avatarSrc, avatarFallback }: Props = $props();

	let text = $state('');
	let images = $state<Array<{ file: File; preview: string; alt: string }>>([]);
	let posting = $state(false);
	let error = $state('');
	let textareaRef: HTMLTextAreaElement | undefined = $state();
	let fileInputRef: HTMLInputElement | undefined = $state();
	let linkCard = $state<LinkCard | null>(null);
	let linkFetching = $state(false);
	let selfLabel = $state('');
	let lastDetectedUrl = '';
	let videoFile = $state<File | null>(null);
	let videoUploading = $state(false);
	let videoProgress = $state(0);
	let threadgateMode = $state<'everyone' | 'mentioned' | 'following' | 'nobody'>('everyone');
	let videoInputRef: HTMLInputElement | undefined = $state();
	let mentionQuery = $state('');
	let mentionSuggestions = $state<AuthorProfile[]>([]);
	let showMentions = $state(false);
	let mentionStart = $state(-1);

	const MAX_GRAPHEMES = 300;
	const MAX_IMAGES = 4;
	const LABEL_OPTIONS = ['', 'sexual', 'nudity', 'porn', 'gore'];

	// ADR-2604261717 — optional GCC stake on a post. 0 = not staked (default,
	// post behaves identically to today). Cycle through preset GCC amounts on
	// the toolbar toggle. Bond locks into ClaimStakeEscrow after the post
	// commits; AT Record CID is anchored on-chain so federation carries the
	// stake binding.
	const STAKE_OPTIONS = [0, 1, 5, 10] as const;
	let stakeBond = $state<number>(0);
	let stakeNote = $state('');

	const graphemeCount = $derived.by(() => {
		if (typeof Intl?.Segmenter === 'function') {
			return [...new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(text)].length;
		}
		return text.length;
	});
	const remaining = $derived(MAX_GRAPHEMES - graphemeCount);
	const canPost = $derived(text.trim().length > 0 && remaining >= 0 && !posting);

	// Auto-focus textarea when modal opens
	$effect(() => {
		if (open) {
			tick().then(() => textareaRef?.focus());
		}
	});

	function close() {
		open = false;
		onCancel?.();
	}

	function autoResize() {
		if (!textareaRef) return;
		textareaRef.style.height = 'auto';
		textareaRef.style.height = Math.min(textareaRef.scrollHeight, 300) + 'px';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); void handlePost(); }
		if (e.key === 'Escape') { close(); }
	}

	function handleInput() {
		autoResize();
		void detectLinkCard();
		void detectMention();
	}

	async function detectMention() {
		if (!textareaRef) return;
		const pos = textareaRef.selectionStart;
		const before = text.slice(0, pos);
		const match = before.match(/@([\w.]*)$/);
		if (!match || match[1].length < 1) { showMentions = false; mentionSuggestions = []; return; }
		mentionQuery = match[1];
		mentionStart = pos - match[0].length;
		try {
			const res = await searchActorsTypeahead(mentionQuery, { limit: 5 });
			mentionSuggestions = res.actors ?? [];
			showMentions = mentionSuggestions.length > 0;
		} catch { showMentions = false; }
	}

	function insertMention(actor: AuthorProfile) {
		const before = text.slice(0, mentionStart);
		const after = text.slice(textareaRef?.selectionStart ?? mentionStart);
		text = `${before}@${actor.handle} ${after}`;
		showMentions = false;
		mentionSuggestions = [];
		textareaRef?.focus();
	}

	async function detectLinkCard() {
		if (images.length > 0 || quotePost) return;
		const urlMatch = text.match(/https?:\/\/[^\s<>)\]]+/);
		if (!urlMatch) { linkCard = null; lastDetectedUrl = ''; return; }
		const url = urlMatch[0];
		if (url === lastDetectedUrl) return;
		lastDetectedUrl = url;
		linkFetching = true;
		try {
			const data = await atQuery<{ title?: string; description?: string; image?: string }>('app.bsky.embed.getExternalMeta', { url }).catch((_err) => null);
			if (data?.title) linkCard = { uri: url, title: data.title, description: data.description ?? '', thumb: data.image };
		} catch { /* best-effort */ } finally { linkFetching = false; }
	}

	function removeLinkCard() { linkCard = null; lastDetectedUrl = ''; }

	function handleVideoSelect(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (file && file.type.startsWith('video/')) { videoFile = file; images = []; linkCard = null; }
		if (input) input.value = '';
	}

	function removeVideo() { videoFile = null; videoProgress = 0; }

	function handleFileSelect(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		if (!input.files) return;
		for (const file of Array.from(input.files)) {
			if (images.length >= MAX_IMAGES) break;
			if (!file.type.startsWith('image/')) continue;
			images = [...images, { file, preview: URL.createObjectURL(file), alt: '' }];
		}
		if (input) input.value = '';
		linkCard = null;
	}

	function removeImage(idx: number) {
		URL.revokeObjectURL(images[idx].preview);
		images = images.filter((_, i) => i !== idx);
	}

	function updateAlt(idx: number, alt: string) {
		images = images.map((img, i) => i === idx ? { ...img, alt } : img);
	}

	// ADR-2604261717 — POST `com.etzhayyim.claim.postStakedAttestation` against
	// authz.etzhayyim.com. The XRPC handler does gcc.approve + ClaimStakeEscrow.postClaim
	// + tx submit serially. Auth = Passkey-bearer session JWT (same token yoro
	// uses for atproto.etzhayyim.com), forwarded as `Authorization: Bearer <jwt>`.
	async function postStakedAttestation(claim: string, bondGcc: number, atRecordCid: string) {
		const token = await getSessionToken();
		if (!token) throw new Error('not signed in');
		const resp = await fetch('https://authz.etzhayyim.com/xrpc/com.etzhayyim.claim.postStakedAttestation', {
			method: 'POST',
			headers: { 'authorization': `Bearer ${token}`, 'content-type': 'application/json' },
			body: JSON.stringify({ claim, bond: bondGcc.toString(), atRecordCid }),
		});
		if (!resp.ok) {
			const body = await resp.text().catch(() => '');
			throw new Error(`HTTP ${resp.status}: ${body.slice(0, 200)}`);
		}
		return resp.json();
	}

	async function handlePost() {
		if (!canPost) return;
		posting = true;
		error = '';
		playTap();
		try {
			// Auth pre-check: verify session before attempting post
			const currentDid = await getCurrentDID();
			if (!currentDid) {
				throw new Error('ログインが必要です。再ログインしてください。');
			}

			const facets = detectFacets(text);
			await resolveFacetMentions(facets, text);
			let embed: unknown = undefined;
			if (videoFile) {
				videoUploading = true;
				const { jobId } = await uploadVideo(videoFile);
				for (let i = 0; i < 60; i++) {
					const status = await getVideoJobStatus(jobId);
					videoProgress = status.progress ?? 0;
					if (status.state === 'completed' && status.blob) { embed = { $type: 'app.bsky.embed.video', video: status.blob, alt: '' }; break; }
					if (status.state === 'failed') throw new Error(status.error ?? 'Video upload failed');
					await new Promise(r => setTimeout(r, 2000));
				}
				videoUploading = false;
			} else if (images.length > 0) {
				const blobs = await Promise.all(images.map(async (img) => {
					const result = await uploadBlob(img.file);
					return { image: result, alt: img.alt || '' };
				}));
				embed = { $type: 'app.bsky.embed.images', images: blobs };
				if (quotePost) embed = { $type: 'app.bsky.embed.recordWithMedia', record: { $type: 'app.bsky.embed.record', record: { uri: quotePost.uri, cid: quotePost.cid } }, media: embed };
			} else if (quotePost) {
				embed = { $type: 'app.bsky.embed.record', record: { uri: quotePost.uri, cid: quotePost.cid } };
			} else if (linkCard) {
				const external: Record<string, unknown> = { uri: linkCard.uri, title: linkCard.title, description: linkCard.description };
				if (linkCard.thumb) {
					try { const r = await fetch(linkCard.thumb); if (r.ok) { const b = await r.blob(); external.thumb = await uploadBlob(new File([b], 'thumb.jpg', { type: b.type || 'image/jpeg' })); } } catch { /* best-effort */ }
				}
				embed = { $type: 'app.bsky.embed.external', external };
			}
			const labels = selfLabel ? [{ val: selfLabel }] : undefined;
			const post = await createPost(text, { facets: facets.length > 0 ? facets : undefined, replyTo, embed, labels });
			// Validate response: uri must contain a valid DID
			if (!post?.uri) {
				throw new Error('投稿の作成に失敗しました（サーバーから応答がありません）');
			}
			const uriDid = post.uri.replace('at://', '').split('/')[0];
			if (!uriDid) {
				throw new Error('投稿の作成に失敗しました（認証エラー: repo が空です。再ログインしてください）');
			}
			if (threadgateMode !== 'everyone' && post.uri) {
				const rules: ThreadgateRule[] = [];
				if (threadgateMode === 'mentioned') rules.push({ type: 'mentionRule' } as any);
				if (threadgateMode === 'following') rules.push({ type: 'followingRule' } as any);
				await setThreadgate(post.uri, rules).catch(e => console.warn('threadgate failed', e));
			}
			if (stakeBond > 0 && post.uri && post.cid) {
				stakeNote = `Staking ${stakeBond} GCC…`;
				const stakeResult = await postStakedAttestation(text, stakeBond, post.cid).catch((e) => {
					console.warn('claim.postStakedAttestation failed', e);
					stakeNote = `Stake failed: ${e?.message ?? e}`;
					return null;
				});
				if (stakeResult?.claimId) {
					try { window.open(`/claim/${stakeResult.claimId}`, '_blank', 'noopener'); } catch { /* popup blocked OK */ }
				}
			}
			for (const img of images) URL.revokeObjectURL(img.preview);
			text = ''; images = []; videoFile = null; videoProgress = 0; linkCard = null; lastDetectedUrl = ''; selfLabel = ''; threadgateMode = 'everyone'; stakeBond = 0; stakeNote = '';
			if (textareaRef) textareaRef.style.height = 'auto';
			playSuccess();
			onPost?.(post);
			onPosted?.(post);
			open = false;
		} catch (e: any) {
			// Extract meaningful error message from various error shapes
			const msg = e?.message || (typeof e?.error === 'string' ? e.error : null) || (e instanceof Error ? e.message : null);
			if (msg) {
				error = msg;
			} else if (e?.status === 401) {
				error = '認証エラー: ログインが必要です。再ログインしてください。';
			} else if (e?.status) {
				error = `投稿に失敗しました (HTTP ${e.status})`;
			} else {
				error = `投稿に失敗しました: ${typeof e === 'string' ? e : JSON.stringify(e) ?? 'Unknown error'}`;
			}
			console.error('createPost failed:', error, e);
		} finally { posting = false; }
	}
</script>

{#if open}
<!-- Backdrop -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="fixed inset-0 z-[60] bg-black/50"
	transition:fade={{ duration: 150 }}
	onclick={close}
	onkeydown={(e) => { if (e.key === 'Escape') close(); }}
></div>

<!-- Modal -->
<div class="fixed inset-x-0 top-0 z-[61] flex justify-center pt-[10vh] px-4 pointer-events-none" transition:fly={{ y: -30, duration: 200 }}>
<div class="w-full max-w-[600px] rounded-2xl bg-[var(--gv2-bg-primary,#1a1a1a)] border border-[var(--gv2-border,#2f2f2f)] shadow-2xl pointer-events-auto flex flex-col max-h-[80vh]">

	<!-- ═══ Top Bar (Bluesky-style: Cancel ... Post) ═══ -->
	<div class="flex items-center justify-between px-4 py-3 border-b border-[var(--gv2-border,#2f2f2f)]">
		<button
			type="button"
			class="text-[15px] text-[var(--gv2-text-primary,#fff)] touch-manipulation active:opacity-60"
			onclick={close}
		>Cancel</button>
		<button
			type="button"
			class="rounded-full bg-[#1185FE] px-5 py-1.5 text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-40 min-w-[72px]"
			onclick={() => void handlePost()}
			disabled={!canPost}
		>{posting ? 'Posting...' : 'Post'}</button>
	</div>

	<!-- ═══ Error Banner ═══ -->
	{#if error}
		<div class="mx-4 mt-2 rounded-xl bg-red-500/10 border border-red-500/30 px-3 py-2">
			<p class="text-[13px] text-red-400">{error}</p>
		</div>
	{/if}

	<!-- ═══ Composer Body (scrollable) ═══ -->
	<div class="flex-1 overflow-y-auto overscroll-contain px-4 py-3">
		<div class="flex gap-3">
			<!-- Avatar -->
			<Avatar src={avatarSrc} fallback={avatarFallback || 'ME'} size="md" class="shrink-0 !h-[42px] !w-[42px]" />

			<!-- Editor -->
			<div class="flex-1 min-w-0">
				<!-- Text input -->
				<textarea
					bind:this={textareaRef}
					bind:value={text}
					class="block w-full min-h-[120px] max-h-[300px] resize-none bg-transparent text-[17px] leading-snug text-[var(--gv2-text-primary,#fff)] placeholder:text-[var(--gv2-text-muted,#777)]/60 focus:outline-none"
					{placeholder}
					oninput={handleInput}
					onkeydown={handleKeydown}
					disabled={posting}
				></textarea>

				<!-- Mention typeahead -->
				{#if showMentions}
					<div class="mt-1 rounded-xl border border-[var(--gv2-border,#2f2f2f)] bg-[var(--gv2-bg-card,#222)] overflow-hidden max-h-[200px] overflow-y-auto shadow-lg">
						{#each mentionSuggestions as actor}
							<button
								type="button"
								class="flex items-center gap-2.5 w-full px-3 py-2.5 text-left touch-manipulation active:bg-[var(--gv2-bg-hover,#2a2a2a)] transition-colors"
								onclick={() => insertMention(actor)}
							>
								<Avatar src={actor.avatar} fallback={actor.displayName?.slice(0, 2) ?? '?'} size="sm" />
								<div class="min-w-0">
									<div class="text-[14px] font-semibold text-[var(--gv2-text-primary,#fff)] truncate">{actor.displayName}</div>
									<div class="text-[12px] text-[var(--gv2-text-muted,#777)] truncate">@{actor.handle}</div>
								</div>
							</button>
						{/each}
					</div>
				{/if}

				<!-- Quote post preview -->
				{#if quotePost}
					<div class="mt-3 rounded-xl border border-[var(--gv2-border,#2f2f2f)] p-3">
						<div class="flex items-center gap-1.5 text-[13px] text-[var(--gv2-text-muted,#777)]">
							<span class="font-semibold text-[var(--gv2-text-primary,#fff)]">{quotePost.author?.displayName ?? ''}</span>
							<span>@{quotePost.author?.handle ?? ''}</span>
						</div>
						{#if quotePost.text}
							<p class="mt-1 text-[14px] text-[var(--gv2-text-secondary,#aaa)] line-clamp-3">{quotePost.text}</p>
						{/if}
					</div>
				{/if}

				<!-- Link card preview -->
				{#if linkCard && images.length === 0 && !quotePost}
					<div class="mt-3 relative rounded-xl border border-[var(--gv2-border,#2f2f2f)] overflow-hidden">
						{#if linkCard.thumb}
							<img src={linkCard.thumb} alt="" class="w-full h-36 object-cover" />
						{/if}
						<div class="p-3">
							<p class="text-[14px] font-semibold text-[var(--gv2-text-primary,#fff)] line-clamp-2">{linkCard.title}</p>
							{#if linkCard.description}
								<p class="text-[13px] text-[var(--gv2-text-muted,#777)] line-clamp-2 mt-1">{linkCard.description}</p>
							{/if}
							<p class="text-[12px] text-[var(--gv2-text-muted,#555)] mt-1.5 truncate">{linkCard.uri}</p>
						</div>
						<button
							type="button"
							class="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-white touch-manipulation active:bg-black/90"
							onclick={removeLinkCard}
							aria-label="Remove link"
						>
							<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
						</button>
					</div>
				{/if}

				<!-- Image gallery (Bluesky-style: equal-width grid) -->
				{#if images.length > 0}
					<div class="mt-3 grid gap-2 {images.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}">
						{#each images as img, i}
							<div class="relative rounded-xl overflow-hidden bg-[var(--gv2-bg-hover,#252525)] {images.length === 1 ? 'aspect-video' : 'aspect-square'}">
								<img src={img.preview} alt={img.alt || 'attachment'} class="w-full h-full object-cover" />
								<!-- Remove -->
								<button
									type="button"
									class="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-white touch-manipulation active:bg-black/90"
									onclick={() => removeImage(i)}
									aria-label="Remove image"
								>
									<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
								</button>
								<!-- ALT badge -->
								<button
									type="button"
									class="absolute bottom-2 left-2 rounded-md bg-black/70 px-1.5 py-0.5 text-[11px] font-bold text-white touch-manipulation {img.alt ? 'bg-[#1185FE]/80' : ''}"
									onclick={() => {
										const alt = prompt('Alt text:', img.alt);
										if (alt !== null) updateAlt(i, alt);
									}}
								>{img.alt ? 'ALT ✓' : '+ ALT'}</button>
							</div>
						{/each}
					</div>
				{/if}

				<!-- Video preview -->
				{#if videoFile}
					<div class="mt-3 relative rounded-xl bg-[var(--gv2-bg-hover,#252525)] p-3">
						<div class="flex items-center gap-2.5">
							<svg class="h-5 w-5 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" /></svg>
							<span class="text-[14px] text-[var(--gv2-text-primary,#fff)] truncate">{videoFile.name}</span>
							<span class="text-[12px] text-[var(--gv2-text-muted,#777)]">{(videoFile.size / 1048576).toFixed(1)} MB</span>
						</div>
						{#if videoUploading}
							<div class="mt-2 h-1.5 rounded-full bg-[var(--gv2-bg-card,#1a1a1a)] overflow-hidden">
								<div class="h-full bg-[#1185FE] transition-all rounded-full" style="width: {videoProgress}%"></div>
							</div>
						{/if}
						<button type="button" class="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-white touch-manipulation active:bg-black/90" onclick={removeVideo} aria-label="Remove video">
							<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
						</button>
					</div>
				{/if}

				<!-- Stake claim badge (ADR-2604261717) -->
				{#if stakeBond > 0 || stakeNote}
					<div class="mt-3 flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-3 py-2">
						<svg class="h-4 w-4 text-emerald-400 shrink-0" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L4 6v6c0 5 4 9 8 10 4-1 8-5 8-10V6l-8-4z" /></svg>
						<div class="min-w-0 flex-1">
							<div class="text-[12px] font-semibold text-emerald-300">
								{stakeBond > 0 ? `Staking ${stakeBond} GCC` : 'Stake'}
							</div>
							<div class="text-[11px] text-emerald-300/70 truncate">
								{stakeNote || '7-day challenge window. Slashed 85/10/5 if a challenger wins.'}
							</div>
						</div>
						{#if stakeBond > 0 && !stakeNote}
							<button type="button" class="text-[12px] text-[var(--gv2-text-muted,#777)] hover:text-[var(--gv2-text-primary,#fff)]" onclick={() => stakeBond = 0}>Remove</button>
						{/if}
					</div>
				{/if}

				<!-- Content label badge -->
				{#if selfLabel}
					<div class="mt-3 flex items-center gap-2">
						<Chip label={selfLabel} />
						<button type="button" class="text-[12px] text-[var(--gv2-text-muted,#777)] touch-manipulation active:text-[var(--gv2-text-primary,#fff)]" onclick={() => selfLabel = ''}>Remove</button>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- ═══ Bottom Toolbar (Bluesky-style: media buttons | char count) ═══ -->
	<div class="flex items-center justify-between px-4 py-2.5 border-t border-[var(--gv2-border,#2f2f2f)]">
		<div class="flex items-center gap-0.5">
			<!-- Image -->
			<button
				type="button"
				class="flex h-9 w-9 items-center justify-center rounded-full text-[#1185FE] touch-manipulation active:bg-[#1185FE]/10 disabled:opacity-30"
				onclick={() => fileInputRef?.click()}
				disabled={images.length >= MAX_IMAGES || !!videoFile}
				aria-label="Add image"
			>
				<svg class="h-[22px] w-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<rect x="3" y="3" width="18" height="18" rx="2" />
					<circle cx="8.5" cy="8.5" r="1.5" />
					<path d="M21 15l-5-5L5 21" />
				</svg>
			</button>
			<input bind:this={fileInputRef} type="file" accept="image/*" multiple class="hidden" onchange={handleFileSelect} />

			<!-- Video -->
			<button
				type="button"
				class="flex h-9 w-9 items-center justify-center rounded-full text-[#1185FE] touch-manipulation active:bg-[#1185FE]/10 disabled:opacity-30"
				onclick={() => videoInputRef?.click()}
				disabled={!!videoFile || images.length > 0}
				aria-label="Add video"
			>
				<svg class="h-[22px] w-[22px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" /></svg>
			</button>
			<input bind:this={videoInputRef} type="file" accept="video/*" class="hidden" onchange={handleVideoSelect} />

			<!-- Threadgate -->
			<button
				type="button"
				class="flex h-9 items-center gap-1 rounded-full px-2 text-[12px] text-[var(--gv2-text-muted,#777)] touch-manipulation active:bg-[var(--gv2-bg-hover,#252525)]"
				onclick={() => {
					const modes: typeof threadgateMode[] = ['everyone', 'mentioned', 'following', 'nobody'];
					threadgateMode = modes[(modes.indexOf(threadgateMode) + 1) % modes.length];
				}}
				aria-label="Reply settings"
			>
				{#if threadgateMode === 'everyone'}
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" /></svg>
					<span>Everyone</span>
				{:else if threadgateMode === 'mentioned'}
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="M11 8v6M8 11h6" /></svg>
					<span>Mentioned</span>
				{:else if threadgateMode === 'following'}
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" /></svg>
					<span>Following</span>
				{:else}
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></svg>
					<span>Nobody</span>
				{/if}
			</button>

			<!-- Stake claim (ADR-2604261717) -->
			<button
				type="button"
				class="flex h-9 items-center gap-1 rounded-full px-2 text-[12px] touch-manipulation active:bg-[var(--gv2-bg-hover,#252525)] {stakeBond > 0 ? 'text-emerald-400 font-semibold' : 'text-[var(--gv2-text-muted,#777)]'}"
				onclick={() => {
					const idx = STAKE_OPTIONS.indexOf(stakeBond as any);
					stakeBond = STAKE_OPTIONS[(idx + 1) % STAKE_OPTIONS.length];
				}}
				aria-label="Stake claim"
				title={stakeBond > 0 ? `Staking ${stakeBond} GCC — challenge window 7d` : 'Stake this claim with a GCC bond'}
			>
				<svg class="h-4 w-4" viewBox="0 0 24 24" fill={stakeBond > 0 ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2"><path d="M12 2L4 6v6c0 5 4 9 8 10 4-1 8-5 8-10V6l-8-4z" /></svg>
				<span>{stakeBond > 0 ? `${stakeBond} GCC` : 'Stake'}</span>
			</button>

			<!-- Content warning -->
			<button
				type="button"
				class="flex h-9 w-9 items-center justify-center rounded-full touch-manipulation active:bg-[var(--gv2-bg-hover,#252525)] {selfLabel ? 'text-[#F59E0B]' : 'text-[var(--gv2-text-muted,#777)]'}"
				onclick={() => {
					const idx = LABEL_OPTIONS.indexOf(selfLabel);
					selfLabel = LABEL_OPTIONS[(idx + 1) % LABEL_OPTIONS.length];
				}}
				aria-label="Content warning"
				title={selfLabel || 'Add content warning'}
			>
				<svg class="h-[20px] w-[20px]" viewBox="0 0 24 24" fill={selfLabel ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="1.75">
					<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
				</svg>
			</button>
		</div>

		<div class="flex items-center gap-3">
			{#if linkFetching}
				<div class="h-4 w-4 rounded-full border-2 border-[var(--gv2-text-muted,#777)] border-t-transparent animate-spin"></div>
			{/if}

			{#if error}
				<span class="text-[13px] font-medium text-red-400 truncate max-w-[250px]" title={error}>{error}</span>
			{/if}

			<!-- Character counter (Bluesky-style: circular progress for last 20) -->
			{#if graphemeCount > 0}
				{#if remaining <= 20}
					<div class="relative h-6 w-6">
						<svg class="h-6 w-6 -rotate-90" viewBox="0 0 20 20">
							<circle cx="10" cy="10" r="8" fill="none" stroke="var(--gv2-border,#2f2f2f)" stroke-width="2" />
							<circle
								cx="10" cy="10" r="8"
								fill="none"
								stroke={remaining < 0 ? '#ef4444' : remaining < 10 ? '#eab308' : '#1185FE'}
								stroke-width="2"
								stroke-dasharray={2 * Math.PI * 8}
								stroke-dashoffset={2 * Math.PI * 8 * (1 - Math.max(0, remaining) / MAX_GRAPHEMES)}
								stroke-linecap="round"
							/>
						</svg>
						<span class="absolute inset-0 flex items-center justify-center text-[9px] font-bold tabular-nums {remaining < 0 ? 'text-red-500' : remaining < 10 ? 'text-yellow-500' : 'text-[var(--gv2-text-muted,#777)]'}">{remaining}</span>
					</div>
				{:else}
					<div class="relative h-5 w-5">
						<svg class="h-5 w-5 -rotate-90" viewBox="0 0 20 20">
							<circle cx="10" cy="10" r="8" fill="none" stroke="var(--gv2-border,#2f2f2f)" stroke-width="2" />
							<circle
								cx="10" cy="10" r="8"
								fill="none" stroke="#1185FE" stroke-width="2"
								stroke-dasharray={2 * Math.PI * 8}
								stroke-dashoffset={2 * Math.PI * 8 * (1 - graphemeCount / MAX_GRAPHEMES)}
								stroke-linecap="round"
							/>
						</svg>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
</div>
{/if}
