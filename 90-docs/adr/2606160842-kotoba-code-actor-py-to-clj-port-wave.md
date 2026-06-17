---
id: adr-2606160842-kotoba-code-actor-py-to-clj-port-wave
title: "ADR-2606160842: kotoba-code-driven actor Python→Clojure port wave (9 actors, test-gated)"
status: active
doc_type: adr
topic: kotoba-code-actor-port-wave
authoritative: true
last_verified: 2026-06-16
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Advances the substrate-native Clojure implementation surface (ADR-2605262130 kotoba Datom log) by porting actor methods off Python."
authoritative_for:
  - 20-actors actor-method Python→Clojure port methodology
related:
  - ADR-2605262130 (kotoba storage substrate unification)
  - ADR-2605312345 (kotoba Datom log first-class canonical state)
  - ADR-2605215000 (Murakumo-only inference)
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
related_repos:
  - github.com/com-junkawasaki/kotoba-code
supersedes: []
superseded_by: []
---

# ADR-2606160842: kotoba-code-driven actor Python→Clojure port wave (9 actors, test-gated)

**Status**: active
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

The substrate boundary (root CLAUDE.md, ADR-2605262130 + 2605312345) makes the **kotoba
Datom log** the canonical state and pushes implementation toward the Clojure/cljc stack.
A coverage audit of `20-actors/` showed the actor-method surface was still Python-dominant:
at the start of this wave **42 of 62 method-bearing actors had any Clojure implementation**
(the rest were Python-only). There was no line-coverage gate; "coverage" here means the
share of actor methods carried as `.cljc` on the substrate-native stack.

`kotoba-code` (`github.com/com-junkawasaki/kotoba-code`) is a model-neutral, **test-gated**,
kotoba-Datom-backed agentic coding agent built on the langchain-clj / langgraph-clj stack.
It drives an OpenAI-compatible model through a ReAct loop (`read_file` / `write_file` /
`run_clojure` / `run_tests`) and **rolls the working tree back on any non-green gate** — a
broken tree is never left behind. This makes it a safe driver for mechanical 1:1 ports.

# Decision

Use `kotoba-code` (model `moonshotai/kimi-k2.7-code` via OpenRouter; OR_KEY injected inline
from the macOS Keychain `service=openrouter`) to port Python-only actor methods to faithful
1:1 `.cljc`, gating each port on a per-actor `bb` test run and registering the new test
namespace into `bb.edn` `test:pywasm` (which `test:clj` depends on).

Conventions established for the wave:

1. **1:1 fidelity** — `methods/<m>.cljc` (ns `<actor>.methods.<m>`) + `methods/test_<m>.cljc`
   (ns `<actor>.methods.test-<m>`), Python exceptions → `(throw (ex-info …))`, dataclasses →
   maps, `pytest.mark.parametrize` expanded into individual assertions, `pytest.approx(x,abs=T)`
   → `(< (Math/abs (- actual x)) T)`.
2. **Gate** — `KC_TEST_CMD="bb -e \"(require 'clojure.test '<ns>)(run-tests …)\""`, `KC_GATE_ROUNDS=3`.
   Independent re-run after green confirms it outside the agent loop.
3. **Cross-language oracle for testless modules** — where no `test_*.py` existed
   (`kakaku`, `meisai/kotoba`), the expected values were produced by running the **real Python**
   and embedded verbatim, so the authored test is a genuine cross-language oracle, never a
   tautology. For `meisai/kotoba` the oracle is the **SHA-256 content-address (CID)**: the cljc
   reproduces Python's `tx_cid` byte-for-byte (`ba0f8ed8…293c6`), proving the kotoba Datom-log
   commit-DAG is content-address-identical across languages.
4. **Target selection** — prefer self-contained, pure-stdlib, network-free, float-light methods.
   Skip methods bound to external engines (`hydrogen_electrolysis` → Rust sim), robotics control
   closures (`mizuho/_substrate`), live HTTP/server tests (`maps/transit`), or RDAP/urllib
   (`yadori`). Float modules are admissible only when the test uses tolerant comparisons.

# Consequences

- **9 actors ported, all green** (121 tests / 234 assertions / 0 failures, run together):

  | actor | module | tests | note |
  |---|---|---:|---|
  | sanae | labor_liberation | 7 | LPS ranking (Math/log10) |
  | todoke | last_mile | 7 | greedy route + G7 envelope (ex-info) |
  | sentei | prune | 15 | prune/regraft + as-of + council gov; SHA-256 |
  | tazuna | teleop_safety | 18 | force-class/deadman/estop safety |
  | kakaku | kakaku_edn | 2 | minimal EDN reader + classify; **cross-lang oracle** |
  | meisai | kotoba | 6 | content-addressed Datom log; **CID byte-identical** |
  | niyaku | stow_plan | 12 | container stowage (discrete) |
  | tedai | desktop | 27 | computer-op safety classifier |
  | karakuri | command | 27 | web-service ServiceOp planner |

- **Coverage**: method-bearing actors with a Clojure impl **42 → 51 (of 62; ~82%)**;
  Python-only **20 → 11**. Each test ns registered in `bb.edn` `test:pywasm`.
- **`meisai/kotoba.cljc`** is directly on-theme: it demonstrates the kotoba Datom-log
  commit-DAG (EAVT, append-only, `tx-cid`/`make-tx`/`verify-chain`) is reproducible in cljc with
  byte-identical content-addressing — a concrete step toward the substrate-native Clojure goal.
