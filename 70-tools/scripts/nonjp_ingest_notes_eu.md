# EU EUR-Lex non-Japan houbun ingestion note

Date: 2026-04-25
Scope: research only. No live DB writes.

## Summary

EUR-Lex can support a no-key EU houbun collector in two phases:

1. Metadata discovery via the Publications Office SPARQL endpoint.
2. Article text extraction from public EUR-Lex XHTML pages by CELEX or ELI URL.

SPARQL is good for canonical work metadata, Cellar URI, CELEX, type, dates, language-specific titles, and links. It did not expose article body text in the tested work-level queries. Article text is available without API keys from EUR-Lex XHTML, with predictable `eli-subdivision` article blocks.

## Endpoints tested

### SPARQL endpoint

Base:

```text
https://publications.europa.eu/webapi/rdf/sparql
```

Headers used:

```text
Accept: application/sparql-results+json
User-Agent: etzhayyim-eurlex-research/0.1
```

Observed response shape:

```json
{
  "head": { "link": [], "vars": ["work", "celex", "date", "type"] },
  "results": {
    "distinct": false,
    "ordered": true,
    "bindings": [
      {
        "work": { "type": "uri", "value": "http://publications.europa.eu/resource/cellar/..." },
        "celex": { "type": "literal", "datatype": "http://www.w3.org/2001/XMLSchema#string", "value": "32024R0770" },
        "type": { "type": "uri", "value": "http://publications.europa.eu/resource/authority/resource-type/REG_IMPL" }
      }
    ]
  }
}
```

Important literal note: `cdm:resource_legal_id_celex` values are `xsd:string`, so exact `"32016R0679"` triple matching returned no rows in some queries. Use `FILTER(STR(?celex) = "...")` or bind typed literals.

### EUR-Lex public text endpoints

Tested and returned HTTP 200 without keys:

```text
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679
https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679
https://eur-lex.europa.eu/legal-content/EN/TXT/XML/?uri=CELEX:32016R0679
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L1937
https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng/xhtml
https://eur-lex.europa.eu/eli/dir/2019/1937/oj/eng/xhtml
```

Observed content types:

```text
TXT/?uri=CELEX:...             -> text/html; charset=UTF-8, regular EUR-Lex page
TXT/HTML/?uri=CELEX:...        -> text/html; charset=UTF-8, XHTML legal text
TXT/XML/?uri=CELEX:...         -> text/xml; charset=UTF-8, NOTICE metadata branch
/eli/.../oj/eng/xhtml          -> text/html; charset=UTF-8, XHTML legal text
```

## SPARQL queries tested

### Bad first attempt

This returned 0 rows because `work_id_document` includes values like `celex:32016R0679`, not bare CELEX:

```sparql
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?work ?p ?o WHERE {
  ?work cdm:work_id_document "32016R0679" .
  ?work ?p ?o .
} LIMIT 80
```

### Work metadata by CELEX

Tested with GDPR `32016R0679`; returned the Cellar work and metadata predicates.

```sparql
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?work ?p ?o WHERE {
  ?work cdm:resource_legal_id_celex ?celex .
  FILTER(STR(?celex) = "32016R0679")
  ?work ?p ?o .
  FILTER(
    CONTAINS(LCASE(STR(?p)), "title") ||
    CONTAINS(LCASE(STR(?p)), "date") ||
    CONTAINS(LCASE(STR(?p)), "type") ||
    CONTAINS(LCASE(STR(?p)), "id")
  )
} LIMIT 120
```

Useful predicates observed:

```text
rdf:type -> cdm:legislation_secondary
rdf:type -> cdm:resource_legal
rdf:type -> cdm:work
owl:sameAs -> http://publications.europa.eu/resource/celex/32016R0679
owl:sameAs -> http://publications.europa.eu/resource/eli/reg/2016/679/oj
cdm:resource_legal_id_celex -> 32016R0679
cdm:resource_legal_type -> R
cdm:work_date_document -> 2016-04-27
cdm:resource_legal_date_entry-into-force -> 2016-05-24
cdm:resource_legal_date_entry-into-force -> 2018-05-25
cdm:resource_legal_date_end-of-validity -> 9999-12-31
cdm:resource_legal_date_signature -> 2016-04-27
cdm:work_has_resource-type -> http://publications.europa.eu/resource/authority/resource-type/REG
cdm:cmr#lastModificationDate -> 2024-12-31T20:10:26.804+01:00
```

