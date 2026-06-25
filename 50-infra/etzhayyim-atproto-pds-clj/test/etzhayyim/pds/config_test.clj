(ns etzhayyim.pds.config-test
  "Invariants for the PDS identity/config: did:web document + describeServer.
  Assertions cross-check against the derived cfg vars (host/pds-did/user-domains)
  so they hold regardless of the env-overridable host."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [etzhayyim.pds.config :as cfg]))

(deftest identity-derivation
  (is (= (str "did:web:" cfg/host) cfg/pds-did))
  (testing "every user-domain is etzhayyim, never gftd"
    (is (seq cfg/user-domains))
    (is (every? #(not (str/includes? % "gftd")) cfg/user-domains))))

(deftest did-document-shape
  (let [doc (cfg/did-document)]
    (is (= cfg/pds-did (get doc "id")))
    (is (some #{"https://www.w3.org/ns/did/v1"} (get doc "@context")))
    (is (= [(str "https://" cfg/host)] (get doc "alsoKnownAs")))
    (testing "the atproto_pds service points at this host (etzhayyim-owned)"
      (let [svc (->> (get doc "service") (filter #(= "#atproto_pds" (get % "id"))) first)]
        (is (= "AtprotoPersonalDataServer" (get svc "type")))
        (is (= (str "https://" cfg/host) (get svc "serviceEndpoint")))))
    (testing "no service endpoint points at gftd"
      (is (not-any? #(str/includes? (str (get % "serviceEndpoint")) "gftd")
                    (get doc "service"))))))

(deftest describe-server-payload
  (let [s (cfg/describe-server)]
    (is (= cfg/pds-did (get s "did")))
    (is (= cfg/user-domains (get s "availableUserDomains")))
    (is (false? (get s "inviteCodeRequired")))
    (is (false? (get s "phoneVerificationRequired")))
    (is (string? (get-in s ["links" "privacyPolicy"])))
    (is (string? (get-in s ["contact" "email"])))))

(deftest revoked-jtis-defaults-empty
  (testing "with no revocation file present, revoked-jtis is the empty set (no revocations)"
    ;; the default file name is unlikely to exist in the test sandbox
    (is (set? (cfg/revoked-jtis)))
    (is (empty? (cfg/revoked-jtis)))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.pds.config-test)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
