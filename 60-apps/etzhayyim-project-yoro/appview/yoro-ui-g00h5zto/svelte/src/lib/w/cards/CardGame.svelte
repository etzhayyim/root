<script lang="ts">
	import type { CardGamePayload, CardGameAction } from '../w-types.js';

	interface Props {
		payload: CardGamePayload;
	}

	let { payload }: Props = $props();
	let playing = $state(false);

	const genreColors: Record<string, string> = {
		brainrot: 'bg-purple-600',
		action: 'bg-blue-500',
		rpg: 'bg-amber-600',
		puzzle: 'bg-green-500',
		arcade: 'bg-cyan-500',
		sandbox: 'bg-orange-500',
		strategy: 'bg-red-500',
	};

	const genreGradients: Record<string, string> = {
		brainrot: 'from-purple-600 to-pink-500',
		action: 'from-blue-500 to-cyan-400',
		rpg: 'from-amber-600 to-yellow-400',
		puzzle: 'from-green-500 to-emerald-400',
		arcade: 'from-cyan-500 to-blue-400',
		sandbox: 'from-orange-500 to-amber-400',
		strategy: 'from-red-500 to-rose-400',
	};

	const badgeColor = $derived(genreColors[payload.genre] ?? 'bg-gray-500');
	const gradient = $derived(genreGradients[payload.genre] ?? 'from-blue-500 to-cyan-400');

	function skinHueToColor(hue: number): string {
		return `hsl(${hue}, 50%, 55%)`;
	}

	function initials(name: string): string {
		return name.slice(0, 2).toUpperCase();
	}

	const primaryAction = $derived(payload.actions?.find((a: CardGameAction) => a.primary));
	const secondaryActions = $derived(payload.actions?.filter((a: CardGameAction) => !a.primary) ?? []);
</script>

{#if playing}
	<div class="fixed inset-0 z-50 bg-black flex flex-col">
		<div class="absolute top-4 right-4 z-50">
			<button
				type="button"
				class="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white text-[20px] backdrop-blur-sm touch-manipulation active:bg-white/20"
				onclick={() => (playing = false)}
			>X</button>
		</div>
		<iframe
			src={payload.play_url}
			title={payload.title}
			class="h-full w-full border-0"
			allow="autoplay; fullscreen; gamepad; xr-spatial-tracking"
		></iframe>
	</div>
{/if}

<div class="max-w-[600px] rounded-2xl bg-gv2-bg-card border border-gv2-border/20 overflow-hidden">
	<!-- Thumbnail / Preview -->
	<div class="relative aspect-video w-full overflow-hidden">
		{#if payload.thumbnail_url}
			<img
				src={payload.thumbnail_url}
				alt={payload.title}
				class="h-full w-full object-cover"
			/>
		{:else}
			<div class="flex h-full w-full items-center justify-center bg-gradient-to-br {gradient}">
				<span class="text-[28px] font-bold text-white/80">{payload.title}</span>
			</div>
		{/if}
		<div class="absolute top-2 left-2">
			<span class="{badgeColor} rounded-full px-2.5 py-0.5 text-[11px] font-bold text-white uppercase tracking-wider">{payload.genre}</span>
		</div>
	</div>

	<!-- Info -->
	<div class="px-3.5 pt-3 pb-3.5">
		<h3 class="text-[15px] font-bold text-gv2-text-primary leading-tight">{payload.title}</h3>
		<p class="mt-1 text-[13px] text-gv2-text-muted leading-snug line-clamp-2">{payload.description}</p>

		<!-- Character strip -->
		{#if payload.characters && payload.characters.length > 0}
			<div class="mt-2.5 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
				{#each payload.characters as char (char.id)}
					<div
						class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
						style="background-color: {skinHueToColor(char.skin_hue)}"
						title="{char.name} ({char.role})"
					>{initials(char.name)}</div>
				{/each}
			</div>
		{/if}

		<!-- Player count -->
		<p class="mt-2 text-[12px] text-gv2-text-muted">Up to {payload.max_players} players</p>

		<!-- Actions -->
		<div class="mt-3 flex items-center gap-2">
			<button
				type="button"
				class="flex-1 rounded-xl bg-gradient-to-r {gradient} py-3 px-6 text-center text-[15px] font-bold text-white touch-manipulation active:opacity-80"
				onclick={() => (playing = true)}
			>{primaryAction?.label ?? 'Play'}</button>
			{#each secondaryActions as action (action.name)}
				<button
					type="button"
					class="rounded-xl border border-gv2-border/30 bg-gv2-bg-card py-3 px-4 text-[13px] font-semibold text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
				>{action.label}</button>
			{/each}
		</div>
	</div>
</div>
