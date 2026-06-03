<script lang="ts">
	import { goto } from '$app/navigation';
	import { Avatar } from '@etzhayyim/design-system';
	import { isSignedIn, clerkUser, displayName as clerkDisplayName } from '$lib/auth';
	import { playClick } from '$lib/sound';
	import * as yoroApi from '$lib/atproto-agent';
	import type { AuthorProfile } from '$lib/atproto-agent';
	import { fade, fly } from 'svelte/transition';
	import { hitl } from '$lib/hitl-store.svelte';

	interface Props {
		open: boolean;
	}

	let { open = $bindable() }: Props = $props();

	let myProfile = $state<AuthorProfile | null>(null);

	$effect(() => {
		if (!$isSignedIn) { myProfile = null; return; }
		yoroApi.getCurrentDID().then((did) => {
			if (did) yoroApi.getAuthorProfile(did).then((p) => { myProfile = p; }).catch((e) => console.warn('getAuthorProfile failed', e));
		}).catch((e) => console.warn('getCurrentDID failed', e));
	});

	const TAB_ROUTES: Record<string, string> = {
		'tab:vibes': '/',
		'tab:search': '/search',
		'tab:talk': '/projects',
		'tab:apps': '/apps',
		'tab:profile': '/profile',
	};

	function navigate(path: string) {
		open = false;
		playClick();
		const route = TAB_ROUTES[path];
		goto(route ?? path);
	}

	const backEasing = (t: number) => { const c1 = 1.70158; const c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
</script>

{#if open}
	<button
		type="button"
		class="fixed inset-0 z-[100] bg-black/50"
		onclick={() => { open = false; }}
		aria-label="メニューを閉じる"
		transition:fade={{ duration: 200 }}
	></button>
	<div
		class="fixed inset-y-0 left-0 z-[101] flex w-[300px] flex-col bg-gv2-bg-primary safe-area-top safe-area-bottom shadow-2xl"
		in:fly={{ x: -300, duration: 350, easing: backEasing }}
		out:fly={{ x: -300, duration: 200 }}
	>
		<!-- Profile header -->
		<div class="border-b border-gv2-border/30 px-5 pb-4 pt-6">
			<Avatar
				src={myProfile?.avatar || $clerkUser?.imageUrl || undefined}
				fallback={(myProfile?.displayName || $clerkDisplayName || 'U').slice(0, 2).toUpperCase()}
				size="lg"
				class="!h-14 !w-14 !text-lg"
			/>
			<div class="mt-3">
				<div class="text-[17px] font-bold text-gv2-text-primary">{myProfile?.displayName || $clerkDisplayName || 'User'}</div>
				<div class="text-[14px] text-gv2-text-muted">@{myProfile?.handle || $clerkUser?.username || 'user'}</div>
			</div>
			<div class="mt-2 flex items-center gap-3 text-[14px]">
				<span>
					<span class="font-bold text-gv2-text-primary">{myProfile?.followersCount ?? 0}</span>
					<span class="text-gv2-text-muted"> フォロワー</span>
				</span>
				<span class="text-gv2-text-muted">·</span>
				<span>
					<span class="font-bold text-gv2-text-primary">{myProfile?.followsCount ?? 0}</span>
					<span class="text-gv2-text-muted"> フォロー</span>
				</span>
			</div>
		</div>

		<!-- Navigation links -->
		<nav class="flex-1 overflow-y-auto py-2">
			{#each [
				{ icon: 'search', label: '検索', action: 'tab:search' },
				{ icon: 'home', label: 'ホーム', action: 'tab:vibes' },
				{ icon: 'chat', label: 'チャット', action: 'tab:talk' },
				{ icon: 'bell', label: 'Activities', action: '/activities' },
				{ icon: 'hash', label: 'フィード', action: 'tab:vibes' },
				{ icon: 'list', label: 'リスト', action: '/public-companies' },
				{ icon: 'bookmark', label: '保存済', action: 'tab:vibes' },
				{ icon: 'history', label: '閲覧履歴', action: '/history' },
				{ icon: 'hitl', label: '意思決定', action: '/tasks/inbox' },
				{ icon: 'profile', label: 'プロフィール', action: 'tab:profile' },
				{ icon: 'settings', label: '設定', action: '/settings' },
				{ icon: 'activity', label: 'LPM Miner', action: '/lpm-dashboard' },
			] as item}
				<button
					type="button"
					class="flex w-full items-center gap-4 px-5 py-3 text-left touch-manipulation active:bg-gv2-bg-hover"
					onclick={() => navigate(item.action)}
				>
					{#if item.icon === 'hitl'}
						<div class="relative">
							<svg class="h-6 w-6 text-[#8B5CF6]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
								<polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
								<polyline points="12 2 12 22" /><polyline points="2 8.5 22 8.5" />
							</svg>
							{#if hitl.pending > 0}
								<span class="absolute -right-1.5 -top-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[#8B5CF6] px-1 text-[10px] font-bold text-white leading-none">{hitl.pending}</span>
							{/if}
						</div>
					{:else if item.icon === 'search'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
					{:else if item.icon === 'home'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
					{:else if item.icon === 'chat'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
					{:else if item.icon === 'bell'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
					{:else if item.icon === 'hash'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 9h16M4 15h16M10 3l-2 18M16 3l-2 18" /></svg>
					{:else if item.icon === 'list'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
					{:else if item.icon === 'bookmark'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" /></svg>
					{:else if item.icon === 'history'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
					{:else if item.icon === 'profile'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4" /><path d="M20 21a8 8 0 1 0-16 0" /></svg>
					{:else if item.icon === 'settings'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
					{:else if item.icon === 'activity'}
						<svg class="h-6 w-6 text-gv2-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
					{/if}
					<span class="text-[17px] font-semibold {item.icon === 'hitl' && hitl.pending > 0 ? 'text-[#8B5CF6]' : 'text-gv2-text-primary'}">{item.label}</span>
				</button>
			{/each}
		</nav>

		<!-- Credit earning CTA -->
		<div class="mx-4 my-3 rounded-2xl bg-[#FFD700]/10 p-4">
			<div class="flex items-center gap-2 mb-1">
				<span class="text-[16px]">💰</span>
				<span class="text-[14px] font-bold text-gv2-text-primary">クレジットを稼ぐ</span>
			</div>
			<p class="text-[12px] text-gv2-text-muted mb-2">タスクに参加して yoro 投稿クレジットを獲得</p>
			<div class="flex gap-2">
				<a href="https://murakumo.etzhayyim.com" class="flex-1 flex items-center justify-center rounded-xl bg-[#FFD700] py-2 text-[12px] font-bold text-gray-900 no-underline touch-manipulation active:opacity-80" onclick={() => { open = false; }}>Murakumo</a>
				<a href="https://hc.etzhayyim.com" class="flex-1 flex items-center justify-center rounded-xl bg-[#58CC02] py-2 text-[12px] font-bold text-white no-underline touch-manipulation active:opacity-80" onclick={() => { open = false; }}>HC Tasks</a>
			</div>
		</div>

		<!-- Footer links -->
		<div class="border-t border-gv2-border/30 px-5 py-4">
			<div class="flex flex-col gap-1">
				<a href="/terms" class="text-[13px] text-[#1185FE] no-underline active:underline" onclick={() => { open = false; }}>Terms of Use</a>
				<a href="/privacy" class="text-[13px] text-[#1185FE] no-underline active:underline" onclick={() => { open = false; }}>Privacy Policy</a>
			</div>
			<div class="mt-3 flex gap-2">
				<a href="/support" class="rounded-full border border-gv2-border px-3 py-1.5 text-[12px] font-medium text-gv2-text-muted no-underline active:bg-gv2-bg-hover" onclick={() => { open = false; }}>Feedback</a>
				<a href="/support" class="rounded-full border border-gv2-border px-3 py-1.5 text-[12px] font-medium text-gv2-text-muted no-underline active:bg-gv2-bg-hover" onclick={() => { open = false; }}>Help</a>
			</div>
		</div>
	</div>
{/if}
