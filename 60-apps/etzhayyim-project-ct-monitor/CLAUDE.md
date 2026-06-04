# ct-monitor.etzhayyim.com

CT / BGP / CVE monitoring — open observability over Certificate Transparency
logs, BGP routing changes, and CVE disclosures.

## Status

Migrated from gftd vendor 2026-06-03 (candidate for etzhayyim front per 3-axis
OR-test — pending review). Identity-only port — the vendor side held no
implementation beyond a deploy stub. Build proceeds here.

## Feeds

- **CT**: Certificate Transparency log monitoring (new cert issuance per domain).
- **BGP**: routing-table change / hijack-pattern detection from public collectors.
- **CVE**: CVE disclosure tracking and affected-component correlation.
