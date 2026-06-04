import { writable, derived } from 'svelte/store';
import type { LanguageCode } from '../language/types.js';

/** Whether a translation request is in progress */
export const translateLoading = writable(false);

/** Last translation error message */
export const translateError = writable<string | null>(null);

/** User's preferred target language for real-time translation */
export const translateTargetLang = writable<LanguageCode | null>(null);

/** Whether page auto-translation is active */
export const pageTranslateActive = writable(false);

/** Whether message auto-translation is enabled for the current convo */
export const messageTranslateEnabled = writable(false);

/** Number of cached translations (TM hits) in the current session */
export const tmHitCount = writable(0);

/** Current page source language (detected) */
export const detectedSourceLang = writable<LanguageCode | null>(null);

/** Whether translate is ready (target lang set) */
export const translateReady = derived(translateTargetLang, ($lang) => $lang !== null);
