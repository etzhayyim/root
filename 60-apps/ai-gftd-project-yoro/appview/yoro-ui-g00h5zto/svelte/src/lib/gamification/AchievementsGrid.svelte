<script lang="ts">
	/**
	 * AchievementsGrid — Full achievements display for profile/credits page.
	 * Shows all achievements grouped by category with locked/unlocked states.
	 */
	import { useGamification, ACHIEVEMENTS, type AchievementDef } from './xp-store.svelte.js';

	interface Props {
		class?: string;
	}

	let { class: cls = '' }: Props = $props();

	const gf = useGamification();
	const unlocked = $derived(new Set(gf.state.achievements));

	type Category = 'social' | 'dojo' | 'streak' | 'milestone' | 'rank';
	const categoryLabels: Record<Category, { label: string; icon: string }> = {
		social: { label: 'Social', icon: '🦋' },
		dojo: { label: 'Dojo', icon: '🥋' },
		streak: { label: 'Streak', icon: '🔥' },
		milestone: { label: 'Milestone', icon: '⚡' },
		rank: { label: 'Rank', icon: '🏆' },
	};

	const grouped = $derived(
		(['social', 'dojo', 'streak', 'milestone', 'rank'] as Category[]).map(cat => ({
			category: cat,
			...categoryLabels[cat],
			items: ACHIEVEMENTS.filter(a => a.category === cat),
			unlockedCount: ACHIEVEMENTS.filter(a => a.category === cat && unlocked.has(a.id)).length,
		}))
	);

	const totalUnlocked = $derived(unlocked.size);
	const totalCount = ACHIEVEMENTS.length;

	const rarityBorder: Record<string, string> = {
		common: 'border-[var(--gv2-border,#333)]',
		rare: 'border-blue-500/40',
		epic: 'border-purple-500/40',
		legendary: 'border-yellow-500/40',
	};
	const rarityGlow: Record<string, string> = {
		common: '',
		rare: 'shadow-blue-500/10',
		epic: 'shadow-purple-500/10',
		legendary: 'shadow-yellow-500/20',
	};
</script>

<div class="{cls}">
	<!-- Overall progress -->
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-[16px] font-bold text-[var(--gv2-text-primary,#fff)]">Achievements</h3>
		<span class="text-[13px] font-semibold text-[var(--gv2-text-muted,#777)]">{totalUnlocked}/{totalCount}</span>
	</div>

	{#each grouped as group}
		<div class="mb-4">
			<div class="flex items-center gap-2 mb-2">
				<span class="text-[14px]">{group.icon}</span>
				<span class="text-[13px] font-semibold text-[var(--gv2-text-secondary,#aaa)]">{group.label}</span>
				<span class="text-[11px] text-[var(--gv2-text-muted,#555)]">{group.unlockedCount}/{group.items.length}</span>
			</div>
			<div class="grid grid-cols-4 gap-2">
				{#each group.items as ach}
					{@const isUnlocked = unlocked.has(ach.id)}
					<div
						class="flex flex-col items-center gap-1 rounded-xl border p-2 transition-all duration-200
							{isUnlocked ? rarityBorder[ach.rarity] : 'border-[var(--gv2-border,#222)]'}
							{isUnlocked ? 'bg-[var(--gv2-bg-card,#1e1e1e)]' : 'bg-[var(--gv2-bg-primary,#111)] opacity-40'}
							{isUnlocked ? 'shadow-md ' + rarityGlow[ach.rarity] : ''}"
						title="{ach.name}: {ach.description}{ach.xpReward > 0 ? ` (+${ach.xpReward} XP)` : ''}"
					>
						<span class="text-[20px] {isUnlocked ? '' : 'grayscale'}">{ach.icon}</span>
						<span class="text-[9px] font-semibold text-center leading-tight text-[var(--gv2-text-secondary,#aaa)] line-clamp-2">{ach.name}</span>
					</div>
				{/each}
			</div>
		</div>
	{/each}
</div>
