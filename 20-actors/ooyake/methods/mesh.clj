;; mesh.clj — ooyake 公 KOTOBA Mesh entry component (Clojure / kotoba-clj).
;;
;; The mesh-hosting face of actor:ooyake (world government atlas). Compiled by
;; kotoba-clj into a kotoba:kais WASM component, placed by the KOTOBA Mesh lattice.
;; Kotoba-native slice: observe gov-unit→parent structural edges as Datom
;; assertions, derive the structural hierarchy via Datalog → civic WAYFINDING.
;; The full address/form/procedure/BPMN atlas stays in the actor's methods.
;;
;; Posture: observational structural mirror (civic wayfinding), non-adjudicating.
;; host-imports: kqe-assert! / kqe-query → kotoba:kais/kqe (needs cap/kqe)
(ns ooyake)

(defn run [ctx]
  ;; observe — public government unit hierarchy (supranational → window).
  (kqe-assert! "ooyake" "prefecture" "under" "national-gov")
  (kqe-assert! "ooyake" "municipality" "under" "prefecture")
  (kqe-assert! "ooyake" "ward-office" "under" "municipality")
  ;; derive — structural hierarchy → wayfinding map (Datalog).
  (kqe-query "wayfinding(?u) :- under(?u)."))

(defn on-http [req]
  ;; read path for the /ooyake route.
  (kqe-query "wayfinding(?u) :- under(?u)."))
