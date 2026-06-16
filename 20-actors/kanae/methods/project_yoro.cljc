(ns kanae.methods.project-yoro
  "project_yoro.py — project kanae fundFlowEdge records into yoro `:yoro.fiscal/*` datoms.
  1:1 Clojure port of `methods/project_yoro.py`.

  The yoro Resource Flow tab reads `:yoro.fiscal/*` + `:yoro.ownership/*` datoms from the kotoba
  Datom log. This projector is the kanae→yoro bridge: it maps each fundFlowEdge endpoint (an
  aggregate fiscal-authority / recipient-class label) to a stable government mirror-actor DID
  (`did:web:etzhayyim.com:actor:<handle>`, entity-as-actor ADR-2606042330) and emits the
  {e,a,v_edn,added} datoms the tab consumes.

  OFFLINE / representative by construction: writes into the same-origin seed snapshot, NOT a live
  published block. Live publication is kanae G7/G11 + Council-gated (no live publish here).

  House style: ':…' keyword strings stay strings; pure projection; file I/O only at the
  merge-into-seed edge (#?(:clj)). Deterministic: same edges → same datoms. v_edn mirrors Python
  `json.dumps(value, ensure_ascii=False)` so danjo.methods.analyze/parse-json round-trips it."
  (:require [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])
            [danjo.methods.budget-ledger :as bl]))

;; ── json.dumps(value, ensure_ascii=False, separators=(",",":")) parity ───────
(defn- json-escape-utf8 ^String [^String s]
  (str/escape s {\" "\\\"" \\ "\\\\"
                 \backspace "\\b" \tab "\\t" \newline "\\n" \formfeed "\\f" \return "\\r"}))

(defn- json-dumps
  "Compact JSON, ensure_ascii=False (raw unicode), dict order preserved (no sort_keys)."
  ^String [v]
  (cond
    (string? v)     (str "\"" (json-escape-utf8 v) "\"")
    (boolean? v)    (if v "true" "false")
    (nil? v)        "null"
    (integer? v)    (str v)
    (number? v)     (str v)
    (map? v)        (str "{" (str/join "," (map (fn [[k val]]
                                                  (str (json-dumps (str k)) ":" (json-dumps val)))
                                                v)) "}")
    (sequential? v) (str "[" (str/join "," (map json-dumps v)) "]")
    :else           (str "\"" (json-escape-utf8 (str v)) "\"")))

