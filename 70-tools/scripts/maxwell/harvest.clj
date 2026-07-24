#!/usr/bin/env bb
;; Maxwell corpus harvester (babashka / kotoba-native).
;; Replaces the Python harvest_gad.py + gate_candidates.py: one process, no venv,
;; no wrapper-shell confusion. Discovers top-level Python actor methods not yet in
;; corpus (skipping *-compat scaffolds + previously-failed units), translates each
;; via gad's llama-server (Gemma 4 26B, /v1, Murakumo-only ADR-2605215000) with a
;; clj-kondo lint-feedback retry loop + paren repair, and appends only error-free
;; (clojure) pairs directly to maxwell-sft-corpus.jsonl.
;;
;; Usage:  bb harvest.clj [--n 40] [--retries 3] [--per-file 2]
(require '[babashka.http-client :as http]
         '[cheshire.core :as json]
         '[clojure.java.io :as io]
         '[clojure.java.shell :refer [sh]]
         '[clojure.string :as str])

(def ROOT (loop [f (io/file (System/getProperty "babashka.file"))
                 n 4] (if (zero? n) f (recur (.getParentFile f) (dec n)))))
(def ACTORS    (io/file (or (System/getenv "ETZHAYYIM_WEST_ACTORS_DIR")
                            (str (io/file ROOT "..")))))
(def CORPUS    (io/file ROOT "90-docs/baien/maxwell-sft-corpus.jsonl"))
(def FAILED    (io/file ROOT "90-docs/baien/maxwell-failed.txt"))
(def KONDO     (str (io/file (System/getProperty "user.home") "bin/clj-kondo")))
(def ENDPOINT  "http://100.82.98.110:11434/v1/chat/completions") ; gad llama-server (Tailscale)
(def MODEL     "gemma4-26b-a4b-q4.gguf")

(def SYSTEM
  (str "You are Maxwell, etzhayyim's Murakumo fleet model. Convert Python actor "
       "methods to idiomatic Clojure following kotoba Datom log conventions "
       "(namespaced keywords, pure stdlib, EAVT). Output ONLY a single top-level "
       "(defn name [...] ...) form inside a ```clojure block — no ns, no prose, "
       "use defn (not defn-), balanced parens."))
;; Charter Rider §2 prohibited signals (minimal pre-pass; ADR-2605192200).
(def PROHIBITED ["runpod" "vertex ai" "aws bedrock" "weapon design" "covert force"
                 "child sexual" "setowner" "transfer() land"])

(defn corpus-ids []
  (if (.exists CORPUS)
    (into #{} (comp (remove str/blank?) (map #(get (json/parse-string % true) :id)))
          (str/split-lines (slurp CORPUS)))
    #{}))
(defn failed-ids []
  (if (.exists FAILED) (into #{} (remove str/blank?) (str/split-lines (slurp FAILED))) #{}))
(defn record-failed! [eid] (spit FAILED (str eid "\n") :append true))

(defn label-for [^java.io.File f]
  (let [repo (.getName
              (first (drop-while #(not (str/starts-with? (.getName ^java.io.File %)
                                                         "com-etzhayyim-"))
                                 (take-while some? (iterate #(.getParentFile ^java.io.File %) f)))))]
    (str repo "/" (.getName f))))

(defn top-level-fns
  "[[fn-name src] ...] for module-level def/async def (indentation-delimited)."
  [py]
  (let [lines (vec (str/split-lines py))]
    (for [i (range (count lines))
          :let [m (re-matches #"(?:async )?def ([A-Za-z_][A-Za-z0-9_]*)\(.*" (nth lines i))]
          :when m]
      (let [body (loop [j (inc i) acc [(nth lines i)]]
                   (if (>= j (count lines)) acc
                       (let [l (nth lines j)]
                         (if (or (str/blank? l) (re-find #"^\s" l))
                           (recur (inc j) (conj acc l)) acc))))]
        [(second m) (str/trimr (str/join "\n" body))]))))

(defn extract-defn [txt]
  (let [m (re-find #"(?s)```(?:clojure|clj)?\s*(.*?)```" txt)
        clj (str/trim (if m (second m) txt))
        bal (- (count (re-seq #"\(" clj)) (count (re-seq #"\)" clj)))]
    (str clj (apply str (repeat (max 0 bal) ")")))))    ; EOF paren repair

(defn lint
  "clj-kondo [error-count, output]. Warnings tolerated (--fail-level error).
   Output is fed back to the teacher so it can fix the exact errors."
  [clj]
  (let [tf (java.io.File/createTempFile "maxwell-lint" ".clj")]
    (try (spit tf clj)
         (let [out (str/trim (:out (sh KONDO "--lint" (str tf) "--fail-level" "error")))
               m (re-find #"errors:\s*(\d+)" out)]
           [(if m (parse-long (second m)) 99) out])
         (finally (.delete tf)))))

(defn chat [messages]
  (-> (http/post ENDPOINT
        {:headers {"Content-Type" "application/json"} :timeout 180000
         :body (json/generate-string
                 {:model MODEL :messages messages :temperature 0 :max_tokens 1024
                  :chat_template_kwargs {:enable_thinking false}})})
      :body (json/parse-string true) :choices first :message :content))

(defn translate
  "Returns the lint-clean clj string on success; :transient when the teacher
   never produced ANY response (gad flaky/down — caller should NOT record a
   permanent failure, retry later); nil when the teacher responded but could
   not be coaxed lint-clean within `retries` (a real, recordable failure)."
  [py-src retries]
  (loop [msgs [{:role "system" :content SYSTEM}
               {:role "user" :content (str "Convert this Python method to Clojure following kotoba Datom log idioms:\n\n```python\n" py-src "\n```\n\nOutput only the Clojure defn form.")}]
         tries (inc retries)
         got-response false]
    (if-not (pos? tries)
      (if got-response nil :transient)        ; exhausted: real-fail vs never-responded
      (let [txt (try (chat msgs) (catch Exception e (binding [*out* *err*] (println "  chat err:" (.getMessage e))) nil))]
        (if (nil? txt)
          (if got-response (recur msgs (dec tries) true) :transient) ; mid-convo blip: retry once; cold blip: transient
          (let [clj (extract-defn txt)]
            (if-not (str/starts-with? (str/triml clj) "(defn")
              (recur (conj msgs {:role "assistant" :content txt}
                                {:role "user" :content "Output ONLY a single (defn ...) form in a ```clojure block."}) (dec tries) true)
              (let [[errs out] (lint clj)]
                (if (zero? errs) clj
                    (recur (conj msgs {:role "assistant" :content (str "```clojure\n" clj "\n```")}
                                      {:role "user" :content (str "clj-kondo reported errors. Fix them, output only the corrected defn:\n" out)}) (dec tries) true))))))))))

(defn charter-ok? [s] (let [low (str/lower-case s)] (not-any? #(str/includes? low %) PROHIBITED)))

(defn -main [& args]
  (let [opts (apply hash-map (map #(if (str/starts-with? % "--") (keyword (subs % 2)) %) args))
        n (parse-long (get opts :n "40"))
        retries (parse-long (get opts :retries "3"))
        per-file (parse-long (get opts :per-file "2"))
        max-transient (parse-long (get opts :max-transient "12"))
        done (atom (into (corpus-ids) (failed-ids)))
        harvested (atom 0) attempts (atom 0) transient* (atom 0) consec (atom 0)
        aborted (atom false)
        py-files (->> (file-seq ACTORS)
                      (filter #(and (.isFile %) (str/ends-with? (str %) ".py")
                                    (not (str/includes? (str %) "-compat"))
                                    (not (str/includes? (str %) "/tests/"))
                                    (not (str/includes? (.getName %) "test"))))
                      (sort-by str))]
    (with-open [w (io/writer CORPUS :append true)]
      (doseq [f py-files :while (and (< @harvested n) (not @aborted))]
        (let [label (label-for f)
              fns (try (top-level-fns (slurp f)) (catch Exception _ []))]
          (loop [fns fns pf 0]
            (when (and (seq fns) (< @harvested n) (< pf per-file) (not @aborted))
              (let [[fn-name py-src] (first fns)
                    eid (str label "/" fn-name)]
                (if (or (@done eid) (< (count py-src) 60) (> (count py-src) 4000))
                  (recur (rest fns) pf)
                  (do (swap! attempts inc)
                      (let [clj (translate py-src retries)]
                        (cond
                          ;; transient teacher failure (gad flaky/down): do NOT record,
                          ;; retry on a later run; abort the batch if it keeps happening.
                          (= clj :transient)
                          (do (swap! transient* inc) (swap! consec inc)
                              (println (str "  [transient] " eid " (gad flaky, not recorded)"))
                              (when (>= @consec max-transient)
                                (reset! aborted true)
                                (println (format "  !! %d consecutive transient failures — gad appears down, aborting batch" @consec))))
                          ;; lint-clean + charter-ok: a real harvested pair.
                          (and (string? clj) (charter-ok? (str py-src "\n" clj)))
                          (do (reset! consec 0)
                              (.write w (str (json/generate-string
                                               {:id eid
                                                :messages [{:role "system" :content SYSTEM}
                                                           {:role "user" :content py-src}
                                                           {:role "model" :content clj}]
                                                :meta {:src (str f) :unit fn-name :teacher MODEL :via "harvest.clj"}}) "\n"))
                              (.flush w) (swap! done conj eid) (swap! harvested inc)
                              (println (format "  [%d/%d] %s (lint-clean)" @harvested n eid)))
                          ;; real failure (teacher responded but no clean/charter-ok defn): record + skip.
                          :else
                          (do (reset! consec 0) (record-failed! eid) (swap! done conj eid)
                              (println (str "  [skip] " eid " (no clean lint)"))))
                        (recur (rest fns) (if (string? clj) (inc pf) pf))))))))))) ; advance pf only on a harvested pair
    (println (format "harvested %d clean / %d attempted / %d transient -> %s"
                     @harvested @attempts @transient* (str CORPUS)))))

(apply -main *command-line-args*)
