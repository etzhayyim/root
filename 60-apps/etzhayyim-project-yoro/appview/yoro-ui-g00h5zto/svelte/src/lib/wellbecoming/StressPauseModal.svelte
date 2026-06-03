<script lang="ts">
	/**
	 * Nintendo-style stress-pause modal.
	 *
	 * Opens when the viewer crosses the doom-scroll threshold or when
	 * `stress_idx > 80`. Plays a calm wind-bell on open, a gentle chime
	 * on resume. Respects `prefers-reduced-motion` and `prefers-reduced-sound`
	 * via the shared `sound.ts` helpers.
	 *
	 * Plan: /root/.claude/plans/yoro-etzhayyim-ai-facebook-zazzy-teapot.md
	 */
	import { onMount, onDestroy } from 'svelte';
	import { playWindBell, playChimeC5 } from '../sound';
	import { resetSessionTopology } from '../session-topology.svelte';

	interface Props {
		open: boolean;
		title?: string;
		message?: string;
		pauseDurationMs?: number;
		onResume?: () => void;
		onDismiss?: () => void;
	}

	let {
		open = $bindable(false),
		title = '休憩しましょう',
		message = 'しばらくスクロールが続いています。深呼吸して、少し休みませんか?',
		pauseDurationMs = 10 * 60 * 1000,
		onResume,
		onDismiss,
	}: Props = $props();

	let resumeAt = $state<number | null>(null);
	let remainingMs = $state(0);
	let timer: ReturnType<typeof setInterval> | null = null;

	function handleOpenChange() {
		if (open) {
			try { playWindBell(); } catch { /* silent */ }
			resumeAt = Date.now() + pauseDurationMs;
			remainingMs = pauseDurationMs;
			if (timer) clearInterval(timer);
			timer = setInterval(() => {
				if (resumeAt === null) return;
				remainingMs = Math.max(0, resumeAt - Date.now());
				if (remainingMs <= 0) { stopTimer(); }
			}, 1000);
		} else {
			stopTimer();
		}
	}
	$effect(() => { void open; handleOpenChange(); });

	function stopTimer() {
		if (timer) { clearInterval(timer); timer = null; }
	}

	function resume() {
		try { playChimeC5(); } catch { /* silent */ }
		resetSessionTopology();
		open = false;
		onResume?.();
	}

	function dismiss() {
		open = false;
		onDismiss?.();
	}

	function onKey(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') dismiss();
	}

	onMount(() => {
		if (typeof window !== 'undefined') window.addEventListener('keydown', onKey);
	});
	onDestroy(() => {
		stopTimer();
		if (typeof window !== 'undefined') window.removeEventListener('keydown', onKey);
	});

	function fmt(ms: number): string {
		const s = Math.max(0, Math.floor(ms / 1000));
		const mm = Math.floor(s / 60).toString().padStart(2, '0');
		const ss = (s % 60).toString().padStart(2, '0');
		return `${mm}:${ss}`;
	}
</script>

{#if open}
	<div
		class="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		aria-labelledby="stress-pause-title"
		onclick={dismiss}
		onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') dismiss(); }}
		tabindex="-1"
	>
		<div
			class="relative mx-4 max-w-md w-full rounded-2xl border border-white/10 bg-[var(--gv2-bg-primary,#1a1a1a)] p-6 shadow-2xl"
			role="document"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			tabindex="-1"
		>
			<div class="flex items-center gap-3">
				<div
					class="h-10 w-10 rounded-full flex items-center justify-center text-xl"
					style="background: linear-gradient(135deg, #6ee7b7, #60a5fa);"
					aria-hidden="true"
				>🕊</div>
				<h2 id="stress-pause-title" class="text-lg font-semibold">{title}</h2>
			</div>
			<p class="mt-3 text-sm opacity-80">{message}</p>

			{#if remainingMs > 0}
				<div class="mt-4 rounded-xl bg-white/5 px-4 py-3 text-center">
					<div class="text-xs opacity-60 mb-1">自動再開まで</div>
					<div class="text-2xl font-mono tabular-nums">{fmt(remainingMs)}</div>
				</div>
			{/if}

			<div class="mt-5 flex gap-2">
				<button
					type="button"
					class="flex-1 rounded-xl px-4 py-2 text-sm font-medium bg-white/10 hover:bg-white/15 transition"
					onclick={dismiss}
				>あとで</button>
				<button
					type="button"
					class="flex-1 rounded-xl px-4 py-2 text-sm font-medium text-white transition"
					style="background: linear-gradient(135deg, #60a5fa, #6ee7b7);"
					onclick={resume}
				>深呼吸して再開</button>
			</div>
		</div>
	</div>
{/if}
