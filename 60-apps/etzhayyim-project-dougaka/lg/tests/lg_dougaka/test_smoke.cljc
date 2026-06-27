(ns lg-dougaka.test-smoke
  "Smoke tests for the lg-dougaka clj port — clojure.test twin of
  lg/tests/test_smoke.py (ADR-2606280030). Covers the graph set, NSID map,
  langgraph.json drift, the HTTP handlers, and the render graph topology."
  (:require [clojure.test :refer [deftest is testing run-tests]]
            [cheshire.core :as json]
            [langgraph.graph :as g]
            [lg-dougaka.server :as server]
            [lg-dougaka.graphs.health :as health]
            [lg-dougaka.graphs.render :as render]))

(def expected-graphs #{"health" "render"})
(def expected-nsid-map {"com.etzhayyim.apps.dougaka.render" "render"})

(deftest server-module-loads
  (is (some? server/GRAPHS))
  (is (map? server/GRAPHS))
  (is (map? server/NSID-MAP)))

(deftest graphs-match-expected-set
  (is (= expected-graphs (set (keys server/GRAPHS)))))

(deftest nsid-map-completeness
  (is (= expected-nsid-map server/NSID-MAP)))

(deftest nsid-map-references-known-graphs
  (doseq [[nsid graph-name] server/NSID-MAP]
    (is (contains? server/GRAPHS graph-name)
        (str "NSID-MAP[" nsid "] → " graph-name " not in GRAPHS"))))

(deftest langgraph-json-graphs-match-server
  (let [cfg (json/parse-string (slurp "langgraph.json"))
        declared (set (keys (get cfg "graphs")))]
    (is (= declared (set (keys server/GRAPHS)))
        (str "drift: langgraph.json=" declared " server=" (set (keys server/GRAPHS))))))

(deftest langgraph-json-has-no-crons
  (let [cfg (json/parse-string (slurp "langgraph.json"))]
    (is (= [] (get cfg "crons" [])))))

(deftest all-graphs-are-invocable
  (doseq [[_name graph] server/GRAPHS]
    (is (some? (g/invoke graph {})))))

;; ── HTTP handler behaviour (analogue of the TestClient tests) ───────────────
(deftest health-endpoint
  (let [r (server/health-handler)]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))))

(deftest ok-endpoint-lists-graphs
  (let [r (server/health-handler)]
    (is (= 200 (:status r)))
    (is (true? (get-in r [:body :ok])))
    (is (= expected-graphs (set (get-in r [:body :graphs]))))))

(deftest unknown-assistant-404
  (let [r (server/runs-handler {"assistant_id" "nope" "input" {}})]
    (is (= 404 (:status r)))))

(deftest unknown-nsid-xrpc-404
  (let [r (server/xrpc-handler "com.etzhayyim.apps.dougaka.unknownMethod" {})]
    (is (= 404 (:status r)))))

(deftest api-key-gate
  (testing "no key configured → authorized"
    (is (nil? (server/check-api-key ""))))
  (testing "configured key mismatch → 401"
    (with-redefs [server/api-key (constantly "secret")]
      (is (= 401 (:status (server/check-api-key "wrong"))))
      (is (nil? (server/check-api-key "secret"))))))

;; ── health graph ────────────────────────────────────────────────────────────
(deftest health-graph-pings
  (is (= true (:ok (g/invoke health/GRAPH {})))))

;; ── render graph topology + node behaviour ──────────────────────────────────
(deftest render-scene-builder
  (let [timeline {:scenes [{:index 0 :location "park" :action "walk"}
                           {:index 1 :location "home" :action "sit"}]
                  :lines [{:scene_index 1 :line_index 1 :speaker "right" :text "b" :emotion "sad"}
                          {:scene_index 0 :line_index 0 :speaker "left" :text "a"}
                          {:scene_index 1 :line_index 0 :speaker "left" :text "c"}]}
        scenes (render/build-scenes-for-compose timeline)]
    (is (= 2 (count scenes)))
    (is (= "park" (:location (first scenes))))
    (is (= [{:speaker "left" :text "a" :emotion "normal"}] (:lines (first scenes))))
    ;; lines sorted by line_index within the scene
    (is (= ["c" "b"] (mapv :text (:lines (second scenes)))))))

(deftest render-empty-timeline-errors
  (is (= "timeline is empty" (:error (g/invoke render/GRAPH {})))))

(deftest render-no-scenes-errors
  (let [final (g/invoke render/GRAPH {:video_id "v1" :timeline {:scenes [] :lines []}})]
    (is (= "no scenes in timeline" (:error final)))))

(deftest render-full-pipeline-with-injected-boundaries
  ;; Inject a renderer that "produces" a real file → exercises the full
  ;; render → upload_video (no creds → blank blob) → write_record → cleanup → audit path.
  (let [written (atom nil)]
    (binding [render/*render-fn* (fn [_scenes out _opts]
                                   (spit out "fake-mp4")
                                   out)
              render/*write-record-fn* (fn [row] (reset! written row))]
      (let [final (g/invoke render/GRAPH
                            {:video_id "vid42"
                             :timeline {:scenes [{:index 0 :location "x" :action "y"}]
                                        :lines [{:scene_index 0 :line_index 0 :text "hi"}]}})]
        (is (nil? (:error final)))
        (is (= "" (:blob_key final)) "no B2 creds → upload skipped with blank key")
        (is (= "done" (:status @written)))
        (is (= "vid42" (:video_id @written)))
        (is (= "at://dougaka.etzhayyim.com/com.etzhayyim.apps.dougaka.render/vid42"
               (:vertex_id @written)))))))

(deftest render-renderer-failure-becomes-error
  (binding [render/*render-fn* (fn [_ _ _] (throw (ex-info "boom" {})))]
    (let [final (g/invoke render/GRAPH
                          {:video_id "v" :timeline {:scenes [{:index 0}]
                                                    :lines [{:scene_index 0 :line_index 0 :text "t"}]}})]
      (is (re-find #"render: " (:error final))))))

(defn run []
  (let [{:keys [fail error]} (run-tests 'lg-dougaka.test-smoke)]
    (System/exit (if (pos? (+ fail error)) 1 0))))
