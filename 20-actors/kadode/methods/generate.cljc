(ns kadode.methods.generate
  "kadode 門出 — resignation-document generator + 使者 relay builder (UPL-guarded).
  1:1 Clojure port of `methods/generate.py` (ADR-2606112238).

  Renders the worker's OWN resignation documents (退職届 / 退職願 / 即時退職通知 / 内容証明 /
  有給取得届) deterministically and content-addresses them (kotoba IPFS CIDv1 + SHA-256), and —
  for non-negotiating scenarios only — builds a 使者 RELAY record that conveys the worker's
  already-formed unilateral resignation to the employer.

  // no-server-key: read-only — kadode holds no key and SENDS nothing here. It drafts the
  // worker's document and builds an UNSENT relay record; actually transmitting it
  // (email/内容証明/郵送) is a G7-gated outward action requiring the worker's consent +
  // operator/Council step.

  CONSTITUTIONAL (the defining boundary):
    G1 — 使者 not 代理人. The generated 退職届 states only \"一身上の都合により\" (personal reasons);
      it NEVER contains a demand, a negotiation, a severance figure, or a settlement (those are
      法律事務 reserved to lawyers, 弁護士法72条). build-relay REFUSES any scenario that needs
      negotiation and returns the escalation route (union/lawyer) instead. assert-no-negotiation
      rejects negotiation/demand text injected into a free-text field.
    G2 — worker-authored. Missing fields render as explicit blanks (［　　］), never invented.
    N3 — non-adjudicating. The document cites its statutory basis (民法627 / 628) as a disclosed
      fact; it never asserts the resignation's enforceability or promises an outcome.

  Reuses kadode.methods.analyze (recommend-route / negotiating-actors) + kadode.methods.cid
  (cidv1-raw / sha256-hex). House style: Python ':…' keyword strings stay strings; string-keyed
  data; pure fns. Portable .cljc."
  (:require [clojure.string :as str]
            [kadode.methods.analyze :as analyze]
            [kadode.methods.cid :as cid]))

;; negotiation / demand language that must NEVER enter a kadode-drafted resignation (G1).
;; Their presence means the matter is 法律事務 → route to a lawyer / union, not a 使者 relay.
(def prohibited-negotiation
  ["示談" "和解金" "解決金" "慰謝料" "損害賠償を請求" "賠償を求め" "減額交渉"
   "退職金を増" "条件交渉" "交渉して" "請求します" "支払えと" "値引き"])

