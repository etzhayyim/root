<script lang="ts">
	import { spring } from 'svelte/motion';
	import { fly, scale } from 'svelte/transition';
	import { Avatar, cn } from '@etzhayyim/design-system';
	import { isSignedIn, clerkUser, displayName, currentOrg, userOrganizations, orgLoading } from '../auth/stores.js';
	import { switchOrganization } from '../auth/passkey.js';
	import { vibesTuning, ALL_MOODS, MOOD_META, MOOD_DEFAULTS, type MoodPreset } from './vibes-store.js';
	import { playClick, playTuneSweep, playMoodSwitch, playOpen, playClose, playAccountSwitch, radioPlay, radioPause, radioResume, radioSetVolume, radioStop } from './tuner-audio.js';
	import { radio, currentTrack, isPlaying, radioPlaylist, radioVolume, radioLoading, type RadioTrack } from './radio-store.js';
	import { theme, ALL_THEMES, THEME_META, type ColorTheme } from '../theme.js';

	function selectColorTheme(t: ColorTheme) {
		theme.set(t);
		playClick();
	}

	const { buttonClass = '' } = $props<{ buttonClass?: string }>();

	let open = $state(false);
	let rootEl: HTMLDivElement | undefined = $state();
	let panelEl: HTMLDivElement | undefined = $state();

	// Teleport action: moves element to document.body to escape backdrop-filter containing block
	function teleport(node: HTMLElement) {
		panelEl = node as HTMLDivElement;
		document.body.appendChild(node);
		return {
			destroy() {
				panelEl = undefined;
				node.remove();
			}
		};
	}

	// === Knob state ===
	let knobDragging = $state(false);
	let knobAngle = spring(0, { stiffness: 0.25, damping: 0.65 });
	let lastDetent = -1;

	// === Fader state ===
	let faderDragging = $state(false);
	let faderY = spring(0, { stiffness: 0.3, damping: 0.7 });

	// Reactive
	let glowColor = $derived(MOOD_META[$vibesTuning.mood].color);
	let energy = $derived($vibesTuning.energy);
	let tempo = $derived($vibesTuning.tempo);

	// VU meter needle angle: -45deg (0) to +45deg (100)
	let vuAngle = $derived(-45 + (energy / 100) * 90);

	// Map energy 0-100 → knob rotation -135 to +135 deg
	const KNOB_MIN = -135;
	const KNOB_MAX = 135;
	function energyToKnobDeg(e: number) { return KNOB_MIN + (e / 100) * (KNOB_MAX - KNOB_MIN); }
	function knobDegToEnergy(deg: number) { return Math.round(((deg - KNOB_MIN) / (KNOB_MAX - KNOB_MIN)) * 100); }

	// Sync knob angle when not dragging
	$effect(() => { if (!knobDragging) knobAngle.set(energyToKnobDeg(energy)); });
	// Sync fader position when not dragging (0=top=100, 1=bottom=0)
	$effect(() => { if (!faderDragging) faderY.set(1 - tempo / 100); });

	// Detent positions on the knob (every 10%)
	const DETENTS = Array.from({ length: 11 }, (_, i) => i * 10);

	function toggle() {
		open = !open;
		if (open) playOpen(); else playClose();
	}
	function close() { if (open) playClose(); open = false; }
	function handleKeydown(e: KeyboardEvent) { if (e.key === 'Escape') close(); }
	function handleDocumentClick(e: MouseEvent) {
		const target = e.target as Node;
		if (rootEl && !rootEl.contains(target) && (!panelEl || !panelEl.contains(target))) close();
	}
	$effect(() => {
		if (!open) return;
		document.addEventListener('click', handleDocumentClick);
		return () => document.removeEventListener('click', handleDocumentClick);
	});

	function selectMood(mood: MoodPreset) {
		vibesTuning.setMood(mood);
		playMoodSwitch();
	}

	// === Knob drag ===
	let knobCenter = { x: 0, y: 0 };
	function startKnob(e: PointerEvent) {
		const el = e.currentTarget as HTMLElement;
		const rect = el.getBoundingClientRect();
		knobCenter = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
		knobDragging = true;
		lastDetent = -1;
		el.setPointerCapture(e.pointerId);
	}
	function moveKnob(e: PointerEvent) {
		if (!knobDragging) return;
		const dx = e.clientX - knobCenter.x;
		const dy = e.clientY - knobCenter.y;
		let rawAngle = Math.atan2(dx, -dy) * (180 / Math.PI); // 0=top, CW positive
		rawAngle = Math.max(KNOB_MIN, Math.min(KNOB_MAX, rawAngle));
		const newEnergy = knobDegToEnergy(rawAngle);
		vibesTuning.setEnergy(newEnergy);
		knobAngle.set(rawAngle);
		// Detent haptic
		const nearestDetent = Math.round(newEnergy / 10);
		if (nearestDetent !== lastDetent) {
			lastDetent = nearestDetent;
			playClick();
		}
		// Tune sweep
		if (Math.abs(newEnergy - (lastDetent * 10)) < 2) {
			playTuneSweep(newEnergy);
		}
	}
	function endKnob() { knobDragging = false; playClick(); }

	// === Fader drag ===
	let faderTrackEl: HTMLDivElement | undefined = $state();
	function startFader(e: PointerEvent) {
		faderDragging = true;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
		moveFader(e);
	}
	function moveFader(e: PointerEvent) {
		if (!faderDragging || !faderTrackEl) return;
		const rect = faderTrackEl.getBoundingClientRect();
		const ratio = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
		const newTempo = Math.round((1 - ratio) * 100);
		vibesTuning.setTempo(newTempo);
		faderY.set(ratio);
		playTuneSweep(newTempo);
	}
	function endFader() { faderDragging = false; playClick(); }

	async function handleSwitchOrg(orgId: string) {
		playAccountSwitch();
		await switchOrganization(orgId);
	}

	// Knob ridges (knurling marks)
	const KNOB_RIDGES = Array.from({ length: 32 }, (_, i) => i * (360 / 32));

	// === Radio state ===
	let radioInitialized = false;

	// Load tracks when mood changes
	$effect(() => {
		const mood = $vibesTuning.mood;
		if (open) radio.loadMood(mood);
	});

	// Sync audio playback with store state
	$effect(() => {
		const track = $currentTrack;
		const playing = $isPlaying;
		const vol = $radioVolume;
		if (!track || !track.audioUrl) {
			if (playing) radioPause();
			return;
		}
		if (playing) {
			radioPlay(track.audioUrl, vol, () => radio.next());
		} else {
			radioPause();
		}
	});

	// Sync volume changes
	$effect(() => {
		radioSetVolume($radioVolume);
	});

	function handleRadioToggle() {
		radio.toggle();
		playClick();
	}
	function handleRadioNext() {
		radio.next();
		playClick();
	}
	function handleRadioPrev() {
		radio.prev();
		playClick();
	}
	function handleRadioTrackSelect(idx: number) {
		radio.selectTrack(idx);
		playClick();
	}

	// Cleanup on panel close
	function closeWithRadioCleanup() {
		close();
	}

	// Format duration mm:ss
	function fmtDur(ms: number): string {
		if (!ms) return '--:--';
		const s = Math.floor(ms / 1000);
		const m = Math.floor(s / 60);
		return `${m}:${String(s % 60).padStart(2, '0')}`;
	}
