# kuruma Technical SEO Checklist (Global from Japan)

## URL and Canonical

- [ ] Locale URL rule fixed: `/{locale}/...` (`ja` included explicitly)
- [ ] Canonical points to same-locale URL (not cross-locale)
- [ ] No duplicate indexable URLs with query params
- [ ] Pagination/crawl filters set to noindex where needed

## Hreflang and Sitemaps

- [ ] Every localized page has reciprocal `hreflang`
- [ ] `x-default` defined for language selector or default page
- [ ] Sitemap index split by locale + page type
- [ ] New/updated pages submitted daily

## Rendering and Crawlability

- [ ] Critical content rendered server-side/prerender-safe
- [ ] robots.txt allows crawl for target paths
- [ ] Structured navigation links available without JS interactions
- [ ] Orphan page count tracked weekly

## Structured Data

- [ ] Vehicle spec pages include valid structured data
- [ ] Review pages include rating/review schema where eligible
- [ ] Breadcrumb schema on all deep pages
- [ ] Organization/WebSite schema at root pages

## CWV and UX

- [ ] LCP image optimized per template
- [ ] CLS-safe ad slot placeholders used
- [ ] INP budget validated on money pages
- [ ] Mobile template passes CWV on top traffic pages

## Ads and Quality Guardrails

- [ ] Ad density cap by template documented
- [ ] Above-the-fold content visible before first ad
- [ ] No intrusive interstitial on organic landing
- [ ] Viewability and complaint rate reviewed weekly

## Analytics and Monitoring

- [ ] Search Console properties per host + locale coverage
- [ ] Dashboard: indexed pages / clicks / CTR / avg position
- [ ] Dashboard: viewability / fill / net eCPM / RPM by template
- [ ] Weekly anomaly alerting thresholds defined
