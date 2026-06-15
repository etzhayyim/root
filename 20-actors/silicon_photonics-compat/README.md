# Silicon Photonics Clean Room Actor (Clojure / Datomic)

Clean-room Silicon photonics / 光電融合 photonic integrated circuit actor in portable Clojure (`.cljc`) over the **kotoba Datom log** (content-addressed EAVT Datalog, Datomic-isomorphic — ADR-2605262130 + ADR-2605312345). CRUD + validation behind a `DatomPort` DI seam; production adapter = kotoba-kqe, tests = `in-memory-datom`. No external managed DB.

```
bb --classpath src:tests -e "(require 'silicon_photonics.actor-test) (clojure.test/run-tests 'silicon_photonics.actor-test)"
```
