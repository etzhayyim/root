#!/usr/bin/env bb
;; intake.clj — 助 (tasuke) plain-language intake: 誰でも使える, no EDN required.
;;
;; Babashka port of methods/intake.py.
;;
;; Lets a non-technical victim build their case by answering plain questions, then hands the
;; case to packet/build-packet / packet/write-packet. The mapping from answers → a :case/* map is
;; a PURE FUNCTION (build-case-from-answers) so it is fully testable without stdin; the interactive
;; loop is a thin shell around it.
;;
;; Charter invariants baked into the mapping, not left to the asker:
;;   G1 — :case/support-cost-jpy is hard-set to 0 (victim is never asked for a fee).
;;   G7 — :case/consent comes from an explicit yes/no; without a clear yes, no case is built (raises).
;;   G7 — :case/server-held-key is hard-set to false.
;;
;; Stdlib only. The loss parser accepts「480000」「48万」「48万円」「480,000円」→ yen as long.
(ns tasuke.methods.intake
  (:require [clojure.string :as str]))

;; ── constants ─────────────────────────────────────────────────────────────────────────────────

;; (field, prompt, kind) tuples — shared by the interactive loop AND the tests.
(def QUESTIONS
  [["consent"    "この内容で被害対応を進めてよいですか? (はい/いいえ)"                       "yesno"]
   ["narrative"  "何が起きましたか? できるだけ具体的に教えてください"                         "text"]
   ["occurred"   "いつ起きましたか? (例: 2026-06-03 朝)"                                   "text"]
   ["loss"       "金銭被害はいくらですか? (例: 48万 / 480000 / なし)"                       "yen"]
   ["service"    "関係するサービス名は? (例: ○○銀行 / LINE / なければ空欄)"                  "text"]
   ["account_id" "対象のアカウントID・口座・URL があれば教えてください"                       "text"]])

(def _YES #{"はい" "yes" "y" "はい。" "ok" "進める" "true" "1"})
(def _NO  #{"いいえ" "no" "n" "やめる" "false" "0" ""})

;; ── parse helpers ─────────────────────────────────────────────────────────────────────────────

(defn parse-yesno
  "True iff the (lowercased/trimmed) answer is in _YES."
  [s]
  (contains? _YES (str/lower-case (str/trim (str s)))))

(defn parse-yen
  "「48万」「480,000円」「なし」→ long yen. Best-effort; returns 0 when none/unparseable."
  [s]
  (let [t (-> (str s)
              (str/trim)
              (str/replace "," "")
              (str/replace "円" ""))]
    (cond
      (or (str/blank? t) (#{"なし" "無し" "ない" "0"} t))
      0

      ;; Match: digits(optional .digits) 万 optional-extra-digits
      :else
      (let [m1 (re-matches #"\s*(\d+(?:\.\d+)?)\s*万\s*(\d+)?\s*" t)]
        (if m1
          (let [man (* (Double/parseDouble (m1 1)) 10000.0)
                extra (if (m1 2) (Long/parseLong (m1 2)) 0)]
            (long (+ man extra)))
          (let [m2 (re-matches #"\s*(\d+)\s*" t)]
            (if m2
              (Long/parseLong (m2 1))
              0)))))))

;; ── SHA-1 case-id (byte-identical to Python hashlib.sha1) ─────────────────────────────────────

(defn- sha1-hex
  "SHA-1 hex digest over UTF-8 bytes — matches Python hashlib.sha1(s.encode()).hexdigest()."
  [^String s]
  (let [md (java.security.MessageDigest/getInstance "SHA-1")
        bs (.digest md (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" (bit-and % 0xff)) bs))))

(defn- _case-id
  "Deterministic case id — first 8 hex chars of SHA-1 over 'narrative|occurred' in UTF-8.
  Byte-identical to Python: hashlib.sha1(f'{narrative}|{occurred}'.encode('utf-8')).hexdigest()[:8]."
  [narrative occurred]
  (let [h (subs (sha1-hex (str narrative "|" occurred)) 0 8)]
    (str "case-" h)))

;; ── build-case-from-answers ───────────────────────────────────────────────────────────────────

(defn build-case-from-answers
  "Map plain answers → a :case/* map. PURE. Raises (G7) if consent is not clearly given.

  answers is a map of string key → string value matching the QUESTIONS field names.
  subject defaults to 'did:web:etzhayyim.com:member:self'."
  ([answers] (build-case-from-answers answers "did:web:etzhayyim.com:member:self"))
  ([answers subject]
   (when-not (parse-yesno (get answers "consent" ""))
     (throw (ex-info "G7: 被害者の明確な同意がなければ case は作成しません (はい/yes が必要)"
                     {:g7 true})))
   (let [narrative (str/trim (str (get answers "narrative" "")))
         occurred  (str/trim (str (get answers "occurred" "")))
         loss-jpy  (parse-yen (get answers "loss" ""))
         case-map  {":case/id"               (or (get answers "case_id")
                                                 (_case-id narrative occurred))
                    ":case/subject"           subject
                    ":case/narrative"         narrative
                    ":case/occurred-at-text"  occurred
                    ":case/loss-jpy"          loss-jpy
                    ":case/service"           (str/trim (str (get answers "service" "")))
                    ":case/account-id"        (str/trim (str (get answers "account_id" "")))
                    ;; ── invariants baked in, never asked ──
                    ":case/consent"           true   ;; G7 (we got here only via an explicit yes)
                    ":case/support-cost-jpy"  0      ;; G1 全て無料
                    ":case/server-held-key"   false} ;; G7 no-server-key
         ]
     (if (> loss-jpy 0)
       (assoc case-map ":case/loss-breakdown" [{":label" "被害額" ":jpy" loss-jpy}])
       case-map))))

;; ── interactive ───────────────────────────────────────────────────────────────────────────────

(defn interactive
  "Ask the questions on the console and return the built case. `ask` is injectable for tests.
  Default ask uses stdin (clojure.core/read-line after printing prompt)."
  ([] (interactive (fn [prompt]
                     (print prompt)
                     (flush)
                     (read-line))))
  ([ask]
   (let [answers (reduce
                   (fn [acc [field prompt _kind]]
                     (let [answer (ask (str prompt "\n> "))]
                       (when (and (= field "consent") (not (parse-yesno answer)))
                         (throw (ex-info "同意が得られませんでした。対応を中止します。"
                                         {:exit true})))
                       (assoc acc field answer)))
                   {}
                   QUESTIONS)]
     (build-case-from-answers answers))))

;; ── main ──────────────────────────────────────────────────────────────────────────────────────

(defn -main [& _args]
  (require '[tasuke.methods.packet :as packet])
  (println "助 (tasuke) — サイバー犯罪 被害対応（無料）。いくつか質問します。\n")
  (let [case (interactive)
        p    ((resolve 'packet/build-packet) case)
        out  ((resolve 'packet/write-packet) p)]
    (println (str "\n" ((resolve 'packet/cover) p)))
    (println (str "\n→ " (count (get p "documents"))
                  " 通の書類を " out "/ に作成しました（費用: ¥" (get p "cost") "）。"))
    (println "  各書類を印刷し、内容を確認・署名のうえ、ご自身で提出してください。")))

(when (= *file* (System/getProperty "babashka.file"))
  (-main))
