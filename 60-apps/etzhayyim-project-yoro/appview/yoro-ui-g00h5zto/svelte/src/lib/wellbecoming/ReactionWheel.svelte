<script lang="ts">
	/**
	 * Nintendo-style radial reaction wheel, opened by long-press (250ms).
	 *
	 * 8 emoji arranged on a circle. Tap outside or Escape dismisses.
	 * Plays `whoosh_up` on open and `sparkle` on select via the Web Audio
	 * synthesiser (`sound.ts`). Silent under `prefers-reduced-motion` /
	 * `prefers-reduced-sound`.
	 *
	 * The 8 reactions map loosely onto the plan's Joucho 5-axis
	 * (vitality / serenity / connection / growth / resilience) plus 3
	 * AT Protocol-standard social reactions (laugh / wow / sad).
	 *
	 * Plan: /root/.claude/plans/yoro-etzhayyim-ai-facebook-zazzy-teapot.md
	 */
	import { onMount, onDestroy } from 'svelte';
	import { playTick, playChimeC5 } from '../sound';

	export interface ReactionChoice {
		id: string;        // stable key (e.g. 'joy')
		emoji: string;
		label: string;
		axis?: 'vitality' | 'serenity' | 'connection' | 'growth' | 'resilience';
	}

	interface Props {
		open: boolean;
		anchor?: { x: number; y: number } | null;
		choices?: ReactionChoice[];
		onSelect?: (choice: ReactionChoice) => void;
		onDismiss?: () => void;
	}

	const DEFAULT_CHOICES: ReactionChoice[] = [
		{ id: 'joy',         emoji: '😊', label: 'うれしい',     axis: 'vitality'   },
		{ id: 'calm',        emoji: '😌', label: 'おだやか',     axis: 'serenity'   },
		{ id: 'gratitude',   emoji: '🙏', label: 'ありがとう',   axis: 'connection' },
		{ id: 'focus',       emoji: '🎯', label: 'がんばる',     axis: 'growth'     },
		{ id: 'resilience',  emoji: '💪', label: 'のりこえる',   axis: 'resilience' },
		{ id: 'laugh',       emoji: '😂', label: 'わらう'                           },
		{ id: 'wow',         emoji: '😮', label: 'おどろき'                         },
		{ id: 'sad',         emoji: '😢', label: 'かなしい'                         },
	];

	let {
		open = $bindable(false),
		anchor = null,
		choices = DEFAULT_CHOICES,
		onSelect,
		onDismiss,
	}: Props = $props();

	const RADIUS = 72;  // px from center

	function positionStyle(): string {
		if (!anchor || typeof window === 'undefined') {
			return 'left: 50%; top: 50%; transform: translate(-50%, -50%);';
		}
		const { x, y } = anchor;
		const vw = window.innerWidth;
		const vh = window.innerHeight;
		// Clamp so the wheel doesn't escape the viewport.
		const cx = Math.max(RADIUS + 24, Math.min(x, vw - RADIUS - 24));
		const cy = Math.max(RADIUS + 24, Math.min(y, vh - RADIUS - 24));
		return `left: ${cx}px; top: ${cy}px; transform: translate(-50%, -50%);`;
	}

	function itemStyle(i: number, n: number): string {
		const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
		const dx = Math.cos(angle) * RADIUS;
		const dy = Math.sin(angle) * RADIUS;
		return `transform: translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px));`;
	}

	function handleOpenChange(nextOpen: boolean) {
		if (nextOpen) { try { playTick(); } catch { /* silent */ } }
	}
	$effect(() => { handleOpenChange(open); });

	function select(c: ReactionChoice) {
		try { playChimeC5(); } catch { /* silent */ }
		onSelect?.(c);
		open = false;
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
		if (typeof window !== 'undefined') window.removeEventListener('keydown', onKey);
	});
</script>

{#if open}
	<div
		class="fixed inset-0 z-[1500]"
		role="dialog"
		aria-modal="true"
		aria-label="リアクションを選ぶ"
		onclick={dismiss}
		onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') dismiss(); }}
		tabindex="-1"
	>
		<div
			class="absolute"
			style={positionStyle()}
			role="menu"
			aria-label="リアクション"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			tabindex="-1"
		>
			<!-- Center disc (anchor dot). -->
			<div
				class="absolute h-11 w-11 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/10 ring-1 ring-white/20 backdrop-blur-sm"
				aria-hidden="true"
			></div>

			{#each choices as c, i (c.id)}
				<button
					type="button"
					class="absolute flex h-12 w-12 items-center justify-center rounded-full bg-[var(--gv2-bg-primary,#1a1a1a)] ring-1 ring-white/20 text-2xl shadow-md transition active:scale-90 hover:bg-white/10"
					style={itemStyle(i, choices.length)}
					aria-label={c.label}
					onclick={() => select(c)}
					role="menuitem"
				>
					<span aria-hidden="true">{c.emoji}</span>
				</button>
			{/each}
		</div>
	</div>
{/if}
