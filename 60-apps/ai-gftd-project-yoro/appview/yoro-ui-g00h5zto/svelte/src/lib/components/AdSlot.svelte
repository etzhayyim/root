<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { Avatar } from '@gftdcojp/design-system';
	import {
		ADSENSE_CLIENT_ID,
		AD_SLOTS,
		EXOCLICK_ZONES,
		HOUSE_AD,
		UNPROVISIONED,
		hasAdConsent,
		providers,
		type AdPlacement,
	} from '$lib/ads/config';

	interface Props {
		placement?: AdPlacement;
		slot?: string;
		format?: 'auto' | 'horizontal' | 'vertical' | 'rectangle' | 'fluid';
		provider?: 'adsense' | 'medianet' | 'exoclick';
		/**
		 * 'post'  — render as a social-post card (avatar + header + body + footer). Default for in-feed placements.
		 * 'plain' — raw ad container with only a Sponsored label. Use for sidebar / header strips.
		 */
		skin?: 'post' | 'plain';
		class?: string;
	}

	const {
		placement,
		slot: slotOverride,
		format: formatOverride,
		provider,
		skin,
		class: cls = '',
	}: Props = $props();

	const spec = placement ? AD_SLOTS[placement] : null;
	const slotId = spec?.id ?? slotOverride ?? UNPROVISIONED;
	const format = spec?.format ?? formatOverride ?? 'auto';
	const minHeight = spec?.minHeight ?? 50;

	const postSkinDefault: AdPlacement[] = ['feed-inline', 'post-detail', 'post-thread', 'search-results'];
	const resolvedSkin: 'post' | 'plain' = skin ?? (placement && postSkinDefault.includes(placement) ? 'post' : 'plain');

	const useMedianet = provider === 'medianet' || (!provider && providers.medianet && !providers.adsense);
	const exoclickZone = placement ? EXOCLICK_ZONES[placement] : undefined;
	const useExoclick = !useMedianet && (provider === 'exoclick' || (!provider && providers.exoclick && !providers.adsense)) && !!exoclickZone;

	let containerEl: HTMLElement | undefined = $state();
	let visible = $state(false);
	let pushed = false;

	const unprovisioned = slotId === UNPROVISIONED;
	const consented = $derived(browser && hasAdConsent());

	onMount(() => {
		if (!browser || !containerEl) return;
		const io = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					if (e.isIntersecting) {
						visible = true;
						io.disconnect();
						break;
					}
				}
			},
			{ rootMargin: '200px' },
		);
		io.observe(containerEl);
		return () => io.disconnect();
	});

	$effect(() => {
		if (!visible || pushed) return;
		if (useExoclick) {
			pushed = true;
			try {
				if (!document.querySelector('script[data-exoclick]')) {
					const s = document.createElement('script');
					s.async = true;
					s.src = 'https://a.magsrv.com/ad-provider.js';
					s.setAttribute('data-exoclick', '1');
					document.head.appendChild(s);
				}
				((window as any).AdProvider = (window as any).AdProvider || []).push({ serve: {} });
			} catch (e) {
				console.warn('exoclick push failed', e);
			}
			return;
		}
		if (unprovisioned) return;
		if (useMedianet) {
			pushed = true;
			try {
				((window as any)._mNHandle = (window as any)._mNHandle || {}).loaded = 0;
				((window as any)._mNDetails = (window as any)._mNDetails || {});
			} catch (e) {
				console.warn('media.net init failed', e);
			}
			return;
		}
		if (!consented) return;
		pushed = true;
		try {
			((window as any).adsbygoogle = (window as any).adsbygoogle || []).push({});
		} catch (e) {
			console.warn('adsbygoogle push failed', e);
		}
	});
</script>

