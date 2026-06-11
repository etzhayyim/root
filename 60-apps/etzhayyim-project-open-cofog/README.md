# open-cofog

Machine-readable UN **COFOG** (Classification of the Functions of Government,
1999, updated 2014) published one **class** at a time as JSON + a small
TypeScript accessor.

- 10 Divisions → ~65 Groups → **96 Classes** (this monorepo's coverage)
- Source taxonomy: https://unstats.un.org/unsd/classifications/Family/Detail/4 (UN Statistics Division, public domain)
- License: Apache-2.0 (code) / public domain (UN data)

## Goal

Give downstream projects — fiscal dashboards, government agents, AT Protocol
public-administration actors — a stable, versioned, JSON-first COFOG dataset
without scraping the UN PDF.

## Layout

```
data/classes/{code}.json         one file per 4-digit Class (authoritative data)
worker/src/taxonomy.ts           Division + Group skeleton
worker/src/classes-index.ts      classes import index + progress counter
worker/src/app.ts                XRPC router
worker/kotodama.jsonld           profile + space + triggers
worker/wrangler.jsonc            CF Worker config
```

## XRPC

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.openCofog.listDivisions` | list 10 divisions |
| `com.etzhayyim.apps.openCofog.listGroups` | list ~65 groups (filter by division) |
| `com.etzhayyim.apps.openCofog.listClasses` | list 96 classes (filter by division/group), paginated |
| `com.etzhayyim.apps.openCofog.getClass` | get one class with full description |

## DID

```
did:web:open-cofog.etzhayyim.com                    primary
did:web:open-cofog.etzhayyim.com:division:{XX}      e.g. :division:01
did:web:open-cofog.etzhayyim.com:group:{XXX}        e.g. :group:011
did:web:open-cofog.etzhayyim.com:class:{XXXX}       e.g. :class:0111
```

## Adding a new class

1. Create `data/classes/{code}.json`.
2. Append `import cXXXX from "../../data/classes/XXXX.json";` and a
   `"XXXX": cXXXX` entry to `worker/src/classes-index.ts`.
3. Bump `IMPLEMENTED_COUNT`.
4. PR + cron deploy (`*/10 * * * *`, `loop` session).

## License

Apache-2.0. UN COFOG data is public domain.
