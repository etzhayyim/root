(ns etzhayyim.kotobase-pin-test
  "Network-free: the kotobase:pin CACAO is well-formed + self-verifies. The HTTP
   leg (pin!) is exercised live by the operator, not here."
  (:require [clojure.test :refer [deftest is]]
            [etzhayyim.kotobase-pin :as kp]
            [cacao.core :as cacao]
            [ed25519.core :as ed])
  (:import (java.security KeyPairGenerator)))

(defn- seed-hex []
  (ed/hexify (byte-array (take-last 32 (seq (.getEncoded (.getPrivate
              (.generateKeyPair (KeyPairGenerator/getInstance "Ed25519")))))))))

(deftest pin-cacao-is-valid-and-scoped
  (let [sh (seed-hex)
        {:keys [cacao-b64 iss] :as minted} (kp/pin-cacao sh)
        v (cacao/verify cacao-b64)]
    (is (= iss (ed/did-key-from-seed-hex sh)) "issuer = the tenant did:key from the seed")
    (is (true? (:valid? v)) "self-signed CACAO verifies under its issuer")
    (is (= iss (:iss v)))
    (is (some #(= "kotoba://can/kotobase:pin" %) (:resources (:payload v)))
        "grants the kotobase:pin capability")
    (is (some #(= (str "kotoba://graph/" iss) %) (:resources (:payload v)))
        "scoped over the tenant DID")
    (is (= {:authorization (str "CACAO " cacao-b64) :x-kotoba-did iss}
           (cacao/auth-header minted)))))