- **Operational pattern**: the OpenRouter `moonshotai/kimi-k2.7-code` routing intermittently
  lands on a flaky provider (Io Net/vllm) that errors on large agentic requests; the gate rolls
  the tree back cleanly, and a clean-leftover → re-probe → retry recovers (the provider re-routes
  to Moonshot AI / Ambient). Code integrity was preserved across every such failure.

# Alternatives Considered

- **Manual hand-porting** — most reliable but defeats the "kotoba code で進める" intent; reserved
  as fallback.
- **Local ollama gemma-4-E4B backend** — available offline but too weak for multi-tool agentic
  ports; OpenRouter/kimi chosen for quality (LiteLLM `:4000` gateway was down).
- **Porting dependency closures** (`mizuho` robotics control, `kanae`→`danjo` cross-actor) — out
  of scope per-tick; deferred until the leaf modules are ported.

# Not Done / Follow-ups

- **noroshi/link_budget** — attempted; not landed (provider failure during a backlogged
  scheduling window; tree rolled back, no partial files). Re-attempt in a future pass.
- Remaining **11 Python-only actors** carry multi-file dependency closures (robotics control,
  kotoba log, sibling-actor imports, external sims, urllib/socket/h3); each needs its closure
  ported, not a single leaf file.
- **`hinagata.tests.test-coverage`** is RED independent of this wave (`coverage-report/report`
  unresolved symbol in sibling in-progress work) — it makes the aggregate `test:pywasm` red; out
  of scope here, tracked separately.

# Continuation 2026-06-16 (stub-repair + workflow slices + supervised-Kimi)

A follow-on session extended this wave with a **Claude-orchestrated** path (multi-agent
`Workflow` fan-out, one agent per actor, each independently re-verified with `bb` before commit)
plus a **supervised-Kimi** leg for `keizu`. All work landed on branch
`clj-port-pilot-and-stub-repairs`, every slice independently re-run before commit.

1. **Broken-stub remediation (NEW, high-value).** An audit found the prior auto-porter had left
   **90** falsely-"done" `.clj`/`.cljc` files: `(throw … "TODO: port-failed")` stubs, wrong
   `(ns root.<actor>…)` prefixes, and — worst — broken `X.clj` files **shadowing** a working
   `X.cljc` (bb loads `.clj` before `.cljc`). These compiled/registered green while every fn
   threw. Repaired to **90 → 5** (the 5 are intentional skips: 4 throwaway
   `kotoba-migration-bakeoff/runs/**` outputs + `murakumo_agent.clj` which has no `.py` source).
   - 14 actors (kanae pilot + fuchi/hakoniwa/ake/hinagata/abaki/danjo/asobi/hikari/hokorobi/
     hoshimori/ainori/funadaiku/himotoki/warifu): pure shadows deleted, stubs re-ported; verified
     **294 tests / 0 failures**.
   - 24 tooling/app units (70-tools + 60-apps): re-ported; all load-clean; `e7m-sim` verified
     byte-for-byte (`factory.ifc` 1112 STEP entities, CDX/ingest JSON identical to Python).

2. **Fresh + gap-fill conversions (workflow slices).** slice 1 = 8 greenfield actors
   (yadori/mizuho/ipaddress/tate/yabai/matsurigoto/noroshi/maps; **469 tests / 8053 assertions**);
   slice 2 = 12 partial actors filled; slice 3 = 14 partial actors filled (**713 tests / 8700
   assertions**). Deferred: `hydrogen_electrolysis` (kami-engine Python pkg, no bb equivalent),
   `kamado/test_ingest` (errors, reverted). `kanae` and `keizu` suites registered as `test:kanae`
   / `test:keizu` and wired into `test:clj` (keizu **119 tests / 455 assertions**, green).

3. **Kimi headless operational finding (corrects the "flaky provider" note above).** The dominant
   failure of `moonshotai/kimi-k2.7-code` driving the **headless** agent loop is NOT just provider
   routing — it is that K2.7 **always reasons and preserves reasoning across turns**, so the
   per-turn output budget is exhausted *during reasoning before the tool_call is emitted*
   (`provider.api_error: "only thinking content … output token budget exhausted"`,
   `finishReason=tool_calls`). **Raising `max_output_size` makes it worse** (the model just reasons
   more to fill the larger budget). The effective fix is to **turn reasoning off**:
   `KIMI_MODEL_DEFAULT_THINKING=false` — with thinking off, k2.6/k2.7 sustain multi-tool turns
   and complete small (1–3 file) units reliably. k2.6 behaves identically (thinking-budget bound).
   Net: headless Kimi is viable only **file-by-file with thinking off**; larger multi-file tasks
   stall. (Provider transients — connection-lost / idle-timeout — remain; the gate still rolls back
   cleanly.) For bulk work the Claude-`Workflow` path was far higher-throughput (48 actors across
   5 verified commits vs. a handful of files per supervised-Kimi unit).

4. **Process lesson.** Load-clean is **insufficient** verification: a Kimi-authored `keizu/_edn.cljc`
   compiled but `parse-edn` threw an NPE (read past `}`, called `atom'` on nil) — caught only by a
   functional smoke, then fixed via a re-drive. Gate ports on a **functional** run, not just `require`.

# References

- `github.com/com-junkawasaki/kotoba-code` — the test-gated porting agent
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605215000 (Murakumo-only inference)
- `bb.edn` `test:pywasm` / `test:clj` — actor Clojure test suites
