;; etzhayyim.kotobase-pin — register a CID with kotobase.net's IPFS Pinning Service
;; using a self-sovereign CACAO, in pure clj. The clj replacement for the earlier
;; throwaway node script (ADR-2606111330): now that com-junkawasaki/ed25519-clj can
;; derive a pubkey/did:key from a raw seed and com-junkawasaki/cacao-clj mints the
;; CAIP-122 CACAO, the whole pin path is clj — no node, no held key.
;;
;; The tenant seed is read from the ENVIRONMENT (KOTOBA_SEED_HEX), minted into a
;; `kotobase:pin` CACAO in-process, and presented as `Authorization: CACAO …` —
;; no platform-held signing key (no-server-key, ADR-2605231525).
;;
;; Usage:
;;   KOTOBA_SEED_HEX=<64hex> bb kotobase:pin <cid> [name] [--endpoint https://kotobase.net]
(ns etzhayyim.kotobase-pin
  (:require [clojure.string :as str]
            [ed25519.core :as ed]
            [cacao.core :as cacao])
  (:import (java.net URL)
           (java.time Instant)
           (java.time.temporal ChronoUnit)))

(def default-endpoint "https://kotobase.net")

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

(defn- http-post-json [^String url headers ^String body]
  (let [conn (doto (.openConnection (URL. url))
               (.setRequestMethod "POST")
               (.setDoOutput true)
               (.setConnectTimeout 15000)
               (.setReadTimeout 30000)
               (.setRequestProperty "content-type" "application/json"))]
    (doseq [[k v] headers] (.setRequestProperty conn k v))
    (.connect conn)
    (with-open [os (.getOutputStream conn)] (.write os (.getBytes body "UTF-8")))
    (let [code (.getResponseCode conn)
          stream (if (>= code 400) (.getErrorStream conn) (.getInputStream conn))
          text (if stream (slurp stream) "")]
      {:status code :body text})))

(defn pin!
  "Register `cid` (optionally named) with kotobase.net's Pinning Service via a
   freshly-minted kotobase:pin CACAO. Returns {:status :body :iss}. Reads the
   tenant seed from env KOTOBA_SEED_HEX (never an argument, never logged)."
  [cid name & {:keys [endpoint] :or {endpoint default-endpoint}}]
  (let [seed-hex (System/getenv "KOTOBA_SEED_HEX")]
    (when-not (and seed-hex (re-matches #"[0-9a-fA-F]{64}" seed-hex))
      (throw (ex-info "set KOTOBA_SEED_HEX to the 64-hex tenant seed (read from your own vault)" {})))
    (let [{:keys [cacao-b64 iss]} (pin-cacao seed-hex)
          {:keys [authorization x-kotoba-did]} (cacao/auth-header {:cacao-b64 cacao-b64 :iss iss})
          body (str "{\"cid\":\"" cid "\",\"name\":\"" (or name cid) "\"}")
          resp (http-post-json (str (str/replace endpoint #"/+$" "") "/pins")
                               {"authorization" authorization "x-kotoba-did" x-kotoba-did}
                               body)]
      (assoc resp :iss iss))))

(defn -main [& args]
  (let [pos (remove #(str/starts-with? % "--") args)
        cid (first pos) name (second pos)
        ep (when-let [i (some #(when (= "--endpoint" (nth args % nil)) %) (range (count args)))]
             (nth args (inc i) default-endpoint))]
    (when-not cid
      (binding [*out* *err*]
        (println "usage: KOTOBA_SEED_HEX=<64hex> bb kotobase:pin <cid> [name] [--endpoint <url>]"))
      (System/exit 2))
    (let [{:keys [status body iss]} (pin! cid name :endpoint (or ep default-endpoint))]
      (println (str "tenant " iss))
      (println (str "POST /pins → HTTP " status))
      (println body)
      (when (>= status 400) (System/exit 1)))))
