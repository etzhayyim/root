;; ported from 20-actors/warifu/cells/refund.py (unit_refactor stage 0)
;; warifu.refund — reverse a settled transaction (purpose always escrow-refund).
(ns warifu.cells.refund
  (:require [clojure.string] [clojure.set] [clojure.edn]))

(declare refund-purpose refund-request refund-result refund-cell refund)

(def refund-purpose "escrow-refund")

(def refund-request
  {:settlement-id nil, :amount-usdc nil, :idempotency-key "", :reason nil})

(def refund-result
  {:refunded false
   :refund-id nil
   :amount-usdc 0
   :tx nil
   :fee-usdc 0
   :reason nil
   :eavt-facts []})

;; TODO: port-failed unit RefundCell (/var/folders/px/b63lssbx5056kq_1t6pvc1f80000gn/T/tmpb5f4iw7i/scratch.clj:2:1: er)
;; class RefundCell:
;;     def __init__(self, substrate: SubstratePort | None = None):
;;         self.substrate: SubstratePort = substrate or UnwiredSubstrate()
;; 
;;     def run(self, req: RefundRequest) -> RefundResult:
;;         s = self.substrate.load_settlement(req.settlement_id)
;;         if s is None:
;;             return RefundResult(refunded=False, reason="settlement not found")
;; 
;;         refundable = s["amount_usdc"] - s.get("refunded_usdc", 0)
;;         if refundable <= 0:
;;             return RefundResult(refunded=False, reason="already fully refunded")
;; 
;;         amount = req.amount_usdc if req.amount_usdc is not None else refundable
;;         if amount <= 0 or amount > refundable:
;;             return RefundResult(refunded=False, reason="refund exceeds refundable amount")
;; 
;;         refund_id, tx = self.substrate.reverse_settlement(req.settlement_id, amount)
;;         facts = [
;;             (refund_id, "warifu/kind", "refund", refund_id),
;;             (refund_id, "warifu/settlement_id", req.settlement_id, refund_id),
;;             (refund_id, "warifu/amount_usdc", amount, refund_id),
;;             (refund_id, "warifu/purpose", REFUND_PURPOSE, refund_id),
;;             (refund_id, "warifu/fee_usdc", 0, refund_id),
;;             (refund_id, "warifu/tx", tx, refund_id),
;;         ]
;;         self.substrate.write_facts(facts)
;;         return RefundResult(
;;             refunded=True, refund_id=refund_id, amount_usdc=amount, tx=tx, eavt_facts=facts
;;         )
(defn refund-cell [& _]
  (throw (ex-info "TODO: port-failed" {:from "RefundCell"})))

(defn refund [req substrate]
  (let [refund-cell (refund-cell)
        result (refund-cell req)]
    result))

