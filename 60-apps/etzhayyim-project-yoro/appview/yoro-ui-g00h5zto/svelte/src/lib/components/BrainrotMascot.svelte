<script lang="ts">
	import { onMount } from 'svelte';

	type CharacterId = 'yoro' | 'skibidi' | 'sigma' | 'ohio' | 'rizz' | 'gyatt';

	interface Props {
		mood?: 'idle' | 'happy' | 'surprised' | 'sigma' | 'nuhuh';
		size?: number;
		class?: string;
		animate?: boolean;
		/** Which character to render. Default: 'yoro' */
		character?: CharacterId;
	}

	const { mood = 'idle', size = 80, class: cls = '', animate = true, character = 'yoro' }: Props = $props();

	const phrasesByChar: Record<CharacterId, string[]> = {
		yoro: ['rizz 全開！💅', 'nuh uh 🚫', 'no cap 🔥', 'slay ✨', 'W しか出ない 🏆', 'bussin fr fr 🍗'],
		skibidi: ['skibidi dop dop 🚽', 'toilet sigma 🗿', 'bop bop yes yes 🎵', 'Ohio final boss 💀'],
		sigma: ['grindset only 💪', 'stay on the path 🐺', 'no distractions 🧠', 'lone wolf 🌙', 'mog or be mogged 😤'],
		ohio: ['only in Ohio 💀', 'Ohio ahh moment 🌽', 'least weird Ohio day 🤡', 'Ohio is NOT real 🌪️'],
		rizz: ['W rizz 💅', 'unspoken rizz ✨', 'rizz god activated 👑', 'rizzler on duty 🫡'],
		gyatt: ['GYATT 👀', 'lord have mercy 🙏', 'bro is down bad 💀', 'respectfully 🫣'],
	};

	const phrases = $derived(phrasesByChar[character] ?? phrasesByChar.yoro);

	let phraseIdx = $state(0);
	let showPhrase = $state(false);
	let bouncing = $state(false);
	let blinking = $state(false);

	function handleClick() {
		phraseIdx = (phraseIdx + 1) % phrases.length;
		showPhrase = true;
		bouncing = true;
		setTimeout(() => { bouncing = false; }, 600);
		setTimeout(() => { showPhrase = false; }, 2200);
	}

	onMount(() => {
		const blinkInterval = setInterval(() => {
			blinking = true;
			setTimeout(() => { blinking = false; }, 150);
		}, 3200);
		const phraseInterval = setInterval(() => {
			phraseIdx = Math.floor(Math.random() * phrases.length);
			showPhrase = true;
			setTimeout(() => { showPhrase = false; }, 2200);
		}, 8000);
		return () => { clearInterval(blinkInterval); clearInterval(phraseInterval); };
	});

	const eyeScaleY = $derived(blinking ? 0.05 : 1);
	const pupilOffset = $derived(mood === 'surprised' ? -1 : mood === 'happy' ? 2 : mood === 'nuhuh' ? -2 : 0);

	// Character color palettes
	const palette: Record<CharacterId, { body: string; belly: string; limb: string; pupil: string; hat: string }> = {
		yoro:    { body: '#58CC02', belly: '#8EE000', limb: '#46A302', pupil: '#1CB0F6', hat: '#e0e0e0' },
		skibidi: { body: '#1CB0F6', belly: '#5CC8F8', limb: '#0E87BF', pupil: '#FF6B9D', hat: '#f0f0f0' },
		sigma:   { body: '#6C63FF', belly: '#9B95FF', limb: '#4F46E5', pupil: '#FFD700', hat: '#2d2d2d' },
		ohio:    { body: '#FF9500', belly: '#FFB84D', limb: '#CC7700', pupil: '#58CC02', hat: '#8B4513' },
		rizz:    { body: '#FF6B9D', belly: '#FF9EC1', limb: '#D44D7A', pupil: '#A855F7', hat: '#FFD700' },
		gyatt:   { body: '#A855F7', belly: '#C084FC', limb: '#7E22CE', pupil: '#FF6B9D', hat: '#1CB0F6' },
	};
	const c = $derived(palette[character] ?? palette.yoro);

	// Character-specific hat names for aria
	const charNames: Record<CharacterId, string> = {
		yoro: 'YORO', skibidi: 'Skibidi', sigma: 'Sigma', ohio: 'Ohio', rizz: 'Rizz', gyatt: 'Gyatt',
	};
</script>

<div
	class="relative inline-flex flex-col items-center select-none {cls}"
	style="width:{size}px"
	role="img"
	aria-label="{charNames[character]}"
