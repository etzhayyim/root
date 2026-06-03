<script lang="ts">
	/**
	 * ActorHero — Hero section for AT Protocol actors.
	 * Layout varies by performerType:
	 *   - service/system: Compact (icon + name + status + capabilities)
	 *   - person/organization: Full (avatar + description + stats + follow)
	 * Nintendo/iOS-style micro-interactions on all interactive elements.
	 */
	import { Avatar, Badge, Chip } from '@etzhayyim/design-system';
	import { playTap, playHover, haptic } from '@etzhayyim/design-system/audio';
	import { followUser, unfollowUser, createProjectConvo } from '$lib/atproto-agent';
	import { goto } from '$app/navigation';
	import { spring } from 'svelte/motion';
	import type { ActorProfileView } from './types.js';

	interface Props {
		profile: ActorProfileView;
	}

	let { profile }: Props = $props();

	let following = $derived(profile.viewerFollowing ?? false);
	let followingLocal = $state<boolean | null>(null);
	const isFollowing = $derived(followingLocal ?? following);
	let followBusy = $state(false);
	let dmBusy = $state(false);

	// Spring interactions for buttons
	const followScale = spring(1, { stiffness: 0.35, damping: 0.55 });
	const dmScale = spring(1, { stiffness: 0.35, damping: 0.55 });
	// Stats hover springs
	const statScalePosts = spring(1, { stiffness: 0.3, damping: 0.6 });
	const statScaleFollowers = spring(1, { stiffness: 0.3, damping: 0.6 });
	const statScaleFollowing = spring(1, { stiffness: 0.3, damping: 0.6 });
	const statScales = [statScalePosts, statScaleFollowers, statScaleFollowing];

	function pressButton(s: typeof followScale) {
		playTap();
		haptic('light');
		s.set(0.88);
		setTimeout(() => s.set(1.06), 80);
		setTimeout(() => s.set(1), 180);
	}

	function statEnter(i: number) {
		statScales[i].set(1.1);
		playHover();
	}
	function statLeave(i: number) { statScales[i].set(1); }
	function statDown(i: number) { statScales[i].set(0.9); haptic('light'); }
	function statUp(i: number) { statScales[i].set(1.1); }

	const isCompact = $derived(profile.performerType === 'service' || profile.performerType === 'system');
	const statusColor = $derived.by(() => {
		const s = profile.service?.status ?? profile.system?.healthStatus;
		if (s === 'online' || s === 'healthy') return 'bg-green-500';
		if (s === 'degraded' || s === 'warning') return 'bg-yellow-500';
		if (s === 'offline' || s === 'critical') return 'bg-red-500';
		return 'bg-gray-500';
	});
	const statusLabel = $derived(profile.service?.status ?? profile.system?.healthStatus ?? '');
	const capabilities = $derived(profile.service?.capabilities ?? []);
	const version = $derived(profile.service?.version ?? profile.system?.version ?? '');

	async function toggleFollow() {
		if (followBusy) return;
		followBusy = true;
		try {
			if (isFollowing) {
				await unfollowUser(profile.did);
				followingLocal = false;
			} else {
				await followUser(profile.did);
				followingLocal = true;
			}
		} catch (e) {
			console.warn('follow toggle failed', e);
		} finally {
			followBusy = false;
		}
	}

	async function handleDM() {
		if (dmBusy) return;
		dmBusy = true;
		try {
			const result = await createProjectConvo(profile.did);
			if (result?.convo?.convoId) {
				await goto(`/projects/${encodeURIComponent(result.convo.convoId)}`, { keepFocus: true, noScroll: true });
			}
		} catch (e) {
			console.warn('DM creation failed', e);
		} finally {
			dmBusy = false;
		}
	}
</script>

