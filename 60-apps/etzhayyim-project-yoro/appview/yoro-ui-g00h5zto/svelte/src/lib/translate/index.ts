// Components
export { default as TranslateButton } from './TranslateButton.svelte';
export { default as PageTranslateBar } from './PageTranslateBar.svelte';

// Client
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
	getLanguageRegistry,
} from './client.js';

// Stores
export {
	translateLoading,
	translateError,
	translateTargetLang,
	pageTranslateActive,
	messageTranslateEnabled,
	tmHitCount,
	detectedSourceLang,
	translateReady,
} from './stores.js';

// Types
export type {
	TranslateConfig,
	TranslatePageRequest,
	TranslatePageResponse,
	TranslateOnDemandRequest,
	TranslateMessageRequest,
	TranslateSignalRequest,
	SignalPlaintextMessage,
	SignalTranslationResult,
	TranslationResult,
	WidgetLookupResult,
	UserLangPreference,
} from './types.js';
