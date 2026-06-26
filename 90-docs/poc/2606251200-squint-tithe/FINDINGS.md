# PoC: squint TS→ClojureScript tooling validation (ADR-2606251200 Decision 3)

**Question (ADR-2606251200 §Decision 3):** is **squint/cherry** (ClojureScript syntax
→ lightweight JS, minimal runtime) viable as the *default* TS→cljs path for the
`60-apps` migration, fit for the **edge / WASM-32** target — reserving shadow-cljs
(full cljs runtime) only for runtime/REPL-heavy apps?

**Subject:** `tithe.ts` — the constitutional **10% Public-Fund split** (ADR-2605192100),
a pure BigInt-micros module **near-duplicated across ≥3 apps** (`ec`, `real-estate`,
`shopping` — identical logic, only the error-prefix string differs). Ideal: small, pure,
charter-relevant, and a real duplication the migration would collapse to one shared module.

## Method

```
npm i squint-cljs
npx squint-cljs compile tithe.cljs            # → tithe.mjs (native JS)
npx esbuild tithe.mjs --bundle --minify       # edge footprint
cp tithe.ts.reference tithe.ts && node parity.mjs   # parity vs the real TS (node v26 strips types)
```

## Results

**1. Exact semantic parity with the TypeScript** (`parity.mjs`, node v26):

| check | result |
|---|---|
| value cases (0, 7, 999, 1000, 1e6, 1.2e14 micros) | **6/6 identical** |
| constitutional **no-rounding-leak** (7 micros → tithe `0`, integer floor) | ✓ |
| negative gross → error type | both `RangeError` |
| non-numeric parse → error type | both `TypeError` |

squint emits **native `BigInt` arithmetic / comparison / `RegExp.test`** and a **plain JS
object** (`{gross, tithe, net}`) matching the TS interface — zero-overhead hot path.

**2. Edge footprint (esbuild --bundle --minify):**

| build | bytes | note |
|---|---|---|
| original `tithe.ts` | **347** | hand-written reference |
| squint **core-free** (this `tithe.cljs`) | **381** | ≈ TS (+34 B, ~10%) |
| squint *naïve* (`re-matches` + cljs truthiness) | 2,097 | drags squint-core lazy-seq via a tree-shaking limit |

The only thing that pulled squint-core in the naïve build was **`truth_`** (cljs-truthiness)
on an interop boolean. Writing the hot condition core-free — `(when (< g ZERO) …)` and
`(when (identical? false (.test …)) …)` (both compile to native `<` / `===`, no `truth_`) —
tree-shakes squint-core to **zero**, landing at **381 B ≈ the TS**.

## Conclusion (validates ADR-2606251200 Decision 3)

- **squint is viable for the edge/WASM target.** Exact parity; native BigInt/arith/regex;
  plain JS objects; **single-digit-KB worst case, ≈ hand-written TS with a small core-free
  discipline** on hot modules.
- **squint ≫ shadow-cljs for footprint** (shadow ships the full cljs runtime + persistent
  data structures, ~10–100× heavier) → the ADR's "**squint/cherry preferred, shadow-cljs
  reserved**" stands.
- **Actionable guidance for the migration:** for hot/edge modules, prefer core-free cljs
  (native interop on conditionals, avoid `re-matches`/truthiness on interop booleans) to
  keep output at TS-parity size; squint-core helpers are fine for cold paths.
- **Unification win demonstrated:** the `ec`/`real-estate`/`shopping` `tithe.ts`
  triplication collapses to **one** `tithe.cljs` — and, written as `.cljc`, the *same*
  tithe math is shared with the bb/clj actor side (write once, run both).

## Files

- `tithe.cljs` — the squint (core-free) port; `npx squint-cljs compile` → `tithe.mjs`.
- `tithe.ts.reference` — the original `ec` `tithe.ts` (parity reference; `cp` → `tithe.ts`).
- `parity.mjs` — the node harness (squint output vs the real TS).
