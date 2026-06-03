<script lang="ts">
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	function goBack() { if (history.length > 1) history.back(); else void goto('/settings'); }
	const sections = [
		{ path: '/settings/privacy-and-security/activity', label: 'Activity visibility', desc: 'Control who can see your activity' },
		{ path: '/moderation', label: 'Moderation', desc: 'Muted accounts, blocked accounts, interaction settings' },
	];
	let requireAuth = $state(false);
</script>

<svelte:head><title>Privacy and Security — YORO</title></svelte:head>

<div class="flex h-full flex-col">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button type="button" class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={goBack} aria-label="Back">
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Privacy and Security</span>
	</div>
	<div class="flex-1 overflow-y-auto scrollbar-none">
		<div class="divide-y divide-gv2-border/20">
			{#each sections as s, i}
				<button type="button" class="flex w-full items-center gap-4 px-4 py-4 text-left touch-manipulation active:bg-gv2-bg-hover/40" onclick={() => goto(s.path)} in:fade={staggerFade(i, { duration: 150 })}>
					<div class="min-w-0 flex-1">
						<span class="block text-[15px] font-bold text-gv2-text-primary">{s.label}</span>
						<span class="block text-[13px] text-gv2-text-muted">{s.desc}</span>
					</div>
					<svg class="h-4 w-4 flex-shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 5l7 7-7 7" /></svg>
				</button>
			{/each}
		</div>
		<div class="px-4 py-4">
			<label class="flex min-h-[52px] items-center justify-between rounded-lg px-3 py-2 touch-manipulation active:bg-gv2-bg-hover/40">
				<div><span class="block text-[15px] text-gv2-text-primary">Require authentication</span><span class="block text-[13px] text-gv2-text-muted">Require login to view your profile</span></div>
				<input type="checkbox" bind:checked={requireAuth} class="h-5 w-5 rounded accent-[#1185FE]" />
			</label>
		</div>
	</div>
</div>
