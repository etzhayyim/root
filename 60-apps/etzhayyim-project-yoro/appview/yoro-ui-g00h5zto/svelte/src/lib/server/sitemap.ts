import { YORO_SITE_ORIGIN } from './bff';

type SitemapUrl = {
	loc: string;
	lastmod?: string;
	changefreq?: string;
	priority?: string;
};

function xmlEscape(s: string): string {
	return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function sitemapResponse(xml: string, maxAge = 3600): Response {
	return new Response(xml, {
		headers: {
			'content-type': 'application/xml; charset=utf-8',
			'cache-control': `public, max-age=${maxAge}, s-maxage=${maxAge}`
		}
	});
}

export function renderSitemapIndexXml(urls: Array<{ loc: string; lastmod?: string }>): string {
	const entries = urls.map(({ loc, lastmod }) =>
		`  <sitemap>\n    <loc>${xmlEscape(loc)}</loc>${lastmod ? `\n    <lastmod>${lastmod}</lastmod>` : ''}\n  </sitemap>`);
	return `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries.join('\n')}\n</sitemapindex>`;
}

export function renderUrlSetXml(urls: SitemapUrl[]): string {
	const entries = urls.map(({ loc, lastmod, changefreq, priority }) =>
		`  <url>\n    <loc>${xmlEscape(loc)}</loc>${lastmod ? `\n    <lastmod>${lastmod}</lastmod>` : ''}${changefreq ? `\n    <changefreq>${changefreq}</changefreq>` : ''}${priority ? `\n    <priority>${priority}</priority>` : ''}\n  </url>`);
	return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries.join('\n')}\n</urlset>`;
}

export function sitemapIndexXml(): string {
	const today = new Date().toISOString().slice(0, 10);
	return renderSitemapIndexXml([
		{ loc: `${YORO_SITE_ORIGIN}/sitemaps/static.xml`, lastmod: today },
		{ loc: `${YORO_SITE_ORIGIN}/sitemaps/actors/index.xml`, lastmod: today }
	]);
}

export function staticSitemapXml(): string {
	return renderUrlSetXml([
		{ loc: `${YORO_SITE_ORIGIN}/`, priority: '1.0', changefreq: 'hourly' },
		{ loc: `${YORO_SITE_ORIGIN}/search`, priority: '0.8', changefreq: 'daily' },
		{ loc: `${YORO_SITE_ORIGIN}/projects`, priority: '0.7', changefreq: 'daily' },
		{ loc: `${YORO_SITE_ORIGIN}/feeds`, priority: '0.7', changefreq: 'daily' },
		{ loc: `${YORO_SITE_ORIGIN}/hashtag/ai`, priority: '0.6', changefreq: 'hourly' },
		{ loc: `${YORO_SITE_ORIGIN}/hashtag/etzhayyim`, priority: '0.6', changefreq: 'hourly' },
		{ loc: `${YORO_SITE_ORIGIN}/hashtag/agent`, priority: '0.6', changefreq: 'hourly' }
	]);
}

const ACTOR_HASH_PREFIXES = Array.from({ length: 256 }, (_, i) => i.toString(16).padStart(2, '0'));

export function actorSitemapIndexXml(prefix?: string): string {
	if (!prefix) {
		return renderSitemapIndexXml(ACTOR_HASH_PREFIXES.map((p) => ({
			loc: `${YORO_SITE_ORIGIN}/sitemaps/actors/hash/${p}.xml`
		})));
	}
	return renderSitemapIndexXml(ACTOR_HASH_PREFIXES.map((suffix) => ({
		loc: `${YORO_SITE_ORIGIN}/sitemaps/actors/hash/${prefix}${suffix}.xml`
	})));
}
