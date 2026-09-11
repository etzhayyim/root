(ns etzhayyim.observatory-sign-host
  "Member-owned host wiring for the Observatory signing and publishing CLI."
  (:require [babashka.http-client :as http]
            [etzhayyim.kotoba-rad-sign :as rad-sign]
            [etzhayyim.observatory-sign :as sign]
            [kagi.cacao :as cacao]
            [kagi.identity :as identity]
            [langchain.kotoba-db :as kotoba-db]))

(def capabilities
  {:keychain-read rad-sign/keychain-read
   :public-key-from-private rad-sign/pubkey-hex-from-priv-b64
   :load-identity identity/load-identity
   :mint-cacao cacao/mint
   :kotoba-conn kotoba-db/kotoba-conn
   :kotoba-api kotoba-db/kotoba-api
   :http-request http/request
   :nonce #(str (java.util.UUID/randomUUID))
   :expiry (fn [ttl-seconds]
             (str (.plusSeconds (java.time.Instant/now) (long ttl-seconds))))})

(defn -main [& args]
  (apply sign/sign-and-publish-with capabilities args))
