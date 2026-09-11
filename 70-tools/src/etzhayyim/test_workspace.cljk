;; etzhayyim.test-workspace — workspace rsync/root pure invariants (cljc port).
;; Run via the aggregate: bb test:helpers
;; Covers build-rsync-command (pure argv) + resolve-workspace-root / count-actor-files
;; (via injected :fs-fn — the live filesystem legs stay deferred).
(ns etzhayyim.test-workspace
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [etzhayyim.workspace :as ws]))

(deftest rsync-command-assembly
  (testing "defaults: -avz --progress + standard excludes + trailing-slash src"
    (is (= ["rsync" "-avz" "--progress"
            "--exclude" "node_modules" "--exclude" ".git" "--exclude" "__pycache__"
            "--exclude" ".venv" "--exclude" "dist" "--exclude" "build"
            "/ws/" "u@h:/d"]
           (ws/build-rsync-command {:workspace-dir "/ws" :remote "u@h:/d"}))))
  (testing "nil workspace-dir → ./ source; custom excludes replace defaults"
    (is (= ["rsync" "-avz" "--progress" "--exclude" "a" "--exclude" "b" "./" "r"]
           (ws/build-rsync-command {:remote "r" :excludes ["a" "b"]}))))
  (testing "dry-run + delete flags inserted before src/remote"
    (let [c (ws/build-rsync-command {:workspace-dir "/ws" :remote "r"
                                     :excludes ["x"] :dry-run true :delete true})]
      (is (= ["rsync" "-avz" "--progress" "--exclude" "x" "--dry-run" "--delete" "/ws/" "r"] c)))))

(deftest workspace-root-resolution
  (testing "explicit dir passes through the (identity) fs-fn"
    (is (= "/explicit" (ws/resolve-workspace-root "/explicit" {}))))
  (testing "nil dir → fs-fn applied to the fallback"
    (is (= "ROOT" (ws/resolve-workspace-root nil {:fs-fn (constantly "ROOT")}))))
  (testing "fs-fn transforms the resolved path"
    (is (= "/x!" (ws/resolve-workspace-root "/x" {:fs-fn (fn [p] (str p "!"))})))))

(deftest actor-file-count-injected
  (is (= 7 (ws/count-actor-files "/root" {:fs-fn (constantly 7)})))
  (is (= 0 (ws/count-actor-files "/root" {:fs-fn (constantly 0)}))))

(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'etzhayyim.test-workspace)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
