(ns etzhayyim.explorer.agent-test
  "Browser-side verification of a Holochain-iso agent registration: the SAME
   checks /explorer runs — base58 did:key decode, kotoba content-address
   recompute, and Web Crypto Ed25519 self-signature + witness attestation —
   against a real registrar-produced genesis source-chain."
  (:require [cljs.test :refer-macros [deftest is testing async]]
            [cljs.reader :as edn]
            [etzhayyim.explorer.chain.agent :as agent]
            [kotoba.datom :as kd]
            ["fs" :as fs]))

(defn- read-edn [path]
  (binding [edn/*default-data-reader-fn* (atom (fn [_t v] v))]
    (edn/read-string (.readFileSync fs path "utf8"))))

(def doc (read-edn "public/kotoba/agents/busshi.agent.kotoba.edn"))
(def rejected (read-edn "public/kotoba/agents/rogue-sybil-rejected.agent.kotoba.edn"))
(def roster (set (:roster/members (read-edn "public/kotoba/agents/member-roster.kotoba.edn"))))
(def validators (set (map :did (:validators/set (read-edn "public/kotoba/agents/validator-set.kotoba.edn")))))
(def ctx {:roster roster :validators validators})

(deftest did-key-decodes-to-genesis-key
  (testing "base58 did:key → raw 32-byte pubkey == the :actor/genesis-key datom"
    (let [raw (agent/did-key->raw-pub (:agent/did doc))
          ;; the genesis-key datom value is base64(rawpub)
          datoms (get-in doc [:chain 0 :datoms])
          gk-b64 (some (fn [[_ _ a v]] (when (= a ":actor/genesis-key") v)) datoms)
          gk-bytes (let [bin (js/atob gk-b64)]
                     (mapv #(.charCodeAt bin %) (range (.-length bin))))]
      (is (= 32 (.-length raw)))
      (is (= gk-bytes (vec (array-seq raw)))))))

(deftest content-address-recomputes
  (testing "genesis :cid recomputes from its datoms (kotoba commit-DAG)"
    (let [{:keys [datoms cid]} (get-in doc [:chain 0])]
      (is (= cid (kd/tx-cid datoms ""))))))

(deftest validated-agent-passes-membrane-in-browser
  (testing "self-sig + member vouch + validator quorum all verify in-browser"
    (async done
      (-> (agent/verify-doc doc ctx)
          (.then (fn [r]
                   (is (:cid-ok r) "content-address integrity")
                   (when (:crypto? r)        ; node/Chrome with SubtleCrypto Ed25519
                     (is (:self-signed r) "agent self-signature")
                     (is (:vouch-ok r) "SBT member CACAO vouch (Sybil boundary)")
                     (is (get-in r [:quorum :met?]) "validator quorum met"))
                   (done)))
          (.catch (fn [e] (is false (str e)) (done)))))))

(deftest rejected-agent-fails-membrane-in-browser
  (testing "an un-vouched (Sybil) agent does NOT pass the membrane"
    (async done
      (-> (agent/verify-doc rejected ctx)
          (.then (fn [r]
                   (when (:crypto? r)
                     (is (not (:vouch-ok r)) "no valid member vouch")
                     (is (not (get-in r [:quorum :met?])) "quorum not met"))
                   (is (seq (:reasons r)) "carries a warrant reason")
                   (done)))
          (.catch (fn [e] (is false (str e)) (done)))))))
