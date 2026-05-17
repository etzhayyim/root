<script lang="ts">
	/**
	 * AchievementToast — Duolingo-style achievement unlock notification.
	 * Slides up from bottom with celebration animation.
	 */
	import { fly, fade } from 'svelte/transition';
	import { playSuccess, playLevelUp } from '$lib/sound';
	import { useGamification } from './xp-store.svelte.js';
	import { onMount } from 'svelte';

	const gf = useGamification();

	const achievements = $derived(gf.pendingAchievements);
	const levelUp = $derived(gf.levelUpFrom);
	const currentLevel = $derived(gf.level);

	let particles = $state<Array<{ id: number; x: number; y: number; color: string; delay: number }>>([]);
	let particleId = 0;

	$effect(() => {
		if (achievements.length > 0) {
			playSuccess();
			spawnParticles();
		}
	});

	$effect(() => {
		if (levelUp !== null) {
			playLevelUp();
			spawnParticles();
		}
	});

	function spawnParticles() {
		const colors = ['#58CC02', '#FFD700', '#1CB0F6', '#FF6B9D', '#A855F7', '#FF9500'];
		const newParticles = Array.from({ length: 12 }, () => ({
			id: particleId++,
			x: 30 + Math.random() * 40,
			y: 30 + Math.random() * 40,
			color: colors[Math.floor(Math.random() * colors.length)],
			delay: Math.random() * 0.3,
		}));
		particles = [...particles, ...newParticles];
		setTimeout(() => {
			particles = particles.filter(p => !newParticles.includes(p));
		}, 1500);
	}

	const rarityBg: Record<string, string> = {
		common: 'from-[#58CC02] to-[#46A302]',
		rare: 'from-[#1CB0F6] to-[#0E87BF]',
		epic: 'from-[#A855F7] to-[#7E22CE]',
		legendary: 'from-[#FFD700] to-[#FF9500]',
	};
</script>

<!-- Achievement Toasts -->
{#each achievements as achievement (achievement.id)}
	<div
		class="fixed bottom-24 left-1/2 z-[200] w-[90vw] max-w-[360px] -translate-x-1/2"
		in:fly={{ y: 100, duration: 400 }}
		out:fade={{ duration: 200 }}
	>
		<div class="relative overflow-hidden rounded-2xl bg-[var(--gv2-bg-card,#1e1e1e)] shadow-2xl border border-[var(--gv2-border,#333)]">
			<!-- Gradient header -->
			<div class="h-1.5 bg-gradient-to-r {rarityBg[achievement.rarity] ?? rarityBg.common}"></div>

			<div class="flex items-center gap-3 px-4 py-3">
				<!-- Icon -->
				<div class="flex h-[48px] w-[48px] items-center justify-center rounded-xl bg-gradient-to-br {rarityBg[achievement.rarity] ?? rarityBg.common} text-[24px] shadow-lg achievement-pop">
					{achievement.icon}
				</div>

				<div class="flex-1 min-w-0">
					<div class="text-[11px] font-bold uppercase tracking-wider text-[#58CC02]">Achievement Unlocked!</div>
					<div class="text-[15px] font-bold text-[var(--gv2-text-primary,#fff)] mt-0.5">{achievement.name}</div>
					<div class="text-[12px] text-[var(--gv2-text-muted,#777)]">{achievement.description}</div>
				</div>

				{#if achievement.xpReward > 0}
					<div class="flex items-center gap-1 rounded-lg bg-[var(--gv2-bg-hover,#252525)] px-2 py-1">
						<span class="text-[12px]">⚡</span>
						<span class="text-[13px] font-bold text-yellow-400">+{achievement.xpReward}</span>
					</div>
				{/if}
			</div>

			<!-- Tap to dismiss -->
			<button
				class="w-full border-t border-[var(--gv2-border,#333)] py-2 text-[12px] text-[var(--gv2-text-muted,#777)] hover:bg-[var(--gv2-bg-hover,#252525)] transition-colors"
				onclick={() => gf.dismissAchievement(achievement.id)}
			>
				Tap to dismiss
			</button>
		</div>
	</div>
{/each}

<!-- Level-up overlay -->
{#if levelUp !== null}
	<div
		class="fixed inset-0 z-[250] flex items-center justify-center bg-black/70"
		in:fade={{ duration: 300 }}
		out:fade={{ duration: 300 }}
	>
		<div class="flex flex-col items-center gap-4 text-center level-up-pop" in:fly={{ y: 40, duration: 500 }}>
			<!-- Celebration particles -->
			{#each particles as p (p.id)}
				<div
					class="absolute w-2 h-2 rounded-full particle-burst"
					style="left: {p.x}%; top: {p.y}%; background: {p.color}; animation-delay: {p.delay}s"
				></div>
			{/each}

			<div class="text-[48px] level-icon-bounce">🎉</div>
			<div class="text-[13px] font-bold uppercase tracking-widest text-[#58CC02]">Level Up!</div>
			<div class="flex items-center gap-3">
				<span class="text-[32px] font-black text-[var(--gv2-text-muted,#555)]">{levelUp}</span>
				<svg class="w-6 h-6 text-[#58CC02]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
				<span class="text-[48px] font-black text-[var(--gv2-text-primary,#fff)]">{currentLevel}</span>
			</div>
			<div class="text-[14px] text-[var(--gv2-text-muted,#777)]">{gf.rank.rank} · {gf.rank.label}</div>
		</div>
	</div>
{/if}

<style>
	.achievement-pop {
		animation: ach-pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
	}
	@keyframes ach-pop {
		0% { transform: scale(0); }
		60% { transform: scale(1.2); }
		100% { transform: scale(1); }
	}

	.level-up-pop {
		animation: lvl-pop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
	}
	@keyframes lvl-pop {
		0% { transform: scale(0.5); opacity: 0; }
		100% { transform: scale(1); opacity: 1; }
	}

	.level-icon-bounce {
		animation: icon-bounce 1s ease-in-out infinite;
	}
	@keyframes icon-bounce {
		0%, 100% { transform: translateY(0) rotate(0deg); }
		25% { transform: translateY(-8px) rotate(-5deg); }
		75% { transform: translateY(-4px) rotate(5deg); }
	}

	.particle-burst {
		animation: burst 1.2s ease-out forwards;
	}
	@keyframes burst {
		0% { transform: translate(0, 0) scale(1); opacity: 1; }
		100% { transform: translate(calc((var(--x, 0) - 50) * 3px), calc((var(--y, 0) - 50) * 3px - 60px)) scale(0); opacity: 0; }
	}

	@media (prefers-reduced-motion: reduce) {
		.achievement-pop, .level-up-pop, .level-icon-bounce, .particle-burst { animation: none; }
	}
</style>
