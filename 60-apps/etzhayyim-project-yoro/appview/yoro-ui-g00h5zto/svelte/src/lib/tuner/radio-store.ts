import { writable, derived } from 'svelte/store';
import type { MoodPreset } from './vibes-store.js';

const PDS = 'https://atproto.etzhayyim.com';

/** A track from tuner.etzhayyim.com musician actors. */
export interface RadioTrack {
	id: string;
	title: string;
	artistName: string;
	audioUrl: string;
	coverUrl: string;
	durationMs: number;
	genre: string;
	mood: string;
	bpm: number;
}

export interface RadioState {
	/** Currently playing track (null = stopped). */
	track: RadioTrack | null;
	/** Loaded playlist for current mood. */
	playlist: RadioTrack[];
	/** Current index in playlist. */
	index: number;
	/** Playback state. */
	playing: boolean;
	/** Volume 0–1. */
	volume: number;
	/** Loading tracks from API. */
	loading: boolean;
	/** Error message if any. */
	error: string;
}

const DEFAULT: RadioState = {
	track: null,
	playlist: [],
	index: 0,
	playing: false,
	volume: 0.7,
	loading: false,
	error: '',
};

const _radio = writable<RadioState>(DEFAULT);

/** Map vibes mood → tuner mood filter. */
const MOOD_MAP: Record<MoodPreset, string> = {
	chill: 'chill',
	hype: 'hype',
	focus: 'focus',
	explore: 'chill',
	cozy: 'chill',
};

/** Fetch tracks for a mood from tuner.etzhayyim.com via PDS XRPC. */
async function fetchTracks(mood: MoodPreset): Promise<RadioTrack[]> {
	const tunerMood = MOOD_MAP[mood] || 'chill';
	try {
		const res = await fetch(`${PDS}/xrpc/com.etzhayyim.apps.tuner.getStationTracks`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ mood: tunerMood, limit: 20 }),
		});
		if (!res.ok) return [];
		const data = await res.json();
		return (data.items || []).map((n: Record<string, unknown>) => ({
			id: (n.id as string) || '',
			title: (n.title as string) || 'Untitled',
			artistName: (n.artistName as string) || 'Unknown',
			audioUrl: (n.audioUrl as string) || '',
			coverUrl: (n.coverUrl as string) || '',
			durationMs: Number(n.durationMs) || 0,
			genre: (n.genre as string) || '',
			mood: (n.mood as string) || '',
			bpm: Number(n.bpm) || 120,
		}));
	} catch {
		return [];
	}
}

export const radio = {
	subscribe: _radio.subscribe,

	/** Load tracks for a mood and reset playlist. */
	async loadMood(mood: MoodPreset) {
		_radio.update(s => ({ ...s, loading: true, error: '' }));
		const tracks = await fetchTracks(mood);
		_radio.update(s => ({
			...s,
			playlist: tracks,
			index: 0,
			track: tracks[0] || null,
			loading: false,
		}));
	},

	/** Start or resume playback. */
	play() {
		_radio.update(s => {
			if (!s.track && s.playlist.length > 0) {
				return { ...s, track: s.playlist[0], index: 0, playing: true };
			}
			return { ...s, playing: true };
		});
	},

	/** Pause playback. */
	pause() {
		_radio.update(s => ({ ...s, playing: false }));
	},

	/** Toggle play/pause. */
	toggle() {
		_radio.update(s => {
			if (!s.track && s.playlist.length > 0) {
				return { ...s, track: s.playlist[0], index: 0, playing: true };
			}
			return { ...s, playing: !s.playing };
		});
	},

	/** Skip to next track. */
	next() {
		_radio.update(s => {
			if (s.playlist.length === 0) return s;
			const nextIdx = (s.index + 1) % s.playlist.length;
			return { ...s, index: nextIdx, track: s.playlist[nextIdx] || null, playing: true };
		});
	},

	/** Skip to previous track. */
	prev() {
		_radio.update(s => {
			if (s.playlist.length === 0) return s;
			const prevIdx = (s.index - 1 + s.playlist.length) % s.playlist.length;
			return { ...s, index: prevIdx, track: s.playlist[prevIdx] || null, playing: true };
		});
	},

	/** Set volume (0–1). */
	setVolume(v: number) {
		_radio.update(s => ({ ...s, volume: Math.max(0, Math.min(1, v)) }));
	},

	/** Select a specific track from playlist. */
	selectTrack(index: number) {
		_radio.update(s => {
			if (index < 0 || index >= s.playlist.length) return s;
			return { ...s, index, track: s.playlist[index] || null, playing: true };
		});
	},

	/** Reset to default state. */
	reset() {
		_radio.set(DEFAULT);
	},
};

export const currentTrack = derived(_radio, $r => $r.track);
export const isPlaying = derived(_radio, $r => $r.playing);
export const radioPlaylist = derived(_radio, $r => $r.playlist);
export const radioVolume = derived(_radio, $r => $r.volume);
export const radioLoading = derived(_radio, $r => $r.loading);
