import { translateLoading, translateError, tmHitCount } from './stores.js';
import type {
	TranslateConfig,
	TranslatePageRequest,
	TranslatePageResponse,
	TranslateOnDemandRequest,
	TranslateMessageRequest,
	TranslateSignalRequest,
	SignalTranslationResult,
	TranslationResult,
	WidgetLookupResult,
} from './types.js';
import type { LanguageCode } from '../language/types.js';

import { AtpAgent } from '@etzhayyim/sdk/atproto';

const DEFAULT_BASE = 'https://i18n.etzhayyim.com';

let config: TranslateConfig = {};
let _agent = new AtpAgent({ service: DEFAULT_BASE });

/** Initialize the translate client */
export function initTranslate(cfg?: TranslateConfig) {
	if (cfg) config = cfg;
	_agent = new AtpAgent({ service: cfg?.baseUrl ?? DEFAULT_BASE });
}

/** XRPC POST to i18n service: /xrpc/com.etzhayyim.i18n.{lcFirstMethod} */
async function xrpcPost<T>(method: string, body: Record<string, unknown>): Promise<T> {
	translateLoading.set(true);
	translateError.set(null);
	const nsid = `com.etzhayyim.i18n.${method.charAt(0).toLowerCase()}${method.slice(1)}`;
	try {
		const res = await _agent.api.call(nsid, body, undefined, { encoding: 'application/json' });
		const data = res.data as { value?: T } & T;
		return ((data as { value?: T }).value ?? data) as T;
	} catch (err) {
		const msg = err instanceof Error ? err.message : typeof err === 'object' && err !== null && 'message' in err ? String((err as { message: unknown }).message) : String(err);
		translateError.set(msg);
		throw err;
	} finally {
		translateLoading.set(false);
	}
}

// --- Page Auto-Translation (Google Translate-like) ---

/** Translate an array of DOM text strings */
export async function translatePage(req: TranslatePageRequest): Promise<TranslatePageResponse> {
	const result = await xrpcPost<TranslatePageResponse>('TranslatePage', {
		texts: req.texts,
		sourceLang: req.sourceLang ?? '',
		targetLang: req.targetLang,
		url: req.url ?? '',
	});
	const hits = result.translations.filter((t, i) => t !== req.texts[i]).length;
	tmHitCount.update((n) => n + hits);
	return result;
}

/**
 * Auto-translate all visible text nodes in the current page.
 * Extracts text, translates in batch, replaces DOM content.
 */
export async function autoTranslatePage(targetLang: LanguageCode): Promise<number> {
	const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
		acceptNode(node) {
			const text = node.textContent?.trim();
			if (!text || text.length < 2) return NodeFilter.FILTER_REJECT;
			const parent = node.parentElement;
			if (parent && (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE' || parent.tagName === 'NOSCRIPT')) {
				return NodeFilter.FILTER_REJECT;
			}
			return NodeFilter.FILTER_ACCEPT;
		},
	});

	const nodes: Text[] = [];
	const texts: string[] = [];
	let node: Node | null;
	while ((node = walker.nextNode())) {
		nodes.push(node as Text);
		texts.push((node.textContent ?? '').trim());
	}

	if (texts.length === 0) return 0;

	const batchSize = 100;
	let translated = 0;
	for (let i = 0; i < texts.length; i += batchSize) {
		const batch = texts.slice(i, i + batchSize);
		const result = await translatePage({ texts: batch, targetLang });
		for (let j = 0; j < result.translations.length; j++) {
			const idx = i + j;
			if (result.translations[j] && result.translations[j] !== texts[idx]) {
				nodes[idx].textContent = result.translations[j];
				translated++;
			}
		}
	}

	// Apply dir="rtl" to <html> if target is RTL
	const rtlLangs = new Set(['ar', 'he', 'fa', 'ur', 'ps', 'sd', 'yi', 'dv', 'ug', 'ckb', 'bal']);
	if (rtlLangs.has(targetLang)) {
		document.documentElement.setAttribute('dir', 'rtl');
	} else {
		document.documentElement.setAttribute('dir', 'ltr');
	}

	return translated;
}

// --- On-Demand Translation (single text) ---

