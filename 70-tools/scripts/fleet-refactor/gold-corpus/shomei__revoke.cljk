;; ported from orgs/etzhayyim/com-etzhayyim-shomei/methods/revoke.py — gold reference (Fable)
;; 証明 (shomei) append-only binding revocation。ADR-2606072100。
;; G5 consent-bound + revocable: subject だけが自分の factor を unlink できる。
;; G10 + Tier-0 永久記憶: revocation は APPEND-ONLY な retraction Datom で、削除ではない。
;;   元 claim の履歴は永久保持 (no right to erasure)。assurance は revoked を EXCLUDE して再計算。
;;
;; factor-kinds / revocation-reasons は factors ns から注入する想定で引数化。
(ns shomei.methods.revoke
  (:require [clojure.string :as str]))

(defn validate-revocation
  "bindingRevocation の構造ゲート。違反で例外。claim を渡すと G5 所有者一致も検査。
  factor-kinds / reasons は許可集合。"
  [rev {:keys [factor-kinds reasons claim]}]
  (let [required [:subject-did :claim-ref :factor-kind :reason :revoked-at :subject-sig]
        missing (remove #(contains? rev %) required)]
    (when (seq missing)
      (throw (ex-info (str "bindingRevocation missing required field(s): " (vec missing))
                      {:missing (vec missing)})))
    (when-not (and (string? (:subject-did rev)) (str/starts-with? (:subject-did rev) "did:"))
      (throw (ex-info "revocation subject-did must be a DID" {})))
    (when-not (contains? factor-kinds (:factor-kind rev))
      (throw (ex-info (str "unknown factor-kind: " (pr-str (:factor-kind rev))) {})))
    (when-not (contains? reasons (:reason rev))
      (throw (ex-info (str "unknown revocation reason: " (pr-str (:reason rev))) {})))
    (when-not (integer? (:revoked-at rev))
      (throw (ex-info "revoked-at must be an integer unix timestamp" {})))
    (when-not (and (string? (:subject-sig rev)) (seq (:subject-sig rev)))
      (throw (ex-info "G7: subject-sig (subject-signed) is mandatory on a revocation" {})))
    ;; G5 — binding の所有者のみ revoke 可
    (when (and claim (not= (:subject-did claim) (:subject-did rev)))
      (throw (ex-info "G5: revocation subject-did must equal the claim's subject-did" {})))
    rev))

(defn active-verified-factors
  "≥1 の verified かつ NON-revoked claim を持つ factor-kind の集合 (append-only as-of)。
  claim が inactive なのは revocation が claim-ref で参照する、または
  subject-did+factor-kind 一致かつ revoked-at ≥ issued-at のとき。"
  [claims revocations]
  (let [revoked-refs (set (keep :claim-ref revocations))
        revoked-kinds (set (map (juxt :subject-did :factor-kind #(long (:revoked-at %)))
                                revocations))]
    (->> claims
         (filter :verified)
         (remove (fn [c]
                   (let [ref (or (:cid c) (:claim-ref c))]
                     (or (and ref (contains? revoked-refs ref))
                         (some (fn [[sd fk ra]]
                                 (and (= sd (:subject-did c))
                                      (= fk (:factor-kind c))
                                      (>= ra (long (:issued-at c)))))
                               revoked-kinds)))))
         (map :factor-kind)
         set)))
