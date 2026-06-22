(ns test-fixtures.sample-cell
  "A trivial cljc cell fixture for the lite-runner native-fire test: a `fire` that
  returns a content-addressed result map, exactly the shape a real cljc cell's
  heartbeat returns.")

(defn fire [] {:cid "bafyfixturecid1234567890"})
