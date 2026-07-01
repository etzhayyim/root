(ns etzhayyim.observatory-diddoc
  "kotoba-genome W4-live — the first-party did.json generator for observatory actors
  (ADR-2606302205 D4; supersedes the keyless did docs of ADR-2606042330 D3).

  Emits the FIRST-PARTY did:web document: the disclosure fields (isObservatory,
  voiceOf=etzhayyim, isMirror=false, subject), the aozora.app service endpoint, and
  alsoKnownAs the kotoba-rad github.io did:web. When the MEMBER supplies the actor's
  own present-only did:key (sealed in Keychain), the doc gains a verificationMethod
  / authentication / assertionMethod; without it (R0 / agent) the doc carries
  `verificationMethod: []` + `pendingMemberKey: true` — NEVER a server-minted key
  (no-server-key). R0 writes a PREVIEW under 80-data/observatory/diddoc/ (not the
  live public/actor/ did docs) — the member swaps them in at publish time.
  .cljc (JVM/bb/cljs/WASM)."
  (:require [etzhayyim.observatory-registry :as reg]
            [clojure.string :as str]
            [clojure.java.io :as io]
            [cheshire.core :as json]))

(def ^:private ns-glyph
  {"cable" "綿津綱" "station" "綿津綱" "craft" "渡り" "gov" "公" "corp" "兜"})

(defn did-doc
  "First-party did.json map for an observatory actor. :did-key = the actor's own
  did:key (member-sealed) or nil (→ pendingMemberKey; NOT a server key)."
  [{:keys [handle subject glyph ns did-key]}]
  (let [did    (str "did:web:etzhayyim.com:actor:" handle)
        gh-did (str "did:web:etzhayyim.github.io:com-etzhayyim-" handle)]
    (cond-> {"@context" ["https://www.w3.org/ns/did/v1"
                         "https://w3id.org/security/suites/ed25519-2020/v1"]
             "id" did
             "alsoKnownAs" (cond-> [gh-did] did-key (conj did-key))
             "service" [{"id" (str did "#aozora")
                         "type" "AtprotoPersonalDataServer"
                         "serviceEndpoint" "https://aozora.app"}]
             "etzhayyim" {"isObservatory" true "voiceOf" "etzhayyim" "isMirror" false
                          "subject" subject "glyph" glyph "ns" ns
                          "note" "first-party disclosure-honest observatory actor (ADR-2606302205 D4). Speaks AS etzhayyim, never AS the subject; private persons consent-gated."}}
      did-key
      (assoc "verificationMethod"
             [{"id" (str did "#key-1") "type" "Ed25519VerificationKey2020"
               "controller" did
               "publicKeyMultibase" (if (str/starts-with? did-key "did:key:")
                                      (subs did-key (count "did:key:")) did-key)}]
             "authentication" [(str did "#key-1")]
             "assertionMethod" [(str did "#key-1")])

      (nil? did-key)
      (assoc "verificationMethod" []
             "pendingMemberKey" true))))

(defn gen-ns
  "Generate first-party did.json PREVIEWS for a namespace (member keys nil at R0 →
  pendingMemberKey). Writes to <out-dir>/<handle>.did.json. Returns
  {:ns :total :written :out-dir :allFirstParty}."
  [ns & {:keys [limit out-dir keys] :or {limit 25 out-dir "80-data/observatory/diddoc" keys {}}}]
  (let [glyph   (ns-glyph ns)
        entries (reg/entity-entries ns)
        sample  (take limit entries)]
    (doseq [[handle subject] sample]
      (let [doc (did-doc {:handle handle :subject subject :glyph glyph :ns ns
                          :did-key (get keys handle)})
            f (str out-dir "/" handle ".did.json")]
        (io/make-parents f)
        (spit f (json/generate-string doc {:pretty true}))))
    {:ns ns :total (count entries) :written (count sample) :out-dir out-dir
     :allFirstParty (every? (fn [[h _]] (false? (get-in (did-doc {:handle h :ns ns}) ["etzhayyim" "isMirror"]))) sample)}))

(defn- flag [args k default] (or (second (drop-while #(not= % k) args)) default))

(defn -gen
  "bb entrypoint. Args: [--ns small|all|<ns>] [--limit N] [--out DIR].
  Writes first-party did.json previews (pendingMemberKey until the member seals a
  key). NEVER writes live public/actor/ did docs and NEVER mints a key."
  [& args]
  (let [ns-arg (flag args "--ns" "small")
        limit  (Integer/parseInt (str (flag args "--limit" "25")))
        out    (flag args "--out" "80-data/observatory/diddoc")
        nss    (case ns-arg
                 "all" ["cable" "station" "craft" "gov" "corp"]
                 "small" ["cable" "station" "craft"]
                 [ns-arg])
        results (mapv #(gen-ns % :limit limit :out-dir out) nss)]
    (println (format "[observatory-diddoc] wrote %d first-party did.json previews (pendingMemberKey; NO server key, NOT live) → %s"
                     (reduce + (map :written results)) out))
    (doseq [r results]
      (println (format "  %-7s %5d entities → %3d first-party did.json (isMirror=false, voiceOf=etzhayyim)"
                       (:ns r) (:total r) (:written r))))
    results))
