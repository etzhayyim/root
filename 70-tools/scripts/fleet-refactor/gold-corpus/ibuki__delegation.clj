;; ported from 20-actors/ibuki/methods/delegation.py — gold reference (Fable)
;; delegation — organism は held key ではなく revocable LEASH の下で生きる。ADR-2606101200 §委任。
;; 正しい資格情報モデルは held root key でも per-beat human presence でもなく、organism 自身の
;; runtime へ委任された scoped/expiring/revocable capability (kotoba CACAO)。
;;   ISSUANCE = human act (member が自分の runtime で CACAO に署名; ibuki は鍵を持たず署名しない)。
;;   INVOCATION = organism の autonomous act (毎 push で opaque cacao-b64 を PRESENT する)。
;;   REVOCATION = consent 撤回 (exp 経過で自己無効化、local log へ fallback)。
;; Deterministic: expiry は caller 供給の now-epoch で判定 (method 内に wall clock なし)。stdlib-only。
(ns ibuki.methods.delegation
  (:require [clojure.string :as str]))

(def capability "datom:transact")                    ; autonomous loop が必要とする唯一の capability
(def required-keys [:cacao-b64 :aud :capability :graph :exp :nonce])

(defn validate
  "member 発行の delegation bundle を構造検証する。違反で例外。nil は呼び出し側が扱う。"
  [bundle]
  (let [missing (remove #(contains? bundle %) required-keys)]
    (when (seq missing)
      (throw (ex-info (str "delegation bundle missing keys " (vec missing)) {:missing (vec missing)})))
    (when (not= (:capability bundle) capability)
      (throw (ex-info (str "delegation capability " (pr-str (:capability bundle))
                           " != " (pr-str capability)) {})))
    (when-not (str/starts-with? (or (:aud bundle) "") "did:")
      (throw (ex-info "delegation audience must be a DID (kotoba checks cacao.aud == operator_did)" {})))
    (when (str/blank? (str (:nonce bundle)))
      (throw (ex-info "delegation must carry a nonce (replay protection)" {})))
    bundle))

(defn usable?
  "organism は now-epoch にこの delegation を graph への書込みに PRESENT できるか?
  bundle メタデータの純関数 — restart 前後で同じ答え。→ [usable? reason]。"
  [bundle now-epoch graph]
  (cond
    (nil? bundle)
    [false "no delegation (local-log-only until a member issues one)"]
    (not= (:graph bundle) graph)
    [false (str "delegation scoped to graph " (pr-str (:graph bundle)) ", not " (pr-str graph))]
    (>= now-epoch (long (:exp bundle)))
    [false (str "delegation expired (exp " (:exp bundle) " <= now " now-epoch ") — falls back to local log")]
    :else
    [true (str "usable (expires " (:exp bundle) ", aud " (:aud bundle) ")")]))

(defn audience
  "この capability が PRESENT される DID = kotoba node の operator DID (organism の DID ではない)。"
  [bundle]
  (:aud bundle))

(defn issuance-template
  "member が署名すべき CACAO PAYLOAD の shape を出す (ibuki は署名しない — 形のみ)。
  aud は NODE DID; resources は SIWE 形の2エントリ; write_author は iss (member) に解決される。"
  [{:keys [member-did node-did graph-cid exp-iso nonce-hex]}]
  {:iss member-did                                   ; member (signer) = on-record write principal
   :aud node-did                                     ; kotoba node (audience)
   :exp exp-iso                                      ; consent の horizon; 更新 = 再同意
   :nonce nonce-hex                                  ; replay protection
   :version "1"
   :resources [(str "kotoba://can/" capability)
               (str "kotoba://graph/" graph-cid)]})