(defn assert-no-negotiation
  "Reject any negotiation/demand language in a worker-supplied free-text field (G1)."
  [text]
  (let [t (or text "")
        hits (filterv #(str/includes? t %) prohibited-negotiation)]
    (when (seq hits)
      (throw (ex-info
              (str "G1 (弁護士法72条): negotiation/demand language is out of scope for a kadode "
                   "document — " hits ". This matter needs a labour union (団体交渉) or a lawyer; "
                   "kadode relays only a unilateral resignation.")
              {:hits hits})))))

(defn- f-field
  "Port of _f: fields.get(key); str(v) when present and non-empty, else the blank ［　　］."
  [fields key]
  (let [v (get fields key)]
    (if (or (nil? v) (= v "")) "［　　］" (str v))))

(def ^:private head-by-kind
  {"taishoku-todoke" "退職届"
   "taishoku-gan" "退職願"
   "sokuji" "退職届（即時退職）"
   "naiyo-shomei" "退職通知書（内容証明）"
   "yukyu" "年次有給休暇取得届"})

(defn render
  "Render a resignation document. `kind` ∈ taishoku-todoke|taishoku-gan|sokuji|naiyo-shomei|yukyu.
  `fields` is a string-keyed map."
  [kind fields]
  ;; any free-text the worker supplies is UPL-scanned before it can reach a document
  (assert-no-negotiation (get fields "note" ""))
  (let [worker (f-field fields "worker")
        employer (f-field fields "employer")
        dept (f-field fields "department")
        position (f-field fields "position")
        rdate (f-field fields "date")
        sdate (f-field fields "submit_date")
        rep (f-field fields "representative")
        head (get head-by-kind kind)]
    (when (nil? head)
      (throw (ex-info (str "unknown document kind: " kind) {:kind kind})))
    (let [L (cond-> [head ""]
              (= kind "taishoku-todoke")
              (into ["私事、"
                     (str "このたび一身上の都合により、来る " rdate " をもって退職いたします。") ""
                     (str "（本書面は民法627条1項に基づく、期間の定めのない労働契約の一方的な解約の意思表示です。"
                          "使用者の承諾を要しません。）")])
              (= kind "taishoku-gan")
              (into ["私事、"
                     (str "このたび一身上の都合により、" rdate " をもって退職いたしたく、お願い申し上げます。")])
              (= kind "sokuji")
              (into ["私事、"
                     (str "このたびやむを得ない事由により、" rdate "（本書面到達日）をもって退職いたします。") ""
                     "（本書面は民法628条に基づく、やむを得ない事由による労働契約の即時解除の意思表示です。）"])
              (= kind "naiyo-shomei")
              (into [(str "私 " worker " は、貴社との労働契約を、本書面の到達をもって、")
                     (str "民法627条1項に基づき " rdate " をもって終了する意思を通知いたします。") ""
                     "（本書面は退職の意思表示の到達を証明する目的で内容証明郵便により送付するものです。）"])
              (= kind "yukyu")
              (into [(str "労働基準法39条に基づき、退職日（" rdate "）までの間、")
                     "保有する年次有給休暇を取得することを届け出ます。"]))
          L (into L ["" (str "　　" sdate) (str "　　" dept "　" position) (str "　　" worker "　　㊞") ""
                     (str employer) (str "代表取締役 " rep "　殿") ""])]
      (str (str/join "\n" L) "\n"))))

(defn build-relay
  "Build a 使者 (messenger) RELAY record — ONLY for non-negotiating scenarios (G1).

  If the scenario's lawful route is a negotiating one (union/lawyer), kadode REFUSES to relay
  and returns the escalation instead — a 使者 may convey an already-formed declaration, never
  conduct a negotiation (弁護士法72条). The record is UNSENT; transmission is G7-gated.

  Returns a string-keyed map mirroring the Python dict exactly."
  ([scenario-id document worker-did employer-ref nodes edges]
   (build-relay scenario-id document worker-did employer-ref nodes edges "1970-01-01T00:00:00Z"))
  ([scenario-id document worker-did employer-ref nodes edges created-at]
   (let [rec (analyze/recommend-route scenario-id nodes edges)
         actor (get rec "route_actor")]
     (if (or (get rec "needs_negotiation") (contains? analyze/negotiating-actors actor))
       (array-map
        "$type" "com.etzhayyim.kadode.escalation"
        "scenario" scenario-id "relayed" false
        "reason" (str "この事案は交渉を要するため、kadode は使者として伝達できません "
                      "(G1 / 弁護士法72条)。労働組合または弁護士へ。")
        "escalateTo" (get rec "route") "escalateActor" actor)
       (let [body (cid/->bytes document)]
         (array-map
          "$type" "com.etzhayyim.kadode.resignationRelay"
          "scenario" scenario-id "relayed" false "status" "drafted-unsent"
          "role" "messenger-使者" "negotiates" false
          "workerDid" worker-did "employerRef" employer-ref
          "documentCid" (cid/cidv1-raw body) "documentSha256" (cid/sha256-hex body)
          "statutoryBasis" "民法627条1項（一方的解約・承諾不要）"
          "createdAt" created-at
          "note" "本記録は未送付。実際の伝達（メール/内容証明/郵送）はワーカー同意＋G7承認が必要。"))))))

#?(:clj
   (defn -main
     "CLI entry: render the worker's OWN resignation document → out/<kind>.md (file I/O at the
     edge)."
     [& argv]
     (let [argv (vec argv)
           arg (fn [flag] (when (some #{flag} argv) (nth argv (inc (.indexOf argv flag)))))
           here (-> *file* clojure.java.io/file .getParentFile .getParentFile)
           kind (or (arg "--kind") "taishoku-todoke")
           fields {"worker" (arg "--worker") "employer" (arg "--employer")
                   "date" (arg "--date") "department" (arg "--dept")}
           outdir (if (arg "--out")
                    (clojure.java.io/file (arg "--out"))
                    (clojure.java.io/file here "out"))
           doc (render kind fields)]
       (.mkdirs outdir)
       (spit (clojure.java.io/file outdir (str kind ".md")) doc)
       (println (str "kadode generate: " kind " → " (count (cid/->bytes doc)) " B"))
       (println (str "  documentCid:    " (cid/cidv1-raw (cid/->bytes doc))))
       (println (str "  → " (clojure.java.io/file outdir (str kind ".md"))
                     " (worker drafts + self-submits; relay is G7-gated)"))
       0)))