;; Endpoint label → (yoro mirror-actor handle, stage tier). Aggregate gov nodes only (G10).
(def ^:private label-did
  [[#"一般会計|National Treasury|General Account" "kokko" "L7"]
   [#"文部科学省|Ministry of Education" "gov-jp-mext" "L5"]
   [#"国立大学法人" "gov-jp-mext-univ-grants" "L1"]
   [#"科学技術振興" "gov-jp-mext-sci-tech" "L1"]])

(def ^:private actor-prefix "did:web:etzhayyim.com:actor:")

;; Minimal profile records so the projected gov nodes resolve as actors on /search + /profile.
(def ^:private profiles
  {"gov-jp-mext"
   {"handle"      "gov-jp-mext.etzhayyim.com"
    "displayName" "文部科学省 (MEXT) — gov mirror"
    "description" "Government mirror-actor (observational, ADR-2606042330). 文教及び科学振興費 fiscal flow assembled by kanae from danjo budget ledger (:representative)."}})

(defn- slug-did [label]
  (or (some (fn [[pat handle _stage]] (when (re-find pat label) (str actor-prefix handle))) label-did)
      ;; fallback: deterministic slug from the label  (re.sub(r"[^a-z0-9]+","-",lower).strip("-")[:32] or "gov-unknown")
      (let [slug0 (-> (str/lower-case label) (str/replace #"[^a-z0-9]+" "-"))
            slug1 (-> slug0 (str/replace #"^-+" "") (str/replace #"-+$" ""))
            slug2 (subs slug1 0 (min 32 (count slug1)))
            slug  (if (= "" slug2) "gov-unknown" slug2)]
        (str actor-prefix "gov-jp-" slug))))

(defn- stage-for [label]
  (or (some (fn [[pat _handle stage]] (when (re-find pat label) stage)) label-did)
      "L5"))

(defn- datom [e a value]
  {"e" e "a" a "v_edn" (json-dumps value) "added" true})

(defn- parse-fy [period]
  (let [t (str/replace (or period "") "FY" "")]
    (if (= "" t)
      0
      #?(:clj (Long/parseLong t) :cljs (js/parseInt t 10)))))

(defn- profile-datoms
  "For each endpoint label that has a defined profile (and not yet seen), emit its
  minimal `:yoro.profile/*` datoms. Returns [datoms seen]."
  [datoms seen labels]
  (reduce
   (fn [[datoms seen] label]
     (let [did    (slug-did label)
           handle (subs did (count actor-prefix))
           prof   (get profiles handle)]
       (if (and prof (not (contains? seen did)))
         (let [pe (str "profile:" did)]
           [(into datoms [(datom pe ":yoro.profile/did" did)
                          (datom pe ":yoro.profile/handle" (get prof "handle"))
                          (datom pe ":yoro.profile/displayName" (get prof "displayName"))
                          (datom pe ":yoro.profile/description" (get prof "description"))])
            (conj seen did)])
         [datoms seen])))
   [datoms seen]
   labels))

(defn project
  "fundFlowEdge list → `:yoro.fiscal/*` (+ minimal `:yoro.profile/*`) datoms."
  [edges]
  (:datoms
   (reduce
    (fn [{:keys [datoms seen]} edge]
      (let [from-label (get-in edge ["fromEndpoint" "label"])
            to-label   (get-in edge ["toEndpoint" "label"])
            from-did   (slug-did from-label)
            to-did     (slug-did to-label)
            fy         (parse-fy (get edge "period"))
            stage      (stage-for from-label)
            e          (str "fiscal:" from-did ":" to-did ":" fy ":" (get edge "flowClass"))
            datoms (into datoms
                         [(datom e ":yoro.fiscal/from" from-did)
                          (datom e ":yoro.fiscal/to" to-did)
                          (datom e ":yoro.fiscal/stage" stage)
                          (datom e ":yoro.fiscal/fiscalYear" fy)
                          (datom e ":yoro.fiscal/amountJpy"
                                 #?(:clj (Long/parseLong (get edge "amount"))
                                    :cljs (js/parseInt (get edge "amount") 10)))
                          (datom e ":yoro.fiscal/basis"
                                 (str (get edge "flowClass") " · " (get edge "_programCode" "")
                                      " (kanae assembled, :representative)"))
                          (datom e ":yoro.fiscal/programCode" (get edge "_programCode" ""))
                          (datom e ":yoro.fiscal/sourceUrl" (get edge "_sourceUrl" ""))
                          (datom e ":yoro.fiscal/observedAt" (get edge "observedAt" ""))])
            [datoms seen] (profile-datoms datoms seen [from-label to-label])]
        {:datoms datoms :seen seen}))
    {:datoms [] :seen #{}}
    edges)))

#?(:clj
   (defn merge-into-seed
     "Idempotently merge projected datoms into the yoro seed snapshot.

     Removes any prior entities this projector owns (by entity id) before adding, so re-runs
     don't duplicate. The hand-authored ooyake demo seed (different entity ids) is untouched."
     [seed-path datoms]
     (let [seed    (bl/load-json seed-path)
           owned   (set (map #(get % "e") datoms))
           before  (count seed)
           kept    (vec (remove #(contains? owned (get % "e")) seed))
           removed (- before (count kept))
           merged  (into kept datoms)]
       (spit (io/file seed-path) (json-dumps merged))
       {"removed" removed "added" (count datoms) "total" (count merged)})))
