import { writable, derived } from 'svelte/store';

/** Mood presets that influence vibes content filtering and visual atmosphere. */
export type MoodPreset = 'chill' | 'hype' | 'focus' | 'explore' | 'cozy';

export interface VibesTuning {
	/** Current mood preset. */
	mood: MoodPreset;
	/** Energy level 0–100: low=calm content, high=intense content. */
	energy: number;
	/** Tempo 0–100: controls content refresh rate and animation speed. */
	tempo: number;
}

const DEFAULT_TUNING: VibesTuning = { mood: 'explore', energy: 50, tempo: 50 };

/** Mood preset → default energy/tempo values. */
export const MOOD_DEFAULTS: Record<MoodPreset, { energy: number; tempo: number }> = {
	chill:   { energy: 20, tempo: 25 },
	hype:    { energy: 90, tempo: 85 },
	focus:   { energy: 40, tempo: 60 },
	explore: { energy: 50, tempo: 50 },
	cozy:    { energy: 15, tempo: 20 },
};

export const MOOD_META: Record<MoodPreset, { label: string; emoji: string; color: string }> = {
	chill:   { label: 'Chill',   emoji: '🌊', color: '#60a5fa' },
	hype:    { label: 'Hype',    emoji: '🔥', color: '#f97316' },
	focus:   { label: 'Focus',   emoji: '🎯', color: '#a78bfa' },
	explore: { label: 'Explore', emoji: '🌍', color: '#4ade80' },
	cozy:    { label: 'Cozy',    emoji: '☕', color: '#fbbf24' },
};

export const ALL_MOODS: MoodPreset[] = ['chill', 'hype', 'focus', 'explore', 'cozy'];

const _tuning = writable<VibesTuning>(DEFAULT_TUNING);

export const vibesTuning = {
	subscribe: _tuning.subscribe,
	set(value: VibesTuning) { _tuning.set(value); },
	update(fn: (current: VibesTuning) => VibesTuning) { _tuning.update(fn); },
	setMood(mood: MoodPreset) {
		const defaults = MOOD_DEFAULTS[mood];
		_tuning.update((t) => ({ ...t, mood, energy: defaults.energy, tempo: defaults.tempo }));
	},
	setEnergy(energy: number) {
		_tuning.update((t) => ({ ...t, energy: Math.max(0, Math.min(100, energy)) }));
	},
	setTempo(tempo: number) {
		_tuning.update((t) => ({ ...t, tempo: Math.max(0, Math.min(100, tempo)) }));
	},
	reset() { _tuning.set(DEFAULT_TUNING); },
};

export const currentMood = derived(_tuning, ($t) => $t.mood);
export const currentEnergy = derived(_tuning, ($t) => $t.energy);
export const currentTempo = derived(_tuning, ($t) => $t.tempo);
export const moodColor = derived(_tuning, ($t) => MOOD_META[$t.mood].color);
