import type { GfAppLink } from './types';

export const apps: GfAppLink[] = [
	// ── Orgs ──
	{
		id: 'gftd',
		name: 'gftd.ai',
		shortName: 'GFTD',
		href: 'https://gftd.ai',
		icon: '🌐',
		category: 'Orgs',
		description: 'GFTD portal',
		external: false
	},

	// ── Security actors (smishing-core path-based DIDs) ──
	{
		id: 'kiyome',
		name: 'smishing.gftd.ai:actor:kiyome',
		shortName: 'Kiyome',
		href: 'https://smishing.gftd.ai',
		icon: '🔍',
		category: 'Services',
		description: 'SMS phishing analysis & threat intelligence',
		external: false,
	},
	{
		id: 'harai',
		name: 'smishing.gftd.ai:actor:harai',
		shortName: 'Harai',
		href: 'https://smishing.gftd.ai',
		icon: '🚫',
		category: 'Services',
		description: 'Smishing enforcement & takedown coordinator',
		external: false,
	},

	// ── Services ──
	{
		id: 'manimani',
		name: 'manimani.gftd.ai',
		shortName: 'Manimani',
		href: 'https://manimani.gftd.ai/embed',
		icon: '🌿',
		category: 'Services',
		description: 'Personal knowledge router — drop a fragment, it lands in the right project',
		external: false
	},
	{
		id: 'news',
		name: 'news.gftd.ai',
		shortName: 'News',
		href: 'https://news.gftd.ai',
		icon: '📰',
		category: 'Services',
		description: 'AI-driven news portal',
		external: false
	},
	{
		id: 'search',
		name: 'search.gftd.ai',
		shortName: 'Search',
		href: 'https://search.gftd.ai',
		icon: '🔎',
		category: 'Services',
		description: 'Unified search and discovery',
		external: false
	},
	{
		id: '6ir',
		name: '6ir.gftd.ai',
		shortName: '6IR',
		href: 'https://6ir.gftd.ai',
		icon: '🧠',
		category: 'Services',
		description: '6IR analytics',
		external: false
	},
	{
		id: 'maps',
		name: 'maps.gftd.ai',
		shortName: 'Maps',
		href: 'https://maps.gftd.ai',
		icon: '🗺️',
		category: 'Services',
		description: 'Spatial maps and geolocation',
		external: false
	},
	{
		id: 'kareyanagi',
		name: 'kareyanagi.gftd.ai',
		shortName: 'Kareyanagi',
		href: 'https://kareyanagi.gftd.ai',
		icon: '🦠',
		category: 'Services',
		description: 'Mold eradication platform with IoT sensors and maps integration',
		external: false
	},
	{
		id: 'drive',
		name: 'drive.gftd.ai',
		shortName: 'Drive',
		href: 'https://drive.gftd.ai',
		icon: '📁',
		category: 'Services',
		description: 'Cloud storage',
		external: false
	},
	{
		id: 'organizer',
		name: 'organizer.gftd.ai',
		shortName: 'Organizer',
		href: 'https://organizer.gftd.ai',
		icon: '🗂️',
		category: 'Services',
		description: 'Upload anything — AI auto-classifies, tags, and organizes',
		external: false
	},
	{
		id: 'sheets',
		name: 'sheets.gftd.ai',
		shortName: 'Sheets',
		href: 'https://sheets.gftd.ai',
		icon: '📊',
		category: 'Services',
		description: 'Spreadsheets',
		external: false
	},
	{
		id: 'docs',
		name: 'docs.gftd.ai',
		shortName: 'Docs',
		href: 'https://docs.gftd.ai',
		icon: '📝',
		category: 'Services',
		description: 'Documentation',
		external: false
	},
	{
		id: 'mailer',
		name: 'mailer.gftd.ai',
		shortName: 'Mailer',
		href: 'https://mailer.gftd.ai',
		icon: '📧',
		category: 'Services',
		description: 'Email client',
		external: false
	},
	{
		id: 'gmail',
		name: 'gmail.gftd.ai',
		shortName: 'Gmail',
		href: 'https://gmail.gftd.ai',
		icon: '✉️',
		category: 'Services',
		description: 'Gmail sync + AI triage + contact DID messenger bridge',
		external: false
	},
	{
		id: 'outlook',
		name: 'outlook.gftd.ai',
		shortName: 'Outlook',
		href: 'https://outlook.gftd.ai',
		icon: '📬',
		category: 'Services',
		description: 'Outlook sync + calendar + contact DID bridge',
		external: false
	},
	{
		id: 'oshikatsu',
		name: 'oshikatsu.gftd.ai',
		shortName: 'Oshikatsu',
		href: 'https://oshikatsu.gftd.ai',
		icon: '🍚',
		category: 'Services',
		description: 'Career support',
		external: false
	},
	{
		id: 'oshinobi',
		name: 'oshinobi.gftd.ai',
		shortName: 'Oshinobi',
		href: 'https://oshinobi.gftd.ai',
		icon: '🥷',
		category: 'Services',
		description: 'Creator subscription platform (tiers, tips, posts)',
		external: false
	},
	{
		id: 'calendar',
		name: 'calendar.gftd.ai',
		shortName: 'Calendar',
		href: 'https://calendar.gftd.ai',
		icon: '📅',
		category: 'Services',
		description: 'Calendar',
		external: false
	},
	{
		id: 'forms',
		name: 'forms.gftd.ai',
		shortName: 'Forms',
		href: 'https://forms.gftd.ai',
		icon: '📋',
		category: 'Services',
		description: 'Forms builder',
		external: false
	},
	{
		id: 'threads',
		name: 'gftd.ai',
		shortName: 'Matrix',
		href: 'https://gftd.ai',
		icon: '💬',
		category: 'Services',
		description: 'Matrix messaging',
		external: false
	},
	{
		id: 'hub',
		name: 'hub.gftd.ai',
		shortName: 'Hub',
		href: 'https://hub.gftd.ai',
		icon: '🏠',
		category: 'Services',
		description: 'Git-compatible project hub',
		external: false
	},
	{
		id: 'translate',
		name: 'translate.gftd.ai',
		shortName: 'Translate',
		href: 'https://translate.gftd.ai',
		icon: '🌍',
		category: 'Services',
		description: 'Translation service',
		external: false
	},
	{
		id: 'images',
		name: 'images.gftd.ai',
		shortName: 'Images',
		href: 'https://images.gftd.ai',
		icon: '🖼️',
		category: 'Services',
		description: 'Image processing',
		external: false
	},
	{
		id: 'videos',
		name: 'douga.gftd.ai',
		shortName: 'Videos',
		href: 'https://douga.gftd.ai',
		icon: '🎬',
		category: 'Services',
		description: 'Video platform',
		external: false
	},
	{
		id: 'videos-legacy',
		name: 'videos.gftd.ai',
		shortName: 'Videos2',
		href: 'https://videos.gftd.ai',
		icon: '🎥',
		category: 'Services',
		description: 'Video platform',
		external: false
	},
	{
		id: 'music',
		name: 'music.gftd.ai',
		shortName: 'Music',
		href: 'https://music.gftd.ai',
		icon: '🎵',
		category: 'Services',
		description: 'Music streaming',
		external: false
	},
	{
		id: 'manga',
		name: 'manga.gftd.ai',
		shortName: 'Manga',
		href: 'https://manga.gftd.ai',
		icon: '📚',
		category: 'Services',
		description: 'Manga reader',
		external: false
	},
	{
		id: 'anime',
		name: 'anime.gftd.ai',
		shortName: 'Anime',
		href: 'https://anime.gftd.ai',
		icon: '🎞️',
		category: 'Services',
		description: 'Anime platform',
		external: false
	},
	{
		id: 'games',
		name: 'games.gftd.ai',
		shortName: 'Games',
		href: 'https://games.gftd.ai',
		icon: '🎮',
		category: 'Services',
		description: 'Games',
		external: false
	},
	{
		id: 'gameya',
		name: 'gameya.gftd.ai',
		shortName: 'Gameya',
		href: 'https://gameya.gftd.ai',
		icon: '🕹️',
		category: 'Services',
		description: 'Playable browser game lab',
		external: false
	},
	{
		id: 'narou',
		name: 'narou.gftd.ai',
		shortName: 'Narou',
		href: 'https://narou.gftd.ai',
		icon: '📖',
		category: 'Services',
		description: 'Novel platform',
		external: false
	},
	{
		id: 'cards',
		name: 'cards.gftd.ai',
		shortName: 'Cards',
		href: 'https://cards.gftd.ai',
		icon: '💳',
		category: 'Services',
		description: 'Stripe Issuing cards',
		external: false
	},
	{
		id: 'tenki',
		name: 'tenki.gftd.ai',
		shortName: 'Tenki',
		href: 'https://tenki.gftd.ai',
		icon: '🌤️',
		category: 'Services',
		description: 'Weather',
		external: false
	},
	{
		id: 'yadoya',
		name: 'yadoya.gftd.ai',
		shortName: 'Yadoya',
		href: 'https://yadoya.gftd.ai',
		icon: '🏨',
		category: 'Services',
		description: 'Lodging and stays',
		external: false
	},
	{
		id: 'fleamarket',
		name: 'fleamarket.gftd.ai',
		shortName: 'FleaMarket',
		href: 'https://fleamarket.gftd.ai',
		icon: '🛍️',
		category: 'Services',
		description: 'Marketplace',
		external: false
	},
	{
		id: 'okaimono',
		name: 'okaimono.gftd.ai',
		shortName: 'Shopping',
		href: 'https://okaimono.gftd.ai',
		icon: '🛒',
		category: 'Services',
		description: 'Shopping',
		external: false
	},
	{
		id: 'yadoya',
		name: 'yadoya.gftd.ai',
		shortName: 'Yadoya',
		href: 'https://yadoya.gftd.ai',
		icon: '🏨',
		category: 'Services',
		description: 'Hotel search and reservation',
		external: false
	},
	{
		id: 'briefing',
		name: 'briefing.gftd.ai',
		shortName: 'Briefing',
		href: 'https://briefing.gftd.ai',
		icon: '📑',
		category: 'Services',
		description: 'Content briefing',
		external: false
	},
	{
		id: 'tsukuru',
		name: 'tsukuru.gftd.ai',
		shortName: 'Tsukuru',
		href: 'https://tsukuru.gftd.ai',
		icon: '🏭',
		category: 'Services',
		description: 'Factory-direct ordering platform',
		external: false
	},
	{
		id: 'cowork',
		name: 'cowork.gftd.ai',
		shortName: 'Cowork',
		href: 'https://cowork.gftd.ai',
		icon: '👥',
		category: 'Services',
		description: 'Co-working',
		external: false
	},
	{
		id: 'shigotoba',
		name: 'shigotoba.gftd.ai',
		shortName: 'Shigotoba',
		href: 'https://shigotoba.gftd.ai',
		icon: '💼',
		category: 'Services',
		description: 'Job board',
		external: false
	},
	{
		id: 'scheduler',
		name: 'scheduler.gftd.ai',
		shortName: 'Scheduler',
		href: 'https://scheduler.gftd.ai',
		icon: '⏰',
		category: 'Services',
		description: 'Scheduler and automation',
		external: false
	},
	{
		id: 'web4',
		name: 'web4.gftd.ai',
		shortName: 'Web4',
		href: 'https://web4.gftd.ai',
		icon: '🔗',
		category: 'Services',
		description: 'Web4 / GCC token',
		external: false
	},
	{
		id: 'society6',
		name: 'society6.gftd.ai',
		shortName: 'Society6',
		href: 'https://society6.gftd.ai',
		icon: '🏛️',
		category: 'Services',
		description: 'COFOG access and Society6 policy portal',
		external: false
	},
	{
		id: 'lawfirm',
		name: 'lawfirm.gftd.ai',
		shortName: 'Law Firm',
		href: 'https://lawfirm.gftd.ai',
		icon: '⚖️',
		category: 'Services',
		description: 'Law firm client portal',
		external: false
	},
	{
		id: 'lawyer',
		name: 'lawyer.gftd.ai',
		shortName: 'Lawyer',
		href: 'https://lawyer.gftd.ai',
		icon: '👨‍⚖️',
		category: 'Services',
		description: 'Lawyer workspace',
		external: false
	},
	{
		id: 'ekyc',
		name: 'ekyc.gftd.ai',
		shortName: 'eKYC',
		href: 'https://ekyc.gftd.ai',
		icon: '🪪',
		category: 'Services',
		description: 'Identity verification',
		external: false
	},
	{
		id: 'shomeisyashin',
		name: 'shomeisyashin.gftd.ai',
		shortName: 'ID Photo',
		href: 'https://shomeisyashin.gftd.ai',
		icon: '📸',
		category: 'Services',
		description: 'AI証明写真メーカー',
		external: false
	},
	{
		id: 'global',
		name: 'global.gftd.ai',
		shortName: 'Global',
		href: 'https://global.gftd.ai',
		icon: '🌏',
		category: 'Services',
		description: 'Global services',
		external: false
	},
	{
		id: 'worlds',
		name: 'worlds.gftd.ai',
		shortName: 'Worlds',
		href: 'https://worlds.gftd.ai',
		icon: '🌌',
		category: 'Services',
		description: 'Virtual worlds',
		external: false
	},
	{
		id: 'pachinko',
		name: 'pachinko.gftd.ai',
		shortName: 'Pachinko',
		href: 'https://pachinko.gftd.ai',
		icon: '🎰',
		category: 'Services',
		description: 'Pachinko simulation',
		external: false
	},
	{
		id: 'casino',
		name: 'casino.gftd.ai',
		shortName: 'Casino',
		href: 'https://casino.gftd.ai',
		icon: '🎲',
		category: 'Services',
		description: 'World casino directory',
		external: false
	},
	{
		id: 'oshiete',
		name: 'oshiete.gftd.ai',
		shortName: 'Oshiete',
		href: 'https://oshiete.gftd.ai',
		icon: '❓',
		category: 'Services',
		description: 'Q&A platform',
		external: false
	},
	{
		id: 'webpage',
		name: 'webpage.gftd.ai',
		shortName: 'Webpage',
		href: 'https://webpage.gftd.ai',
		icon: '🌐',
		category: 'Services',
		description: 'Web page crawl and text extraction',
		external: false
	},
	{
		id: 'marketer',
		name: 'marketer.gftd.ai',
		shortName: 'Marketer',
		href: 'https://marketer.gftd.ai',
		icon: '📣',
		category: 'Services',
		description: 'Marketing tools',
		external: false
	},
	{
		id: 'omikuji',
		name: 'omikuji.gftd.ai',
		shortName: 'Omikuji',
		href: 'https://omikuji.gftd.ai',
		icon: '🎋',
		category: 'Services',
		description: 'Fortune telling',
		external: false
	},
	{
		id: 'aima',
		name: 'aima.gftd.ai',
		shortName: 'AIMA',
		href: 'https://aima.gftd.ai',
		icon: '🤖',
		category: 'Services',
		description: 'AI models',
		external: false
	},
	{
		id: 'robot',
		name: 'robot.gftd.ai',
		shortName: 'Robot',
		href: 'https://robot.gftd.ai',
		icon: '🦾',
		category: 'Services',
		description: 'Robot automation',
		external: false
	},
	{
		id: 'wire',
		name: 'wire.gftd.ai',
		shortName: 'Wire',
		href: 'https://wire.gftd.ai',
		icon: '📡',
		category: 'Services',
		description: 'Messaging',
		external: false
	},
	{
		id: 'lawfirm-admin',
		name: 'lawfirm-admin.gftd.ai',
		shortName: 'LF Admin',
		href: 'https://lawfirm-admin.gftd.ai',
		icon: '🏛️',
		category: 'Services',
		description: 'Law firm admin',
		external: false
	},

	// ── Systems ──
	{
		id: 'performers',
		name: 'gftd.ai',
		shortName: 'Performers',
		href: 'https://gftd.ai',
		icon: '🚀',
		category: 'Systems',
		description: 'Platform dashboard',
		external: false
	},
	{
		id: 'analytics',
		name: 'analytics.gftd.ai',
		shortName: 'Analytics',
		href: 'https://analytics.gftd.ai',
		icon: '📈',
		category: 'Systems',
		description: 'Analytics dashboard',
		external: false
	},
	{
		id: 'ops',
		name: 'ops.gftd.ai',
		shortName: 'Ops',
		href: 'https://ops.gftd.ai',
		icon: '⚙️',
		category: 'Systems',
		description: 'Project operations',
		external: false
	},
	{
		id: 'sre',
		name: 'sre.gftd.ai',
		shortName: 'SRE',
		href: 'https://sre.gftd.ai',
		icon: '🔧',
		category: 'Systems',
		description: 'Site reliability',
		external: false
	},
	{
		id: 'os',
		name: 'os.gftd.ai',
		shortName: 'OS',
		href: 'https://os.gftd.ai',
		icon: '🖥️',
		category: 'Systems',
		description: 'Operating system UI',
		external: false
	},
	{
		id: 'po',
		name: 'po.gftd.ai',
		shortName: 'PO',
		href: 'https://po.gftd.ai',
		icon: '📐',
		category: 'Systems',
		description: 'Projection operator',
		external: false
	},
	{
		id: 'gov',
		name: 'gov.gftd.ai',
		shortName: 'Gov',
		href: 'https://gov.gftd.ai',
		icon: '🏢',
		category: 'Systems',
		description: 'Governance',
		external: false
	},
	{
		id: 'resources',
		name: 'resources.gftd.ai',
		shortName: 'Resources',
		href: 'https://resources.gftd.ai',
		icon: '🗄️',
		category: 'Systems',
		description: 'JSON-LD/RDF resources',
		external: false
	},
	{
		id: 'completer',
		name: 'completer.gftd.ai',
		shortName: 'Completer',
		href: 'https://completer.gftd.ai',
		icon: '✏️',
		category: 'Systems',
		description: 'Code completion',
		external: false
	},
	{
		id: 'har',
		name: 'har.gftd.ai',
		shortName: 'HAR',
		href: 'https://har.gftd.ai',
		icon: '🗂️',
		category: 'Systems',
		description: 'HAR viewer',
		external: false
	},
	{
		id: 'provider-pod',
		name: 'provider-pod.gftd.ai',
		shortName: 'Provider',
		href: 'https://provider-pod.gftd.ai',
		icon: '📦',
		category: 'Systems',
		description: 'Provider pod marketplace',
		external: false
	},
	{
		id: 'ge',
		name: 'ge.gftd.ai',
		shortName: 'GE',
		href: 'https://ge.gftd.ai',
		icon: '🎓',
		category: 'Systems',
		description: 'General education',
		external: false
	},
	{
		id: 'lo',
		name: 'lo.gftd.ai',
		shortName: 'LO',
		href: 'https://lo.gftd.ai',
		icon: '🧩',
		category: 'Systems',
		description: 'Learning objects',
		external: false
	},
	{
		id: 'tia',
		name: 'tia.gftd.ai',
		shortName: 'TIA',
		href: 'https://tia.gftd.ai',
		icon: '🎙️',
		category: 'Systems',
		description: 'TIA assistant',
		external: false
	},
	{
		id: 'wvme',
		name: 'wvme.gftd.ai',
		shortName: 'WVME',
		href: 'https://wvme.gftd.ai',
		icon: '🎛️',
		category: 'Systems',
		description: 'WVME platform',
		external: false
	},
	{
		id: 'tasklist',
		name: 'tasklist.gftd.ai',
		shortName: 'TaskList',
		href: 'https://tasklist.gftd.ai',
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
	const normalized = appId.trim().toLowerCase().replace(/\.gftd\.ai$/, '').replace(/_/g, '-');
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
	return `https://${normalizeAppId(appId)}.gftd.ai`;
}
