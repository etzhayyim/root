;; etzhayyim.test-sops-age — secrets-layer invariants (ADR-2606241500).
;; Run: bb test:sops-age
;;
;; Hermetic: uses real age/sops binaries but NEVER touches the macOS Keychain —
;; the recipient is recorded on a throwaway identity journal and decryption uses
;; an explicit secret (decrypt-with-secret), so CI / any machine runs it green.

(ns etzhayyim.test-sops-age
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [etzhayyim.sops-age :as sops]
            [etzhayyim.kotoba-rad :as rad]
            [etzhayyim.kotoba.log :as log]
            [etzhayyim.kotoba.datom :as d]))

(deftest recipient-derivation
  (testing "age-keygen → secret + recipient; recipient re-derives from the secret"
    (let [{:keys [secret recipient]} (sops/gen-key)]
      (is (str/starts-with? secret "AGE-SECRET-KEY-"))
      (is (str/starts-with? recipient "age1"))
      (is (= recipient (sops/recipient-of-secret secret))
          "recipient is a deterministic function of the secret"))))

(deftest enc-path-mapping
  (is (= "20-actors/cargo/secrets/db.enc.env"
         (sops/enc-path "20-actors/cargo/secrets/db.env")))
  (is (= "x.enc.yaml" (sops/enc-path "x.yaml")))
  (is (= "noext.enc" (sops/enc-path "noext"))))

(def ^:private test-actor "__test_sops_age__")

(defn- g [recipient]
  (rad/genesis-block
   {:name test-actor :did-web (str "did:web:etzhayyim.github.io:com-etzhayyim-" test-actor)
    :delegates [] :threshold 1
    :repo (str "github.com/etzhayyim/com-etzhayyim-" test-actor)
    :pds "https://pds.aozora.app" :collection "com.etzhayyim.apps.test"}))

(deftest record-recipient-binds-to-rid-and-is-idempotent
  (let [path (rad/journal-path test-actor)]
    (io/delete-file path true)
    (try
      (let [{:keys [recipient]} (sops/gen-key)
            genesis (g recipient)
            r1 (sops/record-recipient! test-actor genesis recipient)
            r2 (sops/record-recipient! test-actor genesis recipient)]
        (is (= 1 (:appended r1)) "first record appends one datom")
        (is (= 0 (:appended r2)) "idempotent: same recipient not re-appended")
        (is (= (rad/rid genesis) (:rid r1)) "recipient datom entity = the RID")
        (is (= recipient (sops/journal-recipient test-actor))
            "journal is the SoT for the recipient")
        (testing "the recipient datom is on the sovereign identity log under :rad/age-recipient"
          (let [live (d/live-datoms (log/read-log path))]
            (is (contains? live [(rad/rid genesis) :rad/age-recipient recipient])))))
      (finally (io/delete-file path true)))))

(deftest sops-yaml-render
  (let [txt (sops/sops-yaml-text [["cargo" "age1cargoRECIP"]] "age1ORGrecip")]
    (is (str/includes? txt "path_regex: ^20-actors/cargo/secrets/.*\\.enc\\."))
    (is (str/includes? txt "age1cargoRECIP"))
    (is (str/includes? txt "age1ORGrecip"))
    (testing "per-actor rule lists both the actor key and the org recovery key"
      (is (str/includes? txt "          - age1cargoRECIP\n          - age1ORGrecip\n")))
    (testing "an org-wide fallback rule catches any other *.enc.* path"
      (is (str/includes? txt "path_regex: \\.enc\\.")))))

(deftest roundtrip-and-redaction
  (testing "encrypt → ciphertext hides the secret value → decrypt restores it"
    (let [jpath (rad/journal-path test-actor)
          tmpdir (str (System/getProperty "java.io.tmpdir") "/etzhayyim-sops-test")
          plain (str tmpdir "/db.env")
          cipher (sops/enc-path plain)
          marker "S3CR3T-pAssw0rd-do-not-leak"]
      (io/delete-file jpath true)
      (.mkdirs (io/file tmpdir))
      (try
        (let [{:keys [secret recipient]} (sops/gen-key)]
          ;; bind the recipient to the (throwaway) identity so recipients-for works
          (sops/record-recipient! test-actor (g recipient) recipient)
          (spit plain (str "DB_PASSWORD=" marker "\nAPI_HOST=example.com\n"))
          (let [r (sops/encrypt-file! test-actor plain cipher)
                ct (slurp cipher)]
            (is (= cipher (:out r)))
            (is (some #{recipient} (:recipients r)) "encrypted to the actor recipient")
            (testing "REDACTION: the plaintext secret never appears in the committed ciphertext"
              (is (not (str/includes? ct marker)))
              (is (str/includes? ct "sops") "ciphertext is a sops envelope")
              (testing "structured: non-secret KEYS stay visible (dotenv), VALUES encrypted"
                (is (str/includes? ct "DB_PASSWORD"))
                (is (str/includes? ct "ENC["))))
            (testing "decrypt with the age secret restores the exact plaintext"
              (let [pt (sops/decrypt-with-secret secret cipher)]
                (is (str/includes? pt (str "DB_PASSWORD=" marker)))
                (is (str/includes? pt "API_HOST=example.com"))))
            (testing "a WRONG key cannot decrypt"
              (let [{other :secret} (sops/gen-key)]
                (is (thrown? Exception (sops/decrypt-with-secret other cipher)))))))
        (finally
          (io/delete-file jpath true)
          (io/delete-file plain true)
          (io/delete-file cipher true))))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-sops-age)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
