<script lang="ts">
	/**
	 * KamiYoroMascot — YORO mascot with KAMI Engine 3D (iframe) + SVG fallback.
	 *
	 * Strategy:
	 *   1. Show SVG immediately (no loading spinner)
	 *   2. If WebGPU is available, load iframe with KAMI Engine embed
	 *   3. iframe loads → hide SVG, show 3D
	 *   4. iframe fails/timeout (3s) → keep SVG
	 */
	import { onMount } from 'svelte';

	interface Props {
		width?: number;
		height?: number;
		interactive?: boolean;
		class?: string;
	}

	let { width = 200, height = 220, interactive = true, class: className = '' }: Props = $props();

	let mounted = $state(false);
	let kami3dReady = $state(false);
	let tapped = $state(false);
	let blink = $state(false);

	onMount(() => {
		mounted = true;

		// Blink loop
		const blinkLoop = () => {
			setTimeout(() => {
				blink = true;
				setTimeout(() => { blink = false; }, 150);
				blinkLoop();
			}, 3000 + Math.random() * 3000);
		};
		blinkLoop();

		// Try WebGPU iframe (non-blocking, 3s timeout)
		try {
			if (typeof navigator !== 'undefined' && navigator.gpu) {
				const timeout = setTimeout(() => { /* keep SVG */ }, 3000);
				const iframe = document.getElementById('kami-yoro-iframe') as HTMLIFrameElement | null;
				if (iframe) {
					iframe.onload = () => {
						clearTimeout(timeout);
						// Give KAMI Engine 1s to init after iframe load
						setTimeout(() => { kami3dReady = true; }, 1000);
					};
					iframe.onerror = () => { clearTimeout(timeout); };
				}
			}
		} catch { /* keep SVG */ }
	});

	function handleTap() {
		if (!interactive) return;
		tapped = true;
		setTimeout(() => { tapped = false; }, 400);
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div
	class="relative {className}"
	style="width: {width}px; height: {height}px"
	onclick={handleTap}
>
	<!-- KAMI Engine 3D iframe (hidden until ready) -->
	{#if mounted}
		<iframe
			id="kami-yoro-iframe"
			src="/kami-web/embed.html"
			class="absolute inset-0 w-full h-full rounded-2xl border-0"
			style="display: {kami3dReady ? 'block' : 'none'}; background: transparent;"
			title="YORO 3D"
			sandbox="allow-scripts allow-same-origin"
			loading="lazy"
		></iframe>
	{/if}

	<!-- SVG Fallback (shown until 3D is ready) -->
	{#if !kami3dReady && mounted}
		<div class="w-full h-full flex items-center justify-center">
			<svg
				viewBox="0 0 200 240"
				class="yoro-svg"
				class:yoro-tap={tapped}
				style="width: {width}px; height: {height}px"
				role="img"
				aria-label="YORO mascot"
			>
				<ellipse cx="100" cy="232" rx="38" ry="7" fill="rgba(0,0,0,0.1)" class="yoro-shadow" />
				<ellipse cx="76" cy="214" rx="17" ry="8" fill="#46A302" />
				<ellipse cx="124" cy="214" rx="17" ry="8" fill="#46A302" />
				<ellipse cx="100" cy="165" rx="46" ry="40" fill="#58CC02" />
				<ellipse cx="100" cy="173" rx="26" ry="20" fill="#8EE000" />
				<path d="M 54 152 Q 30 158 32 178" stroke="#46A302" stroke-width="13" fill="none" stroke-linecap="round" class="yoro-arm-l" />
				<circle cx="32" cy="179" r="8" fill="#46A302" class="yoro-arm-l" />
				<path d="M 146 152 Q 170 158 168 178" stroke="#46A302" stroke-width="13" fill="none" stroke-linecap="round" class="yoro-arm-r" />
				<circle cx="168" cy="179" r="8" fill="#46A302" class="yoro-arm-r" />
				<circle cx="100" cy="102" r="48" fill="#58CC02" />
				{#if blink}
					<line x1="65" y1="98" x2="90" y2="98" stroke="#2a6e00" stroke-width="3" stroke-linecap="round" />
					<line x1="110" y1="98" x2="135" y2="98" stroke="#2a6e00" stroke-width="3" stroke-linecap="round" />
				{:else}
					<ellipse cx="78" cy="96" rx="17" ry="17" fill="white" />
					<ellipse cx="122" cy="96" rx="17" ry="17" fill="white" />
					<circle cx="80" cy="100" r="10" fill="#1CB0F6" />
					<circle cx="124" cy="100" r="10" fill="#1CB0F6" />
					<circle cx="80" cy="100" r="4.5" fill="#1A1A2E" />
					<circle cx="124" cy="100" r="4.5" fill="#1A1A2E" />
					<circle cx="85" cy="94" r="3.5" fill="white" />
					<circle cx="129" cy="94" r="3.5" fill="white" />
				{/if}
				<path d="M 73 116 Q 100 140 127 116" stroke="#1A1A1A" stroke-width="2.5" fill="white" stroke-linecap="round" />
				<line x1="88" y1="117" x2="88" y2="126" stroke="#1A1A1A" stroke-width="1.2" />
				<line x1="100" y1="118" x2="100" y2="128" stroke="#1A1A1A" stroke-width="1.2" />
				<line x1="112" y1="117" x2="112" y2="126" stroke="#1A1A1A" stroke-width="1.2" />
				<ellipse cx="58" cy="110" rx="9" ry="5.5" fill="#ff9999" opacity="0.3" />
				<ellipse cx="142" cy="110" rx="9" ry="5.5" fill="#ff9999" opacity="0.3" />
				<ellipse cx="100" cy="62" rx="36" ry="9" fill="#e0e0e0" />
				<rect x="72" y="42" width="56" height="22" rx="7" fill="#ececee" />
				<ellipse cx="100" cy="42" rx="26" ry="9" fill="#e0e0e0" />
				<rect x="82" y="32" width="36" height="13" rx="5" fill="#d8d8da" />
				<circle cx="74" cy="62" r="2" fill="#ccc" />
				<circle cx="126" cy="62" r="2" fill="#ccc" />
			</svg>
		</div>
	{/if}
</div>

<style>
	.yoro-svg {
		animation: yoro-float 3s ease-in-out infinite;
		filter: drop-shadow(0 6px 12px rgba(88, 204, 2, 0.2));
		cursor: pointer;
	}
	.yoro-svg:hover {
		filter: drop-shadow(0 8px 20px rgba(88, 204, 2, 0.3));
	}
	.yoro-tap { animation: yoro-bounce 0.4s ease-out !important; }
	.yoro-shadow { animation: yoro-shadow-pulse 3s ease-in-out infinite; }
	.yoro-arm-l { transform-origin: 54px 152px; animation: yoro-wave-l 4s ease-in-out infinite; }
	.yoro-arm-r { transform-origin: 146px 152px; animation: yoro-wave-r 4s ease-in-out 2s infinite; }

	@keyframes yoro-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
	@keyframes yoro-bounce { 0% { transform: scale(1); } 20% { transform: scale(0.9); } 50% { transform: scale(1.08); } 70% { transform: scale(0.97); } 100% { transform: scale(1); } }
	@keyframes yoro-shadow-pulse { 0%, 100% { rx: 38; } 50% { rx: 34; } }
	@keyframes yoro-wave-l { 0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(-8deg); } 75% { transform: rotate(5deg); } }
	@keyframes yoro-wave-r { 0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(8deg); } 75% { transform: rotate(-5deg); } }
	@media (prefers-reduced-motion: reduce) { .yoro-svg, .yoro-shadow, .yoro-arm-l, .yoro-arm-r { animation: none; } .yoro-tap { animation: none !important; } }
</style>
