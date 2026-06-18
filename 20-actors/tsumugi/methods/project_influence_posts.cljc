(ns tsumugi.methods.project-influence-posts
  "tsumugi 紡ぎ — diachronic influence MIRROR posts (observer voice, dry-run).
  Clojure port of methods/project_influence_posts.py (1:1, the pure core). ADR-2606061500.

  Projects a node/flow into an OBSERVER-voice post ABOUT a figure's documented influence —
  N2: only mirrors may be projected, never first-person (impersonation is unrepresentable —
  there is no branch that emits first-person text); G7: published false (dry-run). Depends only
  on the pure analyze_influence loaders (used by main, omitted); the projection itself is pure
  stdlib, no numpy. The numpy spectral analyze_influence stays unported."
  (:require [clojure.string :as str]))

(def KIND-VERB
  {":influences" "shaped" ":transmits" "was transmitted into" ":cites" "is cited by"
   ":reinterprets" "was reinterpreted by" ":synthesizes" "was synthesized into"
   ":translates" "was carried across language into" ":opposes" "was defined against by"})

(defn project-post
  "Project node (optionally via flow) → an observer-voice mirror post. Raises (N2) if the node
  is not a mirror — impersonation is refused."
  [node flow nodes tick]
  (when-not (get node ":mirror/is-mirror")
    (throw (ex-info (str (get node ":organism/id") " is not a mirror — refuse (N2)") {:gate "N2"})))
  (let [disclaimer (get node ":mirror/disclaimer" "観察像 — 本人ではない (observational mirror)")
        label (get node ":organism/label" (get node ":organism/id"))
        [body pid about-flow]
        (if flow
          (let [frm (get (get nodes (get flow ":flow/from")) ":organism/label" (get flow ":flow/from"))
                to (get (get nodes (get flow ":flow/to")) ":organism/label" (get flow ":flow/to"))
                verb (get KIND-VERB (get flow ":flow/kind") "influenced")
                w (double (get flow ":flow/signed-weight" 0.0))]
            [(str "観察: 「" frm "」 " verb " 「" to "」 (documented influence, weight "
                  (format "%+.2f" w) "). An information channel across history, not an endorsement.")
             (str "post." (subs (get flow ":flow/id") 3))
             (get flow ":flow/id")])
          (let [trad (str/join "," (map #(subs % 1) (get node ":hist/tradition" [])))]
            [(str "観察: 「" label "」 — public influence-bearing node ("
                  (subs (get node ":hist/subkind" "?") 1) "; " trad "). "
                  "Mapped for its documented influence on later thought, never adjudicated for truth.")
             (str "post.node." (get node ":organism/id"))
             nil]))]
    (cond-> {":post/id" pid
             ":post/about-node" (get node ":organism/id")
             ":post/voice" ":observer"            ; LOCKED (N2)
             ":post/text" (str disclaimer "\n" body)
             ":post/tick" tick
             ":post/published" false              ; DRY-RUN (G7)
             ":post/sourcing" ":representative"}
      about-flow (assoc ":post/about-flow" about-flow))))

(defn edn-str
  "Serialise a post map to a single-line EDN map (mirror of edn_str)."
  [p]
  (str "{"
       (str/join " "
                 (map (fn [[k v]]
                        (cond
                          (boolean? v) (str k " " (if v "true" "false"))
                          (and (string? v) (str/starts-with? v ":")) (str k " " v)
                          (string? v) (str k " \"" (-> (str v) (str/replace "\\" "\\\\")
                                                       (str/replace "\"" "\\\"") (str/replace "\n" "\\n")) "\"")
                          :else (str k " " v)))
                      p))
       "}"))
