# Public Company IR/News Ingest Design (Single-Company Increment)

Date: 2026-03-03
Scope: `etzhayyim-project-resources` first increment for one public company (`vale-sa`).

## Goal

Ingest IR/News signals for one company and normalize them into JSON-LD entities under `content/public-company/entity/<company-id>/`.

## Data Model

- Company profile:
  - `content/public-company/company/<company-id>.jsonld`
  - Contains ticker/exchange/country and canonical company identity.
- Source definition:
  - `content/public-company/source/<company-id>.jsonld`
  - Declares IR/News feed URLs using `DataFeed` / `DataFeedItem`.
- Signal entities (generated):
  - `content/public-company/entity/<company-id>/<id>.jsonld`
  - Each entity is a normalized `NewsArticle` with `additionalType=etzhayyim:PublicCompanySignal`.

## Ingest Flow

1. Load company profile and source definition.
2. Fetch each feed URL (RSS/Atom).
3. Parse entries (`title`, `link`, `published`, `summary`).
4. Normalize to JSON-LD signal entities.
5. Deduplicate by canonical URL + title.
6. Write entity files and `index.jsonld`.

## Operational Notes

- This increment is intentionally single-company and feed-driven.
- Additional companies only require new `company/*.jsonld` and `source/*.jsonld` files.
- Future hardening:
  - Official IR feeds per exchange/issuer.
  - Full-text canonicalization and language detection.
  - Entity-linking to ownership/financial statement actors.
