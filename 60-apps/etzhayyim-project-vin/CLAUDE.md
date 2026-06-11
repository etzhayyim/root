# etzhayyim-project-vin — Global Vehicle / VIN Registry

> **T1 Logical Actor**: Manifest-driven (`20-actors/vin/actor-manifest.jsonld`).

`vin.etzhayyim.com` (nanoid: `v1n0g10b`) — Global VIN (ISO 3779) + multi-jurisdiction plate registry. 1.5B registered vehicles (OICA + national registries).

## Schema
- ISO 3779 VIN 17-character (WMI + VDS + VIS)
- multi-jurisdiction license plate (per-country format)
- cohort DID per make/model/year

## cross-actor
- `kuruma` — car model registry (80K models)
- `legal-entity` — manufacturer (OEM) identity
- `sanctions` — vehicle export sanctions screening
