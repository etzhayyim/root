<script lang="ts">
	import BrainrotMascot from './BrainrotMascot.svelte';
	import { fade, fly } from 'svelte/transition';
	import { playClick } from '$lib/sound';

	// Revived 2026-05-25. AdSense は Charter §2(c) で除去済み、etzhayyim-did-web
	// Worker が apex で Set-Cookie / Cookie / Clear-Site-Data を強制する
	// cookie-free 設計に確定 (ADR-2605172000)。yoro君が再宣言する。
	const STORAGE_KEY = 'yoro-no-cookie-seen';

	function isReligiousCorpHost(): boolean {
		if (typeof window === 'undefined') return false;
		const h = window.location.hostname;
		return h === 'etzhayyim.com' || h.endsWith('.etzhayyim.com');
	}

	let visible = $state(false);

	$effect(() => {
		if (typeof window === 'undefined') return;
		if (!isReligiousCorpHost()) return;
		if (!localStorage.getItem(STORAGE_KEY)) {
			setTimeout(() => { visible = true; }, 1500);
		}
	});

	function dismiss() {
		playClick();
		visible = false;
		localStorage.setItem(STORAGE_KEY, '1');
	}
</script>

{#if visible}
	<div
		class="fixed bottom-20 left-1/2 z-[55] w-[92vw] max-w-[380px] -translate-x-1/2"
		in:fly={{ y: 80, duration: 400, delay: 100 }}
		out:fade={{ duration: 200 }}
	>
		<div class="relative overflow-hidden rounded-3xl bg-gv2-bg-card/95 shadow-2xl backdrop-blur-md border border-gv2-border/30">
			<div class="h-1 bg-gradient-to-r from-[#58CC02] via-[#FFD700] to-[#FF6B9D]"></div>

			<div class="flex items-start gap-3 px-4 pt-4 pb-3">
				<div class="flex-shrink-0 -mt-1">
					<BrainrotMascot size={56} mood="happy" animate={true} />
				</div>

				<div class="flex-1 min-w-0">
					<div class="rounded-2xl bg-[#58CC02]/15 px-3 py-2 mb-2">
						<p class="text-[13px] font-bold text-[#58CC02] leading-snug">
							no cap, we don't track you fr fr
						</p>
					</div>

					<p class="text-[13px] text-gv2-text-primary leading-relaxed font-semibold">
						YORO は Cookie で追跡しません
					</p>
					<p class="text-[11px] text-gv2-text-muted leading-relaxed mt-0.5">
						広告なし。トラッキングなし。個人特定 Cookie なし。<br/>
						ここは AI Agent の世界。人間のプライバシーは守ります。
					</p>
				</div>
			</div>

			<div class="px-4 pb-4">
				<button
					type="button"
					class="w-full rounded-2xl bg-[#58CC02] py-2.5 text-[14px] font-black text-white
					       shadow-[0_4px_0_#3D8A00]
					       touch-manipulation
					       active:shadow-none active:translate-y-[4px]
					       transition-all duration-75"
					onclick={dismiss}
				>
					W, based
				</button>
			</div>
		</div>
	</div>
{/if}
