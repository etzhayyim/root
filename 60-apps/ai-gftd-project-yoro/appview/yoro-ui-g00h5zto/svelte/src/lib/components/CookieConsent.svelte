<script lang="ts">
	import { fade, fly } from 'svelte/transition';
	import { playClick } from '$lib/sound';

	const STORAGE_KEY = 'yoro-cookie-consent';

	let visible = $state(false);

	/** true if user has accepted cookie consent (ads allowed) */
	export function hasConsent(): boolean {
		if (typeof window === 'undefined') return false;
		return localStorage.getItem(STORAGE_KEY) === 'accepted';
	}

	$effect(() => {
		if (typeof window === 'undefined') return;
		const stored = localStorage.getItem(STORAGE_KEY);
		if (!stored) {
			setTimeout(() => { visible = true; }, 800);
		}
	});

	function accept() {
		playClick();
		visible = false;
		localStorage.setItem(STORAGE_KEY, 'accepted');
		// Enable personalized ads
		(window as any).adsbygoogle = (window as any).adsbygoogle || [];
	}

	function decline() {
		playClick();
		visible = false;
		localStorage.setItem(STORAGE_KEY, 'declined');
	}
</script>

{#if visible}
	<div
		class="fixed bottom-20 left-1/2 z-[55] w-[92vw] max-w-[420px] -translate-x-1/2"
		in:fly={{ y: 80, duration: 400, delay: 100 }}
		out:fade={{ duration: 200 }}
	>
		<div class="relative overflow-hidden rounded-3xl bg-gv2-bg-card/95 shadow-2xl backdrop-blur-md border border-gv2-border/30">
			<div class="h-1 bg-gradient-to-r from-[#1185FE] via-[#58CC02] to-[#FFD700]"></div>

			<div class="px-4 pt-4 pb-3">
				<p class="text-[14px] font-bold text-gv2-text-primary leading-snug">
					Cookies / Cookie
				</p>
				<p class="text-[12px] text-gv2-text-muted leading-relaxed mt-1.5">
					YORO uses cookies to serve relevant ads via Google AdSense and partner networks.
					See our <a href="/privacy" class="text-[#1185FE] underline">Privacy Policy</a> for details.
				</p>
			</div>

			<div class="flex gap-2 px-4 pb-4">
				<button
					type="button"
					class="flex-1 rounded-2xl border border-gv2-border py-2.5 text-[13px] font-bold text-gv2-text-muted
					       touch-manipulation active:bg-gv2-bg-hover
					       transition-all duration-75"
					onclick={decline}
				>
					Decline
				</button>
				<button
					type="button"
					class="flex-1 rounded-2xl bg-[#1185FE] py-2.5 text-[13px] font-black text-white
					       shadow-[0_4px_0_#0D6ABF]
					       touch-manipulation
					       active:shadow-none active:translate-y-[4px]
					       transition-all duration-75"
					onclick={accept}
				>
					Accept
				</button>
			</div>
		</div>
	</div>
{/if}
