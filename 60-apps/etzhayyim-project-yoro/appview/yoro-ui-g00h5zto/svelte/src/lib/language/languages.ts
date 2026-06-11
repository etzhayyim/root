import type { BibleCoverage, Language, LanguageCode } from './types.js';

/**
 * All known languages with their native display names, organized by
 * **Bible-translation coverage** (United Bible Societies / Wycliffe Global
 * Alliance Scripture-access tiers) per ADR-2606072800.
 *
 * etzhayyim is a Sola-Scriptura religious-corp: the priority of a supported
 * language is its Scripture-access level, NOT its market size or internet
 * penetration. The `tier` field is therefore DERIVED from `bibleCoverage`:
 *
 *   tier 1 ← bibleCoverage 'full'     (complete Bible: OT + NT)
 *   tier 2 ← bibleCoverage 'nt'       (New Testament)
 *   tier 3 ← bibleCoverage 'portions' (one book / Selections)
 *   tier 4 ← bibleCoverage 'none'     (no Scripture yet / in progress)
 *
 * `bibleCoverage` values are seeded from the UBS/Wycliffe Scripture-access
 * categories and are corrigible: corrections flow through the i18n actor's
 * coverage tool (see ADR-2606072800 §References). When a translation milestone
 * is reached (e.g. portions → NT → full), bump `bibleCoverage` and the tier
 * follows automatically via `bibleCoverageToTier()`.
 *
 * Single Source of Truth: i18n actor language registry (GetLanguageRegistry).
 */