</script>

<svelte:window onkeydown={open ? handleKeydown : undefined} />

<div class="relative inline-flex items-center" bind:this={rootEl}>
	<!-- Tuner Button: vintage radio knob icon -->
	<button
		class={cn(
			'group relative inline-flex size-10 items-center justify-center rounded-xl bg-transparent transition-all duration-300',
			'text-[var(--gv2-text-primary,#ffffff)] hover:bg-[var(--gv2-bg-hover,#252525)]',
			open && 'ring-2 ring-offset-1 ring-offset-transparent',
			buttonClass
		)}
		style={open ? `ring-color: ${glowColor}; box-shadow: 0 0 16px ${glowColor}40` : ''}
		onclick={toggle}
		aria-haspopup="dialog"
		aria-expanded={open}
		aria-label="Open tuner"
	>
		<!-- Knob icon with rotation tracking energy -->
		<svg width="22" height="22" viewBox="0 0 24 24" class="transition-transform duration-500" style="transform: rotate({energy * 2.7 - 135}deg)">
			<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4" />
			<circle cx="12" cy="12" r="7" fill="currentColor" opacity="0.15" />
			<circle cx="12" cy="12" r="4" fill="currentColor" opacity="0.3" />
			<!-- Knob indicator line -->
			<line x1="12" y1="12" x2="12" y2="3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
		</svg>
		<span
			class="absolute -bottom-0.5 -right-0.5 size-2.5 rounded-full border border-[var(--gv2-bg-primary,#1a1a1a)] transition-colors duration-300"
			style="background: {glowColor}"
		></span>
	</button>

	<!-- Tuner Panel (teleported to body to escape backdrop-filter stacking context) -->
	{#if open}
		<div
			use:teleport
			class="fixed left-3 top-[calc(var(--gv2-header-height,56px)+4px)] z-[1000] flex w-[min(90vw,360px)] flex-col overflow-hidden rounded-2xl border border-[#2a2520] shadow-[0_8px_40px_rgba(0,0,0,0.6)]"
			style="background: linear-gradient(175deg, #1c1814 0%, #12100d 40%, #0e0c0a 100%)"
			role="dialog"
			aria-label="Tuner"
			in:fly={{ y: -16, duration: 320 }}
			out:fly={{ y: -10, duration: 220 }}
		>
			<!-- Brushed metal texture overlay -->
			<div class="pointer-events-none absolute inset-0 opacity-[0.03]"
				style="background: repeating-linear-gradient(90deg, transparent, transparent 1px, rgba(255,255,255,0.1) 1px, rgba(255,255,255,0.1) 2px)"
			></div>

			<!-- Warm ambient glow (vacuum tube feel) -->
			<div
				class="pointer-events-none absolute -top-16 left-1/2 -translate-x-1/2 h-40 w-40 rounded-full opacity-15 blur-3xl transition-all duration-1000"
				style="background: {glowColor}"
			></div>

			<!-- === HEADER: Vintage label plate === -->
			<header class="relative flex items-center justify-between px-4 pt-3.5 pb-1">
				<div class="flex items-center gap-2.5">
					<span class="text-[11px] font-bold uppercase tracking-[0.25em] text-[#8a7e6b]">Tuner</span>
					<div class="flex items-center gap-1 rounded-sm border border-[#3a3228]/60 bg-[#1a1610] px-2 py-0.5">
						<span class="text-[10px]">{MOOD_META[$vibesTuning.mood].emoji}</span>
						<span class="text-[9px] font-semibold uppercase tracking-wider" style="color: {glowColor}">{MOOD_META[$vibesTuning.mood].label}</span>
					</div>
				</div>
				<button
					class="inline-flex size-7 items-center justify-center rounded text-[#5a5040] hover:text-[#8a7e6b] transition-colors"
					onclick={close} aria-label="Close"
				>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
						<line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
					</svg>
				</button>
			</header>

			<!-- === VU METER === -->
			<div class="relative mx-4 mt-2 mb-1 h-[72px] overflow-hidden rounded-lg border border-[#2a2520]/80"
				style="background: linear-gradient(180deg, #f5f0e6 0%, #e8e0d0 100%)"
			>
				<!-- Scale markings -->
				<div class="absolute inset-x-0 top-2 flex justify-between px-6">
					{#each [0, 20, 40, 60, 80, 100] as mark}
						<span class="text-[7px] font-bold tabular-nums text-[#4a4035]">{mark}</span>
					{/each}
				</div>
				<!-- Scale arc lines -->
				<svg class="absolute inset-0 w-full h-full" viewBox="0 0 320 72" preserveAspectRatio="none">
					<!-- Main arc -->
					<path d="M 30 60 Q 160 -10 290 60" fill="none" stroke="#8a7e6b" stroke-width="0.5" />
					<!-- Tick marks on arc -->
					{#each Array(21) as _, i}
						{@const t = i / 20}
						{@const x = 30 + t * 260}
						{@const y = 60 - Math.sin(t * Math.PI) * 35}
						<line x1={x} y1={y} x2={x} y2={y + (i % 5 === 0 ? 6 : 3)} stroke="#6a6050" stroke-width={i % 5 === 0 ? '1' : '0.5'} />
					{/each}
					<!-- Red zone (80-100) -->
					<path d="M 238 25 Q 264 35 290 60" fill="none" stroke="#c44" stroke-width="1.5" opacity="0.6" />
				</svg>
				<!-- VU Needle -->
				<div
					class="absolute bottom-1 left-1/2 h-[52px] w-[2px] origin-bottom transition-transform"
					style="
						transform: translateX(-1px) rotate({vuAngle}deg);
						background: linear-gradient(to top, #1a1410, #c44 70%, #c44);
						box-shadow: 0 0 3px rgba(200,68,68,0.3);
						transition-duration: {knobDragging ? '50ms' : '600ms'};
						transition-timing-function: {knobDragging ? 'linear' : 'cubic-bezier(0.34, 1.56, 0.64, 1)'};
					"
				></div>
				<!-- Needle pivot -->
				<div class="absolute bottom-0 left-1/2 -translate-x-1/2 size-3 rounded-full bg-[#2a2018] border border-[#4a4035]"></div>
				<!-- VU label -->
				<span class="absolute bottom-1 right-3 text-[7px] font-bold tracking-widest text-[#8a7e6b]">VU</span>
			</div>

			<!-- === MAIN KNOB + FADER ROW === -->
			<div class="flex items-start gap-3 px-4 py-3">

				<!-- KNOB: Analog rotary with knurling -->
				<div class="flex flex-col items-center gap-1.5 flex-1">
					<span class="text-[8px] font-bold uppercase tracking-[0.2em] text-[#5a5040]">Energy</span>
					<!-- Knob housing -->
					<div class="relative flex size-[120px] items-center justify-center">
						<!-- Scale markings around knob -->
						{#each DETENTS as val}
							{@const deg = energyToKnobDeg(val)}
							{@const rad = deg * Math.PI / 180}
							{@const cx = 60 + Math.sin(rad) * 54}
							{@const cy = 60 - Math.cos(rad) * 54}
							<span
								class="absolute text-[7px] font-bold tabular-nums"
								style="left: {cx - 5}px; top: {cy - 5}px; color: {val <= energy ? glowColor : '#3a3228'}"
							>{val}</span>
						{/each}

						<!-- Outer ring (bezel) -->
						<div
							class="absolute size-[96px] rounded-full"
							style="
								background: conic-gradient(from {KNOB_MIN - 90}deg, {glowColor}00 0%, {glowColor}40 {energy}%, {glowColor}00 {energy}%);
								box-shadow: 0 0 20px {glowColor}15;
							"
						></div>

						<!-- Knob body -->
						<div
							class="relative flex size-[80px] cursor-grab items-center justify-center rounded-full active:cursor-grabbing"
							style="
								background: radial-gradient(circle at 38% 32%, #3a3228 0%, #201c16 50%, #151210 100%);
								box-shadow: 0 4px 16px rgba(0,0,0,0.6), inset 0 1px 2px rgba(255,255,255,0.06), 0 0 0 2px #2a2520;
							"
							role="slider"
							aria-label="Energy level"
							aria-valuenow={energy}
							aria-valuemin={0}
							aria-valuemax={100}
							tabindex={0}
							onpointerdown={startKnob}
							onpointermove={moveKnob}
							onpointerup={endKnob}
							onpointercancel={endKnob}
						>
							<!-- Knurling ridges -->
							{#each KNOB_RIDGES as ridgeDeg}
								<div
									class="absolute h-[2px] w-[36px] opacity-[0.07]"
									style="
										transform: rotate({ridgeDeg + $knobAngle}deg);
										background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3) 20%, rgba(255,255,255,0.3) 80%, transparent);
									"
								></div>
							{/each}

							<!-- Center cap -->
							<div
								class="absolute size-[24px] rounded-full"
								style="
									background: radial-gradient(circle at 40% 35%, #2a2520, #151210);
									box-shadow: inset 0 1px 3px rgba(0,0,0,0.5), 0 0 4px {glowColor}10;
								"
							></div>

							<!-- Indicator line (pointer) -->
							<div
								class="absolute top-[6px] left-1/2 h-[28px] w-[2.5px] -translate-x-1/2 origin-bottom rounded-full"
								style="
									transform: translateX(-1.25px) rotate({$knobAngle}deg);
									transform-origin: center 34px;
									background: linear-gradient(to top, transparent 0%, {glowColor} 40%, {glowColor});
									box-shadow: 0 0 4px {glowColor}80;
								"
							></div>
						</div>
					</div>
					<!-- Digital readout -->
					<div
						class="flex items-baseline gap-0.5 rounded border border-[#2a2520] bg-[#0a0908] px-2.5 py-1"
						style="box-shadow: inset 0 1px 4px rgba(0,0,0,0.5)"
					>
						<span class="text-[20px] font-mono font-bold tabular-nums tracking-tight" style="color: {glowColor}; text-shadow: 0 0 8px {glowColor}40">{energy}</span>
						<span class="text-[8px] font-bold text-[#5a5040]">%</span>
					</div>
				</div>

				<!-- FADER: Analog vertical slider (mixing desk style) -->
				<div class="flex flex-col items-center gap-1.5 w-[52px]">
					<span class="text-[8px] font-bold uppercase tracking-[0.2em] text-[#5a5040]">Tempo</span>
					<div
						class="relative h-[130px] w-[32px] rounded-md overflow-hidden"
						style="
							background: linear-gradient(180deg, #151210 0%, #1a1610 100%);
							box-shadow: inset 0 2px 6px rgba(0,0,0,0.6), 0 0 0 1px #2a2520;
						"
						bind:this={faderTrackEl}
					>
						<!-- Track groove -->
						<div class="absolute left-1/2 top-2 bottom-2 w-[3px] -translate-x-1/2 rounded-full"
							style="background: linear-gradient(180deg, #0a0908, #151210); box-shadow: inset 0 1px 2px rgba(0,0,0,0.5)"
						></div>

						<!-- Fill glow -->
						<div
							class="absolute left-1/2 bottom-2 w-[3px] -translate-x-1/2 rounded-full transition-all duration-150"
							style="
								top: calc({$faderY * 100}% + 8px);
								background: linear-gradient(180deg, {glowColor}20, {glowColor}60);
								box-shadow: 0 0 6px {glowColor}30;
							"
						></div>

						<!-- Tick marks -->
						{#each [0, 25, 50, 75, 100] as mark}
							{@const y = (1 - mark / 100) * 100}
							<div class="absolute left-0 h-px w-[6px]" style="top: calc({y}% + 4px); background: #3a3228"></div>
							<div class="absolute right-0 h-px w-[6px]" style="top: calc({y}% + 4px); background: #3a3228"></div>
						{/each}

						<!-- Fader cap -->
						<div
							class="absolute left-1/2 -translate-x-1/2 w-[26px] h-[18px] cursor-grab rounded-[3px] active:cursor-grabbing touch-manipulation"
							style="
								top: calc({$faderY * 100}% - 1px);
								background: linear-gradient(180deg, #3a3228 0%, #2a2520 40%, #201c16 100%);
								box-shadow: 0 2px 6px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.08), 0 0 0 1px #2a2520;
							"
							role="slider"
							aria-label="Tempo"
							aria-valuenow={tempo}
							tabindex={0}
							onpointerdown={startFader}
							onpointermove={moveFader}
							onpointerup={endFader}
							onpointercancel={endFader}
						>
							<!-- Fader grip lines -->
							<div class="absolute inset-x-[5px] top-[5px] h-px bg-white/[0.06]"></div>
							<div class="absolute inset-x-[5px] top-[8px] h-px bg-white/[0.06]"></div>
							<div class="absolute inset-x-[5px] top-[11px] h-px bg-white/[0.06]"></div>
						</div>
					</div>
					<!-- Readout -->
					<div class="flex items-baseline gap-0.5 rounded border border-[#2a2520] bg-[#0a0908] px-2 py-0.5"
						style="box-shadow: inset 0 1px 4px rgba(0,0,0,0.5)"
					>
						<span class="text-[14px] font-mono font-bold tabular-nums" style="color: {glowColor}; text-shadow: 0 0 6px {glowColor}30">{tempo}</span>
					</div>
				</div>
			</div>

			<!-- === MOOD SELECTOR: Rotary switch positions === -->
			<div class="px-4 pb-2.5">
				<div class="flex items-center gap-1 mb-2">
					<span class="text-[8px] font-bold uppercase tracking-[0.2em] text-[#5a5040]">Mood</span>
					<div class="flex-1 h-px bg-[#2a2520]/60"></div>
				</div>
				<div class="flex gap-1">
					{#each ALL_MOODS as mood, i}
						{@const meta = MOOD_META[mood]}
						{@const isActive = $vibesTuning.mood === mood}
						<button
							class={cn(
								'flex flex-1 flex-col items-center gap-1 rounded-lg py-2 transition-all duration-200 touch-manipulation border',
								isActive
									? 'border-[#3a3228]'
									: 'border-transparent hover:border-[#2a2520]/40 active:scale-95'
							)}
							style={isActive
								? `background: linear-gradient(180deg, ${meta.color}12, ${meta.color}06); box-shadow: inset 0 0 12px ${meta.color}10, 0 0 8px ${meta.color}08`
								: 'background: transparent'}
							onclick={() => selectMood(mood)}
							in:scale={{ start: 0.85, delay: i * 40, duration: 250 }}
						>
							<!-- LED indicator -->
							<div
								class="size-[6px] rounded-full transition-all duration-300"
								style={isActive
									? `background: ${meta.color}; box-shadow: 0 0 6px ${meta.color}80, 0 0 12px ${meta.color}40`
									: 'background: #2a2520'}
							></div>
							<span class="text-[14px]">{meta.emoji}</span>
							<span
								class="text-[7px] font-bold uppercase tracking-wider transition-colors duration-200"
								style="color: {isActive ? meta.color : '#4a4035'}"
							>{meta.label}</span>
						</button>
					{/each}
				</div>
			</div>

			<!-- === DIVIDER: Engraved line === -->
			<div class="mx-4 h-px" style="background: linear-gradient(90deg, transparent, #2a2520 20%, #2a2520 80%, transparent)"></div>

			<!-- === RADIO: Now Playing + Controls === -->
			<div class="px-4 py-2.5">
				<div class="flex items-center gap-1 mb-2">
					<span class="text-[8px] font-bold uppercase tracking-[0.2em] text-[#5a5040]">Radio</span>
					<div class="flex-1 h-px bg-[#2a2520]/60"></div>
					{#if $radioLoading}
						<div class="size-3 animate-spin rounded-full border border-[#2a2520] border-t-[#5a5040]"></div>
					{/if}
				</div>

				<!-- Now Playing Display (tape deck style) -->
				<div
					class="relative mb-2 overflow-hidden rounded-lg border border-[#2a2520]/80 px-3 py-2"
					style="background: linear-gradient(180deg, #0e0c0a 0%, #151210 100%); box-shadow: inset 0 1px 4px rgba(0,0,0,0.5)"
				>
					{#if $currentTrack}
						<!-- Track info marquee -->
						<div class="flex items-center gap-2 mb-1.5">
							<!-- On-air indicator -->
							{#if $isPlaying}
								<div class="flex items-center gap-1">
									<div class="size-[5px] rounded-full animate-pulse" style="background: {glowColor}; box-shadow: 0 0 4px {glowColor}80"></div>
									<span class="text-[6px] font-bold uppercase tracking-wider" style="color: {glowColor}">On Air</span>
								</div>
							{:else}
								<span class="text-[6px] font-bold uppercase tracking-wider text-[#3a3228]">Paused</span>
							{/if}
							<div class="flex-1"></div>
							<span class="text-[8px] font-mono tabular-nums text-[#5a5040]">{fmtDur($currentTrack.durationMs)}</span>
						</div>
						<p class="truncate text-[12px] font-medium" style="color: {glowColor}; text-shadow: 0 0 6px {glowColor}30">{$currentTrack.title}</p>
						<p class="truncate text-[9px] text-[#6a6050]">{$currentTrack.artistName}</p>
					{:else}
						<p class="text-center text-[10px] text-[#3a3228] py-1">No station tuned</p>
					{/if}
				</div>

				<!-- Transport controls (tape deck: prev, play/pause, next) -->
				<div class="flex items-center justify-center gap-3 mb-2">
					<button
						class="inline-flex size-8 items-center justify-center rounded-lg transition-all duration-150 active:scale-90 border border-[#2a2520] hover:border-[#3a3228]"
						style="background: linear-gradient(180deg, #1a1610, #12100d)"
						onclick={handleRadioPrev}
						aria-label="Previous track"
					>
						<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" class="text-[#8a7e6b]">
							<path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
						</svg>
					</button>

					<button
						class="inline-flex size-10 items-center justify-center rounded-full transition-all duration-150 active:scale-90 border-2"
						style="
							border-color: {$isPlaying ? glowColor : '#3a3228'};
							background: linear-gradient(180deg, #201c16, #151210);
							box-shadow: {$isPlaying ? `0 0 12px ${glowColor}30` : 'none'};
						"
						onclick={handleRadioToggle}
						aria-label={$isPlaying ? 'Pause' : 'Play'}
					>
						{#if $isPlaying}
							<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="color: {glowColor}">
								<path d="M6 19h4V5H6zm8-14v14h4V5z"/>
							</svg>
						{:else}
							<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="color: {glowColor}">
								<path d="M8 5v14l11-7z"/>
							</svg>
						{/if}
					</button>

					<button
						class="inline-flex size-8 items-center justify-center rounded-lg transition-all duration-150 active:scale-90 border border-[#2a2520] hover:border-[#3a3228]"
						style="background: linear-gradient(180deg, #1a1610, #12100d)"
						onclick={handleRadioNext}
						aria-label="Next track"
					>
						<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" class="text-[#8a7e6b]">
							<path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6z"/>
						</svg>
					</button>
				</div>

				<!-- Volume micro-fader -->
				<div class="flex items-center gap-2">
					<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#5a5040" stroke-width="2" class="shrink-0">
						<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
					</svg>
					<input
						type="range"
						min="0" max="1" step="0.01"
						value={$radioVolume}
						oninput={(e) => radio.setVolume(Number((e.target as HTMLInputElement).value))}
						class="h-1 w-full appearance-none rounded-full cursor-pointer"
						style="background: linear-gradient(90deg, {glowColor} 0%, {glowColor} {$radioVolume * 100}%, #2a2520 {$radioVolume * 100}%)"
						aria-label="Volume"
					/>
					<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#5a5040" stroke-width="2" class="shrink-0">
						<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
						<path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
					</svg>
				</div>

				<!-- Playlist (scrollable, max 3 visible) -->
				{#if $radioPlaylist.length > 0}
					<div class="mt-2 max-h-[72px] overflow-y-auto scrollbar-none flex flex-col gap-0.5">
						{#each $radioPlaylist as track, i (track.id)}
							{@const isCurrent = $currentTrack?.id === track.id}
							<button
								class="flex items-center gap-2 rounded-md px-2 py-1 text-left transition-all duration-150 w-full touch-manipulation"
								style={isCurrent
									? `background: ${glowColor}10; border-left: 2px solid ${glowColor}`
									: 'border-left: 2px solid transparent'}
								onclick={() => handleRadioTrackSelect(i)}
							>
								{#if isCurrent && $isPlaying}
									<!-- Animated bars -->
									<div class="flex items-end gap-px h-3 w-3 shrink-0">
										<div class="w-[2px] bg-current animate-pulse rounded-sm" style="height: 8px; color: {glowColor}; animation-delay: 0ms"></div>
										<div class="w-[2px] bg-current animate-pulse rounded-sm" style="height: 12px; color: {glowColor}; animation-delay: 150ms"></div>
										<div class="w-[2px] bg-current animate-pulse rounded-sm" style="height: 6px; color: {glowColor}; animation-delay: 300ms"></div>
									</div>
								{:else}
									<span class="text-[8px] font-mono tabular-nums text-[#3a3228] w-3 text-center shrink-0">{i + 1}</span>
								{/if}
								<div class="min-w-0 flex-1">
									<p class="truncate text-[10px] font-medium" style="color: {isCurrent ? glowColor : '#8a7e6b'}">{track.title}</p>
									<p class="truncate text-[8px] text-[#4a4035]">{track.artistName}</p>
								</div>
								<span class="text-[7px] font-mono tabular-nums text-[#3a3228] shrink-0">{fmtDur(track.durationMs)}</span>
							</button>
						{/each}
					</div>
				{:else if !$radioLoading}
					<p class="mt-2 text-center text-[9px] text-[#2a2520]">No tracks for this mood yet</p>
				{/if}
			</div>

			<!-- === DIVIDER: Engraved line === -->
			<div class="mx-4 h-px" style="background: linear-gradient(90deg, transparent, #2a2520 20%, #2a2520 80%, transparent)"></div>

			<!-- === COLOR THEME SELECTOR === -->
		<div class="px-4 pb-2.5">
			<div class="flex items-center gap-1 mb-2">
				<span class="text-[8px] font-bold uppercase tracking-[0.2em] text-[#5a5040]">Theme</span>
				<div class="flex-1 h-px bg-[#2a2520]/60"></div>
			</div>
			<div class="grid grid-cols-4 gap-1.5">
				{#each ALL_THEMES as t}
					{@const meta = THEME_META[t]}
					{@const isActive = $theme === t}
					<button
						class="flex flex-col items-center gap-1 rounded-lg py-1.5 transition-all duration-200 touch-manipulation border {isActive ? 'border-[#3a3228]' : 'border-transparent hover:border-[#2a2520]/40 active:scale-95'}"
						style={isActive ? `background: ${meta.swatch}18; box-shadow: inset 0 0 8px ${meta.swatch}10` : ''}
						onclick={() => selectColorTheme(t)}
					>
						<div
							class="size-5 rounded-full border transition-all duration-300"
							style="background: {meta.swatch}; border-color: {isActive ? glowColor : '#2a2520'}; {isActive ? `box-shadow: 0 0 6px ${glowColor}60` : ''}"
						></div>
						<span
							class="text-[7px] font-bold uppercase tracking-wider transition-colors duration-200"
							style="color: {isActive ? glowColor : '#4a4035'}"
						>{meta.label}</span>
					</button>
				{/each}
			</div>
		</div>

		<!-- === DIVIDER: Engraved line === -->
		<div class="mx-4 h-px" style="background: linear-gradient(90deg, transparent, #2a2520 20%, #2a2520 80%, transparent)"></div>

		<!-- === ACCOUNT SWITCHER === -->
			{#if $isSignedIn && $clerkUser}
				<div class="px-4 pt-2.5 pb-3.5">
					<div class="flex items-center gap-1 mb-2">
						<span class="text-[8px] font-bold uppercase tracking-[0.2em] text-[#5a5040]">Station</span>
						<div class="flex-1 h-px bg-[#2a2520]/60"></div>
					</div>

					<!-- Current account -->
					<div class="mb-1.5 flex items-center gap-2.5 rounded-lg border border-[#2a2520] bg-[#151210] px-3 py-2">
						<Avatar
							src={$clerkUser.imageUrl}
							fallback={$displayName}
							size="sm"
							class="!border !border-[#3a3228]"
						/>
						<div class="min-w-0 flex-1">
							<p class="truncate text-[12px] font-medium text-[#c8bda8]">{$displayName}</p>
							<p class="truncate text-[10px] text-[#5a5040]">{$currentOrg?.name || 'Personal'}</p>
						</div>
						<!-- On-air LED -->
						<div class="flex flex-col items-center gap-0.5">
							<div class="size-[5px] rounded-full" style="background: {glowColor}; box-shadow: 0 0 4px {glowColor}60"></div>
							<span class="text-[6px] font-bold uppercase tracking-wider text-[#5a5040]">On</span>
						</div>
					</div>

					{#if $orgLoading}
						<div class="flex items-center justify-center py-2">
							<div class="size-3.5 animate-spin rounded-full border-2 border-[#2a2520] border-t-[#5a5040]"></div>
						</div>
					{:else if $userOrganizations.length > 0}
						<div class="flex flex-col gap-0.5 max-h-[100px] overflow-y-auto scrollbar-none">
							{#each $userOrganizations as org (org.id)}
								{@const isCurrent = $currentOrg?.id === org.id}
								<button
									class={cn(
										'flex items-center gap-2.5 rounded-md px-3 py-1.5 text-left transition-all duration-150 touch-manipulation',
										isCurrent ? 'bg-[#1a1610]' : 'hover:bg-[#151210] active:bg-[#1a1610]'
									)}
									onclick={() => handleSwitchOrg(org.id)}
									disabled={isCurrent}
								>
									<!-- Station preset number -->
									<div
										class="flex size-5 shrink-0 items-center justify-center rounded text-[9px] font-bold font-mono"
										style={isCurrent
											? `background: ${glowColor}20; color: ${glowColor}; box-shadow: 0 0 4px ${glowColor}20`
											: 'background: #1a1610; color: #4a4035'}
									>{org.name.charAt(0).toUpperCase()}</div>
									<span class={cn(
										'truncate text-[11px] font-medium',
										isCurrent ? 'text-[#c8bda8]' : 'text-[#5a5040]'
									)}>{org.name}</span>
									{#if isCurrent}
										<svg class="ml-auto h-3 w-3 shrink-0" style="color: {glowColor}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
											<polyline points="20 6 9 17 4 12" />
										</svg>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				</div>
			{:else}
				<div class="px-4 pt-2.5 pb-3.5">
					<p class="text-center text-[10px] text-[#3a3228]">Sign in to switch stations</p>
				</div>
			{/if}

			<!-- Bottom plate label -->
			<div class="flex items-center justify-center pb-2.5">
				<span class="text-[7px] font-bold uppercase tracking-[0.3em] text-[#2a2520]">etzhayyim Audio Co.</span>
			</div>
		</div>
	{/if}
</div>
