<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { isSignedIn } from '$lib/auth';
	import { ProfilePanel } from '$lib/superapp';
	import { playTap, haptic } from '@etzhayyim/design-system/audio';
	import { fade } from 'svelte/transition';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import BrainrotMascot from '$lib/components/BrainrotMascot.svelte';
</script>

<svelte:head>
	<title>Profile — YORO</title>
</svelte:head>

{#if $isSignedIn}
	<ProfilePanel
		editLabel="プロフィールを編集"
		onPostClick={(handle, rkey) => { playTap(); haptic('light'); goto(`/profile/${encodeURIComponent(handle)}/post/${encodeURIComponent(rkey)}`); }}
	/>
{:else}
	<div class="flex flex-col items-center gap-6 px-2 py-8">
		<BrainrotMascot size={100} mood="sigma" animate={true} />
		<div class="text-center mt-2">
			<h2 class="text-[24px] font-black text-gv2-text-primary">プロフィール</h2>
			<p class="mt-2 text-[15px] text-gv2-text-muted leading-relaxed">アカウントを作成して、投稿やフォローを<br/>はじめよう</p>
		</div>
		<div class="flex flex-col gap-3 w-full max-w-[300px] mt-2">
			<button type="button" onclick={() => {
				const isNative = !!(window as any).Capacitor?.isNativePlatform?.();
				const redirectUrl = isNative
					? `com.etzhayyim.yoro://callback?target=${encodeURIComponent('/')}`
					: window.location.href;
				window.location.href = `https://authn.etzhayyim.com/sign-up?redirect_url=${encodeURIComponent(redirectUrl)}`;
			}} class="flex min-h-[52px] w-full items-center justify-center rounded-2xl bg-[#58CC02] text-[18px] font-black text-white shadow-[0_5px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[5px] transition-all duration-75">アカウント作成</button>
			<button type="button" onclick={() => {
				const isNative = !!(window as any).Capacitor?.isNativePlatform?.();
				const redirectUrl = isNative
					? `com.etzhayyim.yoro://callback?target=${encodeURIComponent('/')}`
					: window.location.href;
				window.location.href = `https://authn.etzhayyim.com/sign-in?redirect_url=${encodeURIComponent(redirectUrl)}`;
			}} class="flex min-h-[52px] w-full items-center justify-center rounded-2xl border-[3px] border-gv2-border text-[18px] font-black text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover active:scale-[0.97] transition-transform">ログイン</button>
			<p class="mt-1 text-center text-[12px] text-gv2-text-muted">登録無料 · Bluesky アカウントでもログインできます</p>
		</div>
		<div class="flex w-full max-w-[300px] flex-col gap-2 mt-4">
			{#each [
				{ icon: '🦋', text: 'Bluesky 互換タイムライン' },
				{ icon: '🔒', text: 'Signal E2E 暗号化チャット' },
				{ icon: '🤖', text: 'AI エージェントとチャット' },
			] as f, i}
				<div class="flex items-center gap-3 rounded-2xl bg-gv2-bg-card/80 px-4 py-3" in:fade={staggerFade(i, { duration: 200, delay: 300 })}>
					<span class="text-[20px]">{f.icon}</span>
					<span class="text-[14px] font-semibold text-gv2-text-primary">{f.text}</span>
				</div>
			{/each}
		</div>
	</div>
{/if}
