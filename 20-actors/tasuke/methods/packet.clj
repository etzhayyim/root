(ns tasuke.methods.packet
  "packet.clj — 助 (tasuke) victim packet generator. Babashka port of methods/packet.py.

  Turns a victim's case into a complete, ready-to-print document packet a real person can take
  to the police / their bank / a platform. This is the usable surface over the R0 engines.

  Invariants preserved by construction: the packet is FREE (G1), member-authored and
  member-submitted (G2/G3), and draft-only at R0 (G9). `build-packet` runs
  `report-gen/assert-member-authored` on every document. 助 generates; the member signs and submits.

  House style: Python ':…' keyword strings stay strings; keyword-valued fields are ':'-prefixed
  strings. STRING map keys exactly as Python (e.g. 'caseId')."
  (:require [clojure.java.io :as io]
            [clojure.string :as str]
            [tasuke.methods.edn :as e]
            [tasuke.methods.report-gen :as rg]
            [tasuke.methods.triage :as t]))

(def ^:private actor-dir (-> *file* io/file .getParentFile .getParentFile))
(def ^:private SEED (io/file actor-dir "data" "seed-cybercrime-cases.kotoba.edn"))
(def ^:private OUT (io/file actor-dir "methods" "out"))
(def ^:private REGISTRY (atom nil))

