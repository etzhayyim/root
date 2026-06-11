/** ISO 639-1 language code */
export type LanguageCode = string;

/**
 * Bible-translation coverage level (United Bible Societies / Wycliffe Global
 * Alliance Scripture-access categories). This is the canonical priority axis
 * for etzhayyim supported languages per ADR-2606072800 (Sola Scriptura): a
 * language's support tier is its Scripture-access tier, not its market size.
 *
 * - `full`     — complete Bible (Old + New Testament) published
 * - `nt`       — New Testament published (OT incomplete or in progress)
 * - `portions` — at least one book / Selections published
 * - `none`     — no Scripture yet (translation in progress or unstarted)
 */
export type BibleCoverage = 'full' | 'nt' | 'portions' | 'none';

/** Language definition with code and native display name */
export interface Language {
	code: LanguageCode;
	name: string;
	/** English name (e.g., "Japanese") */
	enName?: string;
	/** ISO 15924 script code (e.g., "Latn", "Cyrl", "Arab") */
	script?: string;
	/** Text direction: "ltr" or "rtl" */
	dir?: 'ltr' | 'rtl';
	/**
	 * Bible-translation coverage (UBS/Wycliffe). Canonical priority signal.
	 * @see BibleCoverage
	 */
	bibleCoverage?: BibleCoverage;
	/**
	 * Priority tier 1-4 (1=highest). Per ADR-2606072800 the tier IS the
	 * Scripture-access tier, derived from `bibleCoverage`:
	 * 1=full, 2=nt, 3=portions, 4=none.
	 */
	tier?: number;
}

/** Configuration for language detection */
export interface DetectConfig {
	/** Supported language codes to match against */
	supported: LanguageCode[];
	/** Default language if none detected */
	defaultLang: LanguageCode;
	/** Distribution weights for Hindi-speaker regional language selection */
	indiaDistribution?: Record<LanguageCode, number>;
}

/** Props for the LanguageSwitcher component */
export interface LanguageSwitcherProps {
	/** Languages to display in the switcher */
	languages: Language[];
	/** Currently active language code */
	currentLang: LanguageCode;
	/** Function to generate the URL for a given language */
	getUrl: (langCode: LanguageCode) => string;
	/** Callback fired when language changes */
	onchange?: (from: LanguageCode, to: LanguageCode) => void;
	/** UI variant: 'links' renders anchor tags, 'select' renders a dropdown, 'search' renders a searchable dropdown */
	variant?: 'links' | 'select' | 'search';
	/** Additional CSS class for the container */
	class?: string;
}
