# etzhayyim.ie-flow — the information-energy flow agent lifecycle

**ADR-2606211200.** A reusable, per-actor-embeddable **system-of-systems** substrate that unifies
**kotoba** (the Datom ledger) + the **artificial-organism react loop** + the **Google AI
co-scientist** into one agent lifecycle. It generalises ibuki's organism-specific co-scientist
(ADR-2606201200) so *every* actor can measure its own information-energy flow, reason about how to
keep that flow paying for itself while returning order to society (共生), and persist the whole
deliberation to its own content-addressed commit-DAG.

It is the org-native realisation of the founding design (Datomic = the immutable fact/time/causality
ledger; Clojure = the pure order-calculus; the flow ledger = events/nodes/edges/stocks/interventions).

## The lifecycle (one beat)

```
SENSE ─▶ ORIENT ─▶ HYPOTHESIZE ─▶ REVIEW ─▶ RANK ─▶ EVOLVE ─▶ ACT ─▶ OBSERVE ─▶ LEARN ─▶ PERSIST
(fold the   (surprise=  (co-scientist  (Charter  (Elo    (recombine (pre-reg  (score     (Brier    (content-
 flow        distance    catalog →      gates)    tourn.) winners +  DRY-RUN   prior beat  proper-   addressed
 ledger →    from 'flow  hypotheses)              net+    meta-rev)  experiment vs net-gain score →   commit-DAG
 net-gain/   keeps                                order             leak-free) now)       kaizen wt) tx)
 order-      paying')             /well/cost
 index)
```

## Namespaces

| ns | role |
|---|---|
| `metrics`     | entropy · `order-index` (1−H(after)/H(before)) · `net-gain` · `agent-efficiency` · `flow-state` |
| `ledger`      | the IE-flow facts (events/nodes/stocks/interventions) on the kotoba Datom log (append-only) |
| `dynamics`    | `step-system` / `simulate` / `counterfactual` — system dynamics over accumulated-order stocks |
| `coscientist` | Google co-scientist (Generate→Reflect→Rank→Evolve→Meta-review) over the flow metrics, charter-gated |
| `lifecycle`   | the SENSE→…→PERSIST beat; leak-free Brier scoring; idempotent, resume-safe |
| `ingest`      | **real-world data → EDN → measured → DataLad** (`80-data/ie-flow/<source>/`) |
| `embed`       | the per-actor system-of-systems entry point + actor registry |

## Embed it in an actor (3 lines)

```clojure
(require '[etzhayyim.ie-flow.embed :as ie])
(ie/record! "<actor>" measured-events {:as-of n})   ; feed the flow ledger (real measurement in)
(ie/beat!   "<actor>" {:as-of n})                     ; run one co-scientist ReAct beat
(ie/measure "<actor>")                                ; → {:net-gain :order-index :agent-efficiency …}
```

A `measured-event` is `{:id :actor :source :target :type :volume :cost :value :risk :agent?}`.
Register an adopter (with an optional ALIGNED-only catalog extension) in `embed/actor-registry`
and `80-data/ie-flow/registry.edn`. The safety vocabulary is shared and unforkable.

## The shared safety property

Generation is a charter-clean **catalog**, never an LLM free-write, so a predatory mechanism
(`attention-exploitation`, `manipulation`, `asymmetric-surveillance`, `dependence-lock-in`,
`coercion`, `deception`…) is **structurally unrepresentable**, and `review` rejects it if injected.
The gates: **G-parasitism** (projected order ≥ floor — never a net taker), **G-subordinate**
(子孫 wellbecoming ≥ 0 — persistence is instrumental), **G-mechanism** (aligned-only),
**G-falsifiable** (a measurable prediction), **G-leash** (outward = member-principal / dry-run;
no-server-key). Murakumo narrates the meta-review (fail-open template, G6) but never the generation.

## Run

```bash
# tests (27 tests / 80 assertions)
bb -cp "70-tools/src:20-actors/kotodama/src" 70-tools/src/etzhayyim/ie_flow/run_tests.clj

# real-world ingest: the monorepo measures its OWN development metabolism (git → IE-flow)
bb -cp "70-tools/src:20-actors/kotodama/src" \
   -e "(require '[etzhayyim.ie-flow.ingest :as i]) (i/ingest! {:name \"repo-git\" :source :git :range \"-400\"})"
```

Deterministic (no wall clock, no randomness — logical time = log length), append-only (非終末論),
stdlib + `kotoba.datom` only, no network I/O in the loop, no held key.
