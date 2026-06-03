// Web Audio API sound effects — no external assets required
let audioCtx: AudioContext | null = null;

function getCtx(): AudioContext {
	if (!audioCtx || audioCtx.state === 'closed') {
		audioCtx = new AudioContext();
	}
	return audioCtx;
}

/**
 * Respect `prefers-reduced-motion` as a proxy for "reduced sensory load"
 * when a dedicated `prefers-reduced-sound` (Safari-only today) is absent.
 */
function soundMuted(): boolean {
	if (typeof window === 'undefined') return true;
	try {
		if (window.matchMedia('(prefers-reduced-sound: reduce)').matches) return true;
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return true;
	} catch { /* empty */ }
	return false;
}

function tone(
	freq: number,
	start: number,
	duration: number,
	gain: number,
	ctx: AudioContext,
	type: OscillatorType = 'sine'
) {
	const osc = ctx.createOscillator();
	const g = ctx.createGain();
	osc.connect(g);
	g.connect(ctx.destination);
	osc.type = type;
	osc.frequency.setValueAtTime(freq, ctx.currentTime + start);
	g.gain.setValueAtTime(gain, ctx.currentTime + start);
	g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + duration);
	osc.start(ctx.currentTime + start);
	osc.stop(ctx.currentTime + start + duration + 0.01);
}

/** Duolingo-style success ding: C-E-G ascending */
export function playSuccess() {
	try {
		const ctx = getCtx();
		tone(523, 0, 0.15, 0.25, ctx);      // C5
		tone(659, 0.12, 0.15, 0.25, ctx);   // E5
		tone(784, 0.24, 0.3, 0.3, ctx);     // G5
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/sound.ts: suppressed error", error); }
}

/** Short click pop */
export function playClick() {
	try {
		const ctx = getCtx();
		tone(880, 0, 0.08, 0.18, ctx);
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/sound.ts: suppressed error", error); }
}

/** Notification chime */
export function playNotif() {
	try {
		const ctx = getCtx();
		tone(1046, 0, 0.12, 0.2, ctx);       // C6
		tone(1318, 0.1, 0.2, 0.2, ctx);      // E6
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/sound.ts: suppressed error", error); }
}

/** Sad trombone / fail */
export function playFail() {
	try {
		const ctx = getCtx();
		tone(392, 0, 0.12, 0.2, ctx, 'sawtooth');   // G4
		tone(349, 0.1, 0.12, 0.2, ctx, 'sawtooth');  // F4
		tone(311, 0.2, 0.2, 0.2, ctx, 'sawtooth');   // Eb4
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/sound.ts: suppressed error", error); }
}

/** Streak level-up fanfare */
export function playLevelUp() {
	try {
		const ctx = getCtx();
		tone(523, 0, 0.1, 0.2, ctx);
		tone(659, 0.1, 0.1, 0.2, ctx);
		tone(784, 0.2, 0.1, 0.2, ctx);
		tone(1046, 0.3, 0.4, 0.3, ctx);
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/sound.ts: suppressed error", error); }
}

// ── Nintendo-style feed UX kit (Shannon/Bayes/Graph/TDA/Joucho plan) ──
// Plan: /root/.claude/plans/yoro-etzhayyim-ai-facebook-zazzy-teapot.md

/** Soft "pop" for taps — 40ms, ~-14 LUFS perceived. */
export function playTapSoft() {
	if (soundMuted()) return;
	try { tone(720, 0, 0.04, 0.14, getCtx(), 'sine'); }
	catch (e) { console.warn('[sound] playTapSoft', e); }
}

/** Scroll detent tick (every N cards) — 20ms, ultra-short. */
export function playTick() {
	if (soundMuted()) return;
	try { tone(1400, 0, 0.02, 0.08, getCtx(), 'triangle'); }
	catch (e) { console.warn('[sound] playTick', e); }
}

/** Swipe-like chime (C5, 200ms) — vitality-colored. */
export function playChimeC5() {
	if (soundMuted()) return;
	try { tone(523, 0, 0.2, 0.22, getCtx(), 'sine'); }
	catch (e) { console.warn('[sound] playChimeC5', e); }
}

/** Stress/doom-pause modal — wind bell, calm, low harmonic. */
export function playWindBell() {
	if (soundMuted()) return;
	try {
		const ctx = getCtx();
		tone(880, 0, 0.5, 0.14, ctx, 'sine');
		tone(1320, 0.08, 0.4, 0.08, ctx, 'sine');
	} catch (e) { console.warn('[sound] playWindBell', e); }
}

/** Kyu/Dan promotion fanfare — reuses existing level-up, capped once/day by caller. */
export { playLevelUp as playRankPromotion };

/** Skibidi-style toilet flush descending */
export function playSkibidi() {
	try {
		const ctx = getCtx();
		const osc = ctx.createOscillator();
		const g = ctx.createGain();
		osc.connect(g);
		g.connect(ctx.destination);
		osc.type = 'sawtooth';
		osc.frequency.setValueAtTime(600, ctx.currentTime);
		osc.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 0.4);
		g.gain.setValueAtTime(0.25, ctx.currentTime);
		g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
		osc.start(ctx.currentTime);
		osc.stop(ctx.currentTime + 0.5);
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/sound.ts: suppressed error", error); }
}