(defn- kw
  "Mirror of packet._kw: strip leading colon, take last / segment, lower-case."
  [v]
  (-> (str (or v ""))
      (str/replace #"^:+" "")
      (str/split #"/")
      (last)
      (str/lower-case)))

(defn documents-for-kind
  "The single source of truth for which member-authored documents a scam KIND warrants.

  Always the police core (被害届 / 被害状況報告書 / 証拠目録 / 被害額算定書); plus a bank組戻し
  for money-moved cases, a platform request for account/identity cases, and a recovery plan when
  credentials were exposed."
  [case kind evidence]
  (let [ev (or evidence [])
        k (str kind)
        loss (let [v (get case ":case/loss-jpy" 0)] (if (number? v) (long v) 0))
        docs [(rg/damage-report case)
              (rg/incident-statement case)
              (rg/evidence-index-doc case ev)
              (rg/damage-calculation case)]]
    (cond-> docs
      (or (= k "unauthorized-transfer")
          (and (> loss 0) (#{"investment-scam" "fake-billing" "support-scam"} k)))
      (conj (rg/bank-freeze-request case))

      (#{"account-takeover" "impersonation" "sns-fraud" "phishing" "leak-extortion"} k)
      (conj (rg/platform-request case :purpose "凍結・復旧"))

      (#{"account-takeover" "phishing" "support-scam"} k)
      (conj (rg/recovery-plan case :service (get case ":case/service" "（対象サービス）"))))))

(defn- window-registry
  "Lazy seed registry of public windows keyed by :registry/window."
  []
  (when (nil? @REGISTRY)
    (let [seed (e/load-edn SEED)
          windows (get seed ":registry/windows" [])]
      (reset! REGISTRY (into {} (map (fn [w] [(get w ":registry/window") w]) windows)))))
  @REGISTRY)

(defn build-packet
  "Assemble the full packet for a case. Raises (G1/G7) if the case isn't free/consented."
  ([case] (build-packet case nil))
  ([case evidence]
   (let [tri (t/triage case)                 ; G1/G7 gate
         kind (kw (get tri ":triage/scam-kind"))
         docs (documents-for-kind case kind evidence)]
     (doseq [d docs]
       (rg/assert-member-authored d))        ; G1/G2/G3/G9 on every doc
     (let [reg (window-registry)
           windows (mapv (fn [w]
                           (let [r (get reg w {})]
                             {"code" (kw w)
                              "name" (get r ":registry/name" (kw w))
                              "contact" (get r ":registry/contact" "")
                              "basis" (get r ":registry/basis" "")}))
                         (get tri ":triage/windows" []))]
       {"caseId" (get case ":case/id" "case")
        "kind" kind
        "severity" (kw (get tri ":triage/severity"))
        "cost" (get tri ":triage/support-cost-jpy")
        "documents" docs
        "windows" windows
        "actions" (get tri ":triage/actions")
        "deadlines" (get tri ":triage/deadlines")}))))

(defn- cover
  "Render the 00-COVER.md markdown for a built packet."
  [p]
  (let [header [(str "# 助 (tasuke) 被害対応パケット — " (get p "caseId") "\n")
                (str "**被害類型**: " (rg/ja-kind (get p "kind")) "　**緊急度**: "
                     (get p "severity") "　**あなたの負担: ¥" (get p "cost") "（全て無料）**\n")
                (str "> この一式は **あなた本人が作成・署名・提出** する書類です（助 は作成を手伝うだけで、"
                     "提出はあなたが行います）。弁護士費用も利用料も一切かかりません。\n")
                "## まず行うこと（上から順に）\n"]
        actions (map-indexed (fn [i a] (str (inc i) ". " a)) (get p "actions"))
        deadlines (get p "deadlines")
        deadline-section (when (seq deadlines)
                           (cons "\n## ⏰ 期限の注意\n"
                                 (mapv (fn [d] (str "- " d)) deadlines)))
        windows-section (cons "\n## 無料の相談・通報窓口\n"
                              (mapv (fn [w]
                                      (str "- **" (get w "name") "** — " (get w "contact")
                                           (when-let [b (not-empty (str (get w "basis")))]
                                             (str "（" b "）"))))
                                    (get p "windows")))
        docs-section (cons "\n## 同梱書類（印刷して署名のうえ提出）\n"
                           (map-indexed (fn [i d]
                                          (str "- `" (format "%02d" (inc i)) "-"
                                               (str/replace (get d ":doc/kind") #"^:+" "")
                                               ".txt` — 宛先: " (get d ":doc/addressed-to")))
                                        (get p "documents")))]
    (-> (concat header
                actions
                deadline-section
                windows-section
                docs-section)
        (vec)
        (->> (str/join "\n"))
        (str "\n"))))

(defn write-packet
  "Write packet files (00-COVER.md + NN-<kind>.txt) into `outdir`. Returns the output directory.

  If outdir is omitted writes under the default methods/out/packet-<caseId>."
  ([p] (write-packet p nil))
  ([p outdir]
   (let [d (io/file (or outdir (io/file OUT (str "packet-" (get p "caseId")))))]
     (.mkdirs d)
     (spit (io/file d "00-COVER.md") (cover p))
     (doseq [[i doc] (map-indexed vector (get p "documents"))]
       (let [kind (str/replace (get doc ":doc/kind") #"^:+" "")
             f (io/file d (format "%02d-%s.txt" (inc i) kind))]
         (spit f (str (get doc ":doc/body")))))
     d)))

(defn- load-case
  "Load a single case from CLI args."
  [{:keys [file case]}]
  (let [cases (if file
                (let [seed (e/load-edn (io/file file))]
                  (if (map? seed)
                    (get seed ":case/batch" [seed])
                    [seed]))
                (get (e/load-edn SEED) ":case/batch"))]
    (if case
      (or (some #(when (= (get % ":case/id") case) %) cases)
          (throw (ex-info (str "case " (pr-str case) " not found") {})))
      (first cases))))

(defn -main
  "CLI entry point: `bb packet.clj [--case ID] [--file FILE]`."
  [& args]
  (let [named (loop [as args out {}]
                (cond
                  (empty? as) out
                  (and (= (first as) "--case") (next as)) (recur (nnext as) (assoc out :case (second as)))
                  (and (= (first as) "--file") (next as)) (recur (nnext as) (assoc out :file (second as)))
                  :else (recur (rest as) out)))
        c (load-case named)
        packet (build-packet c)
        out (write-packet packet)]
    (println (cover packet))
    (println (str "\n→ wrote " (count (get packet "documents")) " documents to " out "/ (victim cost: ¥" (get packet "cost") ")"))))
