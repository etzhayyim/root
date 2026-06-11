/**
 * inference-consent-state.svelte.ts — Shared state for browser inference TOS consent gate.
 *
 * Module-level singleton (`$state` at file scope) so the consent modal can be
 * triggered from any component — layout header "推論に参加" button, credits page
 * "Start Evolution" / "Join Inference" / "Retry" buttons.
 *
 * **Consent flow:**
 * 1. Caller awaits `requestInferenceConsent()`.
 * 2. If `localStorage('yoro-inference-tos-accepted') === 'accepted'`, resolves immediately.
 * 3. Otherwise, `InferenceConsent.svelte` modal becomes visible.
 * 4. User must scroll to bottom → check agreement → click accept.
 * 5. On accept: `localStorage` set, Promise resolves `true`, caller proceeds with model loading.
 * 6. On decline: Promise never resolves (caller does nothing).
 *
 * **localStorage keys:**
 * - `yoro-inference-tos-accepted`: `'accepted'` when TOS agreed.
 * - `yoro-local-llm-enabled`: cleared on revoke (prevents auto-load).
 *
 * @module
 */

const STORAGE_KEY = 'yoro-inference-tos-accepted';

let _visible = $state(false);
let _onAccept: (() => void) | null = null;

/** Whether the consent modal is currently visible. */
export function isConsentVisible(): boolean {
	return _visible;
}

/** Check if user has already accepted the inference TOS. */
export function hasInferenceConsent(): boolean {
	if (typeof window === 'undefined') return false;
	return localStorage.getItem(STORAGE_KEY) === 'accepted';
}

/** Revoke inference consent and disable auto-load. */
export function revokeInferenceConsent(): void {
	if (typeof window === 'undefined') return;
	localStorage.removeItem(STORAGE_KEY);
	localStorage.removeItem('yoro-local-llm-enabled');
}

/** Record that the user accepted the inference TOS. */
export function acceptInferenceConsent(): void {
	if (typeof window === 'undefined') return;
	localStorage.setItem(STORAGE_KEY, 'accepted');
	_visible = false;
	_onAccept?.();
	_onAccept = null;
}

/** Close the consent modal without accepting. */
export function declineInferenceConsent(): void {
	_visible = false;
	_onAccept = null;
}

/**
 * Show the consent modal. Returns a Promise that resolves to `true` if
 * accepted, or never resolves if declined (caller simply does nothing).
 *
 * If consent was already given, resolves immediately with `true`.
 */
export function requestInferenceConsent(): Promise<boolean> {
	if (hasInferenceConsent()) return Promise.resolve(true);
	return new Promise<boolean>((resolve) => {
		_onAccept = () => resolve(true);
		_visible = true;
	});
}

/** Reactive accessor for the consent modal visibility. */
export function useInferenceConsent() {
	return {
		get visible() { return _visible; },
	};
}