{#snippet creative()}
	{#if !visible}
		<!-- lazy-load placeholder -->
	{:else if useExoclick}
		<ins class="eas6a97888e20" data-zoneid={exoclickZone}></ins>
	{:else if unprovisioned || (!useMedianet && !consented)}
		<a class="house-ad" href={HOUSE_AD.href} target="_blank" rel="noopener noreferrer">
			<div class="house-ad-body">
				<div class="house-ad-title">{HOUSE_AD.title}</div>
				<div class="house-ad-desc">{HOUSE_AD.description}</div>
			</div>
			<div class="house-ad-cta">{HOUSE_AD.cta}</div>
		</a>
	{:else if useMedianet}
		<div id="medianet-{slotId}"></div>
	{:else}
		<ins
			class="adsbygoogle"
			style="display:block"
			data-ad-client={ADSENSE_CLIENT_ID}
			data-ad-slot={slotId}
			data-ad-format={format}
			data-full-width-responsive="true"
		></ins>
	{/if}
{/snippet}

{#if resolvedSkin === 'post'}
	<!-- Social-post skin: blends with yoro feed post layout (avatar + header + body + footer) -->
	<article
		bind:this={containerEl}
		class="ad-post flex w-full gap-2.5 px-4 py-3 text-left {cls}"
		aria-label="Sponsored"
	>
		<div class="flex-shrink-0 pt-0.5">
			<Avatar fallback="Ad" size="md" class="!h-[42px] !w-[42px] !bg-[#1185FE]/15 !text-[#1185FE] !text-[12px] !font-bold" />
		</div>
		<div class="min-w-0 flex-1">
			<div class="flex items-baseline gap-1 text-[15px] leading-tight">
				<span class="truncate font-bold text-gv2-text-primary">Sponsored</span>
				<span class="min-w-0 truncate text-[14px] text-gv2-text-muted">@ads</span>
				<span class="flex-shrink-0 text-[14px] text-gv2-text-muted">·</span>
				<span class="flex-shrink-0 rounded-full bg-[#1185FE]/12 px-1.5 py-0.5 text-[10px] font-bold text-[#1185FE] uppercase tracking-wide">Ad</span>
			</div>
			<div class="mt-2 overflow-hidden rounded-xl" style="min-height: {minHeight}px">
				{@render creative()}
			</div>
			<div class="mt-2.5 flex items-center justify-between text-gv2-text-muted">
				<button type="button" class="text-[12px] hover:text-gv2-text-primary" onclick={(e) => e.stopPropagation()}>
					Why this ad?
				</button>
				<button type="button" class="rounded-full p-1.5 touch-manipulation transition-colors active:bg-gv2-bg-hover" aria-label="more">
					<svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/></svg>
				</button>
			</div>
		</div>
	</article>
{:else}
	<!-- Plain skin: label + creative (for sidebar / header strips where the post shell is overkill) -->
	<div
		bind:this={containerEl}
		class="ad-slot {cls}"
		style="min-height: {minHeight}px"
		aria-label="Sponsored"
	>
		<div class="ad-label">Sponsored</div>
		{@render creative()}
	</div>
{/if}

<style>
	.ad-post {
		width: 100%;
	}
	.ad-slot {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 4px;
		overflow: hidden;
	}
	.ad-label {
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--gv2-text-muted, #888);
		opacity: 0.7;
	}
	.ad-slot :global(ins.adsbygoogle),
	.ad-post :global(ins.adsbygoogle) {
		width: 100%;
	}
	.house-ad {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 14px;
		border-radius: 14px;
		background: linear-gradient(135deg, rgba(17, 133, 254, 0.08), rgba(88, 204, 2, 0.08));
		border: 1px solid rgba(17, 133, 254, 0.18);
		text-decoration: none;
		color: inherit;
	}
	.house-ad-title {
		font-size: 13px;
		font-weight: 700;
		color: var(--gv2-text-primary, #eee);
	}
	.house-ad-desc {
		font-size: 12px;
		color: var(--gv2-text-muted, #aaa);
		margin-top: 2px;
	}
	.house-ad-cta {
		flex-shrink: 0;
		font-size: 12px;
		font-weight: 700;
		color: #1185fe;
	}
</style>
