(ns hinagata.methods.esign
  "hinagata 雛形 — electronic-contract bridge: template → esign envelope → signature verify.
  1:1 Clojure port of `methods/esign.py` (ADR-2606111954).

  Turns a published template into a signable contract document and wires it to the EXISTING
  com.etzhayyim.esign.* substrate: the document body is content-addressed (kotoba IPFS CIDv1 +
  SHA-256), the envelope rosters DID signers, each signer authenticates with their OWN WebAuthn
  passkey bound to their DID.

  // no-server-key: read-only — hinagata NEVER holds a signing key. It only (1) renders the
  // document deterministically, (2) constructs the UNSIGNED envelope record, and (3) VERIFIES
  // the structural binding of a signature a member produced client-side (ADR-2605231525).

  G1 — a contract a member chooses to execute is the member's act, never hinagata advice.

  House style: data maps stay string-keyed; Python ':…' keyword strings stay strings; pure fns;
  file/host I/O only behind #?(:clj …). Requires the good cid.cljc sibling for CIDv1/sha256 and
  analyze.cljc only at the CLI edge. The Python `__main__` writer is behind #?(:clj …)."
  (:require [clojure.string :as str]
            [hinagata.methods.cid :as cid]))

(def ^:private HAS-CLAUSE ":has-clause")
(def ^:private cite-kinds #{":cites-statute" ":mandated-by"})

(defn- lstrip-colon
  "str(x).lstrip(':') — drop a single leading ':' from a stringified value."
  [v]
  (let [s (str v)]
    (if (str/starts-with? s ":") (subs s 1) s)))

(defn render-document
  "Deterministically render a template into a contract body (the bytes that get signed).

  Lists, in stable graph order, the template's clauses and the public statute each clause rests
  on, so the signed document carries its statutory provenance. `fields` fills party/term
  placeholders; missing fields render as explicit `[___]` blanks. PUBLIC reference only (G1)."
  ([template-id nodes edges] (render-document template-id nodes edges nil))
  ([template-id nodes edges fields]
   (let [fields (or fields {})
         t (get nodes template-id)]
     (when (or (nil? t) (not= ":template" (get t ":lt/kind")))
       (throw (ex-info (str "not a template: " template-id) {:template template-id})))
     (let [clause-ids (vec (for [e edges
                                 :when (and (= HAS-CLAUSE (get e ":en/kind"))
                                            (= template-id (get e ":en/from")))]
                             (get e ":en/to")))
           cites (reduce (fn [m e]
                           (if (contains? cite-kinds (get e ":en/kind"))
                             (update m (get e ":en/from") (fnil conj []) (get e ":en/to"))
                             m))
                         {} edges)
           L (transient [])
           P (fn [s] (conj! L s))]
       (P (str "# " (get t ":template/title" template-id)))
       (P "")
       (P (str "Language: " (get t ":template/lang" "—") "  ·  "
               "License: " (get t ":template/license" "Apache-2.0") " + etzhayyim Charter Rider  ·  "
               "Version: " (get t ":template/version" "—") "  ·  "
               "Disclosed stance: " (lstrip-colon (get t ":template/stance" "—"))))
       (P "")
       (P (str "> This is a FAIR, openly-licensed template from the hinagata 雛形 commons. It is "
               "NOT legal advice and NOT a substitute for counsel. The parties execute it as "
               "their own act. Each clause cites the public law it rests on, for traceability."))
       (P "")
       (P "## Parties & Terms")
       (doseq [key ["party_a" "party_b" "effective_date" "term" "governing_law" "amount"]]
         (if (contains? fields key)
           (P (str "- " key ": " (get fields key)))
           (P (str "- " key ": [___]"))))
       (P "")
       (P "## Clauses")
       (doseq [[idx cid-id] (map-indexed vector clause-ids)]
         (let [i (inc idx)
               c (get nodes cid-id {})
               role (lstrip-colon (get c ":clause/role" "—"))
               opt (lstrip-colon (get c ":clause/optionality" "—"))]
           (P (str "### " i ". " (get c ":lt/label" cid-id) "  (" role ", " opt ")"))
           (let [st (get cites cid-id [])]
             (when (seq st)
               (let [refs (str/join "; "
                                    (map (fn [s]
                                           (str/trim
                                            (str (get-in nodes [s ":statute/citation"] s) " "
                                                 "(" (get-in nodes [s ":statute/instrument"] "") ")")))
                                         st))]
                 (P (str "_Rests on:_ " refs)))))
           (P "")))
       (P "## Execution")
       (P (str "Executed electronically via the etzhayyim esign substrate "
               "(com.etzhayyim.esign.envelope): each party signs with a WebAuthn passkey bound to "
               "their DID. Electronic execution rests on eIDAS Art. 25 (EU), ESIGN/UETA (US) and "
               "電子署名法 (JP), as cited by the signature clause."))
       (P "")
       (str (str/join "\n" (persistent! L)) "\n")))))

(defn build-envelope
  "Construct the UNSIGNED com.etzhayyim.esign.envelope record for a rendered document.

  The body is content-addressed (CIDv1 raw) and SHA-256 hashed — the two independent integrity
  anchors the lexicon requires. hinagata produces this record; it is signed client-side."
  ([document requester-did signer-dids]
   (build-envelope document requester-did signer-dids {}))
  ([document requester-did signer-dids
    {:keys [subject signing-order created-at]
     :or {subject "" signing-order "parallel" created-at "1970-01-01T00:00:00Z"}}]
   (let [body (cid/bytes-of document)]
     (when (empty? signer-dids)
       (throw (ex-info "at least one signer required" {})))
     (when-not (contains? #{"sequential" "parallel"} signing-order)
       (throw (ex-info (str "signing_order must be sequential|parallel, got " signing-order)
                       {:signing-order signing-order})))
     {"$type" "com.etzhayyim.esign.envelope"
      "requesterDid" requester-did
      "subject" (subs subject 0 (min 256 (count subject)))
      "documentCid" (cid/cidv1-raw body)
      "documentSha256" (cid/sha256-hex body)
      "documentMimeType" "text/markdown"
      "signers" (vec signer-dids)
      "signingOrder" signing-order
      "status" "pending"
      "createdAt" created-at})))

(defn verify-signature
  "Structurally verify a com.etzhayyim.esign.signature against its envelope. Returns
  [ok? reasons]. Checks roster membership, document-hash anti-tamper, accepted WebAuthn algo,
  and assertion presence. CRYPTOGRAPHIC verification is kotoba-auth's job, not here."
  [envelope signature]
  (let [reasons
        (cond-> []
          (not (some #{(get signature "signerDid")} (get envelope "signers" [])))
          (conj "signerDid not in envelope.signers roster")
          (not= (get signature "documentSha256") (get envelope "documentSha256"))
          (conj "documentSha256 mismatch (document tampered between request and sign)")
          (not (contains? #{"ES256" "EdDSA"} (get signature "webauthnAlgorithm")))
          (conj (str "unsupported webauthn algorithm: " (get signature "webauthnAlgorithm")))
          (not (get signature "assertionEnvelope"))
          (conj "missing assertionEnvelope (encrypted WebAuthn assertion)"))]
    [(zero? (count reasons)) reasons]))

(defn check-completion
  "Return a com.etzhayyim.esign.completedEvent iff every roster signer has a VALID signature;
  else nil. For `sequential` order, roster order is enforced by construction."
  ([envelope signatures] (check-completion envelope signatures "1970-01-01T00:00:00Z"))
  ([envelope signatures completed-at]
   (let [signers (get envelope "signers" [])
         valid-by-did (reduce (fn [m sig]
                                (let [[ok _] (verify-signature envelope sig)]
                                  (if ok (assoc m (get sig "signerDid") sig) m)))
                              {} signatures)]
     (if-not (every? #(contains? valid-by-did %) signers)
       nil
       (let [ordered (mapv #(get valid-by-did %) signers)]
         {"$type" "com.etzhayyim.esign.completedEvent"
          "envelopeCid" (get envelope "documentCid")
          "documentCid" (get envelope "documentCid")
          "documentSha256" (get envelope "documentSha256")
          "signatureCount" (count ordered)
          "completedAt" completed-at})))))

#?(:clj
   (defn -main
     "CLI entry: render a template + build an UNSIGNED esign envelope (file I/O at the edge)."
     [& argv]
     (let [argv (vec argv)
           analyze (requiring-resolve 'hinagata.methods.analyze/load-file*)
           here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (clojure.java.io/file (first argv))
                  (clojure.java.io/file here "data" "seed-legal-template-graph.kotoba.edn"))
           idx (fn [flag] (.indexOf argv flag))
           template-id (if (some #{"--template"} argv) (nth argv (inc (idx "--template"))) "tmpl.nda-mutual")
           requester (if (some #{"--requester"} argv) (nth argv (inc (idx "--requester")))
                         "did:web:etzhayyim.com:actor:hinagata")
           signers (->> (map-indexed vector argv)
                        (filter (fn [[_ a]] (= a "--signer")))
                        (mapv (fn [[i _]] (nth argv (inc i)))))
           signers (if (seq signers) signers ["did:plc:alice" "did:plc:bob"])
           outdir (if (some #{"--out"} argv) (clojure.java.io/file (nth argv (inc (idx "--out"))))
                      (clojure.java.io/file here "out"))
           {:keys [nodes edges]} (analyze seed)
           doc (render-document template-id nodes edges)
           env (build-envelope doc requester signers
                               {:subject (get-in nodes [template-id ":template/title"] "")})]
       (.mkdirs outdir)
       (spit (clojure.java.io/file outdir (str "contract-" template-id ".md")) doc)
       (println (str "hinagata esign: " template-id " → " (count (cid/bytes-of doc)) " B"))
       (println (str "  documentCid:    " (get env "documentCid")))
       (println (str "  documentSha256: " (get env "documentSha256")))
       0)))
