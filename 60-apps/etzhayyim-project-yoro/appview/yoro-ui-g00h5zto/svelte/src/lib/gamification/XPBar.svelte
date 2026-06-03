<script lang="ts">
	/**
	 * XPBar — Duolingo-style XP progress bar with level indicator.
	 * Shows current level, XP progress to next level, streak, and gems.
	 */
	import { useGamification, type KyuDanRank } from './xp-store.svelte.js';

	interface Props {
		compact?: boolean;
		class?: string;
	}

	let { compact = false, class: cls = '' }: Props = $props();

	const gf = useGamification();
	const level = $derived(gf.level);
	const progress = $derived(gf.progress);
	const rank = $derived(gf.rank);
	const state = $derived(gf.state);

	const pctWidth = $derived(Math.round(progress.pct * 100));

	// Rank belt color for the level circle
	const beltBg = $derived(
		rank.minScore >= 2000 ? 'bg-gray-900 ring-white/50'
		: rank.minScore >= 1500 ? 'bg-amber-800 ring-amber-600/50'
		: rank.minScore >= 1000 ? 'bg-blue-600 ring-blue-400/50'
		: rank.minScore >= 600 ? 'bg-emerald-600 ring-emerald-400/50'
		: rank.minScore >= 300 ? 'bg-orange-500 ring-orange-400/50'
		: rank.minScore >= 100 ? 'bg-yellow-500 ring-yellow-400/50'
		: 'bg-gray-500 ring-gray-400/50'
	);
</script>

{#if compact}
	<!-- Compact: single row for header -->
	<div class="flex items-center gap-2 {cls}">
		<!-- Level circle -->
		<div class="flex h-[26px] w-[26px] items-center justify-center rounded-full ring-2 {beltBg} text-[11px] font-black text-white">
			{level}
		</div>
		<!-- XP bar -->
		<div class="relative h-[8px] w-[60px] overflow-hidden rounded-full bg-[var(--gv2-bg-hover,#252525)]">
			<div
				class="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[#58CC02] to-[#8EE000] transition-all duration-500"
				style="width: {pctWidth}%"
			></div>
		</div>
		<!-- Streak -->
		{#if state.streak > 0}
			<div class="flex items-center gap-0.5">
				<span class="text-[14px]">🔥</span>
				<span class="text-[12px] font-bold text-orange-400">{state.streak}</span>
			</div>
		{/if}
		<!-- Gems -->
		{#if state.gems > 0}
			<div class="flex items-center gap-0.5">
				<span class="text-[14px]">💎</span>
				<span class="text-[12px] font-bold text-blue-400">{state.gems}</span>
			</div>
		{/if}
	</div>

{:else}
	<!-- Full: card view for profile/credits -->
	<div class="rounded-2xl bg-[var(--gv2-bg-card,#1e1e1e)] p-4 {cls}">
		<!-- Top row: Level + Rank + XP -->
		<div class="flex items-center gap-3">
			<div class="flex h-[44px] w-[44px] items-center justify-center rounded-full ring-3 {beltBg} text-[18px] font-black text-white shadow-lg">
				{level}
			</div>
			<div class="flex-1 min-w-0">
				<div class="flex items-center gap-2">
					<span class="text-[15px] font-bold text-[var(--gv2-text-primary,#fff)]">Level {level}</span>
					<span class="rounded-md bg-[var(--gv2-bg-hover,#252525)] px-2 py-0.5 text-[11px] font-semibold {rank.color}">{rank.rank}</span>
				</div>
				<div class="text-[12px] text-[var(--gv2-text-muted,#777)] mt-0.5">
					{state.totalXP.toLocaleString()} XP total
				</div>
			</div>
		</div>

		<!-- XP Progress bar -->
		<div class="mt-3">
			<div class="flex items-center justify-between text-[11px] text-[var(--gv2-text-muted,#777)] mb-1">
				<span>{progress.current} / {progress.needed} XP</span>
				<span>Level {level + 1}</span>
			</div>
			<div class="relative h-[10px] overflow-hidden rounded-full bg-[var(--gv2-bg-hover,#252525)]">
				<div
					class="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[#58CC02] to-[#8EE000] transition-all duration-700 ease-out"
					style="width: {pctWidth}%"
				></div>
			</div>
		</div>

		<!-- Stats row -->
		<div class="flex items-center gap-4 mt-3">
			<!-- Streak -->
			<div class="flex items-center gap-1.5">
				<span class="text-[18px]">🔥</span>
				<div>
					<div class="text-[14px] font-bold text-orange-400">{state.streak}</div>
					<div class="text-[10px] text-[var(--gv2-text-muted,#777)]">day streak</div>
				</div>
			</div>
			<!-- XP Today -->
			<div class="flex items-center gap-1.5">
				<span class="text-[18px]">⚡</span>
				<div>
					<div class="text-[14px] font-bold text-yellow-400">{state.dailyXPEarned}</div>
					<div class="text-[10px] text-[var(--gv2-text-muted,#777)]">XP today</div>
				</div>
			</div>
			<!-- Gems (Credits) -->
			<div class="flex items-center gap-1.5">
				<span class="text-[18px]">💎</span>
				<div>
					<div class="text-[14px] font-bold text-blue-400">{state.gems}</div>
					<div class="text-[10px] text-[var(--gv2-text-muted,#777)]">gems</div>
				</div>
			</div>
			<!-- Drills -->
			<div class="flex items-center gap-1.5">
				<span class="text-[18px]">🥋</span>
				<div>
					<div class="text-[14px] font-bold text-emerald-400">{state.drillsCompleted}</div>
					<div class="text-[10px] text-[var(--gv2-text-muted,#777)]">drills</div>
				</div>
			</div>
		</div>

		<!-- Weekly XP chart (mini bar chart) -->
		<div class="mt-3 flex items-end gap-1 h-[32px]">
			{#each state.weeklyXP as dayXP, i}
				{@const maxXP = Math.max(...state.weeklyXP, 1)}
				{@const h = Math.max(4, (dayXP / maxXP) * 32)}
				<div
					class="flex-1 rounded-t-sm transition-all duration-300 {i === 6 ? 'bg-[#58CC02]' : 'bg-[var(--gv2-bg-hover,#333)]'}"
					style="height: {h}px"
					title="{dayXP} XP"
				></div>
			{/each}
		</div>
		<div class="flex justify-between mt-1 text-[9px] text-[var(--gv2-text-muted,#555)]">
			{#each ['月', '火', '水', '木', '金', '土', '日'] as day}
				<span class="flex-1 text-center">{day}</span>
			{/each}
		</div>
	</div>
{/if}
