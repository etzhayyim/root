# Non-Japan World Social-Contract Ingestion Note

Date tested: 2026-04-25 JST. Scope: bootstrap only; no live DB writes.

## Target tables

`vertex_contracts_social_contract` is the hub for constitution/treaty social contracts:

- `vertex_id`, `name`, `constitutional_type`, `jurisdiction`, `adopted_date`, `effective_date`, `scope`, `url`, `un_reg_no`, `source`, `source_record_id`, `confidence`, `last_verified`

`vertex_houbun_treaty` is the houbun treaty metadata/full-text pointer:

- `vertex_id`, `title`, `title_native`, `parties_json`, `signed_date`, `entered_into_force_date`, `un_reg_no`, `depositary`, `source`, `source_record_id`, `source_url`, `language`

The previous repo seed baseline was 10 high-value treaty authority seeds in `70-tools/etzhayyim/etzhayyim/seed_domains.go` (`un_charter`, `udhr`, `geneva_1949`, `iccpr`, `icescr`, `vienna_treaties`, `unclos`, `paris_climate`, `rome_statute`, `wto_marrakesh`); that file was removed 2026-05-20 with the etzhayyim CLI. Treat this list as authority seed, not corpus coverage.

## Tested public sources

### Constitute Project

Docs: `https://www.constituteproject.org/content/data` links to API docs at `https://docs.google.com/document/d/1wATS_IAcOpNZKzMrvO8SMmjCgOZfgH97gmPedVxpMfw/pub`.

Tested endpoint:

```text
GET https://www.constituteproject.org/service/constitutions?lang=en&historic=false
```

Observed response: JSON array, 232 records, 232 public, 193 `in_force=true`. Japan appears as `Japan_1889` and `Japan_1946`; exclude `country_id == "Japan"` for this task.

Header shape:

```json
{
  "country": "Republic of Albania",
  "country_id": "Albania",
  "id": "Albania_2016",
  "in_force": true,
  "is_draft": false,
  "is_historic": false,
  "public": true,
  "region": "Europe",
  "title": "Albania 1998 (rev. 2016)",
  "title_long": "Albania's Constitution of 1998 with Amendments through 2016",
  "year_enacted": "1998",
  "year_revised": "2016",
  "year_updated": "2016"
}
```

Tested full-text endpoint:

```text
GET https://www.constituteproject.org/service/html?cons_id=Australia_1985&lang=en
```

Observed response:

```json
{
  "html": "<h1 class=\"clearfix\"> ... <div class=\"constitution-content\" ...>",
  "title": "Australia 1901 (rev. 1985)"
}
```

`html` length for Australia sample was 173,763 bytes. Use the header endpoint for the first `vertex_contracts_social_contract` pass, and only fetch `html` when article/section extraction is actually implemented. Constitute `locations` also works:

```text
GET https://www.constituteproject.org/service/locations?lang=en
```

Observed: 6 regions, 198 countries. Country `isocode` is numeric ISO-3166, so either convert locally or enrich with Wikidata/ISO table before writing `jurisdiction`.

Mapping to `vertex_contracts_social_contract`:

- `vertex_id`: deterministic `contracts:constitution:constitute:{cons_id}` or repo-local hash convention.
- `name`: `title_long || title`.
- `constitutional_type`: `constitution`.
- `jurisdiction`: ISO-3166 alpha-3 if enriched; otherwise `country_id` only in staging.
- `adopted_date`: `year_enacted` when exact date unavailable.
- `effective_date`: `year_reinstated || year_enacted`.
- `scope`: `national`.
- `url`: `https://www.constituteproject.org/service/html?cons_id={id}&lang=en`.
- `source`: `constitute`.
- `source_record_id`: `id`.
- `confidence`: `0.90` for metadata, lower if jurisdiction is not ISO-normalized.

License caution: Constitute states some English translations are used with permission from HeinOnline/Oxford/IDEA. Store metadata and source URL first; do not bulk persist full translated text until attribution/licensing is reviewed.

### Wikidata

Tested UN Treaty Collection object ID crosswalk:

```sparql
SELECT ?item ?itemLabel ?untc WHERE {
  ?item wdt:P9966 ?untc.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 5
```

Endpoint:

```text
GET https://query.wikidata.org/sparql?format=json&query=...
```

Observed shape:

```json
{
  "head": { "vars": ["item", "itemLabel", "untc"] },
  "results": {
    "bindings": [
      {
        "item": { "type": "uri", "value": "http://www.wikidata.org/entity/Q2115269" },
        "untc": { "type": "literal", "value": "0800000280061ca5" },
        "itemLabel": { "xml:lang": "en", "type": "literal", "value": "Protocol III" }
      }
    ]
  }
}
```

Use this as the broad treaty queue generator: `P9966` gives the UNTC `objid`, and the item QID gives a stable dedupe key. Keep `source_record_id` as `P9966` for UN-sourced treaty rows and store QID in staging/provenance.

Constitution discovery via `P31/P279* = wd:Q7755` is useful for enrichment but too noisy as a primary source; country (`P17`) is often missing. Prefer Constitute for constitution list and Wikidata for ISO alpha-3 (`P298`), aliases, dates, and fallback records.

