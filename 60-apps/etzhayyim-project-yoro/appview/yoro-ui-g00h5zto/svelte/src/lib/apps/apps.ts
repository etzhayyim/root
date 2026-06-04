import type { GfAppLink } from './types';

export const apps: GfAppLink[] = [
	// ── Orgs ──
	{
		id: 'etzhayyim',
		name: 'etzhayyim.com',
		shortName: 'etzhayyim',
		href: 'https://etzhayyim.com',
		icon: '🌐',
		category: 'Orgs',
		description: 'etzhayyim portal',
		external: false
	},

	// ── Security actors (smishing-core path-based DIDs) ──
	{
		id: 'kiyome',
		name: 'smishing.etzhayyim.com:actor:kiyome',
		shortName: 'Kiyome',
		href: 'https://smishing.etzhayyim.com',
		icon: '🔍',
		category: 'Services',
		description: 'SMS phishing analysis & threat intelligence',
		external: false,
	},
	{
		id: 'harai',
		name: 'smishing.etzhayyim.com:actor:harai',
		shortName: 'Harai',
		href: 'https://smishing.etzhayyim.com',
		icon: '🚫',
		category: 'Services',
		description: 'Smishing enforcement & takedown coordinator',
		external: false,
	},

	// ── Services ──
	{
		id: 'manimani',
		name: 'manimani.etzhayyim.com',
		shortName: 'Manimani',
		href: 'https://manimani.etzhayyim.com/embed',
		icon: '🌿',
		category: 'Services',
		description: 'Personal knowledge router — drop a fragment, it lands in the right project',
		external: false
	},
	{
		id: 'news',
		name: 'news.etzhayyim.com',
		shortName: 'News',
		href: 'https://news.etzhayyim.com',
		icon: '📰',
		category: 'Services',
		description: 'AI-driven news portal',
		external: false
	},
	{
		id: 'search',
		name: 'search.etzhayyim.com',
		shortName: 'Search',
		href: 'https://search.etzhayyim.com',
		icon: '🔎',
		category: 'Services',
		description: 'Unified search and discovery',
		external: false
	},
	{
		id: '6ir',
		name: '6ir.etzhayyim.com',
		shortName: '6IR',
		href: 'https://6ir.etzhayyim.com',
		icon: '🧠',
		category: 'Services',
		description: '6IR analytics',
		external: false
	},
	{
		id: 'maps',
		name: 'maps.etzhayyim.com',
		shortName: 'Maps',
		href: 'https://maps.etzhayyim.com',
		icon: '🗺️',
		category: 'Services',
		description: 'Spatial maps and geolocation',
		external: false
	},
	{
		id: 'kareyanagi',
		name: 'kareyanagi.etzhayyim.com',
		shortName: 'Kareyanagi',
		href: 'https://kareyanagi.etzhayyim.com',
		icon: '🦠',
		category: 'Services',
		description: 'Mold eradication platform with IoT sensors and maps integration',
		external: false
	},
	{
		id: 'drive',
		name: 'drive.etzhayyim.com',
		shortName: 'Drive',
		href: 'https://drive.etzhayyim.com',
		icon: '📁',
		category: 'Services',
		description: 'Cloud storage',
		external: false
	},
	{
		id: 'organizer',
		name: 'organizer.etzhayyim.com',
		shortName: 'Organizer',
		href: 'https://organizer.etzhayyim.com',
		icon: '🗂️',
		category: 'Services',
		description: 'Upload anything — AI auto-classifies, tags, and organizes',
		external: false
	},
	{
		id: 'sheets',
		name: 'sheets.etzhayyim.com',
		shortName: 'Sheets',
		href: 'https://sheets.etzhayyim.com',
		icon: '📊',
		category: 'Services',
		description: 'Spreadsheets',
		external: false
	},
	{
		id: 'docs',
		name: 'docs.etzhayyim.com',
		shortName: 'Docs',
		href: 'https://docs.etzhayyim.com',
		icon: '📝',
		category: 'Services',
		description: 'Documentation',
		external: false
	},
	{
		id: 'mailer',
		name: 'mailer.etzhayyim.com',
		shortName: 'Mailer',
		href: 'https://mailer.etzhayyim.com',
		icon: '📧',
		category: 'Services',
		description: 'Email client',
		external: false
	},
	{
		id: 'gmail',
		name: 'gmail.etzhayyim.com',
		shortName: 'Gmail',
		href: 'https://gmail.etzhayyim.com',
		icon: '✉️',
		category: 'Services',
		description: 'Gmail sync + AI triage + contact DID messenger bridge',
		external: false
	},
	{
		id: 'outlook',
		name: 'outlook.etzhayyim.com',
		shortName: 'Outlook',
		href: 'https://outlook.etzhayyim.com',
		icon: '📬',
		category: 'Services',
		description: 'Outlook sync + calendar + contact DID bridge',
		external: false
	},
	{
		id: 'oshikatsu',
		name: 'oshikatsu.etzhayyim.com',
		shortName: 'Oshikatsu',
		href: 'https://oshikatsu.etzhayyim.com',
		icon: '🍚',
		category: 'Services',
		description: 'Career support',
		external: false
	},
	{
		id: 'oshinobi',
		name: 'oshinobi.etzhayyim.com',
		shortName: 'Oshinobi',
		href: 'https://oshinobi.etzhayyim.com',
		icon: '🥷',
		category: 'Services',
		description: 'Creator subscription platform (tiers, tips, posts)',
		external: false
	},
	{
		id: 'calendar',
		name: 'calendar.etzhayyim.com',
		shortName: 'Calendar',
		href: 'https://calendar.etzhayyim.com',
		icon: '📅',
		category: 'Services',
		description: 'Calendar',
		external: false
	},
	{
		id: 'forms',
		name: 'forms.etzhayyim.com',
		shortName: 'Forms',
		href: 'https://forms.etzhayyim.com',
		icon: '📋',
		category: 'Services',
		description: 'Forms builder',
		external: false
	},
	{
		id: 'threads',
		name: 'etzhayyim.com',
		shortName: 'Matrix',
		href: 'https://etzhayyim.com',
		icon: '💬',
		category: 'Services',
		description: 'Matrix messaging',
		external: false
	},
	{
		id: 'hub',
		name: 'hub.etzhayyim.com',
		shortName: 'Hub',
		href: 'https://hub.etzhayyim.com',
		icon: '🏠',
		category: 'Services',
		description: 'Git-compatible project hub',
		external: false
	},
	{
		id: 'translate',
		name: 'translate.etzhayyim.com',
		shortName: 'Translate',
		href: 'https://translate.etzhayyim.com',
		icon: '🌍',
		category: 'Services',
		description: 'Translation service',
		external: false
	},
	{
		id: 'images',
		name: 'images.etzhayyim.com',
		shortName: 'Images',
		href: 'https://images.etzhayyim.com',
		icon: '🖼️',
		category: 'Services',
		description: 'Image processing',
		external: false
	},
	{
		id: 'videos',
		name: 'douga.etzhayyim.com',
		shortName: 'Videos',
		href: 'https://douga.etzhayyim.com',
		icon: '🎬',
		category: 'Services',
		description: 'Video platform',
		external: false
	},
	{
		id: 'videos-legacy',
		name: 'videos.etzhayyim.com',
		shortName: 'Videos2',
		href: 'https://videos.etzhayyim.com',
		icon: '🎥',
		category: 'Services',
		description: 'Video platform',
		external: false
	},
	{
		id: 'music',
		name: 'music.etzhayyim.com',
		shortName: 'Music',
		href: 'https://music.etzhayyim.com',
		icon: '🎵',
		category: 'Services',
		description: 'Music streaming',
		external: false
	},
	{
		id: 'manga',
		name: 'manga.etzhayyim.com',
		shortName: 'Manga',
		href: 'https://manga.etzhayyim.com',
		icon: '📚',
		category: 'Services',
		description: 'Manga reader',
		external: false
	},
	{
		id: 'anime',
		name: 'anime.etzhayyim.com',
		shortName: 'Anime',
		href: 'https://anime.etzhayyim.com',
		icon: '🎞️',
		category: 'Services',
		description: 'Anime platform',
		external: false
	},
	{
		id: 'games',
		name: 'games.etzhayyim.com',
		shortName: 'Games',
		href: 'https://games.etzhayyim.com',
		icon: '🎮',
		category: 'Services',
		description: 'Games',
		external: false
	},
	{
		id: 'gameya',
		name: 'gameya.etzhayyim.com',
		shortName: 'Gameya',
		href: 'https://gameya.etzhayyim.com',
		icon: '🕹️',
		category: 'Services',
		description: 'Playable browser game lab',
		external: false
	},
	{
		id: 'narou',
		name: 'narou.etzhayyim.com',
		shortName: 'Narou',
		href: 'https://narou.etzhayyim.com',
		icon: '📖',
		category: 'Services',
		description: 'Novel platform',
		external: false
	},
	{
		id: 'cards',
		name: 'cards.etzhayyim.com',
		shortName: 'Cards',
		href: 'https://cards.etzhayyim.com',
		icon: '💳',
		category: 'Services',
		description: 'Stripe Issuing cards',
		external: false
	},
	{
		id: 'tenki',
		name: 'tenki.etzhayyim.com',
		shortName: 'Tenki',
		href: 'https://tenki.etzhayyim.com',
		icon: '🌤️',
		category: 'Services',
		description: 'Weather',
		external: false
	},
	{
		id: 'yadoya',
		name: 'yadoya.etzhayyim.com',
		shortName: 'Yadoya',
		href: 'https://yadoya.etzhayyim.com',
		icon: '🏨',
		category: 'Services',
		description: 'Lodging and stays',
		external: false
	},
	{
		id: 'fleamarket',
		name: 'fleamarket.etzhayyim.com',
		shortName: 'FleaMarket',
		href: 'https://fleamarket.etzhayyim.com',
		icon: '🛍️',
		category: 'Services',
		description: 'Marketplace',
		external: false
	},
	{
		id: 'okaimono',
		name: 'okaimono.etzhayyim.com',
		shortName: 'Shopping',
		href: 'https://okaimono.etzhayyim.com',
		icon: '🛒',
		category: 'Services',
		description: 'Shopping',
		external: false
	},
	{
		id: 'yadoya',
		name: 'yadoya.etzhayyim.com',
		shortName: 'Yadoya',
		href: 'https://yadoya.etzhayyim.com',
		icon: '🏨',
		category: 'Services',
		description: 'Hotel search and reservation',
		external: false
	},
	{
		id: 'briefing',
		name: 'briefing.etzhayyim.com',
		shortName: 'Briefing',
		href: 'https://briefing.etzhayyim.com',
		icon: '📑',
		category: 'Services',
		description: 'Content briefing',
		external: false
	},
	{
		id: 'tsukuru',
		name: 'tsukuru.etzhayyim.com',
		shortName: 'Tsukuru',
		href: 'https://tsukuru.etzhayyim.com',
		icon: '🏭',
		category: 'Services',
		description: 'Factory-direct ordering platform',
		external: false
	},
	{
		id: 'cowork',
		name: 'cowork.etzhayyim.com',
		shortName: 'Cowork',
		href: 'https://cowork.etzhayyim.com',
		icon: '👥',
		category: 'Services',
		description: 'Co-working',
		external: false
	},
	{
		id: 'shigotoba',
		name: 'shigotoba.etzhayyim.com',
		shortName: 'Shigotoba',
		href: 'https://shigotoba.etzhayyim.com',
		icon: '💼',
		category: 'Services',
		description: 'Job board',
		external: false
	},
	{
		id: 'scheduler',
		name: 'scheduler.etzhayyim.com',
		shortName: 'Scheduler',
		href: 'https://scheduler.etzhayyim.com',
		icon: '⏰',
		category: 'Services',
		description: 'Scheduler and automation',
		external: false
	},
	{
		id: 'web4',
		name: 'web4.etzhayyim.com',
		shortName: 'Web4',
		href: 'https://web4.etzhayyim.com',
		icon: '🔗',
		category: 'Services',
		description: 'Web4 / GCC token',
		external: false
	},
	{
		id: 'society6',
		name: 'society6.etzhayyim.com',
		shortName: 'Society6',
		href: 'https://society6.etzhayyim.com',
		icon: '🏛️',
		category: 'Services',
		description: 'COFOG access and Society6 policy portal',
		external: false
	},
	{
		id: 'lawfirm',
		name: 'lawfirm.etzhayyim.com',
		shortName: 'Law Firm',
		href: 'https://lawfirm.etzhayyim.com',
		icon: '⚖️',
		category: 'Services',
		description: 'Law firm client portal',
		external: false
	},
	{
		id: 'lawyer',
		name: 'lawyer.etzhayyim.com',
		shortName: 'Lawyer',
		href: 'https://lawyer.etzhayyim.com',
		icon: '👨‍⚖️',
		category: 'Services',
		description: 'Lawyer workspace',
		external: false
	},
	{
		id: 'ekyc',
		name: 'ekyc.etzhayyim.com',
		shortName: 'eKYC',
		href: 'https://ekyc.etzhayyim.com',
		icon: '🪪',
		category: 'Services',
		description: 'Identity verification',
		external: false
	},
	{
		id: 'shomeisyashin',
		name: 'shomeisyashin.etzhayyim.com',
		shortName: 'ID Photo',
		href: 'https://shomeisyashin.etzhayyim.com',
		icon: '📸',
		category: 'Services',
		description: 'AI証明写真メーカー',
		external: false
	},
	{
		id: 'global',
		name: 'global.etzhayyim.com',
		shortName: 'Global',
		href: 'https://global.etzhayyim.com',
		icon: '🌏',
		category: 'Services',
		description: 'Global services',
		external: false
	},
	{
		id: 'worlds',
		name: 'worlds.etzhayyim.com',
		shortName: 'Worlds',
		href: 'https://worlds.etzhayyim.com',
		icon: '🌌',
		category: 'Services',
		description: 'Virtual worlds',
		external: false
	},
	{
		id: 'pachinko',
		name: 'pachinko.etzhayyim.com',
		shortName: 'Pachinko',
		href: 'https://pachinko.etzhayyim.com',
		icon: '🎰',
		category: 'Services',
		description: 'Pachinko simulation',
		external: false
	},
	{
		id: 'casino',
		name: 'casino.etzhayyim.com',
		shortName: 'Casino',
		href: 'https://casino.etzhayyim.com',
		icon: '🎲',
		category: 'Services',
		description: 'World casino directory',
		external: false
	},
	{
		id: 'oshiete',
		name: 'oshiete.etzhayyim.com',
		shortName: 'Oshiete',
		href: 'https://oshiete.etzhayyim.com',
		icon: '❓',
		category: 'Services',
		description: 'Q&A platform',
		external: false
	},
	{
		id: 'webpage',
		name: 'webpage.etzhayyim.com',
		shortName: 'Webpage',
		href: 'https://webpage.etzhayyim.com',
		icon: '🌐',
		category: 'Services',
		description: 'Web page crawl and text extraction',
		external: false
	},
	{
		id: 'marketer',
		name: 'marketer.etzhayyim.com',
		shortName: 'Marketer',
		href: 'https://marketer.etzhayyim.com',
		icon: '📣',
		category: 'Services',
		description: 'Marketing tools',
		external: false
	},
	{
		id: 'omikuji',
		name: 'omikuji.etzhayyim.com',
		shortName: 'Omikuji',
		href: 'https://omikuji.etzhayyim.com',
		icon: '🎋',
		category: 'Services',
		description: 'Fortune telling',
		external: false
	},
	{
		id: 'aima',
		name: 'aima.etzhayyim.com',
		shortName: 'AIMA',
		href: 'https://aima.etzhayyim.com',
		icon: '🤖',
		category: 'Services',
		description: 'AI models',
		external: false
	},
	{
		id: 'robot',
		name: 'robot.etzhayyim.com',
		shortName: 'Robot',
		href: 'https://robot.etzhayyim.com',
		icon: '🦾',
		category: 'Services',
		description: 'Robot automation',
		external: false
	},
	{
		id: 'wire',
		name: 'wire.etzhayyim.com',
		shortName: 'Wire',
		href: 'https://wire.etzhayyim.com',
		icon: '📡',
		category: 'Services',
		description: 'Messaging',
		external: false
	},
	{
		id: 'lawfirm-admin',
		name: 'lawfirm-admin.etzhayyim.com',
		shortName: 'LF Admin',
		href: 'https://lawfirm-admin.etzhayyim.com',
		icon: '🏛️',
		category: 'Services',
		description: 'Law firm admin',
		external: false
	},

	// ── Systems ──
	{
		id: 'performers',
		name: 'etzhayyim.com',
		shortName: 'Performers',
		href: 'https://etzhayyim.com',
		icon: '🚀',
		category: 'Systems',
		description: 'Platform dashboard',
		external: false
	},
	{
		id: 'analytics',
		name: 'analytics.etzhayyim.com',
		shortName: 'Analytics',
		href: 'https://analytics.etzhayyim.com',
		icon: '📈',
		category: 'Systems',
		description: 'Analytics dashboard',
		external: false
	},
	{
		id: 'ops',
		name: 'ops.etzhayyim.com',
		shortName: 'Ops',
		href: 'https://ops.etzhayyim.com',
		icon: '⚙️',
		category: 'Systems',
		description: 'Project operations',
		external: false
	},
	{
		id: 'sre',
		name: 'sre.etzhayyim.com',
		shortName: 'SRE',
		href: 'https://sre.etzhayyim.com',
		icon: '🔧',
		category: 'Systems',
		description: 'Site reliability',
		external: false
	},
	{
		id: 'os',
		name: 'os.etzhayyim.com',
		shortName: 'OS',
		href: 'https://os.etzhayyim.com',
		icon: '🖥️',
		category: 'Systems',
		description: 'Operating system UI',
		external: false
	},
	{
		id: 'po',
		name: 'po.etzhayyim.com',
		shortName: 'PO',
		href: 'https://po.etzhayyim.com',
		icon: '📐',
		category: 'Systems',
		description: 'Projection operator',
		external: false
	},
	{
		id: 'gov',
		name: 'gov.etzhayyim.com',
		shortName: 'Gov',
		href: 'https://gov.etzhayyim.com',
		icon: '🏢',
		category: 'Systems',
		description: 'Governance',
		external: false
	},
	{
		id: 'resources',
		name: 'resources.etzhayyim.com',
		shortName: 'Resources',
		href: 'https://resources.etzhayyim.com',
		icon: '🗄️',
		category: 'Systems',
		description: 'JSON-LD/RDF resources',
		external: false
	},
	{
		id: 'completer',
		name: 'completer.etzhayyim.com',
		shortName: 'Completer',
		href: 'https://completer.etzhayyim.com',
		icon: '✏️',
		category: 'Systems',
		description: 'Code completion',
		external: false
	},
	{
		id: 'har',
		name: 'har.etzhayyim.com',
		shortName: 'HAR',
		href: 'https://har.etzhayyim.com',
		icon: '🗂️',
		category: 'Systems',
		description: 'HAR viewer',
		external: false
	},
	{
		id: 'provider-pod',
		name: 'provider-pod.etzhayyim.com',
		shortName: 'Provider',
		href: 'https://provider-pod.etzhayyim.com',
		icon: '📦',
		category: 'Systems',
		description: 'Provider pod marketplace',
		external: false
	},
	{
		id: 'ge',
		name: 'ge.etzhayyim.com',
		shortName: 'GE',
		href: 'https://ge.etzhayyim.com',
		icon: '🎓',
		category: 'Systems',
		description: 'General education',
		external: false
	},
	{
		id: 'lo',
		name: 'lo.etzhayyim.com',
		shortName: 'LO',
		href: 'https://lo.etzhayyim.com',
		icon: '🧩',
		category: 'Systems',
		description: 'Learning objects',
		external: false
	},
	{
		id: 'tia',
		name: 'tia.etzhayyim.com',
		shortName: 'TIA',
		href: 'https://tia.etzhayyim.com',
		icon: '🎙️',
		category: 'Systems',
		description: 'TIA assistant',
		external: false
	},
	{
		id: 'wvme',
		name: 'wvme.etzhayyim.com',
		shortName: 'WVME',
		href: 'https://wvme.etzhayyim.com',
		icon: '🎛️',
		category: 'Systems',
		description: 'WVME platform',
		external: false
	},
	{
		id: 'tasklist',
		name: 'tasklist.etzhayyim.com',
		shortName: 'TaskList',
		href: 'https://tasklist.etzhayyim.com',
		icon: '✅',
		category: 'Systems',
		description: 'Task approval',
		external: false
	}
];

const appAliases: Record<string, string> = {
	'email-service-adapter': 'mailer',
	'external-service-adapter': 'mailer',
	gmail: 'mailer',
	'web-analytics': 'analytics'
};

export function normalizeAppId(appId: string): string {
	const normalized = appId.trim().toLowerCase().replace(/\.etzhayyim\.ai$/, '').replace(/_/g, '-');
	return appAliases[normalized] ?? normalized;
}

export function findAppById(appId: string): GfAppLink | undefined {
	const normalized = normalizeAppId(appId);
	return apps.find((app) => app.id === normalized);
}

export function resolveAppHref(appId: string, fallbackHref?: string): string {
	const app = findAppById(appId);
	if (app) return app.href;
	if (fallbackHref) return fallbackHref;
	return `https://${normalizeAppId(appId)}.etzhayyim.com`;
}