### Latest regulation page

This returned 10 rows for `32024R...`.

```sparql
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?work ?celex ?date ?type WHERE {
  ?work cdm:resource_legal_id_celex ?celex .
  FILTER(STRSTARTS(STR(?celex), "32024R"))
  OPTIONAL { ?work cdm:resource_legal_date_document ?date }
  OPTIONAL { ?work cdm:work_has_resource-type ?type }
} ORDER BY DESC(?date) LIMIT 10
```

Response examples:

```text
32024R0770 -> resource-type/REG_IMPL
32024R0735 -> resource-type/REG_IMPL
32024R0763 -> resource-type/REG_IMPL
32024R0795R(01) -> resource-type/CORRIGENDUM and resource-type/REG
32024R0595 -> resource-type/REG_DEL
```

Note: `cdm:resource_legal_date_document` did not populate for this query; `cdm:work_date_document` did populate in the single-work GDPR query. Use `work_date_document` for enacted/document date.

### Language-specific titles

Tested with GDPR and returned 24 language expressions.

```sparql
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?expr ?title ?lang WHERE {
  ?work cdm:resource_legal_id_celex ?celex .
  FILTER(STR(?celex) = "32016R0679")
  ?expr cdm:expression_belongs_to_work ?work .
  OPTIONAL { ?expr cdm:expression_title ?title }
  OPTIONAL { ?expr cdm:expression_uses_language ?lang }
} LIMIT 40
```

English row shape:

```json
{
  "expr": { "type": "uri", "value": "http://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0006" },
  "title": { "type": "literal", "value": "Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 ..." },
  "lang": { "type": "uri", "value": "http://publications.europa.eu/resource/authority/language/ENG" }
}
```

## Text extraction shape

### XHTML article blocks

`https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679` returned a large XHTML document. Article blocks are regular enough for deterministic extraction:

```html
<div class="eli-subdivision" id="art_1">
  <p class="oj-ti-art">Article 1</p>
  <div class="eli-title" id="art_1.tit_1">
    <p class="oj-sti-art">Subject-matter and objectives</p>
  </div>
  <div id="001.001">
    <p class="oj-normal">1. This Regulation lays down rules ...</p>
  </div>
  ...
</div>
```

Regex smoke results from tested XHTML:

```text
32016R0679 GDPR regulation: 807,065 bytes, 99 article ids, art_1..art_99
32019L1937 whistleblower directive: 456,572 bytes, 29 article ids, art_1..art_29
32024R1689 AI Act regulation: 1,259,199 bytes, 113 article ids, art_1..art_113
```

Recommended parser:

- Parse as XML/XHTML if possible.
- Find `div.eli-subdivision[id^="art_"]`.
- `article_no`: first descendant `p.oj-ti-art`.
- `title`: first descendant under `div.eli-title`, commonly `p.oj-sti-art`.
- `text`: descendant text after removing title/header nodes, preserving paragraph/list ordering.
- `section`: nearest preceding chapter/title block if needed; can be added later.

### TXT/XML NOTICE

`https://eur-lex.europa.eu/legal-content/EN/TXT/XML/?uri=CELEX:32016R0679` returned a `<NOTICE decoding="eng" type="branch">` document with metadata, not article body as a simple statute XML.

Observed top-level children:

```text
WORK
EXPRESSION
MANIFESTATION
MANIFESTATION
MANIFESTATION
...
```

The first `WORK` includes:

