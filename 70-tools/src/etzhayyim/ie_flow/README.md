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

## Score + organism reward (`score.cljc`, ADR-2606212200)

Every embedded actor is an **information-control actor** in the system + energy flow. `score.cljc`
folds an actor's flow-state into ONE composite **info-control-score** ∈ 0..1 — its active-inference
**利得**: how well it RECTIFIES flow into returned order (`rectify`=order-index), pays for itself
(`phi`=net-gain), stays 共生 (`eta`), is a 利得 not a paid magic-circle (`efficiency`), minus its
`surprise` (variational free energy) — **GATED by 子孫 wellbecoming** (`:descendant`; 0 = veto,
G-subordinate). Weights are DATA (`score-weights.edn`) — re-weighting the whole SoS is a data edit.

The colony aggregate is the **artificial-organism reward**: `colony-reward` = Σ score × (1 +
log10(1+throughput)); its rounded form `:colony-order` is a **negentropy SOURCE** added to ibuki's
metabolic intake (`metabolism/intake-weights` → Φ → reserves → survival). So the organism's reward
= the colony's aggregate information-control. **Active inference at the colony scale.**

```clojure
(require '[etzhayyim.ie-flow.score :as score])
(score/info-control-score flow-state {:descendant 0.85})   ; → {:score 0.45 :vetoed? false :components {…}}
(score/score-roster {actor flow-state …} {actor {:descendant w}})  ; → ranked SoS scoreboard
(score/as-env-source scoreboard)                            ; → {:colony-order n} (feeds ibuki intake)
```

```bash
# the SoS scoreboard: score every actor with a measured flow + fold into the organism reward
bb -cp "20-actors:70-tools/src:orgs/kotoba-lang/kotodama/src" \
   70-tools/src/etzhayyim/ie_flow/scoreboard.clj --write   # → scoreboard.edn + scoreboard.md
# scoreboard.md is the human-readable SoS report (ranked 利得 table + organism-reward delta).
# integration test (needs the actor adapters on the classpath):
bb -cp "20-actors:70-tools/src:orgs/kotoba-lang/kotodama/src" \
   70-tools/src/etzhayyim/ie_flow/test_scoreboard.clj      # 3 tests / 14 assertions
```

### Embedding a gate / observatory actor (`gate-adapter.cljc`)

Verdict-gate + observatory actors (kafun / ugachi / busshi / …) all share the same shape:
an assessment produces ROWS, each routes to a VERDICT/ROUTE, and the actor rectifies a
scattered-risk VOLUME into a realised-order VALUE. `gate-adapter` is that shared plumbing —
an actor supplies only its DOMAIN model (a config map), not 80 forks:

```clojure
(require '[etzhayyim.ie-flow.gate-adapter :as ga])
(defn config [rows]
  {:actor "ugachi" :id-prefix "ugachi-" :source-kind "project" :rows rows
   :route-key "verdict"
   :volume-fn #(double (get % "multigen_risk"))         ; the scattered risk it rectifies
   :value-fn  #(* (volume %) (route-factor (verdict %)) ga/default-value-scale)})  ; realised order
(defn flow-state  [rows] (ga/flow-state (config rows)))
(defn record-flow! [rows opts] (ga/record-flow! (config rows) opts))
```

## Run

```bash
# tests (36 tests / 102 assertions — incl. score)
bb -cp "70-tools/src:orgs/kotoba-lang/kotodama/src" 70-tools/src/etzhayyim/ie_flow/run_tests.clj

# real-world ingest: the monorepo measures its OWN development metabolism (git → IE-flow)
bb -cp "70-tools/src:orgs/kotoba-lang/kotodama/src" \
   -e "(require '[etzhayyim.ie-flow.ingest :as i]) (i/ingest! {:name \"repo-git\" :source :git :range \"-400\"})"
```

Deterministic (no wall clock, no randomness — logical time = log length), append-only (非終末論),
stdlib + `kotoba.datom` only, no network I/O in the loop, no held key.
