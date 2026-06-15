;; ported from /Users/junkawasaki/github/com-junkawasaki/orgs/etzhayyim/root/20-actors/abaki/methods/test_live.py (unit_refactor stage 0)
(ns root.abaki.methods.test-live
  (:require [clojure.string :as str]
            [clojure.set :as set]
            [clojure.edn :as edn]))

(declare gate)

;; TODO: port-failed unit gate (assembled-lint error)
;; gate = LiveGate(
;;     operator_did="did:web:etzhayyim.com:operator:1",
;;     council_level=6,
;;     member_signature="sig_12345"
;; )
;; os.environ["ABAKI_ALLOW_LIVE_PUBLISH"] = "1"
;; routing_policy = {"blocked_entities": [{"id": "entity:compute:megacorp_a", "reason_ci": 100}]}
;; datoms = publish_live(routing_policy, gate, env=os.environ.copy())
(def gate nil) ;; TODO: port-failed const

