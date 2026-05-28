# kotoba / py — Python siblings

Pure-Python packages that ride on top of the kotoba Rust workspace. Each
package keeps its own `pyproject.toml` and is independently versioned and
installable; there is no shared workspace umbrella.

## Packages

### `kotoba_langgraph/` — LangGraph-compatible graph engine for kotoba WASM Components

API-compatible with `langgraph`. Compiled to a WASM Component via
`componentize-py` and embedded in `kotoba-runtime`'s host. Stdlib-only
(no Rust/C extensions) so `componentize-py` can bundle it.

```python
from kotoba_langgraph import StateGraph, START, END, KotobaLLM
```

See: `kotoba_langgraph/__init__.py` for the full API.

### `kotoba_murakumo/` — Modal-compatible facade for the Murakumo fleet

Modal-API-shape Python decorators that route LLM / GPU calls to the
etzhayyim Murakumo Mac mini fleet endpoints declared in
`50-infra/murakumo/fleet.toml`. Never to commercial GPU rental
(constitutional invariant per ADR-2605215000 + ADR-2605262200 §2(i)(2)).

```python
from kotoba_murakumo import App, gpu

app = App("my-inference", fleet="50-infra/murakumo/fleet.toml",
          did="did:web:caller.etzhayyim.com")

@app.function(gpu=gpu.MacMini(node="judah"), model="gemma3:4b")
def quick_classify(text: str) -> str: ...

result = quick_classify.remote("hello")
async for tok in quick_classify.stream("hello"): ...
```

Or as a near-drop-in Modal replacement:

```python
import kotoba_murakumo.modal_compat as modal

stub = modal.App("x", fleet="50-infra/murakumo/fleet.toml")

@stub.function(gpu="A10G")          # → EvoX2 with honest warning
def f(p: str) -> str: ...
```

See: `kotoba_murakumo/README.md` + ADR-2605282000 for the full design,
ADR-2605282100 for the mKOTO economy + Modal-billing-parity layer.

The economy surface adds Modal-equivalent spend caps + pre-flight cost
estimates + post-call billing records:

```python
from kotoba_murakumo import App, gpu
from kotoba_murakumo.economy import BudgetExceeded, InsufficientCredit

app = App("my-inference", fleet="50-infra/murakumo/fleet.toml",
          did="did:web:caller.etzhayyim.com",
          balance_lookup=my_balance_fn)

@app.function(gpu=gpu.EvoX2(), model="llama3.3:70b",
              max_cost_mkoto=10_000_000)        # 10 KOTO cap
def heavy(prompt: str) -> str: ...

# Pre-flight estimate (no HTTP)
est = heavy.estimate("...")                     # UsageEstimate(cost_mkoto_est=...)

# Live dispatch — debits balance; raises pre-HTTP if budget/credit fails
try:
    out = heavy.remote("...")
except BudgetExceeded as e:    print(e.cap_mkoto, e.estimated_mkoto)
except InsufficientCredit as e: print(e.balance_mkoto, e.required_mkoto)

print(app.balance(), app.get_tariff().for_backend("evo-x2"))
```

## Build / test

Each package is independent:

```bash
# kotoba_langgraph
cd kotoba_langgraph && pip install -e . && python -m pytest

# kotoba_murakumo
cd kotoba_murakumo && pip install -e . && python -m pytest
```

The dev box where this README was written has a global-site-packages
pydantic-core / pydantic mismatch in the `langsmith` pytest plugin;
prefix with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` if you hit it.

## Cross-package invariant

Both packages assume the canonical kotoba Rust workspace exists in the
sibling `crates/` tree. Neither vendors the Rust side; they consume it via
HTTP (LiteLLM gateway) or WASM Components (componentize-py output).

## License

Apache-2.0 + etzhayyim Charter Compliance Rider v2.0 — see repo root
`/LICENSE` and `/CHARTER-RIDER.md`.