>
	{#if showPhrase}
		<div
			class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 whitespace-nowrap
			       rounded-2xl bg-yellow-400 px-3 py-1.5 text-[13px] font-bold text-gray-900
			       shadow-lg z-10 speech-bubble"
		>
			{phrases[phraseIdx]}
		</div>
	{/if}

	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<svg
		viewBox="0 0 100 110"
		xmlns="http://www.w3.org/2000/svg"
		style="width:{size}px;height:{size * 1.1}px;cursor:pointer"
		class="{animate ? (bouncing ? 'mascot-bounce' : 'mascot-float') : ''}"
		role="button"
		tabindex="0"
		aria-label="{charNames[character]}"
		onclick={handleClick}
	>
		<!-- Shadow -->
		<ellipse cx="50" cy="107" rx="22" ry="5" fill="rgba(0,0,0,0.12)" />

		<!-- Hat varies by character -->
		{#if character === 'yoro' || character === 'skibidi'}
			<!-- Toilet hat -->
			<ellipse cx="50" cy="22" rx="26" ry="8" fill={c.hat} />
			<rect x="38" y="10" width="24" height="14" rx="4" fill="#f0f0f0" />
			<ellipse cx="50" cy="10" rx="13" ry="5" fill={c.hat} />
			<rect x="44" y="6" width="12" height="6" rx="3" fill="#c8c8c8" />
			<circle cx="30" cy="22" r="2.5" fill="#ccc" />
			<circle cx="70" cy="22" r="2.5" fill="#ccc" />
		{:else if character === 'sigma'}
			<!-- Crown hat -->
			<polygon points="30,24 35,10 42,18 50,6 58,18 65,10 70,24" fill={c.hat} />
			<rect x="30" y="22" width="40" height="6" rx="2" fill={c.hat} />
			<circle cx="38" cy="14" r="2" fill="#FFD700" />
			<circle cx="50" cy="8" r="2.5" fill="#FFD700" />
			<circle cx="62" cy="14" r="2" fill="#FFD700" />
		{:else if character === 'ohio'}
			<!-- Corn hat -->
			<ellipse cx="50" cy="18" rx="14" ry="18" fill="#FFD700" />
			<ellipse cx="50" cy="18" rx="10" ry="14" fill="#FFEC80" />
			{#each [0,1,2,3,4] as i}
				<circle cx={42 + i * 4} cy={10 + (i % 2) * 4} r="2.5" fill="#F5C842" />
				<circle cx={42 + i * 4} cy={18 + (i % 2) * 4} r="2.5" fill="#F5C842" />
			{/each}
			<path d="M 44 2 Q 42 -4 38 0" stroke="#46A302" stroke-width="2" fill="none" />
			<path d="M 56 2 Q 58 -4 62 0" stroke="#46A302" stroke-width="2" fill="none" />
		{:else if character === 'rizz'}
			<!-- Sparkle crown -->
			<circle cx="50" cy="14" r="8" fill="none" stroke={c.hat} stroke-width="3" />
			<circle cx="50" cy="14" r="3" fill={c.hat} />
			<line x1="50" y1="4" x2="50" y2="8" stroke={c.hat} stroke-width="2" />
			<line x1="42" y1="8" x2="44" y2="11" stroke={c.hat} stroke-width="2" />
			<line x1="58" y1="8" x2="56" y2="11" stroke={c.hat} stroke-width="2" />
			<circle cx="36" cy="20" r="3" fill={c.hat} opacity="0.6" />
			<circle cx="64" cy="20" r="3" fill={c.hat} opacity="0.6" />
		{:else if character === 'gyatt'}
			<!-- Headphones -->
			<path d="M 26 36 Q 26 12 50 12 Q 74 12 74 36" stroke={c.hat} stroke-width="5" fill="none" />
			<rect x="20" y="30" width="12" height="16" rx="5" fill={c.hat} />
			<rect x="68" y="30" width="12" height="16" rx="5" fill={c.hat} />
			<rect x="22" y="33" width="8" height="10" rx="3" fill="#333" />
			<rect x="70" y="33" width="8" height="10" rx="3" fill="#333" />
		{/if}

		<!-- Body -->
		<ellipse cx="50" cy="78" rx="30" ry="24" fill={c.body} />
		<ellipse cx="50" cy="82" rx="16" ry="12" fill={c.belly} />

		<!-- Head -->
		<circle cx="50" cy="50" r="28" fill={c.body} />

		<!-- Eyes -->
		<ellipse cx="37" cy="46" rx="11" ry={11 * eyeScaleY} fill="white" />
		<ellipse cx="63" cy="46" rx="11" ry={11 * eyeScaleY} fill="white" />
		<circle cx={38} cy={47 + pupilOffset} r="6" fill={c.pupil} />
		<circle cx={64} cy={47 + pupilOffset} r="6" fill={c.pupil} />
		<circle cx="40" cy={44 + pupilOffset} r="2.5" fill="white" />
		<circle cx="66" cy={44 + pupilOffset} r="2.5" fill="white" />
		<circle cx={38} cy={47 + pupilOffset} r="2.5" fill="#1A1A2E" />
		<circle cx={64} cy={47 + pupilOffset} r="2.5" fill="#1A1A2E" />

		<!-- Mouth -->
		{#if mood === 'happy' || mood === 'idle'}
			<path d="M 36 60 Q 50 72 64 60" stroke="#1A1A1A" stroke-width="3" fill="white" stroke-linecap="round" />
			<path d="M 36 60 Q 50 72 64 60 L 64 63 Q 50 75 36 63 Z" fill="white" />
			<line x1="43" y1="60" x2="43" y2="66" stroke="#1A1A1A" stroke-width="1.5" />
			<line x1="50" y1="61" x2="50" y2="67" stroke="#1A1A1A" stroke-width="1.5" />
			<line x1="57" y1="60" x2="57" y2="66" stroke="#1A1A1A" stroke-width="1.5" />
		{:else if mood === 'surprised'}
			<ellipse cx="50" cy="63" rx="8" ry="6" fill="#1A1A1A" />
			<ellipse cx="50" cy="63" rx="5" ry="4" fill="#ff6b6b" />
		{:else if mood === 'sigma'}
			<path d="M 40 62 Q 52 68 62 60" stroke="#1A1A1A" stroke-width="2.5" fill="none" stroke-linecap="round" />
		{:else if mood === 'nuhuh'}
			<line x1="38" y1="64" x2="62" y2="64" stroke="#1A1A1A" stroke-width="3" stroke-linecap="round" />
		{/if}

		<!-- Cheeks -->
		<ellipse cx="28" cy="57" rx="6" ry="4" fill="#ff9999" opacity="0.4" />
		<ellipse cx="72" cy="57" rx="6" ry="4" fill="#ff9999" opacity="0.4" />

		<!-- Arms -->
		<path d="M 22 68 Q 10 72 14 82" stroke={c.limb} stroke-width="8" fill="none" stroke-linecap="round" />
		<circle cx="14" cy="83" r="5" fill={c.limb} />
		<path d="M 78 68 Q 90 72 86 82" stroke={c.limb} stroke-width="8" fill="none" stroke-linecap="round" />
		<circle cx="86" cy="83" r="5" fill={c.limb} />

		<!-- Feet -->
		<ellipse cx="36" cy="100" rx="12" ry="6" fill={c.limb} />
		<ellipse cx="64" cy="100" rx="12" ry="6" fill={c.limb} />

		<!-- Character-specific accessory -->
		{#if character === 'sigma'}
			<!-- Sunglasses -->
			<rect x="27" y="42" rx="3" width="19" height="10" fill="#1A1A2E" opacity="0.7" />
			<rect x="54" y="42" rx="3" width="19" height="10" fill="#1A1A2E" opacity="0.7" />
			<line x1="46" y1="46" x2="54" y2="46" stroke="#1A1A2E" stroke-width="2" />
		{:else if character === 'rizz'}
			<!-- Heart cheeks instead of blush -->
			<text x="26" y="60" font-size="10" text-anchor="middle">💖</text>
			<text x="74" y="60" font-size="10" text-anchor="middle">💖</text>
		{/if}
	</svg>
</div>

<style>
	@keyframes float {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-6px); }
	}
	@keyframes bounce {
		0% { transform: scale(1) translateY(0); }
		20% { transform: scale(1.15, 0.9) translateY(0); }
		40% { transform: scale(0.9, 1.1) translateY(-12px); }
		60% { transform: scale(1.05, 0.95) translateY(0); }
		80% { transform: scale(0.98, 1.02) translateY(-4px); }
		100% { transform: scale(1) translateY(0); }
	}
	@keyframes fadein-up {
		from { opacity: 0; transform: translateX(-50%) translateY(8px); }
		to   { opacity: 1; transform: translateX(-50%) translateY(0); }
	}
	.mascot-float { animation: float 3s ease-in-out infinite; }
	.mascot-bounce { animation: bounce 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97) forwards; }
	.speech-bubble { animation: fadein-up 0.25s ease-out; }
	.speech-bubble::after {
		content: '';
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		border: 6px solid transparent;
		border-top-color: #facc15;
	}
</style>
