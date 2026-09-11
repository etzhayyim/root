;; ported from 20-actors/karakuri/methods/export.py — gold reference (Fable)
;; karakuri 絡繰 T3 structured-export — data-portability / anti-lock-in leg (G9)。
;; vendor lock-in の構造的逆: MEMBER 自身のデータを portable な kotoba-native 形へ取り出す。
;; G9 不変条件 (構造的に強制):
;;   - export owner は常に member (third-party PII なし)
;;   - export は常に暗号化 (encrypted-envelope ref; artifact は CID/ref を運び plaintext を運ばない)
;; live fetch は G6-gated; R0 は export PLAN のみを出す。
(ns karakuri.methods.export
  (:require [clojure.string :as str]))

(def member "member")                                ; G9 — own data only
(def export-formats #{"kotoba-edn" "json" "csv" "markdown"})
(def encref-prefix "encref:")

(defn build-export-plan
  "MEMBER 自身のデータの dry-run T3 export plan を作る (G9)。
  非 member owner / 未知 format / 非 encref secret-ref で例外。
  plan は暗号化済みで構築され、live fetch は G6-gated。"
  [service & {:keys [fmt owner secret-ref]
              :or {fmt "kotoba-edn" owner member secret-ref ""}}]
  (when (not= owner member)
    (throw (ex-info "G9 violation: export covers the member's OWN data only; no third-party PII"
                    {:g :G9 :owner owner})))
  (when-not (contains? export-formats fmt)
    (throw (ex-info (str "unknown export format " (pr-str fmt)) {:allowed export-formats})))
  (when (and (seq secret-ref) (not (str/starts-with? secret-ref encref-prefix)))
    (throw (ex-info "G9 violation: secret-ref must be an encrypted-envelope ref (encref:…)"
                    {:g :G9 :secret-ref secret-ref})))
  {:service service
   :fmt fmt
   :owner member                                     ; G9 const
   :encrypted true                                   ; G9 const
   :cid ""                                            ; content-addressed ref (live run で set)
   :secret-ref (if (seq secret-ref)
                 secret-ref
                 (str "encref:com.etzhayyim.encrypted/" service "-export"))
   :dry-run true                                      ; G6
   :roundtrip-ok false})
