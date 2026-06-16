(ns matsurigoto.methods.sign-capability
  "sign_capability.py — matsurigoto 政 R1.C: the sign / authority layer (verify-only, NO key).
  1:1 Clojure port of `methods/sign_capability.py` (ADR-2606062300 + 2605231525).

  R0 artifacts are unsigned by construction (G1). This layer attaches a signature WITHOUT
  matsurigoto ever holding a private key: the signature is produced EXTERNALLY by the governing
  organ —
    principal A (:sovereign-governance) : the Council Safe (did:web:etzhayyim.com:council:*).
    principal B (:supplied-to-state)    : the adopting state's OWN key (NOT an etzhayyim did).

  matsurigoto only (a) emits the canonical payload to be signed and (b) ATTACHES a signature
  the caller brings back, after checking the signer is a legitimate authority. It NEVER mints a
  signature. SIGNER-HELD-PRIVATE-KEY = false; `sign-server-side` always RAISES.

  HONEST R1: this verifies STRUCTURE (legitimate signer + payload integrity via sha256). Real
  ed25519 / Safe-threshold verification is R2.

  House style: data maps stay string-keyed; pure fns; canonical JSON + sha256 inlined (no
  dependency). sha256 / I/O behind #?(:clj ...). The Python __main__ demo is omitted."
  (:require [clojure.string :as str]))

(def SIGNER-HELD-PRIVATE-KEY false)  ; G1 / ADR-2605231525 — matsurigoto holds no private key

(def ^:private etzhayyim-council-prefix "did:web:etzhayyim.com:council")

;; ── sha-256 ──
(defn- sha256-hex
  "String → lowercase hex sha-256 digest (UTF-8)."
  [s]
  #?(:clj (let [d (.digest (java.security.MessageDigest/getInstance "SHA-256")
                           (.getBytes ^String s "UTF-8"))]
            (apply str (map #(format "%02x" (bit-and % 0xff)) d)))
     :default (throw (ex-info "bind a sha-256 impl on this host" {}))))

;; ── canonical JSON: json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",",":")) ──
(defn- json-escape-utf8 [s]
  (str/escape s {\" "\\\"" \\ "\\\\"
                 \backspace "\\b" \tab "\\t" \newline "\\n" \formfeed "\\f" \return "\\r"}))

(defn- canonical-json [v]
  (cond
    (string? v)     (str "\"" (json-escape-utf8 v) "\"")
    (boolean? v)    (if v "true" "false")
    (nil? v)        "null"
    (integer? v)    (str v)
    (number? v)     (str v)
    (map? v)        (str "{" (str/join "," (map (fn [k] (str "\"" (json-escape-utf8 (str k)) "\":"
                                                             (canonical-json (get v k))))
                                                (sort (keys v)))) "}")
    (sequential? v) (str "[" (str/join "," (map canonical-json v)) "]")
    :else (throw (ex-info "canonical-json: unsupported value" {:value v}))))

(defn canonical-payload
  "Deterministic sha256 over canonical JSON of an artifact or datom batch."
  [obj]
  (sha256-hex (canonical-json obj)))

(defn- payload
  "Hash the SUBSTANTIVE content only — excluding `proof` and the `status` lifecycle marker."
  [artifact]
  (canonical-payload (into {} (remove (fn [[k _]] (contains? #{"proof" "status"} k)) artifact))))

(defn- legitimate-signer?
  "principal A must be signed by an etzhayyim Council organ; principal B by a NON-etzhayyim did."
  [signer-did authority-mode]
  (let [is-council (str/starts-with? signer-did etzhayyim-council-prefix)]
    (cond
      (= authority-mode ":sovereign-governance") is-council
      (= authority-mode ":supplied-to-state") (not (str/starts-with? signer-did "did:web:etzhayyim.com"))
      :else false)))

(defn sign-server-side
  "STRUCTURAL no-server-key: there is no path for matsurigoto to sign. Always raises."
  [& _]
  (throw (ex-info (str "no-server-key (ADR-2605231525): matsurigoto holds no signing key and "
                       "signs nothing. The Council Safe (principal A) or the adopting state "
                       "(principal B) signs externally; use attach-external-proof() to attach "
                       "their signature.")
                  {})))

(defn attach-external-proof
  "Attach an EXTERNALLY-produced signature to an unsigned artifact. Pure; returns a NEW map.

  Raises if the artifact is already signed, the signer is illegitimate, or the signature empty."
  [artifact signer-did authority-mode signature signed-at]
  (when (some? (get artifact "proof"))
    (throw (ex-info "artifact already signed — a module artifact must arrive unsigned (G1)" {})))
  (when-not (and signature (not= signature ""))
    (throw (ex-info "no external signature supplied — matsurigoto mints none (no-server-key)" {})))
  (when-not (legitimate-signer? signer-did authority-mode)
    (throw (ex-info (str "illegitimate signer " (pr-str signer-did) " for " authority-mode) {})))
  (-> artifact
      (assoc "proof" {"signer_did" signer-did
                      "authority_mode" authority-mode
                      "signature" signature
                      "signed_at" signed-at
                      "payload_sha256" (payload artifact)})
      (assoc "status" (str/replace (get artifact "status") "unsigned" "signed"))
      (assoc "server_held_authority" false)))  ; unchanged — still no operator key

(defn verify-proof
  "Structural verification: a proof present, by a legitimate signer, over the matching payload."
  [signed-artifact]
  (let [proof (get signed-artifact "proof")]
    (if (or (not proof) (not (get proof "signature")))
      false
      (if-not (legitimate-signer? (get proof "signer_did") (get proof "authority_mode"))
        false
        (= (get proof "payload_sha256") (payload signed-artifact))))))
