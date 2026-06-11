<script lang="ts">
	/**
	 * InferenceConsent — Full-screen TOS modal gate for browser inference participation.
	 *
	 * **3 gates before acceptance:**
	 * 1. User must scroll the TOS text to the bottom.
	 * 2. User must check the agreement checkbox (disabled until scrolled).
	 * 3. User must click "Agree and Join Inference" (disabled until checkbox checked).
	 *
	 * TOS content: 12 sections (Japanese) covering device resource usage,
	 * Murakumo network participation, model licensing, inference result
	 * disclaimers, full liability exclusion, indemnification, and
	 * Japan/Tokyo jurisdiction.
	 *
	 * State is managed in {@link inference-consent-state.svelte.ts} (module-level
	 * singleton). This component only renders the UI — visibility is driven by
	 * `useInferenceConsent().visible`.
	 *
	 * @module
	 */
	import { fade, fly } from 'svelte/transition';
	import { playClick } from '$lib/sound';
	import { inferenceConsentDocument } from '$lib/legal';
	import {
		useInferenceConsent,
		acceptInferenceConsent,
		declineInferenceConsent,
	} from './inference-consent-state.svelte.js';

	const consent = useInferenceConsent();

	let scrolledToBottom = $state(false);
	let checked = $state(false);
	let scrollContainer: HTMLDivElement | undefined = $state();

	/** Reset local UI state when modal becomes visible. */
	$effect(() => {
		if (consent.visible) {
			scrolledToBottom = false;
			checked = false;
		}
	});

	function handleScroll() {
		if (!scrollContainer) return;
		const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
		if (scrollTop + clientHeight >= scrollHeight - 40) {
			scrolledToBottom = true;
		}
	}

	function accept() {
		playClick();
		acceptInferenceConsent();
	}

	function decline() {
		playClick();
		declineInferenceConsent();
	}
</script>

{#if consent.visible}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm"
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 150 }}
		role="presentation"
	></div>

	<!-- Modal -->
	<div
		class="fixed inset-0 z-[201] flex items-center justify-center p-4"
		in:fly={{ y: 40, duration: 300, delay: 50 }}
		out:fade={{ duration: 150 }}
		role="dialog"
		aria-modal="true"
		aria-labelledby="inference-tos-title"
	>
		<div class="flex max-h-[90vh] w-full max-w-[560px] flex-col overflow-hidden rounded-3xl border border-gv2-border/40 bg-gv2-bg-card shadow-2xl">
			<!-- Header -->
			<div class="flex-shrink-0 border-b border-gv2-border/30 px-6 pt-5 pb-4">
				<div class="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-400">
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L1 21h22L12 2zm0 4l7.53 13H4.47L12 6zm-1 5v4h2v-4h-2zm0 6v2h2v-2h-2z"/></svg>
					<span>Important Notice Regarding Inference Participation</span>
				</div>
				<h2 id="inference-tos-title" class="mt-2 text-xl font-bold tracking-tight text-gv2-text-primary">
					{inferenceConsentDocument.title}
				</h2>
				<p class="mt-1.5 text-[12px] leading-relaxed text-gv2-text-muted">
					{inferenceConsentDocument.summary}
				</p>
			</div>

			<!-- Scrollable content -->
			<div
				bind:this={scrollContainer}
				onscroll={handleScroll}
				class="flex-1 overflow-y-auto overscroll-contain px-6 py-4"
			>
				<div class="space-y-5">
					{#each inferenceConsentDocument.sections as section}
						<div>
							<h3 class="text-[13px] font-bold text-gv2-text-primary">{section.heading}</h3>
							<div class="mt-1.5 space-y-2">
								{#each section.body as paragraph}
									<p class="text-[12px] leading-[1.7] text-gv2-text-secondary">{paragraph}</p>
								{/each}
							</div>
						</div>
					{/each}
				</div>

				{#if !scrolledToBottom}
					<div class="sticky bottom-0 flex justify-center pt-3 pb-1">
						<div class="rounded-full bg-gv2-bg-hover/80 px-3 py-1 text-[11px] font-medium text-gv2-text-muted backdrop-blur-sm">
							Please scroll to the bottom
						</div>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex-shrink-0 border-t border-gv2-border/30 px-6 py-4">
				<!-- Checkbox -->
				<label class="flex items-start gap-3 cursor-pointer select-none">
					<input
						type="checkbox"
						bind:checked
						disabled={!scrolledToBottom}
						class="mt-0.5 h-5 w-5 rounded border-2 border-gv2-border accent-[#58CC02] disabled:opacity-30"
					/>
					<span class="text-[12px] leading-relaxed text-gv2-text-primary" class:opacity-40={!scrolledToBottom}>
						I have read, understood, and agree to all provisions of the Browser Inference Participation Terms above, including device resource usage, disclaimers, and indemnification clauses.
					</span>
				</label>

				<!-- Buttons -->
				<div class="mt-4 flex gap-3">
					<button
						type="button"
						class="flex-1 rounded-2xl border border-gv2-border py-3 text-[13px] font-bold text-gv2-text-muted
							touch-manipulation active:bg-gv2-bg-hover transition-all duration-75"
						onclick={decline}
					>
						Decline
					</button>
					<button
						type="button"
						class="flex-1 rounded-2xl py-3 text-[13px] font-black text-white
							shadow-[0_4px_0_#3D8A00] touch-manipulation
							active:shadow-none active:translate-y-[4px] transition-all duration-75
							disabled:opacity-30 disabled:shadow-none disabled:cursor-not-allowed"
						class:bg-[#58CC02]={scrolledToBottom && checked}
						class:bg-gv2-border={!scrolledToBottom || !checked}
						disabled={!scrolledToBottom || !checked}
						onclick={accept}
					>
						Agree and Join Inference
					</button>
				</div>

				<p class="mt-3 text-center text-[10px] text-gv2-text-muted">
					Last updated: {inferenceConsentDocument.lastUpdated} | <a href="/terms" class="text-[#1185FE] underline">Terms of Use</a> | <a href="/privacy" class="text-[#1185FE] underline">Privacy Policy</a>
				</p>
			</div>
		</div>
	</div>
{/if}
