import type { Language, LanguageCode } from './types.js';

/**
 * All known languages with their native display names, organized by tier.
 * Single Source of Truth: i18n App (main.go langRegistry).
 * This file is generated from GetLanguageRegistry API.
 */
export const ALL_LANGUAGES: Language[] = [
	// Tier 1 — Core (25)
	{ code: 'ja', name: '日本語', enName: 'Japanese', script: 'Jpan', dir: 'ltr', tier: 1 },
	{ code: 'en', name: 'English', enName: 'English', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'es', name: 'Español', enName: 'Spanish', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'fr', name: 'Français', enName: 'French', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'de', name: 'Deutsch', enName: 'German', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'pt', name: 'Português', enName: 'Portuguese', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'it', name: 'Italiano', enName: 'Italian', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'nl', name: 'Nederlands', enName: 'Dutch', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'ru', name: 'Русский', enName: 'Russian', script: 'Cyrl', dir: 'ltr', tier: 1 },
	{ code: 'zh', name: '中文', enName: 'Chinese', script: 'Hans', dir: 'ltr', tier: 1 },
	{ code: 'ko', name: '한국어', enName: 'Korean', script: 'Kore', dir: 'ltr', tier: 1 },
	{ code: 'ar', name: 'العربية', enName: 'Arabic', script: 'Arab', dir: 'rtl', tier: 1 },
	{ code: 'hi', name: 'हिन्दी', enName: 'Hindi', script: 'Deva', dir: 'ltr', tier: 1 },
	{ code: 'bn', name: 'বাংলা', enName: 'Bengali', script: 'Beng', dir: 'ltr', tier: 1 },
	{ code: 'ta', name: 'தமிழ்', enName: 'Tamil', script: 'Taml', dir: 'ltr', tier: 1 },
	{ code: 'te', name: 'తెలుగు', enName: 'Telugu', script: 'Telu', dir: 'ltr', tier: 1 },
	{ code: 'mr', name: 'मराठी', enName: 'Marathi', script: 'Deva', dir: 'ltr', tier: 1 },
	{ code: 'gu', name: 'ગુજરાતી', enName: 'Gujarati', script: 'Gujr', dir: 'ltr', tier: 1 },
	{ code: 'kn', name: 'ಕನ್ನಡ', enName: 'Kannada', script: 'Knda', dir: 'ltr', tier: 1 },
	{ code: 'ml', name: 'മലയാളം', enName: 'Malayalam', script: 'Mlym', dir: 'ltr', tier: 1 },
	{ code: 'pa', name: 'ਪੰਜਾਬੀ', enName: 'Punjabi', script: 'Guru', dir: 'ltr', tier: 1 },
	{ code: 'tr', name: 'Türkçe', enName: 'Turkish', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'th', name: 'ไทย', enName: 'Thai', script: 'Thai', dir: 'ltr', tier: 1 },
	{ code: 'vi', name: 'Tiếng Việt', enName: 'Vietnamese', script: 'Latn', dir: 'ltr', tier: 1 },
	{ code: 'id', name: 'Indonesia', enName: 'Indonesian', script: 'Latn', dir: 'ltr', tier: 1 },
	// Tier 2 — High internet penetration (25)
	{ code: 'pl', name: 'Polski', enName: 'Polish', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'uk', name: 'Українська', enName: 'Ukrainian', script: 'Cyrl', dir: 'ltr', tier: 2 },
	{ code: 'sv', name: 'Svenska', enName: 'Swedish', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'no', name: 'Norsk', enName: 'Norwegian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'da', name: 'Dansk', enName: 'Danish', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'fi', name: 'Suomi', enName: 'Finnish', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'cs', name: 'Čeština', enName: 'Czech', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'ro', name: 'Română', enName: 'Romanian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'hu', name: 'Magyar', enName: 'Hungarian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'el', name: 'Ελληνικά', enName: 'Greek', script: 'Grek', dir: 'ltr', tier: 2 },
	{ code: 'he', name: 'עברית', enName: 'Hebrew', script: 'Hebr', dir: 'rtl', tier: 2 },
	{ code: 'fa', name: 'فارسی', enName: 'Persian', script: 'Arab', dir: 'rtl', tier: 2 },
	{ code: 'sr', name: 'Српски', enName: 'Serbian', script: 'Cyrl', dir: 'ltr', tier: 2 },
	{ code: 'hr', name: 'Hrvatski', enName: 'Croatian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'bg', name: 'Български', enName: 'Bulgarian', script: 'Cyrl', dir: 'ltr', tier: 2 },
	{ code: 'sk', name: 'Slovenčina', enName: 'Slovak', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'lt', name: 'Lietuvių', enName: 'Lithuanian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'lv', name: 'Latviešu', enName: 'Latvian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'et', name: 'Eesti', enName: 'Estonian', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'ms', name: 'Bahasa Melayu', enName: 'Malay', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'fil', name: 'Filipino', enName: 'Filipino', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'sw', name: 'Kiswahili', enName: 'Swahili', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'zu', name: 'isiZulu', enName: 'Zulu', script: 'Latn', dir: 'ltr', tier: 2 },
	{ code: 'am', name: 'አማርኛ', enName: 'Amharic', script: 'Ethi', dir: 'ltr', tier: 2 },
	{ code: 'my', name: 'မြန်မာ', enName: 'Burmese', script: 'Mymr', dir: 'ltr', tier: 2 },
	// Tier 3 — Mid-population (50)
	{ code: 'km', name: 'ខ្មែរ', enName: 'Khmer', script: 'Khmr', dir: 'ltr', tier: 3 },
	{ code: 'lo', name: 'ລາວ', enName: 'Lao', script: 'Laoo', dir: 'ltr', tier: 3 },
	{ code: 'ka', name: 'ქართული', enName: 'Georgian', script: 'Geor', dir: 'ltr', tier: 3 },
	{ code: 'hy', name: 'Հայերեն', enName: 'Armenian', script: 'Armn', dir: 'ltr', tier: 3 },
	{ code: 'az', name: 'Azərbaycan', enName: 'Azerbaijani', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'uz', name: "Oʻzbek", enName: 'Uzbek', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'kk', name: 'Қазақ', enName: 'Kazakh', script: 'Cyrl', dir: 'ltr', tier: 3 },
	{ code: 'ky', name: 'Кыргызча', enName: 'Kyrgyz', script: 'Cyrl', dir: 'ltr', tier: 3 },
	{ code: 'tg', name: 'Тоҷикӣ', enName: 'Tajik', script: 'Cyrl', dir: 'ltr', tier: 3 },
	{ code: 'tk', name: 'Türkmen', enName: 'Turkmen', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'mn', name: 'Монгол', enName: 'Mongolian', script: 'Cyrl', dir: 'ltr', tier: 3 },
	{ code: 'ne', name: 'नेपाली', enName: 'Nepali', script: 'Deva', dir: 'ltr', tier: 3 },
	{ code: 'si', name: 'සිංහල', enName: 'Sinhala', script: 'Sinh', dir: 'ltr', tier: 3 },
	{ code: 'ur', name: 'اردو', enName: 'Urdu', script: 'Arab', dir: 'rtl', tier: 3 },
	{ code: 'ps', name: 'پښتو', enName: 'Pashto', script: 'Arab', dir: 'rtl', tier: 3 },
	{ code: 'sd', name: 'سنڌي', enName: 'Sindhi', script: 'Arab', dir: 'rtl', tier: 3 },
	{ code: 'ha', name: 'Hausa', enName: 'Hausa', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'yo', name: 'Yorùbá', enName: 'Yoruba', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ig', name: 'Igbo', enName: 'Igbo', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'rw', name: 'Kinyarwanda', enName: 'Kinyarwanda', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'so', name: 'Soomaali', enName: 'Somali', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'mg', name: 'Malagasy', enName: 'Malagasy', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'sn', name: 'chiShona', enName: 'Shona', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ny', name: 'Chichewa', enName: 'Chichewa', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'xh', name: 'isiXhosa', enName: 'Xhosa', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'af', name: 'Afrikaans', enName: 'Afrikaans', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'sq', name: 'Shqip', enName: 'Albanian', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'mk', name: 'Македонски', enName: 'Macedonian', script: 'Cyrl', dir: 'ltr', tier: 3 },
	{ code: 'sl', name: 'Slovenščina', enName: 'Slovenian', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'bs', name: 'Bosanski', enName: 'Bosnian', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'mt', name: 'Malti', enName: 'Maltese', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'is', name: 'Íslenska', enName: 'Icelandic', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ga', name: 'Gaeilge', enName: 'Irish', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'cy', name: 'Cymraeg', enName: 'Welsh', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'gl', name: 'Galego', enName: 'Galician', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'eu', name: 'Euskara', enName: 'Basque', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ca', name: 'Català', enName: 'Catalan', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'lb', name: 'Lëtzebuergesch', enName: 'Luxembourgish', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'be', name: 'Беларуская', enName: 'Belarusian', script: 'Cyrl', dir: 'ltr', tier: 3 },
	{ code: 'tl', name: 'Tagalog', enName: 'Tagalog', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ceb', name: 'Cebuano', enName: 'Cebuano', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'jv', name: 'Basa Jawa', enName: 'Javanese', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'su', name: 'Basa Sunda', enName: 'Sundanese', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'mi', name: 'Te Reo Māori', enName: 'Maori', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'sm', name: 'Gagana Samoa', enName: 'Samoan', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'to', name: 'Lea Fakatonga', enName: 'Tongan', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'fj', name: 'Vosa Vakaviti', enName: 'Fijian', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'haw', name: "ʻŌlelo Hawaiʻi", enName: 'Hawaiian', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ht', name: 'Kreyòl Ayisyen', enName: 'Haitian Creole', script: 'Latn', dir: 'ltr', tier: 3 },
	{ code: 'ku', name: 'Kurdî', enName: 'Kurdish', script: 'Latn', dir: 'ltr', tier: 3 },
	// Tier 4 — Long-tail (100+)
	{ code: 'yi', name: 'ייִדיש', enName: 'Yiddish', script: 'Hebr', dir: 'rtl', tier: 4 },
	{ code: 'dv', name: 'ދިވެހި', enName: 'Dhivehi', script: 'Thaa', dir: 'rtl', tier: 4 },
	{ code: 'ug', name: 'ئۇيغۇرچە', enName: 'Uyghur', script: 'Arab', dir: 'rtl', tier: 4 },
	{ code: 'bo', name: 'བོད་སྐད', enName: 'Tibetan', script: 'Tibt', dir: 'ltr', tier: 4 },
	{ code: 'or', name: 'ଓଡ଼ିଆ', enName: 'Odia', script: 'Orya', dir: 'ltr', tier: 4 },
	{ code: 'as', name: 'অসমীয়া', enName: 'Assamese', script: 'Beng', dir: 'ltr', tier: 4 },
	{ code: 'mai', name: 'मैथिली', enName: 'Maithili', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'sat', name: 'ᱥᱟᱱᱛᱟᱲᱤ', enName: 'Santali', script: 'Olck', dir: 'ltr', tier: 4 },
	{ code: 'ks', name: 'कॉशुर', enName: 'Kashmiri', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'doi', name: 'डोगरी', enName: 'Dogri', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'mni', name: 'মৈতৈলোন্', enName: 'Manipuri', script: 'Beng', dir: 'ltr', tier: 4 },
	{ code: 'kok', name: 'कोंकणी', enName: 'Konkani', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'bho', name: 'भोजपुरी', enName: 'Bhojpuri', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'awa', name: 'अवधी', enName: 'Awadhi', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'mag', name: 'मगही', enName: 'Magahi', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'raj', name: 'राजस्थानी', enName: 'Rajasthani', script: 'Deva', dir: 'ltr', tier: 4 },
	{ code: 'ckb', name: 'کوردیی ناوەندی', enName: 'Central Kurdish', script: 'Arab', dir: 'rtl', tier: 4 },
	{ code: 'bal', name: 'بلوچی', enName: 'Baluchi', script: 'Arab', dir: 'rtl', tier: 4 },
	{ code: 'om', name: 'Afaan Oromoo', enName: 'Oromo', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ti', name: 'ትግርኛ', enName: 'Tigrinya', script: 'Ethi', dir: 'ltr', tier: 4 },
	{ code: 'ln', name: 'Lingála', enName: 'Lingala', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'lg', name: 'Luganda', enName: 'Ganda', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'wo', name: 'Wolof', enName: 'Wolof', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ff', name: 'Fulfulde', enName: 'Fula', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'bm', name: 'Bamanankan', enName: 'Bambara', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ee', name: 'Eʋegbe', enName: 'Ewe', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'tw', name: 'Twi', enName: 'Twi', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ak', name: 'Akan', enName: 'Akan', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ts', name: 'Xitsonga', enName: 'Tsonga', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'tn', name: 'Setswana', enName: 'Tswana', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'st', name: 'Sesotho', enName: 'Sotho', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ss', name: 'SiSwati', enName: 'Swati', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 've', name: 'Tshivenḓa', enName: 'Venda', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'nr', name: 'isiNdebele', enName: 'South Ndebele', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'nso', name: 'Sesotho sa Leboa', enName: 'Northern Sotho', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'gd', name: 'Gàidhlig', enName: 'Scottish Gaelic', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'br', name: 'Brezhoneg', enName: 'Breton', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'oc', name: 'Occitan', enName: 'Occitan', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'co', name: 'Corsu', enName: 'Corsican', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'sc', name: 'Sardu', enName: 'Sardinian', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'fy', name: 'Frysk', enName: 'Western Frisian', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'fo', name: 'Føroyskt', enName: 'Faroese', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'se', name: 'Davvisámegiella', enName: 'Northern Sami', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'rm', name: 'Rumantsch', enName: 'Romansh', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'an', name: 'Aragonés', enName: 'Aragonese', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ast', name: 'Asturianu', enName: 'Asturian', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'gn', name: "Avañe'ẽ", enName: 'Guarani', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'qu', name: 'Runasimi', enName: 'Quechua', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'ay', name: 'Aymar aru', enName: 'Aymara', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'nah', name: 'Nāhuatl', enName: 'Nahuatl', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'zh-TW', name: '繁體中文', enName: 'Traditional Chinese', script: 'Hant', dir: 'ltr', tier: 4 },
	{ code: 'pt-BR', name: 'Português (Brasil)', enName: 'Brazilian Portuguese', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'sr-Latn', name: 'Srpski (latinica)', enName: 'Serbian (Latin)', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'nb', name: 'Norsk bokmål', enName: 'Norwegian Bokmål', script: 'Latn', dir: 'ltr', tier: 4 },
	{ code: 'nn', name: 'Nynorsk', enName: 'Norwegian Nynorsk', script: 'Latn', dir: 'ltr', tier: 4 },
];

/** Lookup map: language code -> Language */
const languageMap = new Map<LanguageCode, Language>(
	ALL_LANGUAGES.map((l) => [l.code, l])
);

/**
 * Filter ALL_LANGUAGES to only the given codes, preserving the order from ALL_LANGUAGES.
 */
export function filterLanguages(codes: LanguageCode[]): Language[] {
	const set = new Set(codes);
	return ALL_LANGUAGES.filter((l) => set.has(l.code));
}

/**
 * Get the native display name for a language code.
 * Returns the code itself if unknown.
 */
export function getLanguageName(code: LanguageCode): string {
	return languageMap.get(code)?.name ?? code;
}

/**
 * All language codes.
 */
export const ALL_LANGUAGE_CODES: LanguageCode[] = ALL_LANGUAGES.map((l) => l.code);

/**
 * Top 10 gaming population languages, ordered by estimated gaming user population.
 * Used as TMS translation priority and Paraglide target locales.
 *
 * | Rank | Code | Language           | Est. Gaming Population |
 * |------|------|--------------------|------------------------|
 * | 1    | en   | English            | ~1,531M speakers       |
 * | 2    | zh   | Chinese (Mandarin) | ~1,477M speakers       |
 * | 3    | es   | Spanish            | ~516M speakers         |
 * | 4    | hi   | Hindi              | high growth (India)    |
 * | 5    | ar   | Arabic             | MENA gaming growth     |
 * | 6    | pt   | Portuguese         | Brazil gaming market   |
 * | 7    | bn   | Bengali            | growing (India/BD)     |
 * | 8    | ru   | Russian            | strong PC gaming       |
 * | 9    | ja   | Japanese           | strong gaming culture  |
 * | 10   | ko   | Korean             | strong esports culture |
 */
export const GAMING_POPULATION_LANGUAGES: LanguageCode[] = [
	'en', 'zh', 'es', 'hi', 'ar', 'pt', 'bn', 'ru', 'ja', 'ko',
];

/**
 * Filter ALL_LANGUAGES to the gaming population top-10, preserving gaming rank order.
 */
export function getGamingLanguages(): Language[] {
	const map = new Map(ALL_LANGUAGES.map((l) => [l.code, l]));
	return GAMING_POPULATION_LANGUAGES.map((code) => map.get(code)).filter(
		(l): l is Language => l !== undefined
	);
}

/**
 * Get languages filtered by tier (1=highest priority, 4=long-tail).
 */
export function getLanguagesByTier(maxTier: number): Language[] {
	return ALL_LANGUAGES.filter((l) => (l.tier ?? 1) <= maxTier);
}

/**
 * Get all RTL languages.
 */
export function getRTLLanguages(): Language[] {
	return ALL_LANGUAGES.filter((l) => l.dir === 'rtl');
}

/**
 * Search languages by code, native name, or English name (case-insensitive).
 */
export function searchLanguages(query: string): Language[] {
	const q = query.toLowerCase();
	return ALL_LANGUAGES.filter(
		(l) =>
			l.code.toLowerCase().includes(q) ||
			l.name.toLowerCase().includes(q) ||
			(l.enName?.toLowerCase().includes(q) ?? false)
	);
}
