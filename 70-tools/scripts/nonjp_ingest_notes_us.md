# Non-Japan houbun ingestion note: USA GovInfo

Date: 2026-04-25
Scope: source research only. No live DB writes.

## Existing repo fit

- `orgs/etzhayyim/com-etzhayyim-app-houbun/CLAUDE.md` already reserves:
  - `did:web:houbun.etzhayyim.com:usa:cfr`
  - `did:web:houbun.etzhayyim.com:usa:usc`
- `00-contracts/lexicons/com/etzhayyim/apps/houbun/ingestStatuteUsa.json` describes GovInfo CFR/USCODE ingestion, but its current wording assumes `USCODE` is available through GovInfo bulkdata JSON. Tested endpoints show that is not true for keyless bulkdata JSON.
- Target graph tables are `vertex_houbun_statute`, `vertex_houbun_article`, `edge_houbun_statute_article`. This note does not modify them.

## Keyless URLs tested

### GovInfo bulkdata discovery

`GET https://www.govinfo.gov/bulkdata/json`

Headers used:

```text
Accept: application/json
```

Status/content type:

```text
200 application/json
```

Shape:

```json
{
  "files": [
    {
      "displayLabel": "Code of Federal Regulations (Annual Edition)",
      "folder": true,
      "formattedLastModifiedTime": "24-Apr-2026 19:36",
      "justFileName": "CFR",
      "link": "https://www.govinfo.gov/bulkdata/json/CFR",
      "name": "CFR"
    },
    {
      "displayLabel": "Electronic Code of Federal Regulations",
      "folder": true,
      "formattedLastModifiedTime": "24-Apr-2026 21:45",
      "justFileName": "ECFR",
      "link": "https://www.govinfo.gov/bulkdata/json/ECFR",
      "name": "ECFR"
    }
  ]
}
```

Important: `USCODE` was not present in this bulkdata root listing.

### CFR annual edition index

`GET https://www.govinfo.gov/bulkdata/json/CFR/2024`

Headers used:

```text
Accept: application/json
```

Status/content type:

```text
200 application/json
```

Shape:

```json
{
  "files": [
    {
      "cfrTitle": 11,
      "displayLabel": "title-11",
      "folder": true,
      "formattedLastModifiedTime": "06-Jun-2025 14:20",
      "justFileName": "title-11",
      "link": "https://www.govinfo.gov/bulkdata/json/CFR/2024/title-11",
      "name": "title-11"
    },
    {
      "displayLabel": "CFR-2024.zip",
      "fileExtension": "zip",
      "folder": false,
      "formattedSize": "179 MB",
      "link": "https://www.govinfo.gov/bulkdata/CFR/2024/CFR-2024.zip",
      "mimeType": "application/zip",
      "size": 187702369
    }
  ]
}
```

### CFR title file listing

`GET https://www.govinfo.gov/bulkdata/json/CFR/2024/title-1`

Status/content type:

```text
200 application/json
```

Shape:

```json
{
  "files": [
    {
      "displayLabel": "CFR-2024-title1-vol1.xml",
      "fileExtension": "xml",
      "folder": false,
      "formattedLastModifiedTime": "19-Nov-2025 13:26",
      "formattedSize": "795.6 KB",
      "justFileName": "CFR-2024-title1-vol1.xml",
      "link": "https://www.govinfo.gov/bulkdata/CFR/2024/title-1/CFR-2024-title1-vol1.xml",
      "mimeType": "application/xml",
      "name": "CFR-2024-title1-vol1.xml",
      "size": 814725
    },
    {
      "displayLabel": "CFR-2024-title-1.zip",
      "fileExtension": "zip",
      "folder": false,
      "link": "https://www.govinfo.gov/bulkdata/CFR/2024/title-1/CFR-2024-title-1.zip",
      "mimeType": "application/zip"
    }
  ]
}
```

### CFR annual XML

`GET https://www.govinfo.gov/bulkdata/CFR/2024/title-1/CFR-2024-title1-vol1.xml`

Status/content type:

```text
200 text/xml
```

Observed XML shape:

```xml
<CFRDOC>
  <AMDDATE>Dec. 29, 2022</AMDDATE>
  <FMTR>
    <TITLEPG>
      <TITLENUM>Title 1</TITLENUM>
      <SUBJECT>General Provisions</SUBJECT>
      <REVISED>Revised as of January 1, 2023</REVISED>
    </TITLEPG>
  </FMTR>
  ...
  <SECTION>
    <SECTNO>§ 1.1</SECTNO>
    <SUBJECT>Definitions.</SUBJECT>
    <P>...</P>
  </SECTION>
</CFRDOC>
```

Section extraction path:

- statute metadata: title-level or volume-level row from `TITLEPG` plus file listing metadata.
- article/section rows: every `<SECTION>`.
- article number: normalized text of `<SECTNO>`.
- article title: normalized text of the first direct `<SUBJECT>` under `<SECTION>`.
- article text: concatenate section children in document order, primarily `<P>`, nested paragraph/list/table text when present.
- source URL: XML file URL plus a local fragment such as `#section-1.1` if generated.