```text
URI -> http://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1
SAMEAS -> eli/reg/2016/679/oj
SAMEAS -> celex/32016R0679
RESOURCE_LEGAL_ID_CELEX -> 32016R0679
WORK_DATE_DOCUMENT -> 2016-04-27
RESOURCE_LEGAL_TYPE -> R
RESOURCE_LEGAL_DATE_ENTRY-INTO-FORCE -> 2016-05-24 and 2018-05-25
RESOURCE_LEGAL_DATE_END-OF-VALIDITY -> 9999-12-31
RESOURCE_LEGAL_ELI -> http://data.europa.eu/eli/reg/2016/679/oj
```

Use NOTICE XML as fallback metadata verification, not primary article text.

## Mapping to houbun tables

Source path DID:

```text
did:web:houbun.etzhayyim.com:eu:eur-lex
```

`vertex_houbun_statute`:

```text
jurisdiction: eu
statute_id: CELEX, e.g. 32016R0679
title: ENG expression title if available
title_native: same as title for ENG, or multilingual JSON requires schema change
statute_type: resource-type terminal token or CELEX type, e.g. REG, DIR, REG_IMPL
enacted_date: cdm:work_date_document
effective_date: cdm:resource_legal_date_entry-into-force, choose latest for multi-row or keep first until schema supports arrays
repealed_date: cdm:resource_legal_date_end-of-validity if not 9999-12-31
source: eur-lex
source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}
license: EUR-Lex reuse notice / attribution required
language: en
article_count: parsed XHTML article block count
```

`vertex_houbun_article`:

```text
statute_ref: statute vertex_id
article_no: "Article 1", etc.
section: optional chapter/section label
title: article title, e.g. "Subject-matter and objectives"
text: normalized article body
language: en
source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex}#art_1
article_did/blake3_hash: follow existing houbun content-address convention
amended_at: SPARQL cdm:cmr#lastModificationDate or document date until proper consolidated-version lineage is implemented
```

## Bounded ingestion plan

No live writes during research. Proposed bounded worker sequence:

1. Build `eurlex_sparql_page(kind, year, offset, limit)` for `R` and `L` CELEX families:
   - Regulations: `FILTER(REGEX(STR(?celex), "^3[0-9]{4}R"))`
   - Directives: `FILTER(REGEX(STR(?celex), "^3[0-9]{4}L"))`
   - Start with years 2024, 2023, 2022 and `LIMIT 100 OFFSET n`.
2. For each CELEX, fetch metadata via SPARQL and select the ENG title expression.
3. Fetch XHTML from:
   - `https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{celex}`
   - fallback `https://eur-lex.europa.eu/eli/{reg|dir}/{year}/{number}/oj/eng/xhtml` when ELI is available.
4. Parse articles deterministically from `div.eli-subdivision[id^="art_"]`.
5. Dry-run output to JSONL first:
   - `statute` record
   - `article[]` records
   - parser stats: bytes, article_count, missing_title_count, text_chars
6. Operator review for 20 high-value acts:
   - `32016R0679` GDPR
   - `32019L1937` Whistleblower Directive
   - `32024R1689` AI Act
   - plus 17 recent `REG`, `DIR`, and selected `REG_IMPL`
7. Only after review, add an ingest script with `--dry-run` default and explicit `--write-live` opt-in. Keep concurrency at 2-4 requests per host with backoff; cache raw XHTML/XML under a temp/cache directory for repeatability.

## Risks and decisions

- Consolidated versus original OJ text: tested URLs fetch OJ text. Consolidated versions need separate CELEX/version handling; do not mix lineage in phase 1.
- Multiple effective dates: existing table has one `effective_date`. Preserve one date and keep full source metadata in a future raw evidence table or JSON column if schema evolves.
- Article extraction by XHTML class/id is reliable for tested regulation/directive samples but needs drift tests over older acts and corrigenda.
- Some CELEX rows are corrigenda or implementing/delegated acts. Filter by `work_has_resource-type` if the first pass should only include core `REG` and `DIR`.
- EUR-Lex reuse requires attribution. Store `source_url` and `source = eur-lex`; include attribution in app display/export.
