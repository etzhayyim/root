# hakkou rw-free

Phase E Option B reference implementation of hakkou (発酵 / fermentation) on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md), hakkou migrates from vendor's `createKyselyDb` + BPMN ferment-pipeline.bpmn to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **2 of 2 (100%) canonical** hakkou commands ported + 1 helper.

| Tier | Commands | Slice |
|---|---|---|
| Ferment | startFerment, getFerment, updateFermentStatus | **1** |

## Bonsai vascular flow

```
koke (fixSignal)  →  hakkou (startFerment)  →  ki (absorb)
                                              → synthesize → bloom
```

## State machine

```
pending → running → done
              ↘ failed
```

Each transition is driven by the LangServer pod via `updateFermentStatus`.

## Authority-chain DIDs

```
did:web:hakkou.etzhayyim.com:ferment:{fermentId-slug}
```

## Sibling reference impls (10 actors)

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
| koke | 4/4 | complete |
| **hakkou** | **3 (2/2 canonical)** | **complete** |