{#if isCompact}
	<!-- Compact hero: service / system -->
	<div class="flex items-center gap-3 px-4 py-3 border-b border-[var(--gv2-border,#2f2f2f)]">
		{#if profile.icon}
			<span class="text-2xl shrink-0">{profile.icon}</span>
		{:else}
			<Avatar src={profile.avatar} fallback={profile.displayName?.slice(0, 2) ?? '?'} size="sm" />
		{/if}
		<div class="flex-1 min-w-0">
			<div class="flex items-center gap-2">
				<span class="text-[15px] font-bold truncate">{profile.displayName}</span>
				{#if statusLabel}
					<span class="flex items-center gap-1 text-[11px] text-[var(--gv2-text-muted,#777)]">
						<span class="inline-block h-2 w-2 rounded-full {statusColor}"></span>
						{statusLabel}
					</span>
				{/if}
				{#if version}
					<span class="text-[11px] text-[var(--gv2-text-muted,#777)]">v{version}</span>
				{/if}
			</div>
			{#if capabilities.length > 0}
				<div class="flex flex-wrap gap-1 mt-1">
					{#each capabilities.slice(0, 6) as cap}
						<Chip label={cap} />
					{/each}
				</div>
			{/if}
		</div>
		<button
			type="button"
			class="shrink-0 rounded-full px-4 py-1.5 text-[13px] font-semibold touch-manipulation focus-glow {isFollowing ? 'bg-[var(--gv2-bg-hover,#252525)] text-[var(--gv2-text-secondary,#aaa)]' : 'bg-[var(--gv2-accent,#3b82f6)] text-white'}"
			style="transform: scale({$followScale})"
			onclick={() => { pressButton(followScale); toggleFollow(); }}
			onpointerdown={() => followScale.set(0.92)}
			onpointerup={() => followScale.set(1)}
			onpointerleave={() => followScale.set(1)}
			disabled={followBusy}
		>{isFollowing ? 'Following' : 'Follow'}</button>
	</div>
{:else}
	<!-- Full hero: person / organization -->
	<div class="border-b border-[var(--gv2-border,#2f2f2f)]">
		<!-- Banner gradient -->
		<div class="h-20 w-full" style="background: linear-gradient(135deg, {profile.accent ?? 'var(--gv2-accent,#3b82f6)'} 0%, transparent 100%), var(--gv2-bg-primary,#0a0a0a);"></div>

		<div class="px-4 -mt-8">
			<!-- Avatar (interactive hover glow) -->
			<Avatar src={profile.avatar ?? profile.organization?.logo} fallback={profile.displayName?.slice(0, 2) ?? '?'} size="lg" interactive class="ring-4 ring-[var(--gv2-bg-primary,#0a0a0a)]" />

			<!-- Name + handle -->
			<div class="mt-2">
				<h2 class="text-[17px] font-bold">{profile.displayName}</h2>
				<p class="text-[13px] text-[var(--gv2-text-muted,#777)]">@{profile.handle}</p>
				{#if profile.person?.occupation}
					<p class="text-[13px] text-[var(--gv2-text-secondary,#aaa)] mt-0.5">{profile.person.occupation}</p>
				{/if}
				{#if profile.organization?.jurisdiction}
					<p class="text-[13px] text-[var(--gv2-text-secondary,#aaa)] mt-0.5">{profile.organization.jurisdiction}</p>
				{/if}
			</div>

			<!-- Description -->
			{#if profile.description}
				<p class="text-[14px] text-[var(--gv2-text-primary,#fff)] mt-2 line-clamp-3">{profile.description}</p>
			{/if}

			<!-- Stats (hover-reactive, Nintendo-style bounce) -->
			<div class="flex gap-4 mt-3 text-[13px]">
				{#each [
					{ count: profile.postsCount, label: 'posts' },
					{ count: profile.followersCount, label: 'followers' },
					{ count: profile.followsCount, label: 'following' },
				] as stat, i}
					<span
						class="cursor-pointer select-none touch-manipulation"
						style="transform: scale({i === 0 ? $statScalePosts : i === 1 ? $statScaleFollowers : $statScaleFollowing}); display: inline-block"
						onpointerenter={() => statEnter(i)}
						onpointerleave={() => statLeave(i)}
						onpointerdown={() => statDown(i)}
						onpointerup={() => statUp(i)}
					>
						<strong>{stat.count}</strong>
						<span class="text-[var(--gv2-text-muted,#777)]">{stat.label}</span>
					</span>
				{/each}
			</div>

			<!-- Scores (Dojo / Joucho) -->
			{#if profile.scores?.dojo || profile.scores?.joucho}
				<div class="flex flex-wrap gap-3 mt-3">
					{#if profile.scores?.dojo}
						<div class="flex items-center gap-1.5 rounded-lg bg-[var(--gv2-bg-hover,#1a1a1a)] px-3 py-1.5 card-float cursor-default">
							<span class="text-[13px] font-bold text-emerald-400">{profile.scores.dojo.avgScore}</span>
							<span class="text-[12px] text-[var(--gv2-text-muted,#777)]">Dojo</span>
							<span class="text-[11px] text-[var(--gv2-text-muted,#555)]">({profile.scores.dojo.drillsCompleted} drills)</span>
						</div>
					{/if}
					{#if profile.scores?.joucho}
						<div class="flex items-center gap-1.5 rounded-lg bg-[var(--gv2-bg-hover,#1a1a1a)] px-3 py-1.5 card-float cursor-default">
							<span class="text-[13px] font-bold" class:text-amber-400={profile.scores.joucho.grade === 'S'} class:text-blue-400={profile.scores.joucho.grade === 'A'} class:text-green-400={profile.scores.joucho.grade === 'B'} class:text-yellow-400={profile.scores.joucho.grade === 'C'} class:text-gray-400={profile.scores.joucho.grade === 'D'}>{profile.scores.joucho.grade}</span>
							<span class="text-[12px] text-[var(--gv2-text-muted,#777)]">情緒 {profile.scores.joucho.avgScore}</span>
							<span class="text-[11px] text-[var(--gv2-text-muted,#555)]">({profile.scores.joucho.reviewCount} reviews)</span>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Badges -->
			{#if profile.person?.competenceBadge}
				<div class="mt-2">
					<Badge value={profile.person.competenceBadge} variant="accent" />
				</div>
			{/if}
			{#if profile.organization?.memberCount}
				<div class="mt-2 text-[12px] text-[var(--gv2-text-muted,#777)]">
					{profile.organization.memberCount} members
				</div>
			{/if}

			<!-- Tags -->
			{#if (profile.person?.tags?.length ?? 0) > 0 || (profile.organization?.tags?.length ?? 0) > 0}
				<div class="flex flex-wrap gap-1 mt-2">
					{#each (profile.person?.tags ?? profile.organization?.tags ?? []) as tag}
						<Chip label={tag} />
					{/each}
				</div>
			{/if}

			<!-- Actions (spring press + haptic) -->
			<div class="flex gap-2 mt-3 pb-4">
				<button
					type="button"
					class="rounded-full px-5 py-2 text-[14px] font-semibold touch-manipulation focus-glow {isFollowing ? 'bg-[var(--gv2-bg-hover,#252525)] text-[var(--gv2-text-secondary,#aaa)]' : 'bg-[var(--gv2-accent,#3b82f6)] text-white'}"
					style="transform: scale({$followScale})"
					onclick={() => { pressButton(followScale); toggleFollow(); }}
					onpointerdown={() => followScale.set(0.92)}
					onpointerup={() => followScale.set(1)}
					onpointerleave={() => followScale.set(1)}
					disabled={followBusy}
				>{isFollowing ? 'Following' : 'Follow'}</button>
				<button
					type="button"
					class="rounded-full px-5 py-2 text-[14px] font-semibold bg-[var(--gv2-bg-hover,#252525)] text-[var(--gv2-text-primary,#fff)] touch-manipulation focus-glow"
					style="transform: scale({$dmScale})"
					onclick={() => { pressButton(dmScale); handleDM(); }}
					onpointerdown={() => dmScale.set(0.92)}
					onpointerup={() => dmScale.set(1)}
					onpointerleave={() => dmScale.set(1)}
					disabled={dmBusy}
				>{dmBusy ? '...' : 'DM'}</button>
			</div>
		</div>
	</div>
{/if}
