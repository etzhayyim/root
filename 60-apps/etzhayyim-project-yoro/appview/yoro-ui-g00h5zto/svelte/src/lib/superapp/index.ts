export { default as ThreadPanel } from './ThreadPanel.svelte';
export { default as SuperAppTabBar } from './SuperAppTabBar.svelte';
export { default as SuperAppLayout } from './SuperAppLayout.svelte';
export { default as AmbientBackground } from './AmbientBackground.svelte';
export { default as SplashScreen } from './SplashScreen.svelte';
export { default as VibesPanel } from './VibesPanel.svelte';
export { default as ProfilePanel } from './ProfilePanel.svelte';
// ProviderPanel: import directly from './ProviderPanel.svelte' (viem dependency excluded from barrel)
export { default as AppsPanel } from './ServicesPanel.svelte';
export { default as SettingsPanel } from './SettingsPanel.svelte';

// Panel components (used by route pages directly)
export { default as SearchPanel } from './SearchPanel.svelte';
export { default as ServicesPanel } from './ServicesPanel.svelte';
// WalletPanel: import directly from './WalletPanel.svelte' (viem dependency excluded from barrel)

export { default as Tuner } from '../tuner/Tuner.svelte';
export {
	vibesTuning,
	currentMood,
	currentEnergy,
	currentTempo,
	moodColor,
	ALL_MOODS,
	MOOD_META,
	MOOD_DEFAULTS,
} from '../tuner/vibes-store.js';
export type { MoodPreset, VibesTuning } from '../tuner/vibes-store.js';

export {
	currentTab,
	pathToTab,
	activeServiceApp,
	isActorOpen,
	openActor,
	closeActor,
	openSupportRoom,
	threadAppContext,
	threadUnreadCount,
	openTalkForApp,
} from './stores.js';
export type { SuperAppTab } from './stores.js';

// Actor frame (AT Protocol actor-based app rendering)
export { default as ActorFrame } from '../actor/ActorFrame.svelte';
export { default as ActorHero } from '../actor/ActorHero.svelte';
export {
	getMessagingClient,
	getMessagingCommandClient,
	getMessagingQueryClient,
	clearMessagingClients,
} from './messaging-client.js';
export {
	MessagingCommandService,
	MessagingQueryService,
	MessagingCompatService,
	MessagingService,
} from '../gen/etzhayyim/actor/v1/messaging_pb.js';
