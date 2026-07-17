# Flat west multirepo migration

## Target

The workspace keeps repositories directly below their GitHub organisation:

```text
orgs/etzhayyim/com-etzhayyim-<actor>
orgs/etzhayyim/<shared-library-or-service>
orgs/gftdcojp/<business-repository>
```

`actor`, `engine`, `protocol`, `app`, `infra`, `tool`, `data`, `docs`, and
`governance` are classifications in manifest/repository metadata. They are not another
directory layer. The old `00-contracts` through `90-docs` names are historical monorepo
layers and must not be reproduced in new repositories.

## Ownership test

Extract code as a shared library when all of the following are true:

1. two or more independent repositories consume the same API;
2. the code has no actor DID, product policy, deployment target, or private dataset
   ownership of its own;
3. it can be versioned and tested without the old root classpath.

Keep or create an individual repository when it owns an actor identity, a deployable
runtime, an independently released engine/protocol, an application, or a dataset with a
distinct retention/access policy. Repository-local adapters stay with their owner even
when they call a shared library.

Current shared-library extraction prerequisites are `kotoba.datom`,
`etzhayyim.ie-flow.*`, and `moyai.ledger`. They must be consumed as pinned dependencies
before their legacy root locations can disappear.

## Safe removal gate

A legacy component may be removed only when every gate passes:

- canonical independent repository exists and is registered in west;
- all implementation, tests, schemas, and required data are present there;
- root-relative consumers have been repointed;
- actor-to-actor dependencies are explicit and pinned;
- a fleet cell can resolve its namespace from independent checkouts, when applicable;
- relevant tests pass outside the monorepo classpath;
- a `*-MOVED.md` tombstone records the canonical repository.

Content equality is checked by hash, not by matching filenames alone. Generated identity
metadata may differ, but a root-only implementation or dataset blocks deletion until it
has been deliberately merged.

## Migration order

1. Freeze numbered layers and prevent new dependencies on their paths.
2. Extract common libraries and change consumers to pinned dependencies.
3. Consolidate non-fleet duplicates whose independent repositories are proven complete.
4. Make fleet classpath resolution use west checkouts, then consolidate fleet actors.
5. Publish remaining actors, engines, apps, infrastructure, tools, and datasets as
   independent repositories and register them in west.
6. Move cross-repository ADR/rules to the superproject governance corpus and retire the
   numbered directories once no live reference remains.

## First verified consolidation in this pass

`os` and `umisachi` were non-fleet, had no live root-relative runtime consumer, and their
independent repositories contained every non-metadata file from the legacy copies by
SHA-256 comparison. Their canonical homes are:

- <https://github.com/etzhayyim/com-etzhayyim-os>
- <https://github.com/etzhayyim/com-etzhayyim-umisachi>

`karute` also passed the content containment check but remains in root because an
application still resolves its actor manifest through a root-relative path. It must be
repointed before consolidation.
