# koke kotoba

Phase E Option B reference implementation of koke (苔 / moss) on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-kotoba-write-target-options.md), koke migrates from vendor's `createKyselyDb` pattern to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **4 of 4 (100%) canonical** koke commands ported.

| Tier | Commands | Slice |
|---|---|---|
| Fixation | fixSignal, getFixation, listFixations, releaseCarbon | **1** |

## Bonsai vascular flow (with ki sibling)

```
koke (fixSignal)  →  hakkou (startFerment)  →  ki (absorb)
                                              → synthesize → bloom
```

## Authority-chain DIDs

```
did:web:koke.etzhayyim.com:fixation:{fixationId-slug}    — Fixation (glucose)
```

## Sibling reference impls

| Actor | Coverage | Status |
|---|---|---|
| hanrei | 31/31 | complete |
| ipaddress | 37/37 | complete |
| sbom | 17/N (canonical 4/4) | canonical complete |
| kiyo | 12/12 | complete |
| ki | 4/4 | complete |
| otakiage | 13 (10/10 canonical) | complete |
| houki | 9 (8/8 canonical) | complete |
| open-banking | 5/5 | complete |
| open-denki | 12/12 | complete |
| **koke** | **4/4** | **complete** |
