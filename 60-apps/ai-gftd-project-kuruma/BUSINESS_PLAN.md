# kuruma.etzhayyim.com Business Plan (Global from Japan)

## 1. Objective

- Target: ad revenue 10,000,000 JPY / month
- Positioning: publish high-trust Japanese car information globally (specs, comparisons, reviews, ownership insights)
- Core strategy: Japan-origin data + multilingual distribution + high-intent SEO pages

## 2. Revenue Formula (Ad-only Target)

Use a simple operating formula:

`Monthly Revenue = PV × (viewable ad impressions per PV) × (net eCPM / 1000)`

Planning assumptions:

- Viewable ad impressions per PV: 2.4
- Net eCPM (blended after demand mix): 1,200 JPY

Then:

- Required PV = `10,000,000 / (2.4 × 1,200 / 1000)` = about 3.47M PV/month
- Practical target range: 3.3M-3.6M PV/month

This is consistent with the existing internal target in `CLAUDE.md` (~3.3M PV/month).

## 3. GTM Premise: "Japan Information to Global"

### Content moat

- Japanese maker/model depth (kei cars, JDM trims, reliability, maintenance culture)
- Structured specs + comparison tables + year/trim deltas
- Country-specific explainers:
  - import eligibility
  - fuel economy interpretation
  - left/right-hand-drive caveats
  - ownership cost context

### Language rollout

- Tier 1: `ja`, `en`
- Tier 2: `es`, `pt`, `de`, `fr`
- Tier 3: `zh`, `ko`, `th`, `vi`, `ar`

Principle:

- Publish in Japanese first (source of truth)
- Translate + localize, not literal translation
- Add market notes per locale (units, regulation caveats, buyer intent terms)

## 4. Traffic Strategy

### SEO portfolio split

- 40%: model/spec pages (`make + model + year + specs`)
- 25%: comparison pages (`A vs B`, segment comparisons)
- 20%: ownership/use-case pages (family, city, snow, long-drive, fuel-cost)
- 15%: reviews and editorial explainers

### Distribution mix target

- 70%: organic search
- 10%: Google Discover / news-like evergreen refresh
- 10%: social/video referral
- 10%: partner/backlink/referral

## 5. Monetization Design

### Ad inventory

- Header banner
- In-article slot every ~3 paragraphs
- Comparison-table side slot (desktop)
- Sticky footer/mobile anchor

### Yield optimization

- Header bidding + AdSense fallback
- Floor price by geo and device
- Separate ad density policy by template (spec vs compare vs review)
- RPM dashboard by locale/page-type

### Non-ad supplement (not required for 10M plan, but reduces risk)

- Dealer/parts affiliate links
- Insurance/loan lead-gen placements (selected locales)

## 6. 4-Phase Execution Plan

### Phase 1 (Month 0-3): Foundation

- Build 500 high-quality Japanese canonical pages
- Launch multilingual URL framework and hreflang/sitemap operations
- Implement analytics baseline (PV, RPM, viewability, CWV, indexation)

KPI gate:

- 80k PV/month
- 300+ indexed quality pages
- 80%+ pages passing CWV mobile

### Phase 2 (Month 4-8): SEO Scale in JA+EN

- Expand to 2,000 pages (spec + compare heavy)
- Weekly refresh workflow for high-demand pages
- Start EN localization with market-intent keyword sets

KPI gate:

- 400k PV/month
- JA+EN blended net eCPM >= 900 JPY
- 25+ top-3 ranking keywords in core clusters

### Phase 3 (Month 9-14): Global Expansion

- Add ES/PT/DE/FR at scale for top 20% pages
- Country landing pages (import/use-case/legal caveat summaries)
- Link acquisition via auto media/community references

KPI gate:

- 1.5M PV/month
- Non-JA traffic share >= 45%
- Blended net eCPM >= 1,050 JPY

### Phase 4 (Month 15-20): Revenue Optimization to 10M

- Reach 3.3M-3.6M PV/month
- Focus on high-RPM templates (comparison, review, buyer intent)
- Aggressive ad-yield tuning + UX guardrails

KPI gate:

- 10,000,000 JPY/month ad revenue
- Blended viewability >= 65%
- Bounce/engagement stable (no short-term ad overloading)

## 7. 90-Day Action Plan (Immediate)

1. Define 1,000-page keyword map (JA source + EN intent mapping).
2. Ship technical SEO baseline: hreflang, sitemap index, canonical rules, structured data.
3. Build 100 "money pages" first: comparison + review + spec detail.
4. Introduce page templates with strict CWV budgets.
5. Start ad stack test (2 SSP + AdSense fallback), dashboard by locale/page-type.

## 8. Operating Metrics (Weekly Review)

- Acquisition: impressions, clicks, CTR, ranking by cluster
- Content: publish count, refresh count, indexation latency
- Monetization: PV, sessions, viewability, fill, net eCPM, RPM
- Quality: CWV pass rate, template-level engagement, ad-complaint rate

## 9. Risk and Countermeasures

- Risk: low-quality mass translation hurts SEO trust
  - Countermeasure: Japanese canonical + expert review + locale QA checklist
- Risk: ad load increases short-term RPM but drops long-term traffic
  - Countermeasure: template-level ad density caps and engagement guardrails
- Risk: broad content scope dilutes authority
  - Countermeasure: "Japan-origin automotive authority" only (no unrelated verticals)

## External references used for this plan

- Dentsu: 2024 Japan advertising spend (official): https://www.dentsu.co.jp/news/release/2025/0227-010853.html
- Dentsu: 2024 internet ad media detailed analysis: https://www.dentsu.co.jp/news/release/2025/0312-010858.html
- JAMA: overseas production statistics (2024): https://www.jama.or.jp/release/latest_update/2024/2903/
- Google Search Central: managing multi-regional/multilingual sites: https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites
- Google Search Central: creating helpful, reliable, people-first content: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google Search Central: Core Web Vitals and Search: https://developers.google.com/search/docs/appearance/core-web-vitals