### eCFR current XML, optional overlay

`GET https://www.govinfo.gov/bulkdata/json/ECFR`

Status/content type:

```text
200 application/json
```

Shape:

```json
{
  "files": [
    {
      "cfrTitle": 24,
      "displayLabel": "title-24",
      "folder": true,
      "link": "https://www.govinfo.gov/bulkdata/json/ECFR/title-24"
    }
  ]
}
```

`GET https://www.govinfo.gov/bulkdata/json/ECFR/title-1`

Status/content type:

```text
200 application/json
```

Shape:

```json
{
  "files": [
    {
      "displayLabel": "ECFR-title1.xml",
      "fileExtension": "xml",
      "folder": false,
      "formattedLastModifiedTime": "20-May-2024 16:55",
      "formattedSize": "473.1 KB",
      "link": "https://www.govinfo.gov/bulkdata/ECFR/title-1/ECFR-title1.xml",
      "mimeType": "application/xml",
      "size": 484409
    }
  ]
}
```

Use eCFR only as a current/non-official overlay unless houbun explicitly wants current editorial text. Annual CFR is the official edition.

### U.S. Code GovInfo bulkdata negative tests

`GET https://www.govinfo.gov/bulkdata/json/USCODE`

`GET https://www.govinfo.gov/bulkdata/json/USCODE/2023`

`GET https://www.govinfo.gov/bulkdata/json/USCODE/118`

All returned:

```json
{"message":"The Requested Resource could not be found."}
```

Status:

```text
404 application/json
```

Conclusion: do not plan U.S. Code collection through GovInfo bulkdata JSON.

### U.S. Code GovInfo package discovery through sitemaps

`GET https://www.govinfo.gov/sitemap/USCODE_sitemap_index.xml`

Status/content type:

```text
200 text/xml
```

Shape:

```xml
<sitemapindex>
  <sitemap>
    <loc>https://www.govinfo.gov/sitemap/USCODE_2023_sitemap.xml</loc>
    <lastmod>...</lastmod>
  </sitemap>
</sitemapindex>
```

`GET https://www.govinfo.gov/sitemap/USCODE_2023_sitemap.xml`

Status/content type:

```text
200 text/xml
```

Shape:

```xml
<urlset>
  <url>
    <loc>https://www.govinfo.gov/app/details/USCODE-2023-title1</loc>
    <lastmod>2025-06-16T12:44:00.045Z</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

Package ID is the last path segment, e.g. `USCODE-2023-title1`.

### U.S. Code title HTML

`GET https://www.govinfo.gov/content/pkg/USCODE-2023-title1/html/USCODE-2023-title1.htm`

Status/content type:

```text
200 text/html
```

Observed shape:

```html
<!-- AUTHORITIES-PUBLICATION-YEAR:2023 -->
<!-- AUTHORITIES-LAWS-ENACTED-THROUGH-DATE:20240103 -->
<!-- AUTHORITIES-USC-TITLE-NAME:TITLE 1 - GENERAL PROVISIONS -->
<!-- AUTHORITIES-USC-TITLE-ENUM:1 -->
<!-- AUTHORITIES-USC-TITLE-STATUS:positive-law -->
...
<!-- documentid:1_1 currentthrough:20240103 documentPDFPage:2 -->
<!-- itempath:/010/CHAPTER 1/Sec. 1 -->
<!-- field-start:head -->
<h3 class="section-head">&sect;1. Words denoting number, gender, and so forth</h3>
<!-- field-start:statute -->
<p class="statutory-body">...</p>
```

Title HTML contains metadata comments and section bodies, enough for section-level extraction without an API key.

### U.S. Code granule HTML

`GET https://www.govinfo.gov/content/pkg/USCODE-2023-title1/html/USCODE-2023-title1-chap1-sec1.htm`

Status/content type:

```text
200 text/html
```

Observed shape:

```html
<span>United States Code, 2023 Edition</span>
<span>Title 1 - GENERAL PROVISIONS</span>
<span>CHAPTER 1 - RULES OF CONSTRUCTION</span>
<span>Sec. 1 - Words denoting number, gender, and so forth</span>
<!-- documentid:1_1 usckey:... currentthrough:20240103 documentPDFPage:2 -->
<!-- itempath:/010/CHAPTER 1/Sec. 1 -->
<h3 class="section-head">&sect;1. Words denoting number, gender, and so forth</h3>
<!-- field-start:statute -->
<p class="statutory-body">...</p>
```

Granule URL is predictable only after deriving or discovering granule IDs. For bounded ingestion, parse section bodies from title HTML first; optionally generate granule URLs for source provenance when the ID is easy.

### U.S. Code XML negative test on GovInfo

