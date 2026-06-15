# Nvidia Cosmos Clean Room Actor (Clojure / Datomic)

Clean-room World Foundation Models / Physical AI simulation actor in portable Clojure (`.cljc`) over the **kotoba Datom log** (content-addressed EAVT Datalog, Datomic-isomorphic — ADR-2605262130 + ADR-2605312345). CRUD + validation behind a `DatomPort` DI seam; production adapter = kotoba-kqe, tests = `in-memory-datom`. No external managed DB.

```
bb --classpath src:tests -e "(require 'nvidia_cosmos.actor-test) (clojure.test/run-tests 'nvidia_cosmos.actor-test)"
```
