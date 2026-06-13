(ns warifu.cells.substrate
  "warifu substrate port — the DI seam between cells and kotoba/@etzhayyim/sdk.

  1:1 port of `cells/substrate.py` (the subset the refund cell needs + the
  loud-failing default). R0 scaffold (ADR-2605302000). Cells depend on the
  `SubstratePort` protocol, never on a concrete client. In production an
  `@etzhayyim/sdk`-backed adapter is injected (R1); tests inject an in-memory
  fake. Per ADR-2605231525 no platform key is held; money never lives in the
  cells — `reverse_settlement` emits ERC-4337 UserOps via the adapter.

  Conventions (yobel/ports.cljc + mimamori/methods/bond.cljc house style):
    - SubstratePort as a Clojure defprotocol (the Python `Protocol`)
    - UnwiredSubstrate as a defrecord whose every method throws ex-info — the
      sentinel that fails loudly so a forgotten injection never silently
      settles money (Python `NotImplementedError`)
    - settlement/refund maps use STRING keys verbatim from the Python payload
      (\"amount_usdc\"/\"refunded_usdc\"/\"funding\"/…) — not kebab keywords —
      because they are kotoba payload dict keys, not Clojure structural keys
    - EAVT facts are [E A V T] vectors (kotoba write contract), A is the
      \"warifu/…\" string attribute verbatim")

;; ── SubstratePort (Python Protocol → Clojure protocol) ────────────
;;
;; Only the methods the refund cell actually calls are required by the port
;; the cell depends on; the full Python Protocol surface (resolve_card,
;; usdc_balance, place_hold, settle_transfer, open_dispute, …) lives in the
;; sibling cell ports and is not reproduced here (port what refund.py imports).

(defprotocol SubstratePort
  "The DI seam the refund cell calls into."
  (load-settlement [this settlement-id]
    "Return the settlement map for `settlement-id`, or nil if absent.
     (Python `load_settlement(settlement_id) -> Optional[dict]`.)")
  (reverse-settlement [this settlement-id amount-usdc]
    "Reverse `amount-usdc` of a settlement; return [refund-id tx].
     (Python `reverse_settlement(settlement_id, amount_usdc) -> (str, str)`.)")
  (write-facts [this facts]
    "Append EAVT facts (a seq of [E A V T] vectors) to the ledger.
     (Python `write_facts(facts) -> None`.)"))

;; ── UnwiredSubstrate (loud-failing default sentinel) ──────────────

(defn- unwired-fail
  "raise NotImplementedError(...) — the warifu R0 forgotten-injection guard."
  [op]
  (throw (ex-info
          (str "warifu R0: substrate '" op "' not wired — inject "
               "@etzhayyim/sdk adapter or an in-memory fake")
          {:warifu/unwired-substrate true :op op})))

(defrecord UnwiredSubstrate []
  SubstratePort
  (load-settlement [_ _]      (unwired-fail "load_settlement"))
  (reverse-settlement [_ _ _] (unwired-fail "reverse_settlement"))
  (write-facts [_ _]          (unwired-fail "write_facts")))

(defn unwired-substrate
  "Construct the default loud-failing UnwiredSubstrate sentinel."
  []
  (->UnwiredSubstrate))
