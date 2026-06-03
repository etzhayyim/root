/**
 * Web Audio API sound effects for the analog tuner.
 * All sounds are synthesized — no external files needed.
 */

let ctx: AudioContext | null = null;

function getCtx(): AudioContext {
	if (!ctx) ctx = new AudioContext();
	if (ctx.state === 'suspended') ctx.resume();
	return ctx;
}

/** Soft click — dial detent feedback. */
export function playClick() {
	try {
		const ac = getCtx();
		const osc = ac.createOscillator();
		const gain = ac.createGain();
		osc.type = 'sine';
		osc.frequency.setValueAtTime(3200, ac.currentTime);
		osc.frequency.exponentialRampToValueAtTime(1200, ac.currentTime + 0.03);
		gain.gain.setValueAtTime(0.08, ac.currentTime);
		gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.05);
		osc.connect(gain).connect(ac.destination);
		osc.start(ac.currentTime);
		osc.stop(ac.currentTime + 0.05);
	} catch { /* silent fail on unsupported browsers */ }
}

/** Tuning sweep — continuous dial rotation feedback. */
export function playTuneSweep(frequency: number) {
	try {
		const ac = getCtx();
		const osc = ac.createOscillator();
		const gain = ac.createGain();
		osc.type = 'sine';
		osc.frequency.setValueAtTime(200 + frequency * 8, ac.currentTime);
		gain.gain.setValueAtTime(0.03, ac.currentTime);
		gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.08);
		osc.connect(gain).connect(ac.destination);
		osc.start(ac.currentTime);
		osc.stop(ac.currentTime + 0.08);
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed error", error); }
}

/** Mood switch — warm chord confirmation. */
export function playMoodSwitch() {
	try {
		const ac = getCtx();
		const freqs = [440, 554, 659];
		for (const freq of freqs) {
			const osc = ac.createOscillator();
			const gain = ac.createGain();
			osc.type = 'sine';
			osc.frequency.setValueAtTime(freq, ac.currentTime);
			gain.gain.setValueAtTime(0.06, ac.currentTime);
			gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.3);
			osc.connect(gain).connect(ac.destination);
			osc.start(ac.currentTime);
			osc.stop(ac.currentTime + 0.3);
		}
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed error", error); }
}

/** Panel open — rising whoosh. */
export function playOpen() {
	try {
		const ac = getCtx();
		const osc = ac.createOscillator();
		const gain = ac.createGain();
		osc.type = 'sine';
		osc.frequency.setValueAtTime(180, ac.currentTime);
		osc.frequency.exponentialRampToValueAtTime(600, ac.currentTime + 0.15);
		gain.gain.setValueAtTime(0.05, ac.currentTime);
		gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.2);
		osc.connect(gain).connect(ac.destination);
		osc.start(ac.currentTime);
		osc.stop(ac.currentTime + 0.2);
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed error", error); }
}

/** Panel close — falling whoosh. */
export function playClose() {
	try {
		const ac = getCtx();
		const osc = ac.createOscillator();
		const gain = ac.createGain();
		osc.type = 'sine';
		osc.frequency.setValueAtTime(600, ac.currentTime);
		osc.frequency.exponentialRampToValueAtTime(180, ac.currentTime + 0.12);
		gain.gain.setValueAtTime(0.04, ac.currentTime);
		gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.15);
		osc.connect(gain).connect(ac.destination);
		osc.start(ac.currentTime);
		osc.stop(ac.currentTime + 0.15);
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed error", error); }
}

/** Account switch — double click. */
export function playAccountSwitch() {
	try {
		const ac = getCtx();
		for (let i = 0; i < 2; i++) {
			const osc = ac.createOscillator();
			const gain = ac.createGain();
			osc.type = 'sine';
			osc.frequency.setValueAtTime(1800, ac.currentTime + i * 0.08);
			gain.gain.setValueAtTime(0.07, ac.currentTime + i * 0.08);
			gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + i * 0.08 + 0.06);
			osc.connect(gain).connect(ac.destination);
			osc.start(ac.currentTime + i * 0.08);
			osc.stop(ac.currentTime + i * 0.08 + 0.06);
		}
	} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed error", error); }
}

// === Radio Music Playback (HTML5 Audio) ===

let radioAudio: HTMLAudioElement | null = null;
let _onEnded: (() => void) | null = null;

/** Get or create the shared radio Audio element. */
function getRadioAudio(): HTMLAudioElement {
	if (!radioAudio) {
		radioAudio = new Audio();
		radioAudio.crossOrigin = 'anonymous';
		radioAudio.addEventListener('ended', () => { _onEnded?.(); });
	}
	return radioAudio;
}

/** Play a track URL. Calls onEnded when track finishes. */
export function radioPlay(url: string, volume: number, onEnded?: () => void) {
	const audio = getRadioAudio();
	_onEnded = onEnded || null;
	if (audio.src !== url) {
		audio.src = url;
		audio.load();
	}
	audio.volume = Math.max(0, Math.min(1, volume));
	audio.play().catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed async error", error); });
}

/** Pause radio playback. */
export function radioPause() {
	radioAudio?.pause();
}

/** Resume radio playback. */
export function radioResume(volume: number) {
	if (!radioAudio) return;
	radioAudio.volume = Math.max(0, Math.min(1, volume));
	radioAudio.play().catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/tuner/tuner-audio.ts: suppressed async error", error); });
}

/** Set radio volume (0–1). */
export function radioSetVolume(v: number) {
	if (radioAudio) radioAudio.volume = Math.max(0, Math.min(1, v));
}

/** Get current playback position (seconds). */
export function radioGetTime(): number {
	return radioAudio?.currentTime || 0;
}

/** Get track duration (seconds). */
export function radioGetDuration(): number {
	return radioAudio?.duration || 0;
}

/** Stop and reset radio. */
export function radioStop() {
	if (radioAudio) {
		radioAudio.pause();
		radioAudio.src = '';
		_onEnded = null;
	}
}
