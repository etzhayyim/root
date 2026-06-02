# regulator_bulk fixture

Local fixture for the first akashi R1 parser. It models a regulator-style
public bulk export and is intentionally not fetched by any cell.

- Source family: `regulator-repository`
- Parser: `/20-actors/akashi/adapters/regulator_bulk_fixture_parser.py`
- Output Lexicons: `adDisclosureSnapshot`, `advertiserIdentity`,
  `creativeDisclosure`, `deliveryDisclosure`, `landingEvidence`,
  `methodNote`, `sourcePolicySnapshot`
- Boundary: fixture-only; no platform API or page collection
