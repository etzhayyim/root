import { writable, derived } from 'svelte/store';

/** Primary bottom tab IDs for the SuperApp shell (Bluesky-like layout). */
export type SuperAppTab = 'vibes' | 'search' | 'talk' | 'apps' | 'profile';

/** Currently active tab — synced from URL path in +layout.svelte. */
export const currentTab = writable<SuperAppTab>('vibes');

/** Derive tab from URL pathname. Called from layout $effect. */
export function pathToTab(pathname: string): SuperAppTab {
	if (pathname.startsWith('/search')) return 'search';
	if (pathname.startsWith('/projects') || pathname.startsWith('/messages') || pathname.startsWith('/talk')) return 'talk';
	if (pathname.startsWith('/activities') || pathname.startsWith('/notifications')) return 'vibes';
	if (pathname.startsWith('/apps')) return 'apps';
	if (pathname === '/profile' || (pathname.startsWith('/profile/') && !pathname.includes('/post/'))) return 'profile';
	if (pathname.startsWith('/settings') || pathname.startsWith('/moderation')) return 'profile';
	return 'vibes';
}

/** Active actor app ID (nanoid). null = no actor open (showing native tab content). */
export const activeServiceApp = writable<string | null>(null);

/** Whether an actor app is currently open. */
export const isActorOpen = derived(activeServiceApp, ($app) => $app !== null);

/** Open an actor app by nanoid. Navigates to apps page and sets the active app. */
export function openActor(nanoid: string) {
	activeServiceApp.set(nanoid);
	import('$app/navigation').then(({ goto }) => goto('/apps'));
}

/** Close the current actor app and return to apps grid. */
export function closeActor() {
	activeServiceApp.set(null);
}

export interface ThreadAppContext {
	nanoid: string;
	name: string;
	icon?: string;
	servicePath?: string;
	resourceId?: string;
	defaultConvos?: Array<{ id: string; name: string }>;
}

/** Thread app context — when set, Talk tab auto-selects this app's server. */
export const threadAppContext = writable<ThreadAppContext | null>(null);

/** Unread message count for the Talk tab badge. */
export const threadUnreadCount = writable<number>(0);

/** Open Talk tab to the etzhayyim support convo. */
export function openSupportRoom() {
	openTalkForApp('etzhayyim', 'Support', undefined, {
		defaultConvos: [{ id: 'support', name: 'support' }],
	});
}

/** Navigate to messages with a specific app's server selected. */
export function openTalkForApp(
	nanoid: string,
	name: string,
	icon?: string,
	options?: Omit<ThreadAppContext, 'nanoid' | 'name' | 'icon'>
) {
	threadAppContext.set({ nanoid, name, icon, ...(options ?? {}) });
	import('$app/navigation').then(({ goto }) => goto('/projects'));
}
