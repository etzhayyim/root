(ns aburi.tools.build
  "aburi 炙り — WASM component build (babashka; replaces the old wasm/build.sh).
  ADR-2606161630 + ADR-2606014600. Invoked via `bb aburi:build-wasm`.

  Builds the aburi actor as a WASI Component-Model component with componentize-py and reports its
  IPFS CID. OPERATOR STEP — not run in CI. The pure methods + the representative seed are bundled
  beside app.py (the sandbox has no FS). Requires: python3 (componentize-py via venv), node/npx
  (jco), ipfs, wasm-tools. The componentize-py output bundles CPython → dag-pb multiblock → T2
  donated-mesh tier (ADR-2606014500); the CID is not always byte-reproducible, so re-record on a
  real bump. Returns the built CID string."
  (:require [babashka.fs :as fs]
            [babashka.process :refer [shell]]
            [clojure.string :as str]))

(def ^:private gen-seed-py
  ;; mirror the old shell one-liner: embed the seed EDN as a python string literal
  "import sys,pathlib,json; s=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'); pathlib.Path('_seed.py').write_text('SEED_EDN = '+json.dumps(s)+chr(10), encoding='utf-8'); print(f'_seed.py generated ({len(s)} bytes embedded)')")

(def ^:private sanity-py
  "import app, json; r=json.loads(app.compute()); assert r['own_data'] and r['reciprocity_restoring'] and r['non_adjudicating'], r; print('python sanity OK —', len(r['who_tracks_you']), 'trackers ranked')")

;; bound at LOAD time (*file* is only valid while loading) → tools/ -> aburi/
(def actor-dir (-> *file* fs/parent fs/parent str))

(defn build
  "Run the full build; returns the CID (string). actor-dir defaults to this namespace's actor root."
  ([] (build actor-dir))
  ([actor-dir]
   (let [wasm (fs/file actor-dir "wasm")
         methods (fs/file actor-dir "methods")
         seed (fs/file actor-dir "data" "seed-tracker-exposure.kotoba.edn")
         venv (or (System/getenv "CPY_VENV") "/tmp/cpy-venv")
         opts {:dir (str wasm) :inherit true}]
     ;; 1. bundle the pure methods + embed the seed beside app.py
     (doseq [m ["analyze.py" "datom_emit.py" "coverage_report.py"]]
       (fs/copy (fs/file methods m) (fs/file wasm m) {:replace-existing true}))
     (shell opts "python3" "-c" gen-seed-py (str seed))
     ;; 2. offline sanity — the charter invariants must hold before we build
     (shell opts "python3" "-c" sanity-py)
     ;; 3. componentize-py (install into a venv on first run)
     (when-not (fs/executable? (fs/file venv "bin" "componentize-py"))
       (shell "python3" "-m" "venv" venv)
       (shell (str venv "/bin/pip") "install" "--quiet" "componentize-py"))
     (shell opts (str venv "/bin/componentize-py")
            "-d" "wit" "-w" "aburi-actor" "componentize" "app" "-o" "aburi-actor.wasm")
     (shell opts "wasm-tools" "validate" "aburi-actor.wasm")
     (shell opts "npx" "-y" "@bytecodealliance/jco@latest"
            "transpile" "aburi-actor.wasm" "-o" "transpiled" "--name" "aburi")
     ;; 4. content-address (CIDv1, matches `ipfs add --cid-version=1`)
     (let [cid (-> (shell {:dir (str wasm) :out :string}
                          "ipfs" "add" "-Q" "--only-hash" "--cid-version=1" "aburi-actor.wasm")
                   :out str/trim)
           size (-> (fs/size (fs/file wasm "aburi-actor.wasm")))]
       (println (format "aburi-actor.wasm  %d bytes  CID=%s" size cid))
       (println "If the CID changed, set :actor/wasm-cid in actor-profile-seed.kotoba.edn")
       (println "  and wasmCid in infra-actors.ts + public/actor/aburi/{did,profile}.json.")
       (println "NOTE: dag-pb (multi-block, bundles CPython) → T2 donated-mesh tier (ADR-2606014500).")
       cid))))

(defn -main [& _]
  (build)
  (System/exit 0))