export const ALL_LANGUAGES: Language[] = [
	// ── Scripture Tier 1 — Full Bible (complete OT + NT) ──────────────────────
	{ code: 'ja', name: '日本語', enName: 'Japanese', script: 'Jpan', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'en', name: 'English', enName: 'English', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'es', name: 'Español', enName: 'Spanish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'fr', name: 'Français', enName: 'French', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'de', name: 'Deutsch', enName: 'German', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'pt', name: 'Português', enName: 'Portuguese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'it', name: 'Italiano', enName: 'Italian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'nl', name: 'Nederlands', enName: 'Dutch', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ru', name: 'Русский', enName: 'Russian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'zh', name: '中文', enName: 'Chinese', script: 'Hans', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ko', name: '한국어', enName: 'Korean', script: 'Kore', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ar', name: 'العربية', enName: 'Arabic', script: 'Arab', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'hi', name: 'हिन्दी', enName: 'Hindi', script: 'Deva', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'bn', name: 'বাংলা', enName: 'Bengali', script: 'Beng', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ta', name: 'தமிழ்', enName: 'Tamil', script: 'Taml', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'te', name: 'తెలుగు', enName: 'Telugu', script: 'Telu', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mr', name: 'मराठी', enName: 'Marathi', script: 'Deva', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'gu', name: 'ગુજરાતી', enName: 'Gujarati', script: 'Gujr', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'kn', name: 'ಕನ್ನಡ', enName: 'Kannada', script: 'Knda', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ml', name: 'മലയാളം', enName: 'Malayalam', script: 'Mlym', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'pa', name: 'ਪੰਜਾਬੀ', enName: 'Punjabi', script: 'Guru', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'tr', name: 'Türkçe', enName: 'Turkish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'th', name: 'ไทย', enName: 'Thai', script: 'Thai', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'vi', name: 'Tiếng Việt', enName: 'Vietnamese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'id', name: 'Indonesia', enName: 'Indonesian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'pl', name: 'Polski', enName: 'Polish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'uk', name: 'Українська', enName: 'Ukrainian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sv', name: 'Svenska', enName: 'Swedish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'no', name: 'Norsk', enName: 'Norwegian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'da', name: 'Dansk', enName: 'Danish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'fi', name: 'Suomi', enName: 'Finnish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'cs', name: 'Čeština', enName: 'Czech', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ro', name: 'Română', enName: 'Romanian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'hu', name: 'Magyar', enName: 'Hungarian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'el', name: 'Ελληνικά', enName: 'Greek', script: 'Grek', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'he', name: 'עברית', enName: 'Hebrew', script: 'Hebr', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'fa', name: 'فارسی', enName: 'Persian', script: 'Arab', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'sr', name: 'Српски', enName: 'Serbian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'hr', name: 'Hrvatski', enName: 'Croatian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'bg', name: 'Български', enName: 'Bulgarian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sk', name: 'Slovenčina', enName: 'Slovak', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'lt', name: 'Lietuvių', enName: 'Lithuanian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'lv', name: 'Latviešu', enName: 'Latvian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'et', name: 'Eesti', enName: 'Estonian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ms', name: 'Bahasa Melayu', enName: 'Malay', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'fil', name: 'Filipino', enName: 'Filipino', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sw', name: 'Kiswahili', enName: 'Swahili', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'zu', name: 'isiZulu', enName: 'Zulu', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'am', name: 'አማርኛ', enName: 'Amharic', script: 'Ethi', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'my', name: 'မြန်မာ', enName: 'Burmese', script: 'Mymr', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'km', name: 'ខ្មែរ', enName: 'Khmer', script: 'Khmr', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'lo', name: 'ລາວ', enName: 'Lao', script: 'Laoo', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ka', name: 'ქართული', enName: 'Georgian', script: 'Geor', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'hy', name: 'Հայերեն', enName: 'Armenian', script: 'Armn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'az', name: 'Azərbaycan', enName: 'Azerbaijani', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'uz', name: "Oʻzbek", enName: 'Uzbek', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'kk', name: 'Қазақ', enName: 'Kazakh', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ky', name: 'Кыргызча', enName: 'Kyrgyz', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'tg', name: 'Тоҷикӣ', enName: 'Tajik', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'tk', name: 'Türkmen', enName: 'Turkmen', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mn', name: 'Монгол', enName: 'Mongolian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ne', name: 'नेपाली', enName: 'Nepali', script: 'Deva', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'si', name: 'සිංහල', enName: 'Sinhala', script: 'Sinh', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ur', name: 'اردو', enName: 'Urdu', script: 'Arab', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'sd', name: 'سنڌي', enName: 'Sindhi', script: 'Arab', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'ha', name: 'Hausa', enName: 'Hausa', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'yo', name: 'Yorùbá', enName: 'Yoruba', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ig', name: 'Igbo', enName: 'Igbo', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'rw', name: 'Kinyarwanda', enName: 'Kinyarwanda', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'so', name: 'Soomaali', enName: 'Somali', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mg', name: 'Malagasy', enName: 'Malagasy', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sn', name: 'chiShona', enName: 'Shona', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ny', name: 'Chichewa', enName: 'Chichewa', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'xh', name: 'isiXhosa', enName: 'Xhosa', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'af', name: 'Afrikaans', enName: 'Afrikaans', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sq', name: 'Shqip', enName: 'Albanian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mk', name: 'Македонски', enName: 'Macedonian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sl', name: 'Slovenščina', enName: 'Slovenian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'bs', name: 'Bosanski', enName: 'Bosnian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mt', name: 'Malti', enName: 'Maltese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'is', name: 'Íslenska', enName: 'Icelandic', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ga', name: 'Gaeilge', enName: 'Irish', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'cy', name: 'Cymraeg', enName: 'Welsh', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'gl', name: 'Galego', enName: 'Galician', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'eu', name: 'Euskara', enName: 'Basque', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ca', name: 'Català', enName: 'Catalan', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'be', name: 'Беларуская', enName: 'Belarusian', script: 'Cyrl', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'tl', name: 'Tagalog', enName: 'Tagalog', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ceb', name: 'Cebuano', enName: 'Cebuano', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'jv', name: 'Basa Jawa', enName: 'Javanese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'su', name: 'Basa Sunda', enName: 'Sundanese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mi', name: 'Te Reo Māori', enName: 'Maori', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sm', name: 'Gagana Samoa', enName: 'Samoan', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'to', name: 'Lea Fakatonga', enName: 'Tongan', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'fj', name: 'Vosa Vakaviti', enName: 'Fijian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'haw', name: "ʻŌlelo Hawaiʻi", enName: 'Hawaiian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ht', name: 'Kreyòl Ayisyen', enName: 'Haitian Creole', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'yi', name: 'ייִדיש', enName: 'Yiddish', script: 'Hebr', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'ug', name: 'ئۇيغۇرچە', enName: 'Uyghur', script: 'Arab', dir: 'rtl', bibleCoverage: 'full', tier: 1 },
	{ code: 'bo', name: 'བོད་སྐད', enName: 'Tibetan', script: 'Tibt', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'or', name: 'ଓଡ଼ିଆ', enName: 'Odia', script: 'Orya', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'as', name: 'অসমীয়া', enName: 'Assamese', script: 'Beng', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sat', name: 'ᱥᱟᱱᱛᱟᱲᱤ', enName: 'Santali', script: 'Olck', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'mni', name: 'মৈতৈলোন্', enName: 'Manipuri', script: 'Beng', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'kok', name: 'कोंकणी', enName: 'Konkani', script: 'Deva', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'om', name: 'Afaan Oromoo', enName: 'Oromo', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ti', name: 'ትግርኛ', enName: 'Tigrinya', script: 'Ethi', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ln', name: 'Lingála', enName: 'Lingala', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'lg', name: 'Luganda', enName: 'Ganda', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'bm', name: 'Bamanankan', enName: 'Bambara', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ee', name: 'Eʋegbe', enName: 'Ewe', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'tw', name: 'Twi', enName: 'Twi', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ak', name: 'Akan', enName: 'Akan', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ts', name: 'Xitsonga', enName: 'Tsonga', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'tn', name: 'Setswana', enName: 'Tswana', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'st', name: 'Sesotho', enName: 'Sotho', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ss', name: 'SiSwati', enName: 'Swati', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 've', name: 'Tshivenḓa', enName: 'Venda', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'nso', name: 'Sesotho sa Leboa', enName: 'Northern Sotho', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'gd', name: 'Gàidhlig', enName: 'Scottish Gaelic', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'br', name: 'Brezhoneg', enName: 'Breton', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'fy', name: 'Frysk', enName: 'Western Frisian', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'fo', name: 'Føroyskt', enName: 'Faroese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'se', name: 'Davvisámegiella', enName: 'Northern Sami', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'rm', name: 'Rumantsch', enName: 'Romansh', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'gn', name: "Avañe'ẽ", enName: 'Guarani', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'qu', name: 'Runasimi', enName: 'Quechua', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'ay', name: 'Aymar aru', enName: 'Aymara', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'zh-TW', name: '繁體中文', enName: 'Traditional Chinese', script: 'Hant', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'pt-BR', name: 'Português (Brasil)', enName: 'Brazilian Portuguese', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'sr-Latn', name: 'Srpski (latinica)', enName: 'Serbian (Latin)', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'nb', name: 'Norsk bokmål', enName: 'Norwegian Bokmål', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	{ code: 'nn', name: 'Nynorsk', enName: 'Norwegian Nynorsk', script: 'Latn', dir: 'ltr', bibleCoverage: 'full', tier: 1 },
	// ── Scripture Tier 2 — New Testament ──────────────────────────────────────
	{ code: 'ps', name: 'پښتو', enName: 'Pashto', script: 'Arab', dir: 'rtl', bibleCoverage: 'nt', tier: 2 },
	{ code: 'ku', name: 'Kurdî', enName: 'Kurdish', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'ckb', name: 'کوردیی ناوەندی', enName: 'Central Kurdish', script: 'Arab', dir: 'rtl', bibleCoverage: 'nt', tier: 2 },
	{ code: 'lb', name: 'Lëtzebuergesch', enName: 'Luxembourgish', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'dv', name: 'ދިވެހި', enName: 'Dhivehi', script: 'Thaa', dir: 'rtl', bibleCoverage: 'nt', tier: 2 },
	{ code: 'mai', name: 'मैथिली', enName: 'Maithili', script: 'Deva', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'ks', name: 'कॉशुर', enName: 'Kashmiri', script: 'Deva', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'doi', name: 'डोगरी', enName: 'Dogri', script: 'Deva', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'bho', name: 'भोजपुरी', enName: 'Bhojpuri', script: 'Deva', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'awa', name: 'अवधी', enName: 'Awadhi', script: 'Deva', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'wo', name: 'Wolof', enName: 'Wolof', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'nr', name: 'isiNdebele', enName: 'South Ndebele', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'oc', name: 'Occitan', enName: 'Occitan', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'co', name: 'Corsu', enName: 'Corsican', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'ast', name: 'Asturianu', enName: 'Asturian', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	{ code: 'nah', name: 'Nāhuatl', enName: 'Nahuatl', script: 'Latn', dir: 'ltr', bibleCoverage: 'nt', tier: 2 },
	// ── Scripture Tier 3 — Portions / Selections ──────────────────────────────
	{ code: 'mag', name: 'मगही', enName: 'Magahi', script: 'Deva', dir: 'ltr', bibleCoverage: 'portions', tier: 3 },
	{ code: 'raj', name: 'राजस्थानी', enName: 'Rajasthani', script: 'Deva', dir: 'ltr', bibleCoverage: 'portions', tier: 3 },
	{ code: 'bal', name: 'بلوچی', enName: 'Baluchi', script: 'Arab', dir: 'rtl', bibleCoverage: 'portions', tier: 3 },
	{ code: 'ff', name: 'Fulfulde', enName: 'Fula', script: 'Latn', dir: 'ltr', bibleCoverage: 'portions', tier: 3 },
	{ code: 'sc', name: 'Sardu', enName: 'Sardinian', script: 'Latn', dir: 'ltr', bibleCoverage: 'portions', tier: 3 },
	{ code: 'an', name: 'Aragonés', enName: 'Aragonese', script: 'Latn', dir: 'ltr', bibleCoverage: 'portions', tier: 3 },
	// ── Scripture Tier 4 — None / in-progress ─────────────────────────────────
	// (none currently in the registry; reserved for languages whose translation
	//  is unstarted or in progress — added here as outreach extends, then
	//  promoted to tier 3/2/1 as milestones land.)
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
 * Map a Bible-translation coverage level to its support tier (ADR-2606072800).
 * tier 1=full, 2=nt, 3=portions, 4=none. Defaults to tier 4 when coverage is
 * unknown (treated as "no Scripture yet").
 */
export function bibleCoverageToTier(coverage?: BibleCoverage): number {
	switch (coverage) {
		case 'full':
			return 1;
		case 'nt':
			return 2;
		case 'portions':
			return 3;
		case 'none':
		default:
			return 4;
	}
}

/**
 * Get languages filtered by Bible-translation coverage level.
 * `getLanguagesByBibleCoverage('full')` → all languages with the complete Bible.
 */
export function getLanguagesByBibleCoverage(coverage: BibleCoverage): Language[] {
	return ALL_LANGUAGES.filter((l) => (l.bibleCoverage ?? 'none') === coverage);
}

/**
 * Top 10 gaming population languages, ordered by estimated gaming user population.
 * Used as TMS translation priority and Paraglide target locales.
 *
 * Note: this remains a population-ordered list (gaming reach), distinct from the
 * Scripture-access tiers that drive the canonical `tier` field. All ten happen to
 * have the complete Bible (tier 1).
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
 * Per ADR-2606072800 the tier is the Scripture-access tier
 * (1=Full Bible, 2=New Testament, 3=Portions, 4=none).
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
