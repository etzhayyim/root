<script lang="ts">
	interface PostEmbed {
		type: 'images' | 'external' | 'record' | 'video';
		images?: Array<{ thumb: string; fullsize: string; alt?: string }>;
		external?: { uri: string; title: string; description: string; thumb?: string };
		record?: { uri: string; cid: string; text?: string; author?: { did: string; handle: string; displayName: string; avatar?: string } };
		video?: { thumb?: string; playlist?: string; alt?: string };
	}

	interface Props {
		embed: PostEmbed;
		class?: string;
	}

	let { embed, class: className = '' }: Props = $props();

	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	function openLightbox(index: number) {
		lightboxIndex = index;
		lightboxOpen = true;
	}
</script>

{#if embed.type === 'images' && embed.images?.length}
	<div class="mt-2 {className}" data-testid="post-embed-images">
		{#if embed.images.length === 1}
			<button type="button" class="w-full overflow-hidden rounded-xl bg-black/5 dark:bg-white/5" onclick={(e) => { e.stopPropagation(); openLightbox(0); }}>
				<img
					src={embed.images[0].thumb}
					alt={embed.images[0].alt || ''}
					data-testid="post-embed-image"
					class="mx-auto max-w-full max-h-[500px] object-contain"
					loading="lazy"
				/>
			</button>
		{:else if embed.images.length === 2}
			<div class="grid grid-cols-2 gap-0.5 overflow-hidden rounded-xl">
				{#each embed.images as img, i}
					<button type="button" class="overflow-hidden" onclick={(e) => { e.stopPropagation(); openLightbox(i); }}>
						<img src={img.thumb} alt={img.alt || ''} data-testid="post-embed-image" class="h-[200px] w-full object-cover" loading="lazy" />
					</button>
				{/each}
			</div>
		{:else if embed.images.length === 3}
			<div class="grid grid-cols-2 gap-0.5 overflow-hidden rounded-xl">
				<button type="button" class="row-span-2 overflow-hidden" onclick={(e) => { e.stopPropagation(); openLightbox(0); }}>
					<img src={embed.images[0].thumb} alt={embed.images[0].alt || ''} data-testid="post-embed-image" class="h-full w-full object-cover" loading="lazy" />
				</button>
				{#each embed.images.slice(1) as img, i}
					<button type="button" class="overflow-hidden" onclick={(e) => { e.stopPropagation(); openLightbox(i + 1); }}>
						<img src={img.thumb} alt={img.alt || ''} data-testid="post-embed-image" class="h-[150px] w-full object-cover" loading="lazy" />
					</button>
				{/each}
			</div>
		{:else}
			<div class="grid grid-cols-2 gap-0.5 overflow-hidden rounded-xl">
				{#each embed.images.slice(0, 4) as img, i}
					<button type="button" class="overflow-hidden" onclick={(e) => { e.stopPropagation(); openLightbox(i); }}>
						<img src={img.thumb} alt={img.alt || ''} data-testid="post-embed-image" class="aspect-square w-full object-cover" loading="lazy" />
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Lightbox -->
	{#if lightboxOpen && embed.images}
		<div
			class="fixed inset-0 z-[100] flex items-center justify-center bg-black/90"
			role="dialog"
			onclick={() => { lightboxOpen = false; }}
			onkeydown={(e) => { if (e.key === 'Escape') lightboxOpen = false; }}
		>
			<button type="button" class="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white touch-manipulation active:bg-white/20" onclick={() => { lightboxOpen = false; }} aria-label="閉じる">
				<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
			</button>
			<img
				src={embed.images[lightboxIndex]?.fullsize || embed.images[lightboxIndex]?.thumb}
				alt={embed.images[lightboxIndex]?.alt || ''}
				class="max-h-[90vh] max-w-[90vw] object-contain"
				onclick={(e) => e.stopPropagation()}
			/>
			{#if embed.images.length > 1}
				<div class="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-1.5">
					{#each embed.images as _, i}
						<button
							type="button"
							class="h-2 w-2 rounded-full transition-colors {i === lightboxIndex ? 'bg-white' : 'bg-white/40'}"
							onclick={(e) => { e.stopPropagation(); lightboxIndex = i; }}
						></button>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
{:else if embed.type === 'video' && embed.video}
	<div class="mt-2 overflow-hidden rounded-xl {className}">
		{#if embed.video.playlist}
			<video
				src={embed.video.playlist}
				poster={embed.video.thumb}
				controls
				playsinline
				class="w-full max-h-[400px]"
				preload="none"
			>
				<track kind="captions" />
			</video>
		{:else if embed.video.thumb}
			<div class="relative">
				<img src={embed.video.thumb} alt={embed.video.alt || ''} class="w-full max-h-[400px] object-cover" loading="lazy" />
				<div class="absolute inset-0 flex items-center justify-center">
					<div class="flex h-14 w-14 items-center justify-center rounded-full bg-black/60 text-white">
						<svg class="h-7 w-7 ml-1" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3" /></svg>
					</div>
				</div>
			</div>
		{/if}
		{#if embed.video.alt}
			<p class="px-2 py-1 text-[13px] text-gv2-text-muted">{embed.video.alt}</p>
		{/if}
	</div>
{:else if embed.type === 'external' && embed.external}
	<a
		href={embed.external.uri}
		class="mt-2 block overflow-hidden rounded-xl border border-gv2-border/30 no-underline transition-colors active:bg-gv2-bg-hover/30 {className}"
		target="_blank"
		rel="noopener noreferrer"
		onclick={(e) => e.stopPropagation()}
	>
		{#if embed.external.thumb}
			<img src={embed.external.thumb} alt="" class="w-full h-[160px] object-cover" loading="lazy" />
		{/if}
		<div class="px-3 py-2.5">
			<p class="text-[11px] text-gv2-text-muted truncate">{new URL(embed.external.uri).hostname}</p>
			<p class="mt-0.5 text-[15px] font-semibold text-gv2-text-primary line-clamp-2">{embed.external.title}</p>
			{#if embed.external.description}
				<p class="mt-0.5 text-[14px] text-gv2-text-muted line-clamp-2">{embed.external.description}</p>
			{/if}
		</div>
	</a>
{:else if embed.type === 'record' && embed.record}
	<div class="mt-2 rounded-xl border border-gv2-border/30 px-3 py-2.5 {className}" onclick={(e) => e.stopPropagation()}>
		{#if embed.record.author}
			<div class="flex items-center gap-1.5 text-[14px]">
				{#if embed.record.author.avatar}
					<img src={embed.record.author.avatar} alt="" class="h-4 w-4 rounded-full" />
				{/if}
				<span class="font-bold text-gv2-text-primary">{embed.record.author.displayName}</span>
				<span class="text-gv2-text-muted">@{embed.record.author.handle}</span>
			</div>
		{/if}
		{#if embed.record.text}
			<p class="mt-1 text-[14px] text-gv2-text-primary line-clamp-3 whitespace-pre-wrap">{embed.record.text}</p>
		{/if}
	</div>
{/if}
