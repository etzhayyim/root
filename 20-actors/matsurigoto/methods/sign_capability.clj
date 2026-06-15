;; sign_capability.clj — matsurigoto 政 R1.C: the sign / authority layer (verify-only, NO server key).
;;
;; Clojure port of sign_capability.py (ADR-2606062300 + ADR-2605231525), Wave 1 of the clj-native
;; migration (ADR-2606142300). R0 artifacts are unsigned by construction (G1). This layer attaches
;; a signature WITHOUT matsurigoto ever holding a private key: the signature is produced EXTERNALLY
;; by the governing organ —
;;   principal A (:sovereign-governance) : the Council 5-of-7 Safe / 1 SBT=1 vote
;;                                         (did:web:etzhayyim.com:council:*).
;;   principal B (:supplied-to-state)    : the adopting state's OWN key (NOT an etzhayyim did).
;;
;; matsurigoto only (a) emits the canonical payload to be signed and (b) ATTACHES a signature the
;; caller brings back, after checking the signer is legitimate for the principal. It NEVER mints a
;; signature: `signer-held-private-key` is false and `sign-server-side` always RAISES (the
;; okaimono member-principal / server-sig-refused pattern, ADR-2605231525).
;;
;; HONEST R1: verifies STRUCTURE (legitimate signer + payload integrity via sha256). Real
;; ed25519 / Safe-threshold crypto is R2. The payload digest is an INTERNAL integrity hash
;; (deterministic, self-consistent across signing) — not a cross-system content address, so no
;; byte-parity with Python is claimed. stdlib only.
(ns matsurigoto.methods.sign-capability
  (:require [clojure.string :as str])
  (:import [java.security MessageDigest]))

(def signer-held-private-key false)  ; G1 / ADR-2605231525 — matsurigoto holds no private key
(def ^:private council-prefix "did:web:etzhayyim.com:council")
(def ^:private etzhayyim-prefix "did:web:etzhayyim.com")

;; ── canonical JSON (sorted keys, ensure_ascii=False) for the integrity digest ──
(defn- esc [^String s]
  (let [sb (StringBuilder.)]
    (.append sb \")
    (doseq [c s]
      (cond
        (= c \")         (.append sb "\\\"")
        (= c \\)         (.append sb "\\\\")
        (= c \newline)   (.append sb "\\n")
        (= c \return)    (.append sb "\\r")
        (= c \tab)       (.append sb "\\t")
        (< (int c) 0x20) (.append sb (format "\\u%04x" (int c)))
        :else            (.append sb c)))
    (.append sb \")
    (.toString sb)))

(defn- cjson [x]
  (cond
    (map? x)        (str "{"
                         (->> x
                              (sort-by (fn [[k _]] (if (keyword? k) (name k) (str k))))
                              (map (fn [[k v]] (str (esc (if (keyword? k) (name k) (str k))) ":" (cjson v))))
                              (str/join ","))
                         "}")
    (sequential? x) (str "[" (str/join "," (map cjson x)) "]")
    (keyword? x)    (esc (str x))
    (string? x)     (esc x)
    (boolean? x)    (if x "true" "false")
    (integer? x)    (str x)
    (nil? x)        "null"
    :else           (esc (str x))))

(defn- sha256-hex [^String s]
  (apply str (map #(format "%02x" (bit-and (int %) 0xff))
                  (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8")))))

(defn canonical-payload
  "Deterministic content digest (sha256 over canonical JSON) for an artifact or datom batch."
  [obj]
  (sha256-hex (cjson obj)))

(defn- payload
  "Hash the SUBSTANTIVE content only — excluding :proof and the :status lifecycle marker (which
   flips unsigned→signed) so the digest is stable across signing."
  [artifact]
  (canonical-payload (dissoc artifact :proof :status)))

(defn- legitimate-signer?
  "principal A must be signed by an etzhayyim Council organ; principal B by a NON-etzhayyim
   (the adopting state's own) did — etzhayyim never holds the state's key."
  [signer-did authority-mode]
  (let [council? (str/starts-with? (str signer-did) council-prefix)]
    (case authority-mode
      :sovereign-governance council?
      :supplied-to-state    (not (str/starts-with? (str signer-did) etzhayyim-prefix))
      false)))

(defn sign-server-side
  "STRUCTURAL no-server-key: there is no path for matsurigoto to sign. Always raises."
  [& _]
  (throw (ex-info (str "no-server-key (ADR-2605231525): matsurigoto holds no signing key and signs "
                       "nothing. The Council Safe (principal A) or the adopting state (principal B) "
                       "signs externally; use attach-external-proof to attach their signature.")
                  {:no-server-key true})))

(defn attach-external-proof
  "Attach an EXTERNALLY-produced signature to an unsigned artifact. Pure; returns a NEW map. Raises
   if already signed (G1), the signer is illegitimate for the principal, or the signature is empty."
  [artifact {:keys [signer-did authority-mode signature signed-at]}]
  (when (some? (:proof artifact))
    (throw (ex-info "artifact already signed — a module artifact must arrive unsigned (G1)" {})))
  (when (str/blank? (str signature))
    (throw (ex-info "no external signature supplied — matsurigoto mints none (no-server-key)" {})))
  (when-not (legitimate-signer? signer-did authority-mode)
    (throw (ex-info (str "illegitimate signer " (pr-str signer-did) " for " authority-mode) {})))
  (assoc artifact
         :proof {:signer-did     signer-did
                 :authority-mode authority-mode
                 :signature      signature
                 :signed-at      signed-at
                 :payload-sha256 (payload artifact)}
         :status (str/replace (:status artifact) "unsigned" "signed")
         :server-held-authority false))                    ; unchanged — still no operator key

(defn verify-proof
  "Structural verification: a proof is present, by a legitimate signer, over the matching payload.
   (Cryptographic ed25519 / Safe-threshold check is R2.)"
  [signed-artifact]
  (let [proof (:proof signed-artifact)]
    (boolean
     (and proof
          (not (str/blank? (str (:signature proof))))
          (legitimate-signer? (:signer-did proof) (:authority-mode proof))
          (= (:payload-sha256 proof) (payload signed-artifact))))))
