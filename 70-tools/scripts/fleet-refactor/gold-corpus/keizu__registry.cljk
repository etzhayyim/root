;; ported from 20-actors/keizu/methods/registry.py — gold reference (Fable)
;; 系図 (keizu) public-source registry access. ADR-2606066000.
;; registry を読み、ingest/bridge へソースカタログを公開する。
;; G11 honesty は registry 駆動: verified ソースの記録のみ :authoritative、
;; それ以外は :representative。SOURCE_DENY は Charter Rider §2(e)/N5 の runtime guard。
;;
;; WASM premise: I/O は注入する。registry の読み取りは load-fn 経由 (slurp/fetch を host が渡す)。
(ns keizu.methods.registry
  (:require [clojure.string :as str]))

;; Charter Rider §2(e)/N5 — 禁止された商用 gov-intel ターミナル (簡略 deny-set)。
(def source-deny #{"janes" "stratfor" "recordedfuture" "palantir"})

(defn source-denied
  "texts のいずれかが禁止ターミナルを引用していれば、その語を返す (なければ nil)。"
  [texts]
  (some (fn [t]
          (let [lower (when (string? t) (str/lower-case t))]
            (some #(when (and lower (str/includes? lower %)) %)
                  source-deny)))
        texts))

(defn source-ids [registry]
  (mapv #(get % "sourceId") (get registry "sources")))

(defn get-source
  "sourceId でソースを引く。無ければ例外。"
  [registry source-id]
  (or (some #(when (= (get % "sourceId") source-id) %)
            (get registry "sources"))
      (throw (ex-info (str "no such source " (pr-str source-id))
                      {:source-id source-id}))))

(defn sourcing-for
  "G11 — registry が verified と印した時のみ :authoritative、他は :representative。
  未知 id は保守的に :representative (自動 authoritative にしない)。"
  [registry source-id]
  (let [status (try (get (get-source registry source-id) "verificationStatus" "")
                    (catch clojure.lang.ExceptionInfo _ nil))]
    (if (= status "verified") :authoritative :representative)))

(defn assert-source-allowed
  "Charter Rider §2(e)/N5 — texts が商用 gov-intel ターミナルを引用していれば例外。"
  [& texts]
  (when-let [d (source-denied texts)]
    (throw (ex-info (str "Rider §2(e)/N5: " (pr-str d)
                         " is a prohibited commercial gov-intel terminal")
                    {:denied d}))))