/** Translate a single text string */
export async function translateOnDemand(req: TranslateOnDemandRequest): Promise<TranslationResult> {
	const data = await xrpcPost<Record<string, unknown>>('TranslateOnDemand', {
		sourceText: req.sourceText,
		targetLang: req.targetLang,
		messageKey: req.messageKey ?? '',
		domainHint: req.domainHint ?? '',
	});
	return {
		translatedText: data.targetText as string,
		sourceLang: 'en',
		targetLang: req.targetLang,
		qualityScore: data.qualityScore as number,
		source: data.source as 'tmCache' | 'llm' | 'sameLang',
	};
}

// --- AT Protocol Message Translation ---

/** Translate an AT Protocol convo message */
export async function translateMessage(req: TranslateMessageRequest): Promise<TranslationResult> {
	const data = await xrpcPost<Record<string, unknown>>('TranslateMessage', {
		text: req.text,
		targetLang: req.targetLang,
		sourceLang: req.sourceLang ?? '',
		recordUri: req.recordUri ?? '',
		convoId: req.convoId ?? '',
		senderDid: req.senderDid ?? '',
	});
	return {
		translatedText: data.translatedText as string,
		sourceLang: data.sourceLang as string,
		targetLang: data.targetLang as string,
		qualityScore: data.qualityScore as number,
		source: data.source as 'tmCache' | 'llm' | 'sameLang',
	};
}

// --- Signal E2E Message Translation ---

/** Translate Signal protocol plaintext messages (after client-side decryption) */
export async function translateSignal(req: TranslateSignalRequest): Promise<SignalTranslationResult[]> {
	const data = await xrpcPost<{ translations: SignalTranslationResult[] }>('TranslateSignal', {
		plaintextMessages: req.plaintextMessages.map((m) => ({
			id: m.id,
			text: m.text,
			senderDid: m.senderDid ?? '',
			sourceLang: m.sourceLang ?? '',
		})),
		targetLang: req.targetLang,
		sessionId: req.sessionId ?? '',
	});
	return data.translations.map((t) => ({
		id: t.id,
		translatedText: t.translatedText,
		sourceLang: t.sourceLang,
		qualityScore: t.qualityScore,
		source: t.source,
	}));
}

// --- Widget: Inline Editor ---

/** Look up a term across all target languages in Translation Memory */
export async function widgetLookup(term: string, targetLangs?: LanguageCode[], projectId?: string): Promise<WidgetLookupResult> {
	const data = await xrpcPost<Record<string, unknown>>('WidgetLookup', {
		term,
		targetLangs: targetLangs ?? [],
		projectId: projectId ?? '',
	});
	return {
		term: data.term as string,
		translations: (data.translations as WidgetLookupResult['translations']) ?? [],
		sourceHash: (data.sourceHash as string) ?? '',
	};
}

/** Get 3 alternative translation suggestions for a term */
export async function widgetSuggest(term: string, targetLang: LanguageCode, context?: string, projectId?: string): Promise<string[]> {
	const data = await xrpcPost<{ suggestions: string[] }>('WidgetSuggest', {
		term,
		targetLang,
		context: context ?? '',
		projectId: projectId ?? '',
	});
	return data.suggestions ?? [];
}

/** Approve a translation (human review → TM with qualityScore 1.0) */
export async function widgetApprove(term: string, targetLang: LanguageCode, approved: string, projectId?: string): Promise<void> {
	await xrpcPost('WidgetApprove', {
		term,
		targetLang,
		approved,
		projectId: projectId ?? '',
	});
}

// --- User Language Preference ---

/** Set user's preferred translation target language */
export async function setUserLang(lang: LanguageCode, convoId?: string): Promise<void> {
	await xrpcPost('SetUserLang', {
		lang,
		convoId: convoId ?? '',
	});
}

/** Get user's preferred translation target language */
export async function getUserLang(convoId?: string): Promise<LanguageCode | null> {
	const data = await xrpcPost<{ lang: string }>('GetUserLang', {
		convoId: convoId ?? '',
	});
	return data.lang || null;
}

// --- Language Registry ---

/** Fetch the 200+ language registry from the i18n service */
export async function getLanguageRegistry(tierLimit?: number, search?: string) {
	return xrpcPost<{ languages: Array<{ code: string; name: string; enName: string; script: string; dir: string; tier: number }>; total: number }>(
		'GetLanguageRegistry',
		{ tierLimit: tierLimit ?? 4, search: search ?? '' },
	);
}
