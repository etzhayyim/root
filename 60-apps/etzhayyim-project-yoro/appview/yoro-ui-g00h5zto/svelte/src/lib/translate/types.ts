import type { LanguageCode } from '../language/types.js';

/** Configuration for the translation client */
export interface TranslateConfig {
	/** Base URL for the i18n service (default: https://i18n.etzhayyim.com) */
	baseUrl?: string;
}

/** Page auto-translation request */
export interface TranslatePageRequest {
	texts: string[];
	sourceLang?: LanguageCode;
	targetLang: LanguageCode;
	url?: string;
}

/** Page auto-translation response */
export interface TranslatePageResponse {
	translations: string[];
	sourceLang: string;
	targetLang: string;
	total: number;
}

/** Single text on-demand translation request */
export interface TranslateOnDemandRequest {
	sourceText: string;
	targetLang: LanguageCode;
	messageKey?: string;
	domainHint?: string;
}

/** AT Protocol message translation request */
export interface TranslateMessageRequest {
	text: string;
	targetLang: LanguageCode;
	sourceLang?: LanguageCode;
	recordUri?: string;
	convoId?: string;
	senderDid?: string;
}

/** Signal E2E plaintext message for translation */
export interface SignalPlaintextMessage {
	id: string;
	text: string;
	senderDid?: string;
	sourceLang?: LanguageCode;
}

/** Signal batch translation request */
export interface TranslateSignalRequest {
	plaintextMessages: SignalPlaintextMessage[];
	targetLang: LanguageCode;
	sessionId?: string;
}

/** Individual signal translation result */
export interface SignalTranslationResult {
	id: string;
	translatedText: string;
	sourceLang: string;
	qualityScore: number;
	source: 'tmCache' | 'llm' | 'sameLang' | 'empty' | 'error';
}

/** Widget term lookup result */
export interface WidgetLookupResult {
	term: string;
	translations: Array<{
		lang: LanguageCode;
		text: string;
		qualityScore: number;
		source: string;
	}>;
	sourceHash: string;
}

/** Translation result (generic) */
export interface TranslationResult {
	translatedText: string;
	sourceLang: string;
	targetLang: string;
	qualityScore: number;
	source: 'tmCache' | 'llm' | 'sameLang';
}

/** User language preference */
export interface UserLangPreference {
	lang: LanguageCode;
	convoId?: string;
}
