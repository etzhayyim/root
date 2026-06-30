(ns kanmon.cells.social-post.state-machine
  "Phase state machine for the 関門 (kanmon) social_post cell — the publication membrane
  that lets the actor self-publish its 入試 OPENING map + leverage digest to the mesh/AT-proto
  WITHOUT a server-held key. ADR-2606272355 (self-publication seed) + ADR-2606281500
  (seed-and-grow doctrine).

  Mirror of the danjo/keizu accountability membranes, adapted to kanmon's OPENING-map posture.
  A record (an exam OPENING observation or a leverage digest) enters; it is DRAFTED into a
  dry-run post ONLY if:

    G-source     — ≥2 public ministry/test-body primary citations are present;
    G-mirror     — the post is a non-adjudicating OPENING map (isMirror); it narrates the gate
                   STRUCTURE, never ranks/scores a student (the content-scan rail rejects
                   偏差値/序列/合否予測/person-targeting);
    no-server-key— server-held-key is false (the actor self-signs in its mesh runtime under a
                   revocable member CACAO leash; the server never does, ADR-2605231525);
    R0-gate      — status is dry-run; a 'published' request REFUSES (live broadcast is the
                   seed-and-grow GROWTH step on the mesh, §1.12 / G-leash).

  Self-contained. Stdlib only. Deterministic — the seed grows on the mesh, not here."
  (:require [clojure.string :as str]))

(def disclaimer
  "【観測ミラー / 入試 OPENING map — NOT a ranking, NOT exam-prep, 非断定】")

(def phase-init "init")
(def phase-drafted "drafted")
(def phase-refused "refused")

(def state-defaults
  {"phase"            phase-init
   "subject"          ""
   "sources"          []
   "requested_status" "dry-run"
   "server_held_key"  false
   "payload"          {}
   "refusal"          ""})

;; content-scan rail (kanmon negative space — no ranking / prediction / person-targeting)
(def ^:private forbidden
  ["偏差値" "序列" "ランキング" "合否予測" "合格判定" "rank students" "pass-prediction" "個人を特定"])

(defn- content-hit [text]
  (first (filter #(str/includes? (str text) %) forbidden)))

(defn- cell-state [state]
  (merge state-defaults (get state "cell_state" {})))

(defn- lstrip-colon [s] (str/replace (str s) #"^:+" ""))

(defn transition-to-drafted
  "Drive one record toward a dry-run post payload, or refuse with the failed invariant.
  Pure: (state) -> {\"cell_state\" {…}}."
  [state]
  (let [cs0 (cell-state state)
        cs  (assoc cs0
                   "subject"          (get state "subject" (get cs0 "subject"))
                   "sources"          (get state "sources" (get cs0 "sources"))
                   "requested_status" (lstrip-colon (get state "requested_status" (get cs0 "requested_status")))
                   "server_held_key"  (boolean (get state "server_held_key" (get cs0 "server_held_key"))))
        refuse (fn [msg] {"cell_state" (assoc cs "refusal" msg "phase" phase-refused)})]
    (cond
      (< (count (get cs "sources")) 2)
      (refuse "G-source: a post needs ≥2 public ministry/test-body primary citations")

      (get cs "server_held_key")
      (refuse "no-server-key: server-held-key must be false; the actor self-signs in its mesh runtime (ADR-2605231525)")

      (not= (get cs "requested_status") "dry-run")
      (refuse "R0-gate: only dry-run posts; live broadcast is the seed-and-grow GROWTH step on the mesh (§1.12/G-leash)")

      (content-hit (get cs "subject"))
      (refuse (str "content-scan: non-emittable (kanmon negative space — no ranking/prediction/person): "
                   (content-hit (get cs "subject"))))

      :else
      (let [payload {":post/subject" (get cs "subject")
                     ":post/body" (str disclaimer " " (get cs "subject"))
                     ":post/status" ":dry-run"
                     ":post/is-mirror" true
                     ":post/non-adjudicating-notice" true
                     ":post/server-held-key" false
                     ":post/sources" (get cs "sources")}]
        {"cell_state" (assoc cs "payload" payload "refusal" "" "phase" phase-drafted)}))))
