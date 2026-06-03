<script lang="ts">
	import { onMount } from 'svelte';
	import { playLevelUp } from '$lib/sound';

	interface Props {
		class?: string;
	}
	const { class: cls = '' }: Props = $props();

	const STORAGE_KEY = 'yoro_streak';

	type StreakData = {
		count: number;
		lastDate: string; // YYYY-MM-DD
		xp: number;
	};

	let streak = $state<StreakData>({ count: 0, lastDate: '', xp: 0 });
	let justLeveledUp = $state(false);

	function todayStr(): string {
		return new Date().toISOString().slice(0, 10);
	}

	onMount(() => {
		try {
			const raw = localStorage.getItem(STORAGE_KEY);
			const data: StreakData = raw ? JSON.parse(raw) : { count: 0, lastDate: '', xp: 0 };
			const today = todayStr();
			const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);

			if (data.lastDate === today) {
				streak = data;
			} else if (data.lastDate === yesterday) {
				streak = { count: data.count + 1, lastDate: today, xp: data.xp + 10 };
				if (streak.count % 7 === 0) {
					justLeveledUp = true;
					playLevelUp();
					setTimeout(() => { justLeveledUp = false; }, 2000);
				}
				localStorage.setItem(STORAGE_KEY, JSON.stringify(streak));
			} else {
				streak = { count: 1, lastDate: today, xp: (data.xp || 0) + 10 };
				localStorage.setItem(STORAGE_KEY, JSON.stringify(streak));
			}
		} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/components/StreakBadge.svelte: suppressed error", error); }
	});

	function addXP(amount: number) {
		streak = { ...streak, xp: streak.xp + amount };
		try { localStorage.setItem(STORAGE_KEY, JSON.stringify(streak)); } catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/components/StreakBadge.svelte: suppressed error", error); }
	}

	// expose addXP for parent
	export { addXP };

	const flameColor = $derived(
		streak.count >= 30 ? 'text-purple-400'
		: streak.count >= 14 ? 'text-orange-400'
		: streak.count >= 7  ? 'text-yellow-400'
		: 'text-orange-300'
	);
</script>

<div class="flex items-center gap-3 {cls}">
	<!-- Streak -->
	<div class="flex items-center gap-1">
		<span class="text-[20px] {justLeveledUp ? 'animate-spin' : ''}"
			title="{streak.count} 日連続！">🔥</span>
		<span class="text-[14px] font-bold {flameColor}">{streak.count}</span>
	</div>
	<!-- XP -->
	<div class="flex items-center gap-1">
		<span class="text-[16px]">⚡</span>
		<span class="text-[13px] font-semibold text-yellow-400">{streak.xp} XP</span>
	</div>
</div>
