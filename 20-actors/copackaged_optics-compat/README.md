# Copackaged Optics Clean Room Actor (Clojure / Datomic)

Clean-room Co-packaged optics / 光電融合 optical interconnect actor in portable Clojure (`.cljc`) over the **kotoba Datom log** (content-addressed EAVT Datalog, Datomic-isomorphic — ADR-2605262130 + ADR-2605312345). CRUD + validation behind a `DatomPort` DI seam; production adapter = kotoba-kqe, tests = `in-memory-datom`. No external managed DB.

```
bb --classpath src:tests -e "(require 'copackaged_optics.actor-test) (clojure.test/run-tests 'copackaged_optics.actor-test)"
```
