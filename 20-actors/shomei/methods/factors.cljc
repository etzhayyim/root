(ns shomei.methods.factors
  "factors.cljc — 証明 (shomei) factor taxonomy + assurance ladder (SSoT). ADR-2606072100.
  1:1 Clojure port of `methods/factors.py`.

  Every external-identity factor maps to exactly one independence CLASS; the Identity
  Assurance Level (IAL) is a pure function of the SET of verified factor classes — never of
  the person (G8). Closed-vocab keys are STRINGS (the Python factorKind/factorClass strings),
  per the root CLAUDE.md convention. Pure fns; closed-vocab violations → ex-info.

  ::order metadata pins FACTOR_CLASS / ALLOWED_PROOFS insertion order so any derived listing
  matches the Python dict-iteration order byte-for-byte (>8 entries)."
  (:require [clojure.string :as str]
            [clojure.set :as set]))

;; factorKind → factorClass (independence class). G8: assurance counts DISTINCT classes,
;; so two key-class wallets (EVM + BTC) raise count but not class-diversity.
(def FACTOR_CLASS
  ^{::order ["webauthn" "wallet-evm" "wallet-btc" "sns-github" "sns-x" "sns-google" "sns-apple"
             "gov-mynumber" "gov-passport" "gov-license"
             "etz-base-membership" "etz-adherent-sbt" "etz-at-oath"]}
  {"webauthn" "device"
   "wallet-evm" "key"
   "wallet-btc" "key"
   "sns-github" "social"
   "sns-x" "social"
   "sns-google" "social"
   "sns-apple" "social"
   "gov-mynumber" "government"
   "gov-passport" "government"
   "gov-license" "government"
   "etz-base-membership" "covenant"
   "etz-adherent-sbt" "covenant"
   "etz-at-oath" "covenant"})

(def CLASSES ["device" "key" "social" "government" "covenant"])

;; factorKind → allowed proofKinds (G4 cryptographic-proof-mandatory).
(def ALLOWED_PROOFS
  ^{::order ["webauthn" "wallet-evm" "wallet-btc" "sns-github" "sns-x" "sns-google" "sns-apple"
             "gov-mynumber" "gov-passport" "gov-license"
             "etz-base-membership" "etz-adherent-sbt" "etz-at-oath"]}
  {"webauthn" #{"webauthn-assertion"}
   "wallet-evm" #{"eip191" "eip1271"}
   "wallet-btc" #{"bip322"}
   "sns-github" #{"oauth-sub" "signed-gist" "dns-txt"}
   "sns-x" #{"oauth-sub"}
   "sns-google" #{"oauth-sub"}
   "sns-apple" #{"oauth-sub"}
   "gov-mynumber" #{"nfc-jpki"}
   "gov-passport" #{"nfc-jpki"}
   "gov-license" #{"nfc-jpki"}
   "etz-base-membership" #{"base-l2-event"}
   "etz-adherent-sbt" #{"erc5192-sbt"}
   "etz-at-oath" #{"at-record-sig"}})

(def FACTOR_KINDS (set (keys FACTOR_CLASS)))
(def PROOF_KINDS (set (mapcat identity (vals ALLOWED_PROOFS))))

;; G3: government factors carry NO plaintext identifier; encryptedPayloadCid is mandatory.
(def GOV_FACTORS (set (for [[k c] FACTOR_CLASS :when (= c "government")] k)))
(def COVENANT_FACTORS (set (for [[k c] FACTOR_CLASS :when (= c "covenant")] k)))
;; Only inherently-public, pseudonymous factors may carry a plaintext externalHandle.
(def PUBLIC_HANDLE_FACTORS
  (set (for [k (keys FACTOR_CLASS)
             :when (or (str/starts-with? k "wallet-") (str/starts-with? k "sns-"))] k)))
;; G11: gov L2 proof is Council-gated (ADR-2605260000); the R0 cell .solve() raises.
(def GATED_PROOFS #{"nfc-jpki"})

(def REVOCATION_REASONS
  #{"key-rotated" "key-lost" "account-closed" "compromised" "superseded" "voluntary"})

(defn factor-class [kind]
  (if-not (contains? FACTOR_CLASS kind)
    (throw (ex-info (str "unknown factorKind: " (pr-str kind)) {:kind kind}))
    (get FACTOR_CLASS kind)))

(defn assurance-level
  "Identity Assurance Level from the SET of verified factor classes + factor count.

  0 did-only · 1 self-attested (≥1 factor) · 2 multi-factor (≥2 factors, ≥2 classes) ·
  3 covenant-bound (IAL2 + a covenant etzhayyim factor) · 4 government-verified
  (a gov factor paired with ≥1 other class; Council-attested, ADR-2605260000)."
  [classes count]
  (let [n (clojure.core/count classes)]
    (cond
      (zero? count) 0
      (and (contains? classes "government") (>= n 2)) 4
      (and (contains? classes "covenant") (>= n 2) (>= count 2)) 3
      (and (>= n 2) (>= count 2)) 2
      :else 1)))

(defn proof-of-personhood
  "Sybil-RESISTANCE (not sybil-proof): ≥2 independent classes. Never a person ranking."
  [level n-classes]
  (and (>= level 2) (>= n-classes 2)))
