# kotoba.datom → kotoba-lang/kotoba-datom (relocated 2026-07-17)

The canonical source of the `kotoba.datom` codec (content-addressed Datom-log,
commit-DAG) has been **extracted to its own west-managed repo**:

    github.com/kotoba-lang/kotoba-datom   (ns kotoba.datom, byte-identical)

as part of the 20-actors monorepo→multirepo split (ADR-2606112300 /
ADR-2605312345 lineage; 20-actors split per ADR-2607171100).

`datom.cljc` in THIS directory is **retained, not deleted** — two in-repo
consumers still reach it via a relative source-path and must repoint first:

  - `60-apps/etzhayyim-project-explorer` (shadow-cljs.edn :source-paths
    `../../20-actors/kotodama/src`)
  - `20-actors/ibuki` (bb.edn :paths `../kotodama/src`)

app-aozora already repoints at kotoba-lang/kotoba-datom. Once explorer + ibuki
(and the fleet-launched actors that import kotoba.datom) repoint, delete this
copy and leave only this tombstone. Do NOT edit datom.cljc here — make changes
in kotoba-lang/kotoba-datom and re-sync.