### UN Treaty Collection

Tested detail page:

```text
HEAD/GET https://treaties.un.org/Pages/showDetails.aspx?objid=0800000280061ca5
```

Observed: HTTP 200, `content-type: text/html; charset=utf-8`, ASP.NET session cookies. The HTML contains structured labels in text and links to official PDFs.

Sample extracted text prefix:

```text
Registration Number 43425
Title Protocol additional to the Geneva Conventions of 12 August 1949, and relating to the adoption of an additional distinctive emblem (Protocol III)
Participant(s) Submitter Switzerland
Places/dates of conclusion Place Date Geneva 08/12/2005
EIF information 14 January 2007, in accordance with article 11
Authentic texts Spanish Russian French English Chinese Arabic
Depositary Government of Switzerland
Registration Date Switzerland 15 January 2007
Subject terms Geneva Conventions (with Protocols)
Agreement type Multilateral
UNTS Volume Number 2404 (p.261)
Text document(s) volume-2404-I-43425.pdf
```

HTML links observed:

- `/doc/Publication/UNTS/Volume%202404/Part/volume-2404-I-43425.pdf`
- `/doc/Publication/UNTS/Volume%202404/v2404.pdf`
- `/Pages/showActionDetails.aspx?objid=...&clang=_en`

Mapping to `vertex_houbun_treaty`:

- `vertex_id`: deterministic `houbun:treaty:untc:{objid}`.
- `title`: parsed `Title`.
- `parties_json`: participants/actions parsed from the detail page, initially `[]` if not robust.
- `signed_date`: parsed `Places/dates of conclusion Date`.
- `entered_into_force_date`: parsed `EIF information`.
- `un_reg_no`: parsed `Registration Number`.
- `depositary`: parsed `Depositary`.
- `source`: `un-treaty-collection`.
- `source_record_id`: UNTC `objid`.
- `source_url`: `https://treaties.un.org/Pages/showDetails.aspx?objid={objid}`.
- `language`: `multilingual` or authentic text list.

Mapping to `vertex_contracts_social_contract`:

- `name`: same parsed title.
- `constitutional_type`: `treaty`.
- `jurisdiction`: `international`.
- `adopted_date`: signed/conclusion date.
- `effective_date`: EIF date.
- `scope`: `multilateral` or parsed agreement type.
- `url`: UNTC detail URL.
- `un_reg_no`: registration number.
- `source`: `un-treaty-collection`.
- `source_record_id`: UNTC `objid`.
- `confidence`: `0.85` for HTML parsed fields, `0.95` for direct Wikidata `P9966` crosswalk existence.

UNTC has no simple public JSON API in the tested path. Treat the ASP.NET HTML as source-of-record and parse conservatively; persist raw fetch snapshots outside DB first for reproducibility.

## Bounded parallel ingestion plan

1. Constitution metadata pass, non-Japan only.
   Fetch `constitutions?lang=en&historic=false`, filter `public == true`, `country_id != "Japan"`, and preferably `in_force == true` for phase 1. Expected phase-1 size is about 192 rows after Japan exclusion. Stage rows as JSONL before any DB writer.

2. Constitution enrichment pass.
   Fetch `locations?lang=en`, join by `country_id`, convert numeric ISO to alpha-3, and optionally enrich alpha-3 from Wikidata `P298`. Keep uncertain jurisdictions in staging, not production inserts.

3. Treaty queue pass.
   Page Wikidata `P9966` records in bounded chunks (`LIMIT 500 OFFSET n` or QID-range slicing to avoid endpoint strain). For each binding, derive UNTC detail URL and dedupe by `objid`.

4. Treaty detail pass.
   Fetch UNTC detail pages with low concurrency per agent (`2-4`), parse only stable labels: Registration Number, Title, conclusion date, EIF information, authentic texts, depositary, agreement type, UNTS volume, text-document PDF links. Store parsed JSONL plus source URL and fetched timestamp.

5. Dry-run validation.
   Validate required fields before writing: constitution rows require `source_record_id`, `name`, `source`, `jurisdiction`; treaty rows require `source_record_id`, `title/name`, `source_url`. Generate deterministic `vertex_id` and report duplicates.

6. DB writer, separate later step.
   Only after staging review, insert/upsert into `vertex_contracts_social_contract` and `vertex_houbun_treaty`. This request explicitly says not to modify live DB, so writer should be disabled by default and require an explicit `--write` flag plus non-live DSN confirmation.

## Agent sharding

- `constitute-header-agent`: one-shot metadata fetch and Japan exclusion.
- `constitute-html-agent`: optional full-text fetch, disabled until license review.
- `wikidata-untc-agent-{n}`: SPARQL queue shards by `OFFSET` or QID numeric range.
- `untc-detail-agent-{n}`: HTML/PDF-link fetch and parser, rate-limited and retrying 429/5xx.
- `validator-agent`: schema normalization, deterministic IDs, duplicate report, no DB access.

Recommended first bootstrap cap: constitutions `<= 200`, treaties `<= 1,000` UNTC detail pages. That is enough to prove parsing, dedupe, and table mapping without turning this into an unbounded crawl.
