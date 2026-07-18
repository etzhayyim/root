#!/usr/bin/env bb
;; mesh_migrate.clj — scaffold the KOTOBA Mesh hosting face of an etzhayyim actor.
;;
;; Generalizes the kabuto/busshi mesh pilot (ADR kotoba-mesh-wasm-hosting): for a
;; clj-native actor it emits the two artifacts that put the actor on the KOTOBA
;; Mesh lattice (kotoba-lattice) —
;;   • kotoba.app.edn   — wadm-style manifest (http trigger /<id>, cap/kqe)
;;   • methods/mesh.clj  — run + on-http component SCAFFOLD (kotoba-clj subset):
;;                         observe a slice as Datom assertions, derive via Datalog.
;;
;; The manifest is fully mechanical. The mesh.clj body is a SCAFFOLD the actor
;; author fills with the actor's real kotoba-native slice (kabuto = supply edges,
;; busshi = producer concentration) — the full `.cljc` analyze logic stays put
;; until kotoba-clj grows maps/sort/decimals.
;;
;; Usage (from repo root):
;;   bb 70-tools/scripts/mesh_migrate.clj orgs/etzhayyim/com-etzhayyim-<actor> [...more]
;;   bb 70-tools/scripts/mesh_migrate.clj --all     # every clj-native actor w/o a mesh.clj
;;
;; Idempotent: never overwrites an existing methods/mesh.clj or kotoba.app.edn.
;; Verify each result with:  kotoba component build orgs/etzhayyim/com-etzhayyim-<actor>/src/<actor>/methods/mesh.clj

(require '[clojure.edn :as edn]
         '[clojure.string :as str]
         '[babashka.fs :as fs])

(defn- read-edn-manifest [dir]
  (let [f (fs/file dir "manifest.edn")]
    (when (fs/exists? f)
      (let [m (edn/read-string (slurp (fs/file f)))]
        {:id (:actor/id m) :glyph (:actor/glyph m)}))))

(defn- read-jsonld-manifest [dir]
  (let [f (fs/file dir "manifest.jsonld")]
    (when (fs/exists? f)
      (let [s (slurp (fs/file f))
            grab (fn [k] (second (re-find (re-pattern (str "\"" k "\"\\s*:\\s*\"([^\"]+)\"")) s)))]
        {:id (some-> (or (grab "name") (grab "id")) (str/replace #"^actor:" ""))
         :glyph (grab "glyph")}))))

(defn- actor-meta [dir]
  (or (read-edn-manifest dir) (read-jsonld-manifest dir)
      {:id (fs/file-name dir) :glyph ""}))

(defn- manifest-edn [{:keys [id glyph]}]
  (format ";; kotoba.app.edn — actor:%s %s KOTOBA Mesh application manifest (generated scaffold).
;; Deploy:  kotoba app deploy kotoba.app.edn  (compiles methods/mesh.clj → CID → control datoms)
{:kotoba.app/name    \"%s\"
 :kotoba.app/version \"0.1.0\"
 :kotoba.app/components
 [{:name     \"%s\"
   :src      \"methods/mesh.clj\"                  ; Clojure default → run + on-http
   :scale    1
   :triggers [{:type :http :route \"/%s\"}]
   :requires #{:cap/kqe}}]

 :kotoba.app/placement {:spread  :zone
                        :require {:tier \"edge\"}}}
" id glyph id id id))

(defn- mesh-clj [{:keys [id glyph]}]
  (format ";; mesh.clj — %s %s KOTOBA Mesh entry component (Clojure / kotoba-clj) — GENERATED SCAFFOLD.
;;
;; The mesh-hosting face of actor:%s. Compiled by kotoba-clj into a real
;; kotoba:kais WASM component and placed by the KOTOBA Mesh lattice. SCAFFOLD —
;; replace the observe/derive bodies with this actor's real kotoba-native slice
;; (cf. kabuto = supply edges, busshi = producer concentration). The full
;; .cljc analyze logic stays put until kotoba-clj grows maps/sort/decimals.
;;
;; host-imports used:  kqe-assert! / kqe-query  → kotoba:kais/kqe  (needs cap/kqe)
(ns %s)

(defn run [ctx]
  ;; observe — assert this actor's representative slice into the append-only
  ;; kotoba Datom log (graph \"%s\"). Aggregate-first; never a target-list.
  (kqe-assert! \"%s\" \"subject\" \"relates\" \"object\")   ;; TODO: real %s observations
  ;; derive — Datalog over the same datoms (a resilience/accountability map).
  (kqe-query \"derived(?s) :- relates(?s).\"))

(defn on-http [req]
  ;; read path for the /%s route.
  (kqe-query \"derived(?s) :- relates(?s).\"))
" id glyph id id id id id id id))

(defn- emit! [dir]
  (let [m (actor-meta dir)
        man (fs/file dir "kotoba.app.edn")
        mesh (fs/file dir "methods" "mesh.clj")
        wrote (atom [])]
    (when-not (:id m)
      (println "  ! skip (no actor id):" (str dir)) )
    (fs/create-dirs (fs/file dir "methods"))
    (when-not (fs/exists? mesh)
      (spit (fs/file mesh) (mesh-clj m)) (swap! wrote conj "methods/mesh.clj"))
    (when-not (fs/exists? man)
      (spit (fs/file man) (manifest-edn m)) (swap! wrote conj "kotoba.app.edn"))
    (println (format "  %s %s → %s"
                     (:glyph m) (:id m)
                     (if (seq @wrote) (str/join " + " @wrote) "(already migrated, left as-is)")))))

(defn- clj-native? [dir]
  (and (fs/directory? dir)
       (seq (concat (fs/glob dir "methods/*.clj{,c}") (fs/glob dir "cells/*.clj{,c}")))))

(let [args *command-line-args*
      dirs (if (= (first args) "--all")
             (filter clj-native? (map str (fs/list-dir "20-actors")))
             args)]
  (when (empty? dirs)
    (println "usage: bb 70-tools/scripts/mesh_migrate.clj <orgs/etzhayyim/com-etzhayyim-actor>... | --all")
    (System/exit 1))
  (println (format "mesh-migrate: scaffolding %d actor(s)" (count dirs)))
  (doseq [d dirs] (emit! d))
  (println "done. verify: kotoba component build <actor>/methods/mesh.clj"))