`GET https://www.govinfo.gov/content/pkg/USCODE-2023-title1/xml/USCODE-2023-title1.xml`

Result:

```text
302 https://www.govinfo.gov/error
```

Following redirect returns GovInfo error HTML. `mods.xml` under the same package was also `404`.

Conclusion: GovInfo keyless U.S. Code full text is available as HTML/PDF from tested package URLs, not package XML. If XML/USLM is required, use OLRC (`uscode.house.gov`) as a separate source, not GovInfo.

## Mapping to houbun records

### CFR

`vertex_houbun_statute`:

- `jurisdiction`: `usa`
- `statute_id`: `CFR-{year}-title{n}` for title-level, or `CFR-{year}-title{n}-vol{v}` for volume-level if keeping printed volume boundaries.
- `title`: `Title {n} - {TITLEPG/SUBJECT}`
- `statute_type`: `regulation`
- `source`: `govinfo-cfr`
- `source_url`: JSON listing URL or XML file URL.
- `license`: `public-domain`
- `language`: `en`
- `article_count`: count of extracted `<SECTION>`.
- `props`: JSON with `year`, `title`, `volume`, `revised`, `amddate`, `lastModified`, `size`.

`vertex_houbun_article`:

- `statute_ref`: parent statute record ref.
- `article_no`: CFR section number, e.g. `§ 1.1`.
- `section`: hierarchical path if available from ancestor headings.
- `title`: section subject.
- `text`: normalized section text.
- `language`: `en`
- `amended_at`: use title revision date initially; preserve `AMDDATE` in props.
- `source_url`: XML file URL.

### U.S. Code

`vertex_houbun_statute`:

- `jurisdiction`: `usa`
- `statute_id`: package ID, e.g. `USCODE-2023-title1`
- `title`: `TITLE 1 - GENERAL PROVISIONS`
- `statute_type`: `law`
- `source`: `govinfo-usc`
- `source_url`: title HTML URL.
- `license`: `public-domain`
- `language`: `en`
- `article_count`: count of parsed `section-head`/`statutory-body` section blocks.
- `props`: JSON with `publicationYear`, `currentThrough`, `titleNumber`, `titleStatus`, `packageLastmod`.

`vertex_houbun_article`:

- `article_no`: section number from `h3.section-head`, e.g. `§1`.
- `section`: `itempath` comment or chapter path.
- `title`: text after section number in `h3.section-head`.
- `text`: concatenate `p.statutory-body*` between `field-start:statute` and the next section/field end.
- `source_url`: title HTML URL, or granule HTML URL when generated.

## Bounded ingestion plan

1. Metadata-only dry run, no DB writes.
   - Fetch `https://www.govinfo.gov/bulkdata/json/CFR/{year}`.
   - Fetch `https://www.govinfo.gov/sitemap/USCODE_{year}_sitemap.xml`.
   - Emit NDJSON manifest rows only: source, package/statute ID, title number, URL, last modified, size.

2. CFR pilot.
   - Limit to `year=2024`, `title=1`.
   - Fetch `https://www.govinfo.gov/bulkdata/json/CFR/2024/title-1`.
   - Parse only XML files, not zip.
   - Extract up to 100 `<SECTION>` rows into local NDJSON.
   - Validate required houbun fields and stable content hash generation.

3. U.S. Code pilot.
   - Limit to `year=2023`, `title=1`.
   - Discover package from `USCODE_2023_sitemap.xml`.
   - Fetch `https://www.govinfo.gov/content/pkg/USCODE-2023-title1/html/USCODE-2023-title1.htm`.
   - Extract up to 100 section blocks into local NDJSON.
   - Do not depend on GovInfo XML for USCODE.

4. Expand in bounded batches.
   - CFR: one title per worker, max 2 concurrent GovInfo requests per worker, retry 429/5xx with exponential backoff, persist manifest checkpoints by URL and last modified.
   - U.S. Code: one title package per worker, max 2 concurrent package fetches, parse title HTML rather than crawling every granule page.
   - Batch output: local NDJSON or staging table only; live insert requires a separate approval/runbook.

5. Later production hardening.
   - Add parser tests using saved tiny fixtures for CFR `<SECTION>` and USCODE HTML `field-start:statute`.
   - Add source-specific `props` schemas.
   - Add lineage only after amendment/update semantics are defined; initial import should be snapshot rows with `amended_at`/`currentThrough`.

## Open decisions

- CFR official annual vs eCFR current: annual CFR is official; eCFR can improve freshness but should be marked as current editorial overlay.
- U.S. Code XML: GovInfo keyless XML was not available at tested package URLs. If XML is mandatory, use OLRC as a separate `source`, likely `olrc-usc`, instead of pretending it is GovInfo.
- Statute granularity: title-level is simpler and matches GovInfo USCODE packages; CFR can be title-level or volume-level. Volume-level avoids huge parent records and better matches XML files.
