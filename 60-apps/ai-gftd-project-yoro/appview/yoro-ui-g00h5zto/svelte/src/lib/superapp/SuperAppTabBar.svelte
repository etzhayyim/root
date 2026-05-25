<script lang="ts">
	import { BottomNav } from '@etzhayyim/design-system';
import { page } from '$app/stores';
import { currentTab, threadUnreadCount, type SuperAppTab } from './stores.js';
import { moodColor } from '../tuner/vibes-store.js';

	const TAB_ROUTES: Record<SuperAppTab, string> = {
		vibes: '/',
		search: '/search',
		talk: '/projects',
		apps: '/apps',
		profile: '/profile',
	};

	interface Props {
		/**
		 * Optional subset of tabs to display. Defaults to the standard 5-tab set:
		 * vibes | search | talk | apps | profile
		 */
		tabs?: SuperAppTab[];
	}

let { tabs }: Props = $props();
function show(tab: SuperAppTab) { return !tabs || tabs.includes(tab); }

type BottomNavProps = typeof BottomNav extends { $$prop_def: infer Props } ? Props : never;
type BottomNavItems = BottomNavProps['items'];
const navItems: BottomNavItems = [
	...(show('vibes') ? [{ href: '/', value: 'vibes', label: 'Vibes', icon: vibesIcon }] : []),
	...(show('search') ? [{ href: '/search', value: 'search', label: 'Search', icon: searchIcon }] : []),
	...(show('talk') ? [{ href: '/projects', value: 'talk', label: 'Talk', icon: talkIcon }] : []),
	...(show('apps') ? [{ href: '/apps', value: 'apps', label: 'Apps', icon: appsIcon }] : []),
	...(show('profile') ? [{ href: '/profile', value: 'profile', label: 'Profile', icon: profileIcon }] : []),
] as BottomNavItems;
</script>

{#snippet vibesIcon()}
	<svg class="w-7 h-7" viewBox="0 0 24 24" fill={$currentTab === 'vibes' ? 'currentColor' : 'none'} stroke="currentColor" stroke-width={$currentTab === 'vibes' ? '0' : '2'} stroke-linecap="round" stroke-linejoin="round">
		<polygon points="5 3 19 12 5 21 5 3" />
	</svg>
{/snippet}

{#snippet searchIcon()}
	<svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width={$currentTab === 'search' ? '2.5' : '2'} stroke-linecap="round" stroke-linejoin="round">
		<circle cx="11" cy="11" r="8" />
		<path d="M21 21l-4.35-4.35" />
	</svg>
{/snippet}

{#snippet talkIcon()}
	<div class="relative">
		<svg class="w-7 h-7" viewBox="0 0 24 24" fill={$currentTab === 'talk' ? 'currentColor' : 'none'} stroke="currentColor" stroke-width={$currentTab === 'talk' ? '0' : '2'} stroke-linecap="round" stroke-linejoin="round">
			<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
		</svg>
		{#if $threadUnreadCount > 0 && $currentTab !== 'talk'}
			<span class="absolute -top-1.5 -right-1.5 min-w-[16px] h-[16px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center leading-none pulse-badge">{$threadUnreadCount > 99 ? '99+' : $threadUnreadCount}</span>
		{/if}
	</div>
{/snippet}

{#snippet appsIcon()}
	<svg class="w-7 h-7" viewBox="0 0 24 24" fill={$currentTab === 'apps' ? 'currentColor' : 'none'} stroke="currentColor" stroke-width={$currentTab === 'apps' ? '0' : '2'} stroke-linecap="round" stroke-linejoin="round">
		<rect x="3" y="3" width="7" height="7" rx="1.5" />
		<rect x="14" y="3" width="7" height="7" rx="1.5" />
		<rect x="14" y="14" width="7" height="7" rx="1.5" />
		<rect x="3" y="14" width="7" height="7" rx="1.5" />
	</svg>
{/snippet}

{#snippet profileIcon()}
	<svg class="w-7 h-7" viewBox="0 0 24 24" fill={$currentTab === 'profile' ? 'currentColor' : 'none'} stroke="currentColor" stroke-width={$currentTab === 'profile' ? '0' : '2'} stroke-linecap="round" stroke-linejoin="round">
		{#if $currentTab === 'profile'}
			<circle cx="12" cy="8" r="4" fill="currentColor" />
			<path d="M20 21a8 8 0 1 0-16 0" fill="currentColor" />
		{:else}
			<circle cx="12" cy="8" r="4" />
			<path d="M20 21a8 8 0 1 0-16 0" />
		{/if}
	</svg>
{/snippet}

<div style="box-shadow: 0 -2px 8px rgba(0,0,0,0.1), 0 -1px 12px var(--tuner-mood-glow, transparent)">
	<BottomNav
		items={navItems}
		activePath={$page.url.pathname}
		accentClass="text-[var(--gv2-accent)]"
		inactiveClass="text-etzhayyim-muted"
		class="!bg-[var(--gv2-bg-primary,#0a0a0a)] !border-[var(--gv2-border,#2f2f2f)] transition-shadow duration-700"
	/>
</div>
