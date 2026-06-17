# FINDING — autonomous-heartbeat `head-cid` is O(n²) per beat (ADR-2606160842 clj-port wave)

**Status**: ALL 9 heartbeat actors FIXED (2026-06-17). Recipe + per-actor verification below.
**Severity**: 常駐化 (resident-daemon) scaling defect. Not a correctness bug — the loop stays
deterministic / resume-safe and the commit-DAG still verifies; only wall-clock degrades, and it
degrades *with corpus size*, so it is invisible at R0 seed scale and bites after live ingest grows
the log.

## The anti-pattern

The autonomous-heartbeat actors share one `methods/kotoba.cljc` shape (an append-only,
content-addressed Datom commit-DAG). Each heartbeat calls `make-tx` with
`:prev-cid (head-cid log-path)`, and the shared `head-cid` is:

```clojure
(defn head-cid [log-path]
  (let [txs (read-log log-path)]          ; <-- parses EVERY tx line in the whole log
    (if (seq txs) (get (last txs) ":tx/cid") "")))
```

`read-log` slurps + EDN-parses **every** transaction line just to read the **last** tx's CID.
Two compounding costs:

1. **O(n²) in log length** — beat *k* re-parses all *k−1* prior txs. Over an N-beat run that is
   ΣO(k) = O(N²).
2. **Large per-tx constant** — these heartbeats re-emit the *entire* observed graph into each tx
   (`graph-datoms` over the whole corpus), so a single tx can be tens of thousands of datoms.
   Parsing even one such tx is seconds.

Measured on kanjo (corpus grown to 1.18 MB / ~30k datoms-per-tx by the live EDGAR ingest): a
3-beat run exceeded **300 s** (per-cycle 2 s → 9 s → 14 s; `verify-chain` 19 s). The
`test-autorun` suite was the lone RED in the otherwise-green ported fleet.

## The fix (behaviour-preserving, proven CID-identical)

`head-cid` reads only the **last line** and extracts the top-level `:tx/cid "b<hex>"` by string
scan. `tx-to-edn` serializes `:tx/cid` *before* the huge `:tx/datoms`, so the scan finds it near
the line head and never EDN-parses the graph — O(1) in tx size, O(1) prior-tx parses:

```clojure
(defn head-cid [log-path]
  (let [f (clojure.java.io/file (str log-path))]
    (if-not (.exists f)
      ""
      (let [last-line (->> (str/split-lines (slurp f))
                           (map str/trim)
                           (remove (fn [l] (or (str/blank? l) (str/starts-with? l ";"))))
                           last)]
        (or (when last-line (second (re-find #":tx/cid \"(b[0-9a-f]+)\"" last-line))) "")))))
```

Verify per actor: `(= (head-cid log) (get (last (read-log log)) ":tx/cid"))` must be `true`, and
the actor's `test_autorun` suite must stay green. (For kanjo the invariant suite was *also* made
hermetic — run against the bounded seed, not the unbounded live corpus — since invariants are
dataset-agnostic; do the same for any actor whose merged corpus has grown.)

Both edits are local to the actor's own `kotoba.cljc` / `test_autorun.cljc`. The shared per-line
EDN reader (`*-edn` / `parse-tokens`) is **not** touched.

## Affected actors (corpus size → risk tier)

| actor | corpus | head-cid → read-log? | status |
|---|---|---|---|
| kanjo | 1.18 MB | yes | **FIXED** — suite 23t/182a 4.3s (was >300s); hermetic seed |
| kabuto | 774 KB | yes | **FIXED** — CID-identical; suite 21t/147a 9.5s |
| shionome | 16 KB | yes (uses `peek`) | **FIXED** — suite 195t/1154a |
| sukashi | 44 KB | yes | **FIXED** — CID-identical; suite 30t/454a |
| watatsuna | 60 KB | yes | **FIXED** — CID-identical; suite 34t/125a |
| watari | 24 KB | yes | **FIXED** — CID-identical; suite 20t/1101a |
| ipaddress | 32 KB | yes | **FIXED** — test-autorun 6t/23a |
| yabai | 36 KB | yes | **FIXED** — test-autorun 7t/203a |
| hakoniwa | 20 KB | yes | **FIXED** — runtime 10t/31a + simulate 7t/154a |
| mimamori | — | no (different head impl) | n/a |

All 9 verified green after the fix (the append-only / tamper / persistence tests exercise head-cid
linkage). The 7 smaller actors were green pre-fix only because their R0 seeds are small; they are
now O(1)/beat so they stay fast as their G7 live ingest grows the log. (Follow-up done: ipaddress /
yabai / hakoniwa, previously absent from the `bb`-runner sweep, now ship a `run_tests.sh` and are
covered by the fleet green-check — 57 bb-runner actors.)
