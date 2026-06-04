# Public Company Accounting Inputs

Place curated or reported annual accounting snapshots here to override modeled estimates in `resource-flow.jsonld` generation.

Path pattern:

- `content/public-company/accounting/<company-id>.jsonld`

Example schema:

```json
{
  "@context": ["https://schema.org/", {"gftd": "https://resources.gftd.ai/ontology#", "prov": "http://www.w3.org/ns/prov#"}],
  "@type": "gftd:PublicCompanyAccounting",
  "identifier": "apple-inc-accounting-2025",
  "company_id": "apple-inc",
  "currency": "USD",
  "year": 2025,
  "revenueMUsd": 391035,
  "cogsMUsd": 214137,
  "opexMUsd": 54847,
  "capexMUsd": 11018,
  "taxMUsd": 20548,
  "ebitdaMUsd": 101503,
  "modelSource": "sec-10k-curated",
  "modelPrecision": "reported"
}
```

When absent, the flow generator falls back to `gftd-public-company-flow-model-v1` estimates.
