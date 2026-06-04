export { default as LanguageSwitcher } from './LanguageSwitcher.svelte';

export {
	ALL_LANGUAGES,
	ALL_LANGUAGE_CODES,
	GAMING_POPULATION_LANGUAGES,
	filterLanguages,
	getLanguageName,
	getGamingLanguages,
	getLanguagesByTier,
	getRTLLanguages,
	searchLanguages,
} from './languages.js';

export {
	detectLanguage,
	selectByDistribution,
	INDIA_LANGUAGE_DISTRIBUTION,
} from './detect.js';

export { replacePathLang, extractPathLang } from './url.js';

export type {
	Language,
	LanguageCode,
	DetectConfig,
	LanguageSwitcherProps,
} from './types.js';
