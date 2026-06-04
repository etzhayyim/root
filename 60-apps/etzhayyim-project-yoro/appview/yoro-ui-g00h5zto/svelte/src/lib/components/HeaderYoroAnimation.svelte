<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		class?: string;
	}

	let { class: cls = '' }: Props = $props();

	type AnimPattern = 'peek-left' | 'peek-right' | 'swing' | 'sleep' | 'bounce' | 'roll' | 'dance' | 'hang';

	const PATTERNS: AnimPattern[] = ['peek-left', 'peek-right', 'swing', 'sleep', 'bounce', 'roll', 'dance', 'hang'];

	let pattern = $state<AnimPattern>('peek-left');
	let blinking = $state(false);
	let visible = $state(false);

	onMount(() => {
		visible = true;
		// Pick random initial pattern
		pattern = PATTERNS[Math.floor(Math.random() * PATTERNS.length)];

		// Rotate pattern every 6-10s
		const rotateInterval = setInterval(() => {
			const next = PATTERNS[Math.floor(Math.random() * PATTERNS.length)];
			pattern = next;
		}, 6000 + Math.random() * 4000);

		// Blink loop
		const blinkInterval = setInterval(() => {
			if (pattern === 'sleep') return;
			blinking = true;
			setTimeout(() => { blinking = false; }, 150);
		}, 2800 + Math.random() * 2000);

		return () => {
			clearInterval(rotateInterval);
			clearInterval(blinkInterval);
		};
	});

	function handleClick() {
		// Cycle to next pattern on tap
		const idx = PATTERNS.indexOf(pattern);
		pattern = PATTERNS[(idx + 1) % PATTERNS.length];
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
{#if visible}
<div
	class="header-yoro-wrap {cls}"
	onclick={handleClick}
	role="img"
	aria-label="yoro-kun animation"
>
	<!-- Peek from left of text -->
	{#if pattern === 'peek-left'}
		<svg viewBox="0 0 28 28" class="yoro-mini yoro-peek-left" xmlns="http://www.w3.org/2000/svg">
			<circle cx="14" cy="12" r="10" fill="#58CC02" />
			{#if blinking}
				<line x1="8" y1="11" x2="12" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				<line x1="16" y1="11" x2="20" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
			{:else}
				<ellipse cx="10" cy="10" rx="3.5" ry="3.5" fill="white" />
				<ellipse cx="18" cy="10" rx="3.5" ry="3.5" fill="white" />
				<circle cx="11" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="19" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="11" cy="11" r="0.8" fill="#1A1A2E" />
				<circle cx="19" cy="11" r="0.8" fill="#1A1A2E" />
				<circle cx="12" cy="9.5" r="1" fill="white" />
				<circle cx="20" cy="9.5" r="1" fill="white" />
			{/if}
			<path d="M 9 16 Q 14 21 19 16" stroke="#1A1A1A" stroke-width="1.2" fill="white" stroke-linecap="round" />
			<ellipse cx="6" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="22" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<!-- tiny arm waving -->
			<path d="M 3 16 Q 0 12 2 8" stroke="#46A302" stroke-width="2.5" fill="none" stroke-linecap="round" class="wave-arm" />
			<circle cx="2" cy="8" r="1.5" fill="#46A302" class="wave-arm" />
		</svg>

	<!-- Peek from right of text -->
	{:else if pattern === 'peek-right'}
		<svg viewBox="0 0 28 28" class="yoro-mini yoro-peek-right" xmlns="http://www.w3.org/2000/svg">
			<circle cx="14" cy="12" r="10" fill="#58CC02" />
			{#if blinking}
				<line x1="8" y1="11" x2="12" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				<line x1="16" y1="11" x2="20" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
			{:else}
				<ellipse cx="10" cy="10" rx="3.5" ry="3.5" fill="white" />
				<ellipse cx="18" cy="10" rx="3.5" ry="3.5" fill="white" />
				<circle cx="11" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="19" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="11" cy="11" r="0.8" fill="#1A1A2E" />
				<circle cx="19" cy="11" r="0.8" fill="#1A1A2E" />
				<circle cx="12" cy="9.5" r="1" fill="white" />
				<circle cx="20" cy="9.5" r="1" fill="white" />
			{/if}
			<path d="M 9 16 Q 14 21 19 16" stroke="#1A1A1A" stroke-width="1.2" fill="white" stroke-linecap="round" />
			<ellipse cx="6" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="22" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<path d="M 25 16 Q 28 12 26 8" stroke="#46A302" stroke-width="2.5" fill="none" stroke-linecap="round" class="wave-arm-r" />
			<circle cx="26" cy="8" r="1.5" fill="#46A302" class="wave-arm-r" />
		</svg>

	<!-- Swinging from the text -->
	{:else if pattern === 'swing'}
		<svg viewBox="0 0 28 36" class="yoro-mini yoro-swing" xmlns="http://www.w3.org/2000/svg">
			<!-- arms gripping top -->
			<path d="M 10 2 L 10 6" stroke="#46A302" stroke-width="2.5" stroke-linecap="round" />
			<path d="M 18 2 L 18 6" stroke="#46A302" stroke-width="2.5" stroke-linecap="round" />
			<circle cx="10" cy="2" r="1.5" fill="#46A302" />
			<circle cx="18" cy="2" r="1.5" fill="#46A302" />
			<circle cx="14" cy="16" r="10" fill="#58CC02" />
			{#if blinking}
				<line x1="8" y1="15" x2="12" y2="15" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				<line x1="16" y1="15" x2="20" y2="15" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
			{:else}
				<ellipse cx="10" cy="14" rx="3.5" ry="3.5" fill="white" />
				<ellipse cx="18" cy="14" rx="3.5" ry="3.5" fill="white" />
				<circle cx="11" cy="15" r="2" fill="#1CB0F6" />
				<circle cx="19" cy="15" r="2" fill="#1CB0F6" />
				<circle cx="11" cy="15" r="0.8" fill="#1A1A2E" />
				<circle cx="19" cy="15" r="0.8" fill="#1A1A2E" />
			{/if}
			<path d="M 9 20 Q 14 24 19 20" stroke="#1A1A1A" stroke-width="1.2" fill="white" stroke-linecap="round" />
			<ellipse cx="6" cy="18" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="22" cy="18" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<!-- feet dangling -->
			<ellipse cx="10" cy="27" rx="3" ry="2" fill="#46A302" class="dangle-l" />
			<ellipse cx="18" cy="27" rx="3" ry="2" fill="#46A302" class="dangle-r" />
		</svg>

	<!-- Sleeping on the text -->
	{:else if pattern === 'sleep'}
		<svg viewBox="0 0 36 28" class="yoro-mini yoro-sleep" xmlns="http://www.w3.org/2000/svg">
			<circle cx="14" cy="14" r="10" fill="#58CC02" />
			<!-- closed eyes (sleeping) -->
			<path d="M 7 12 Q 10 14 13 12" stroke="#2a6e00" stroke-width="1.5" fill="none" stroke-linecap="round" />
			<path d="M 15 12 Q 18 14 21 12" stroke="#2a6e00" stroke-width="1.5" fill="none" stroke-linecap="round" />
			<!-- little smile -->
			<path d="M 10 18 Q 14 20 18 18" stroke="#1A1A1A" stroke-width="1" fill="none" stroke-linecap="round" />
			<ellipse cx="6" cy="16" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="22" cy="16" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<!-- Zzz -->
			<text x="26" y="10" class="zzz zzz-1" fill="var(--gv2-text-muted, #666)" font-size="6" font-weight="bold">z</text>
			<text x="30" y="6" class="zzz zzz-2" fill="var(--gv2-text-muted, #666)" font-size="5" font-weight="bold">z</text>
			<text x="33" y="3" class="zzz zzz-3" fill="var(--gv2-text-muted, #666)" font-size="4" font-weight="bold">z</text>
			<!-- body lying flat -->
			<ellipse cx="14" cy="24" rx="8" ry="3" fill="#46A302" />
		</svg>

	<!-- Bouncing on top of text -->
	{:else if pattern === 'bounce'}
		<svg viewBox="0 0 28 28" class="yoro-mini yoro-bounce-anim" xmlns="http://www.w3.org/2000/svg">
			<circle cx="14" cy="12" r="10" fill="#58CC02" />
			{#if blinking}
				<line x1="8" y1="11" x2="12" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				<line x1="16" y1="11" x2="20" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
			{:else}
				<ellipse cx="10" cy="10" rx="3.5" ry="3.5" fill="white" />
				<ellipse cx="18" cy="10" rx="3.5" ry="3.5" fill="white" />
				<circle cx="11" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="19" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="11" cy="11" r="0.8" fill="#1A1A2E" />
				<circle cx="19" cy="11" r="0.8" fill="#1A1A2E" />
			{/if}
			<!-- open excited mouth -->
			<ellipse cx="14" cy="17" rx="4" ry="3" fill="#1A1A1A" />
			<ellipse cx="14" cy="17" rx="2.5" ry="2" fill="#ff6b6b" />
			<ellipse cx="6" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="22" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<!-- feet -->
			<ellipse cx="10" cy="23" rx="3.5" ry="2" fill="#46A302" />
			<ellipse cx="18" cy="23" rx="3.5" ry="2" fill="#46A302" />
		</svg>

	<!-- Rolling across -->
	{:else if pattern === 'roll'}
		<svg viewBox="0 0 28 28" class="yoro-mini yoro-roll" xmlns="http://www.w3.org/2000/svg">
			<g class="roll-body">
				<circle cx="14" cy="14" r="10" fill="#58CC02" />
				{#if blinking}
					<line x1="8" y1="13" x2="12" y2="13" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
					<line x1="16" y1="13" x2="20" y2="13" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				{:else}
					<ellipse cx="10" cy="12" rx="3.5" ry="3.5" fill="white" />
					<ellipse cx="18" cy="12" rx="3.5" ry="3.5" fill="white" />
					<!-- dizzy spiral eyes -->
					<circle cx="10" cy="12" r="2.5" fill="none" stroke="#1CB0F6" stroke-width="1" />
					<circle cx="18" cy="12" r="2.5" fill="none" stroke="#1CB0F6" stroke-width="1" />
					<circle cx="10" cy="12" r="1" fill="#1CB0F6" />
					<circle cx="18" cy="12" r="1" fill="#1CB0F6" />
				{/if}
				<path d="M 10 18 Q 14 20 18 18" stroke="#1A1A1A" stroke-width="1" fill="none" stroke-linecap="round" />
			</g>
		</svg>

	<!-- Dance -->
	{:else if pattern === 'dance'}
		<svg viewBox="0 0 32 30" class="yoro-mini yoro-dance" xmlns="http://www.w3.org/2000/svg">
			<circle cx="16" cy="12" r="10" fill="#58CC02" />
			{#if blinking}
				<line x1="10" y1="11" x2="14" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				<line x1="18" y1="11" x2="22" y2="11" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
			{:else}
				<ellipse cx="12" cy="10" rx="3.5" ry="3.5" fill="white" />
				<ellipse cx="20" cy="10" rx="3.5" ry="3.5" fill="white" />
				<circle cx="13" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="21" cy="11" r="2" fill="#1CB0F6" />
				<circle cx="13" cy="11" r="0.8" fill="#1A1A2E" />
				<circle cx="21" cy="11" r="0.8" fill="#1A1A2E" />
			{/if}
			<!-- happy open mouth -->
			<path d="M 11 16 Q 16 21 21 16" stroke="#1A1A1A" stroke-width="1.2" fill="white" stroke-linecap="round" />
			<ellipse cx="8" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="24" cy="14" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<!-- arms up dance pose -->
			<path d="M 6 14 Q 2 8 5 4" stroke="#46A302" stroke-width="2.5" fill="none" stroke-linecap="round" class="dance-arm-l" />
			<circle cx="5" cy="4" r="1.5" fill="#46A302" class="dance-arm-l" />
			<path d="M 26 14 Q 30 8 27 4" stroke="#46A302" stroke-width="2.5" fill="none" stroke-linecap="round" class="dance-arm-r" />
			<circle cx="27" cy="4" r="1.5" fill="#46A302" class="dance-arm-r" />
			<!-- feet -->
			<ellipse cx="12" cy="24" rx="3.5" ry="2" fill="#46A302" class="dance-foot-l" />
			<ellipse cx="20" cy="24" rx="3.5" ry="2" fill="#46A302" class="dance-foot-r" />
			<!-- music notes -->
			<text x="1" y="6" class="music-note note-1" fill="var(--gv2-accent, #1CB0F6)" font-size="5">&#9835;</text>
			<text x="27" y="4" class="music-note note-2" fill="var(--gv2-accent, #1CB0F6)" font-size="4">&#9834;</text>
		</svg>

	<!-- Hanging from text bottom -->
	{:else if pattern === 'hang'}
		<svg viewBox="0 0 28 34" class="yoro-mini yoro-hang" xmlns="http://www.w3.org/2000/svg">
			<!-- arms gripping top edge -->
			<rect x="8" y="0" width="12" height="3" rx="1.5" fill="#46A302" />
			<path d="M 10 3 L 10 8" stroke="#46A302" stroke-width="2.5" stroke-linecap="round" />
			<path d="M 18 3 L 18 8" stroke="#46A302" stroke-width="2.5" stroke-linecap="round" />
			<circle cx="14" cy="18" r="10" fill="#58CC02" />
			{#if blinking}
				<line x1="8" y1="17" x2="12" y2="17" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
				<line x1="16" y1="17" x2="20" y2="17" stroke="#2a6e00" stroke-width="1.5" stroke-linecap="round" />
			{:else}
				<ellipse cx="10" cy="16" rx="3.5" ry="3.5" fill="white" />
				<ellipse cx="18" cy="16" rx="3.5" ry="3.5" fill="white" />
				<circle cx="11" cy="17" r="2" fill="#1CB0F6" />
				<circle cx="19" cy="17" r="2" fill="#1CB0F6" />
				<circle cx="11" cy="17" r="0.8" fill="#1A1A2E" />
				<circle cx="19" cy="17" r="0.8" fill="#1A1A2E" />
				<circle cx="12" cy="15.5" r="1" fill="white" />
				<circle cx="20" cy="15.5" r="1" fill="white" />
			{/if}
			<path d="M 9 22 Q 14 26 19 22" stroke="#1A1A1A" stroke-width="1.2" fill="white" stroke-linecap="round" />
			<ellipse cx="6" cy="20" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<ellipse cx="22" cy="20" rx="2" ry="1.5" fill="#ff9999" opacity="0.3" />
			<!-- dangling feet -->
			<ellipse cx="10" cy="30" rx="3.5" ry="2" fill="#46A302" class="dangle-l" />
			<ellipse cx="18" cy="30" rx="3.5" ry="2" fill="#46A302" class="dangle-r" />
		</svg>
	{/if}
</div>
{/if}

<style>
	.header-yoro-wrap {
		display: inline-flex;
		align-items: center;
		cursor: pointer;
		user-select: none;
		position: relative;
	}

	.yoro-mini {
		width: 22px;
		height: auto;
		filter: drop-shadow(0 1px 2px rgba(88, 204, 2, 0.3));
		transition: filter 0.2s;
	}
	.yoro-mini:hover {
		filter: drop-shadow(0 2px 6px rgba(88, 204, 2, 0.5));
	}

	/* ── Peek left: slide in from left ── */
	.yoro-peek-left {
		animation: peek-in-left 0.5s ease-out forwards, gentle-bob 2.5s ease-in-out 0.5s infinite;
	}
	@keyframes peek-in-left {
		from { transform: translateX(-8px) scale(0.6); opacity: 0; }
		to { transform: translateX(0) scale(1); opacity: 1; }
	}

	/* ── Peek right: slide in from right ── */
	.yoro-peek-right {
		animation: peek-in-right 0.5s ease-out forwards, gentle-bob 2.5s ease-in-out 0.5s infinite;
	}
	@keyframes peek-in-right {
		from { transform: translateX(8px) scale(0.6); opacity: 0; }
		to { transform: translateX(0) scale(1); opacity: 1; }
	}

	/* ── Gentle bob (shared idle) ── */
	@keyframes gentle-bob {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-2px); }
	}

	/* ── Wave arm (peek-left) ── */
	.wave-arm {
		transform-origin: 3px 16px;
		animation: wave 0.8s ease-in-out 0.6s infinite alternate;
	}
	@keyframes wave {
		from { transform: rotate(0deg); }
		to { transform: rotate(-25deg); }
	}

	/* ── Wave arm right (peek-right) ── */
	.wave-arm-r {
		transform-origin: 25px 16px;
		animation: wave-r 0.8s ease-in-out 0.6s infinite alternate;
	}
	@keyframes wave-r {
		from { transform: rotate(0deg); }
		to { transform: rotate(25deg); }
	}

	/* ── Swing pattern ── */
	.yoro-swing {
		transform-origin: 14px 2px;
		animation: swing-pendulum 2s ease-in-out infinite;
	}
	@keyframes swing-pendulum {
		0%, 100% { transform: rotate(-8deg); }
		50% { transform: rotate(8deg); }
	}

	/* ── Dangling feet ── */
	.dangle-l {
		animation: dangle-foot 1.5s ease-in-out infinite;
	}
	.dangle-r {
		animation: dangle-foot 1.5s ease-in-out 0.4s infinite;
	}
	@keyframes dangle-foot {
		0%, 100% { transform: translateX(0); }
		50% { transform: translateX(-2px); }
	}

	/* ── Sleep pattern ── */
	.yoro-sleep {
		animation: sleep-breathe 3s ease-in-out infinite;
	}
	@keyframes sleep-breathe {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.03); }
	}

	/* ── Zzz floating ── */
	.zzz {
		opacity: 0;
	}
	.zzz-1 {
		animation: zzz-float 2.5s ease-in-out infinite;
	}
	.zzz-2 {
		animation: zzz-float 2.5s ease-in-out 0.5s infinite;
	}
	.zzz-3 {
		animation: zzz-float 2.5s ease-in-out 1s infinite;
	}
	@keyframes zzz-float {
		0% { opacity: 0; transform: translateY(0); }
		30% { opacity: 0.8; }
		70% { opacity: 0.8; }
		100% { opacity: 0; transform: translateY(-6px); }
	}

	/* ── Bounce pattern ── */
	.yoro-bounce-anim {
		animation: yoro-header-bounce 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97) infinite;
	}
	@keyframes yoro-header-bounce {
		0%, 100% { transform: translateY(0) scaleY(1); }
		30% { transform: translateY(-6px) scaleY(1.05); }
		50% { transform: translateY(0) scaleY(0.92) scaleX(1.05); }
		70% { transform: translateY(-3px) scaleY(1.02); }
	}

	/* ── Roll pattern ── */
	.yoro-roll {
		animation: roll-across 3s linear infinite;
	}
	.roll-body {
		transform-origin: 14px 14px;
		animation: roll-spin 1s linear infinite;
	}
	@keyframes roll-across {
		0% { transform: translateX(-12px); }
		50% { transform: translateX(12px); }
		100% { transform: translateX(-12px); }
	}
	@keyframes roll-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	/* ── Dance pattern ── */
	.yoro-dance {
		animation: dance-sway 0.5s ease-in-out infinite alternate;
	}
	@keyframes dance-sway {
		from { transform: rotate(-5deg) translateY(0); }
		to { transform: rotate(5deg) translateY(-2px); }
	}
	.dance-arm-l {
		transform-origin: 6px 14px;
		animation: dance-arm-left 0.4s ease-in-out infinite alternate;
	}
	.dance-arm-r {
		transform-origin: 26px 14px;
		animation: dance-arm-right 0.4s ease-in-out 0.2s infinite alternate;
	}
	@keyframes dance-arm-left {
		from { transform: rotate(0deg); }
		to { transform: rotate(-20deg); }
	}
	@keyframes dance-arm-right {
		from { transform: rotate(0deg); }
		to { transform: rotate(20deg); }
	}
	.dance-foot-l {
		animation: dance-step-l 0.5s ease-in-out infinite alternate;
	}
	.dance-foot-r {
		animation: dance-step-r 0.5s ease-in-out 0.25s infinite alternate;
	}
	@keyframes dance-step-l {
		from { transform: translateX(0); }
		to { transform: translateX(-2px) translateY(-1px); }
	}
	@keyframes dance-step-r {
		from { transform: translateX(0); }
		to { transform: translateX(2px) translateY(-1px); }
	}

	/* ── Music notes ── */
	.music-note {
		opacity: 0;
	}
	.note-1 {
		animation: note-float 1.5s ease-out infinite;
	}
	.note-2 {
		animation: note-float 1.5s ease-out 0.7s infinite;
	}
	@keyframes note-float {
		0% { opacity: 0; transform: translateY(0); }
		30% { opacity: 1; }
		100% { opacity: 0; transform: translateY(-8px) translateX(3px); }
	}

	/* ── Hang pattern ── */
	.yoro-hang {
		animation: hang-sway 2.5s ease-in-out infinite;
	}
	@keyframes hang-sway {
		0%, 100% { transform: rotate(-3deg); }
		50% { transform: rotate(3deg); }
	}

	@media (prefers-reduced-motion: reduce) {
		.yoro-mini,
		.wave-arm, .wave-arm-r,
		.dangle-l, .dangle-r,
		.zzz, .roll-body,
		.dance-arm-l, .dance-arm-r,
		.dance-foot-l, .dance-foot-r,
		.music-note {
			animation: none !important;
		}
	}
</style>
