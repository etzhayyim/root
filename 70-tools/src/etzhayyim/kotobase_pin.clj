;; etzhayyim.kotobase-pin — register a CID with kotobase.net's IPFS Pinning Service
;; using a self-sovereign CACAO, in pure clj. The clj replacement for the earlier
;; throwaway node script (ADR-2606111330): com-junkawasaki/ed25519-clj derives the
;; pubkey/did:key from the raw seed, com-junkawasaki/cacao-clj mints the CAIP-122
;; CACAO — no node, no held key.
;;
;; The tenant seed is RESOLVED, not pasted: env KOTOBA_SEED_HEX (direct) → else the
;; 1Password item via `op` (an interactive session OR an OP_SERVICE_ACCOUNT_TOKEN
;; for cron). So `bb kotobase:pin <cid>` is a one-shot CLI — no human re-enters the
;; secret each time, and it is automatable. The CACAO is presented as
;; `Authorization: CACAO …` — no platform-held signing key (no-server-key, ADR-2605231525).
;;
;; Usage:
;;   bb kotobase:pin <cid> [name] [--endpoint https://kotobase.net]
;;     (seed auto-resolved: KOTOBA_SEED_HEX, else 1Password via op)
;;   override the vault item: KOTOBASE_OP_ITEM / KOTOBASE_OP_VAULT / KOTOBASE_OP_FIELD
;;   non-interactive (cron): export OP_SERVICE_ACCOUNT_TOKEN=…  (op reads it; no prompt)
(ns etzhayyim.kotobase-pin
  (:require [clojure.string :as str]
            [babashka.http-client :as http]
            [babashka.process :as p]
            [ed25519.core :as ed]
            [cacao.core :as cacao])
  (:import (java.time Instant)
           (java.time.temporal ChronoUnit)))

(def default-endpoint "https://kotobase.net")

;; ── seed resolution (env → 1Password) ─────────────────────────────────────────
(def op-item  (or (System/getenv "KOTOBASE_OP_ITEM")  "bgpbu66h7dl7sjzxk2ffrdrywq")) ; gftd.kotobase/KOTOBA_SEED
(def op-vault (or (System/getenv "KOTOBASE_OP_VAULT") "gftdcojp"))
(def op-field (or (System/getenv "KOTOBASE_OP_FIELD") "credential"))

(defn- op-read-seed
  "Fetch the tenant seed from 1Password via `op` — works with an interactive session
   OR a non-interactive OP_SERVICE_ACCOUNT_TOKEN (cron). Returns the trimmed value or nil."
  []
  (try
    (let [{:keys [exit out]} (p/sh "op" "item" "get" op-item "--vault" op-vault
                                   "--fields" (str "label=" op-field) "--reveal")]
      (when (zero? exit) (not-empty (str/replace (str out) #"\s" ""))))
    (catch Exception _ nil)))

(defn resolve-seed
  "The tenant seed hex: env KOTOBA_SEED_HEX first (direct), else 1Password via op.
   Throws with actionable guidance if neither yields a valid 64-hex seed."
  []
  (let [s (or (some-> (System/getenv "KOTOBA_SEED_HEX") str/trim not-empty)
              (op-read-seed))]
    (when-not (and s (re-matches #"[0-9a-fA-F]{64}" s))
      (throw (ex-info (str "no tenant seed. Provide one of:\n"
                           "  • KOTOBA_SEED_HEX=<64hex> (direct)\n"
                           "  • sign in to 1Password (op item " op-item " /" op-field "), or\n"
                           "  • export OP_SERVICE_ACCOUNT_TOKEN=… for non-interactive/cron use")
                      {:exit 2})))
    s))

(defn pin-cacao
  "Mint a CACAO granting `kotobase:pin` over the tenant DID (derived from the raw
   seed). `now`/`exp` are java.time.Instant; defaults to now … now+365d.
   Returns the cacao.core/mint result {:cacao-b64 :iss :siwe}."
  ([seed-hex] (pin-cacao seed-hex (Instant/now) (.plus (Instant/now) 365 ChronoUnit/DAYS)))
  ([seed-hex ^Instant now ^Instant exp]
   (let [seed (ed/unhex seed-hex)
         tenant (ed/did-key-from-seed seed)]
     (cacao/mint {:seed seed
                  :aud tenant                                 ; tenant-scoped capability
                  :iat (str (.truncatedTo now ChronoUnit/SECONDS))
                  :exp (str (.truncatedTo exp ChronoUnit/SECONDS))
                  :nonce (str "pin-" (.getEpochSecond now))
                  :domain "kotobase.net"
                  :resources [(str "kotoba://can/kotobase:pin")
                              (str "kotoba://graph/" tenant)]}))))

(defn- http-post-json
  "POST JSON via babashka.http-client (bb's GraalVM disallows HttpURLConnection
   setRequestMethod over HTTPS — use the http-client). Never throws on a 4xx/5xx."
  [url headers body]
  (let [r (http/post url {:headers (assoc headers "content-type" "application/json")
                          :body body :throw false :timeout 45000})]
    {:status (:status r) :body (str (:body r))}))

(defn pin!
  "Register `cid` (optionally named) with kotobase.net's Pinning Service via a
   freshly-minted kotobase:pin CACAO. Returns {:status :body :iss}. The tenant seed
   is resolved from env / 1Password (never an argument, never logged)."
  [cid name & {:keys [endpoint] :or {endpoint default-endpoint}}]
  (let [{:keys [cacao-b64 iss]} (pin-cacao (resolve-seed))
        {:keys [authorization x-kotoba-did]} (cacao/auth-header {:cacao-b64 cacao-b64 :iss iss})
        body (str "{\"cid\":\"" cid "\",\"name\":\"" (or name cid) "\"}")
        resp (http-post-json (str (str/replace endpoint #"/+$" "") "/pins")
                             {"authorization" authorization "x-kotoba-did" x-kotoba-did}
                             body)]
    (assoc resp :iss iss)))

(defn -main [& args]
  (let [pos (remove #(str/starts-with? % "--") args)
        cid (first pos) name (second pos)
        ep (when-let [i (some #(when (= "--endpoint" (nth args % nil)) %) (range (count args)))]
             (nth args (inc i) default-endpoint))]
    (when-not cid
      (binding [*out* *err*]
        (println "usage: bb kotobase:pin <cid> [name] [--endpoint <url>]")
        (println "  seed auto-resolved: KOTOBA_SEED_HEX, else 1Password via op (or OP_SERVICE_ACCOUNT_TOKEN)"))
      (System/exit 2))
    (let [{:keys [status body iss]} (pin! cid name :endpoint (or ep default-endpoint))]
      (println (str "tenant " iss))
      (println (str "POST /pins → HTTP " status))
      (println body)
      (when (or (nil? status) (>= status 400)) (System/exit 1)))))
