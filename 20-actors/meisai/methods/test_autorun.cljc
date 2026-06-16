(ns meisai.methods.test-autorun
  "test_autorun.py — meisai autonomous intake heartbeat + kotoba Datom-log invariants.
  ADR-2606122400. 1:1 Clojure port of methods/test_autorun.py (the check() asserts → clojure.test).

  Guards the autonomy + persistence contract:
    - one content-addressed tx per NEW intake, appended to a verifiable commit-DAG;
    - dedup by intake content CID: a second cycle over the same intakes appends NOTHING
      (resume-safe), and tamper is detected by verify-chain;
    - G3 local-only: the loop touches only the paths it is given (no network modules imported).

  The __main__ demo is OMITTED."
  (:require [clojure.test :refer [deftest is run-tests]]
            [clojure.string :as str]
            #?(:clj [clojure.java.io :as io])
            [meisai.methods.autorun :as autorun]
            [meisai.methods.kotoba :as kotoba])
  #?(:clj (:import [java.io File]
                   [java.nio.file Files]
                   [java.nio.file.attribute FileAttribute])))

(def edn-a
  "{:source :sumitclub :statement/month \"2026-05\" :statement/total-jpy 46540
 :statement/rows [{:date \"2026-05-02\" :merchant \"AMAZON.CO.JP\" :amount_jpy 3980}
                  {:date \"2026-05-15\" :merchant \"JR東日本\" :amount_jpy 42560}]}
")

(def edn-b
  "{:source :sumitclub :statement/month \"2026-04\" :statement/total-jpy 1200
 :statement/rows [{:date \"2026-04-03\" :merchant \"SUICA\" :amount_jpy 1200}]}
")

#?(:clj
   (defn- mk-tempdir []
     (.toFile (Files/createTempDirectory "meisai-autorun-"
                                         (make-array FileAttribute 0)))))

(deftest test-autorun-heartbeat
  #?(:clj
     (let [td (mk-tempdir)
           intake (io/file td "intake")
           _ (.mkdir intake)
           log (.getAbsolutePath (io/file td "meisai.datoms.kotoba.edn"))]
       (try
         (spit (io/file intake "2026-05.edn") edn-a)
         (spit (io/file intake "2026-04.edn") edn-b)

         (let [r1 (autorun/run-cycle 1 (.getAbsolutePath intake) log)]
           (is (= (count (get r1 "appended")) 2)
               "first cycle ingests both intakes")
           (is (get (kotoba/verify-chain log) :ok) "chain verifies")
           (is (= (get (nth (kotoba/read-log log) 1) ":tx/prev")
                  (get (nth (kotoba/read-log log) 0) ":tx/cid"))
               "txs link (commit-DAG)"))

         (let [r2 (autorun/run-cycle 2 (.getAbsolutePath intake) log)]
           (is (and (= (count (get r2 "appended")) 0) (= (get r2 "skipped") 2))
               "second cycle appends nothing (dedup by intake CID)")
           (is (= (count (kotoba/read-log log)) 2) "log length still 2"))

         (spit (io/file intake "2026-06.edn")
               (str/replace edn-a "2026-05" "2026-06"))
         (let [r3 (autorun/run-cycle 3 (.getAbsolutePath intake) log)]
           (is (= (count (get r3 "appended")) 1) "new intake → exactly one new tx")
           (is (get (kotoba/verify-chain log) :ok) "chain still verifies"))

         (let [head-before (kotoba/head-cid log)
               r4 (autorun/run-cycle 4 (.getAbsolutePath intake) log)]
           (is (and (= (kotoba/head-cid log) head-before) (empty? (get r4 "appended")))
               "resume-safe: idle cycle leaves head unchanged"))

         ;; tamper-detect: flip one amount in the persisted log
         (let [tampered (str/replace (slurp log) "42560" "1")]
           (spit log tampered)
           (is (false? (get (kotoba/verify-chain log) :ok)) "tamper is detected"))
         (finally
           (doseq [^File f (reverse (file-seq td))] (.delete f)))))
     :cljs
     (is true)))

(deftest test-method-pack-imports-local-only
  ;; G3: no network machinery may be imported anywhere in the method-pack (cljc siblings)
  #?(:clj
     (let [here autorun/here
           forbidden ["urllib" "http.client" "import http" "socket" "requests"
                      "subprocess"]
           cljc-srcs (->> (.listFiles ^File here)
                          (filter (fn [^File f]
                                    (and (.isFile f)
                                         (str/ends-with? (.getName f) ".cljc")
                                         (not (str/starts-with? (.getName f) "test_")))))
                          (map slurp)
                          (apply str))
           offenders (filter #(str/includes? cljc-srcs %) forbidden)]
       (is (empty? offenders) (str "method-pack imports are local-only (G3): " offenders)))
     :cljs
     (is true)))

#?(:clj (defn -main [& _] (run-tests 'meisai.methods.test-autorun)))
