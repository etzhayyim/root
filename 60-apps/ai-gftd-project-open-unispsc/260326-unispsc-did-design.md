# UNISPSC DID Design (Canonical)

Date: 2026-03-26  
Scope: `ai-gftd-project-open-unispsc`, app namespace = `unispsc`

## 1. Decision

- Use repository directory `ai-gftd-project-open-unispsc`.
- Runtime identity/namespace is `unispsc`.
- Adopt DID path model compatible with platform rule:
  - `did:web:{app}.gftd.ai:{path}`
  - path segments must be alpha-start.

## 2. Canonical DID Shapes

- App DID:
  - `did:web:unispsc.gftd.ai`
- Segment DID:
  - `did:web:unispsc.gftd.ai:seg{NN}`
  - Example: `did:web:unispsc.gftd.ai:seg43`
- Commodity DID:
  - `did:web:unispsc.gftd.ai:seg{NN}:commodity:c{UNSPSC8}`
  - Example: `did:web:unispsc.gftd.ai:seg43:commodity:c43211501`

Rationale:
- `seg43` is alpha-start.
- `c43211501` uses `c` prefix to avoid numeric-first segment.
- DID path and NSID suffix remain isomorphic.

## 3. Lexicon Namespace

Canonical:
- `ai.gftd.apps.unispsc.*`

Examples:
- `ai.gftd.apps.unispsc.commodity`
- `ai.gftd.apps.unispsc.procurement`
- `ai.gftd.apps.unispsc.supplier`
- `ai.gftd.apps.unispsc.standard`
- `ai.gftd.apps.unispsc.risk`

## 4. Migration Phases

1. Spec-first (done)
- Update design docs/WIT comments to canonical naming.

2. Canonical-read-default
- Switch UI/API default links to `unispsc.gftd.ai`.

3. Canonical-only
- Write/read/subscribe all flows only via `ai.gftd.apps.unispsc.*`.
- Do not emit compatibility aliases.

## 5. Validation Checklist

- `segNN` and `c{UNSPSC8}` are always alpha-start.
- `commodity_code` remains raw 8-digit in payload.
- DID controller graph:
  - `did:web:unispsc.gftd.ai` CONTROLS `did:web:unispsc.gftd.ai:seg43`
  - `did:web:unispsc.gftd.ai:seg43` CONTROLS `did:web:unispsc.gftd.ai:seg43:commodity:c43211501`
