(ns kaiyaku.methods.plan
  "kaiyaku 解約 — severance-plan builder (dry-run only at R0).
  1:1 Clojure port of `methods/plan.py` (ADR-2606112201).

  Turns a :sever / :review decision on a tie into a concrete severance plan routed through
  the safest adapter tier (the karakuri ServiceOp tiering, ADR-2606039200):

    T1 official-API cancel      — service publishes a cancellation API
    T2 ToS-permitted browser    — browser-use headless plan over the MEMBER's OWN session;
                                  refused by construction when the service browser stance is
                                  :prohibited or :unknown (G3)
    T3 self-submit procedure    — generated checklist / 解約通知文 the member submits THEMSELVES

  CONSTITUTIONAL (read before any change):
    G3 — ToS-honest, NO detection-evasion: evasion verbs are structurally unrepresentable —
      make-step raises on them. A :prohibited/:unknown browser stance falls to T3.
    G5/G6 — severance is DESTRUCTIVE: every plan requires member-sig + explicit dry-run
      confirm; execute raises at R0 (live execution = Council Lv6+ + operator gate).
    G8 — cost-of-severance honesty: notice period / 違約金 are carried into the plan and
      shown to the member; kaiyaku never plans around a contractual obligation.

  Reuses kaiyaku.methods.analyze (load-file* / analyze). House style: Python ':…' keyword
  strings stay strings; pure fns; file/JSON I/O behind #?(:clj …). Portable .cljc.
  NOTE: the Python __main__ CLI demo is ported as -main behind #?(:clj)."
  (:require [clojure.string :as str]
            [kaiyaku.methods.analyze :as analyze]
            #?(:clj [clojure.java.io :as io])))

(def EVASION-VERBS
  #{"captcha-solve" "proxy-rotate" "stealth" "rate-limit-bypass"
    "fingerprint-spoof" "ip-rotate" "anti-bot-bypass"})

(def PLANNABLE #{":sever" ":review-cascade"})

(defn make-step
  "The only step constructor. Evasion verbs are unrepresentable (G3) — raises."
  [verb detail]
  (when (contains? EVASION-VERBS verb)
    (throw (ex-info (str "G3: detection-evasion verb '" verb "' is unrepresentable in kaiyaku")
                    {:verb verb})))
  {"verb" verb "detail" detail "mode" "dry-run"})

(defn select-tier
  "Safest-first adapter routing (karakuri ADR-2606039200 pattern)."
  [svc]
  (let [cancel (or (get svc ":svc/cancel") {})]
    (cond
      (= (get cancel ":api") ":available") "T1"
      (= (get cancel ":browser") ":permitted") "T2"
      :else "T3")))                       ; :prohibited / :unknown refuses T2 by construction

(defn build-plan
  "One severance plan for one tie. Dry-run only; never executes."
  [svc tie]
  (let [rec (get tie "recommendation")]
    (when-not (contains? PLANNABLE rec)
      (throw (ex-info (str "not plannable: recommendation " rec
                           " (only " (vec (sort PLANNABLE)) ")")
                      {:recommendation rec})))
    (let [tier (select-tier svc)
          svc-id (get tie "svc")
          steps (transient [])]
      (doseq [d (get tie "dependents")]
        (conj! steps (make-step "rehome-dependency"
                                (str "move " d " off " svc-id " (SSO/payment) BEFORE severing"))))
      (cond
        (= tier "T1")
        (conj! steps (make-step "api-cancel"
                                (str "call the published cancellation API of " svc-id)))
        (= tier "T2")
        (conj! steps (make-step "browser-cancel"
                                (str "browser-use plan over the member's OWN session on " svc-id
                                     " (ToS-permitted surface only)")))
        :else
        (conj! steps (make-step "self-submit"
                                (str "generate 解約/退会 procedure + notice text for " svc-id
                                     "; the MEMBER submits it themselves"))))
      (conj! steps (make-step "export-own-data"
                              (str "T3 portability export of the member's own data from "
                                   svc-id " before closure")))
      (conj! steps (make-step "confirm-closure"
                              "verify the service confirms 解約/退会 (email/record)"))
      {"svc" svc-id
       "svc_label" (get tie "svc_label")
       "tier" tier
       "recommendation" rec
       "steps" (persistent! steps)
       ;; G8 cost-of-severance honesty — carried, never planned around
       "notice_days" (get svc ":svc/notice-days" 0)
       "penalty_jpy" (get svc ":svc/penalty-jpy" 0)
       ;; G5 destructive gates — required before ANY live execution
       "requires" {"member_sig" true "dry_run_confirm" true
                   "council_lv6_operator_gate" true}
       "mode" "dry-run"})))

(defn plans
  "All severance plans for the plannable ties of a 縁-ledger."
  [nodes edges]
  (let [res (analyze/analyze nodes edges)]
    (reduce
     (fn [out tie]
       (if (contains? PLANNABLE (get tie "recommendation"))
         (conj out (build-plan (get nodes (get tie "svc")) tie))
         out))
     []
     (get res "ties"))))

(defn execute
  "R0: live execution is Council Lv6+ + operator + member-sig gated (G5/G6) — raises."
  [_plan]
  (throw (#?(:clj RuntimeException. :cljs js/Error.)
          "kaiyaku R0: live severance execution is gated (G5/G6) — dry-run only")))

(defn- comma-int
  "Python f'{n:,}' over an integer (group digits with commas)."
  [n]
  (let [s (str (long n))
        neg (str/starts-with? s "-")
        digits (if neg (subs s 1) s)
        grouped (->> (vec digits) reverse (partition-all 3)
                     (map #(apply str (reverse %))) reverse (str/join ","))]
    (str (when neg "-") grouped)))

(defn report
  "Render the severance-plans markdown (1:1 with report)."
  [ps]
  (let [L (transient ["# kaiyaku severance plans (dry-run — G5/G6 gated)" ""])]
    (doseq [p ps]
      (let [notice (get p "notice_days")
            penalty (get p "penalty_jpy")
            sev (if (or (and (number? notice) (not (zero? notice)))
                        (and (number? penalty) (not (zero? penalty)))
                        (and (not (number? notice)) notice)
                        (and (not (number? penalty)) penalty))
                  (str " · notice " notice "d · penalty ¥" (comma-int penalty))
                  "")]
        (conj! L (str "## " (get p "svc_label") " — " (get p "tier")
                      " (" (get p "recommendation") ")" sev))
        (doseq [[i s] (map-indexed vector (get p "steps"))]
          (conj! L (str (inc i) ". [" (get s "verb") "] " (get s "detail"))))
        (conj! L "")))
    (str (str/join "\n" (persistent! L)) "\n")))

;; ── JSON export (yoro UI, wave 40) — json.dumps(ps, ensure_ascii=False, indent=1)
(defn- json-str [s]
  (str "\"" (-> (str s)
                (str/replace "\\" "\\\\")
                (str/replace "\"" "\\\"")
                (str/replace "\n" "\\n")
                (str/replace "\r" "\\r")
                (str/replace "\t" "\\t"))
       "\""))

(defn- json-scalar [v]
  (cond
    (true? v) "true"
    (false? v) "false"
    (nil? v) "null"
    (string? v) (json-str v)
    (and (number? v) (or (instance? Double v) (instance? Float v)))
    (let [d (double v)] (if (== d (Math/rint d)) (str (long d) ".0") (str d)))
    (number? v) (str v)
    :else (json-str v)))

(defn ->json
  "Faithful json.dumps(x, ensure_ascii=False, indent=1) for our plan shapes
  (string-keyed maps, vectors, scalars). Mirrors Python's 1-space indent layout."
  ([x] (->json x 0))
  ([x depth]
   (let [pad (apply str (repeat (inc depth) " "))
         pad0 (apply str (repeat depth " "))]
     (cond
       (map? x)
       (if (empty? x)
         "{}"
         (str "{\n"
              (str/join ",\n"
                        (map (fn [[k v]] (str pad (json-str k) ": " (->json v (inc depth))))
                             x))
              "\n" pad0 "}"))
       (sequential? x)
       (if (empty? x)
         "[]"
         (str "[\n"
              (str/join ",\n" (map (fn [v] (str pad (->json v (inc depth)))) x))
              "\n" pad0 "]"))
       :else (json-scalar x)))))

#?(:clj
   (defn -main
     "CLI entry: analyze a seed → out/severance-plans.md + severance-plans.json (file I/O edge)."
     [& argv]
     (let [argv (vec argv)
           here (-> *file* io/file .getParentFile .getParentFile)
           seed (if (and (seq argv) (not (str/starts-with? (first argv) "--")))
                  (io/file (first argv))
                  (io/file here "data" "seed-en-ledger.kotoba.edn"))
           outdir (if (some #{"--out"} argv)
                    (io/file (nth argv (inc (.indexOf argv "--out"))))
                    (io/file here "out"))
           {:keys [nodes edges]} (analyze/load-file* seed)
           ps (plans nodes edges)]
       (.mkdirs outdir)
       (spit (io/file outdir "severance-plans.md") (report ps))
       (spit (io/file outdir "severance-plans.json") (->json ps))   ; yoro UI (wave 40)
       (println (str "kaiyaku: " (count ps) " severance plans (dry-run) → "
                     (io/file outdir "severance-plans.md")))
       0)))
