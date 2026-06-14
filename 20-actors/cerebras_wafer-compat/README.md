# Cerebras Wafer Clean Room Actor (Clojure / Datomic)

Clean-room Wafer-scale AI accelerator design actor in portable Clojure (`.cljc`) over the **kotoba Datom log** (content-addressed EAVT Datalog, Datomic-isomorphic — ADR-2605262130 + ADR-2605312345). CRUD + validation behind a `DatomPort` DI seam; production adapter = kotoba-kqe, tests = `in-memory-datom`. No external managed DB.

```
bb --classpath src:tests -e "(require 'cerebras_wafer.actor-test) (clojure.test/run-tests 'cerebras_wafer.actor-test)"
```
