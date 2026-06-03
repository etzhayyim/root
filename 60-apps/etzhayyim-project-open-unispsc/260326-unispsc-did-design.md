# UNISPSC DID Design (Canonical)

Date: 2026-03-26
Scope: `etzhayyim-project-open-unispsc`, app namespace = `unispsc`

## 1. Decision

- Use repository directory `etzhayyim-project-open-unispsc`.
- Runtime identity/namespace is `unispsc`.
- Adopt DID path model compatible with platform rule:
  - `did:web:{app}.etzhayyim.com:{path}`
  - path segments must be alpha-start.

## 2. Canonical DID Shapes

- App DID:
  - `did:web:unispsc.etzhayyim.com`
- Segment DID:
  - `did:web:unispsc.etzhayyim.com:seg{NN}`
  - Example: `did:web:unispsc.etzhayyim.com:seg43`
- Commodity DID:
  - `did:web:unispsc.etzhayyim.com:seg{NN}:commodity:c{UNSPSC8}`
  - Example: `did:web:unispsc.etzhayyim.com:seg43:commodity:c43211501`

Rationale:
- `seg43` is alpha-start.
- `c43211501` uses `c` prefix to avoid numeric-first segment.
- DID path and NSID suffix remain isomorphic.

## 3. Lexicon Namespace

Canonical:
- `com.etzhayyim.apps.unispsc.*`

Examples:
- `com.etzhayyim.apps.unispsc.commodity`
- `com.etzhayyim.apps.unispsc.procurement`
- `com.etzhayyim.apps.unispsc.supplier`
- `com.etzhayyim.apps.unispsc.standard`
- `com.etzhayyim.apps.unispsc.risk`

## 4. Migration Phases

1. Spec-first (done)
- Update design docs/WIT comments to canonical naming.

2. Canonical-read-default
- Switch UI/API default links to `unispsc.etzhayyim.com`.

3. Canonical-only
- Write/read/subscribe all flows only via `com.etzhayyim.apps.unispsc.*`.
- Do not emit compatibility aliases.

## 5. Validation Checklist

- `segNN` and `c{UNSPSC8}` are always alpha-start.
- `commodity_code` remains raw 8-digit in payload.
- DID controller graph:
  - `did:web:unispsc.etzhayyim.com` CONTROLS `did:web:unispsc.etzhayyim.com:seg43`
  - `did:web:unispsc.etzhayyim.com:seg43` CONTROLS `did:web:unispsc.etzhayyim.com:seg43:commodity:c43211501`
