export { default as AppShell } from './AppShell.svelte';
export { default as Header } from './Header.svelte';
export { default as Sidebar } from './Sidebar.svelte';
export { default as Footer } from './Footer.svelte';
export { default as ContentArea } from './ContentArea.svelte';
export { default as ThemeToggle } from './ThemeToggle.svelte';
export { default as LegalDocumentPage } from './legal/LegalDocumentPage.svelte';
export {
	privacyDocument,
	termsDocument,
	supportSummary,
} from './legal/content';
export type {
	LegalDocument,
	LegalSection,
} from './legal/content';

export { theme, resolvedTheme, setTheme, toggleTheme, ALL_THEMES, THEME_META } from './theme';
export type { Theme, ColorTheme, ThemeMeta } from './theme';

// Re-export design-system primitives for one-stop imports.
export * from '@etzhayyim/design-system';

// Unified facade for appshellv2-* packages.
export * from './auth';
export * from './language';
export * from './mcp';
// wallet removed (viem optional dep, not used by yoro)
export * from './apps';
export { default as SuperAppTabBar } from './superapp/SuperAppTabBar.svelte';
export { default as SearchPanel } from './superapp/SearchPanel.svelte';
export { default as ServicesPanel } from './superapp/ServicesPanel.svelte';
export { default as SettingsPanel } from './superapp/SettingsPanel.svelte';
export { default as ProviderPanel } from './superapp/ProviderPanel.svelte';
export { default as ProfilePanel } from './superapp/ProfilePanel.svelte';
export {
	currentTab,
	activeServiceApp,
	isActorOpen,
	openActor,
	closeActor,
} from './superapp/stores.js';
export type { SuperAppTab } from './superapp/stores.js';
// Provider network (distributed inference).
export * from './provider';

// Translation (page auto-translate, AT/Signal message translate, widget editor).
export { default as TranslateButton } from './translate/TranslateButton.svelte';
export { default as PageTranslateBar } from './translate/PageTranslateBar.svelte';
export {
	initTranslate,
	translatePage,
	autoTranslatePage,
	translateOnDemand,
	translateMessage,
	translateSignal,
	widgetLookup,
	widgetSuggest,
	widgetApprove,
	setUserLang,
	getUserLang,
} from './translate/client.js';
export {
	translateLoading,
	translateError,
	translateTargetLang,
	pageTranslateActive,
	messageTranslateEnabled,
	translateReady,
} from './translate/stores.js';

// Unified facade for build-safety tooling.
// safe-builder: use @etzhayyim/vite-plugin-safe-builder directly
