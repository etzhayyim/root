(ns etzhayyim.organism-publish
  "Regenerate the /organism live feeds from the kotoba Datom log and publish them
  to etzhayyim.com — the clj/bb replacement for the removed
  50-infra/etzhayyim-did-web/scripts/organism-pulse-deploy.sh (root CLAUDE.md:
  operational code = clj/bb over the kotoba Datom log, not .sh).

  Why this exists: the resident `organism:heartbeat` loop writes fresh pulse/health
  JSON locally every few seconds, but the CF Worker serves `public/` STATICALLY —
  so production only updates on a `wrangler deploy`. There is no deploy step inside
  the heartbeat loop, so without this published feed the live site goes stale even
  while the local loop is healthy. Run this on a coarse LaunchAgent
  (com.etzhayyim.organism.publish, every 2 min) to keep etzhayyim.com/organism/*
  and /murakumo current.

  The pulse/joucho/trajectory feeds are produced IN-PROCESS by etzhayyim.vitals —
  the very fns the heartbeat folds every 6 s, so they never System/exit. Only the
  deploy shells out to npm/wrangler (system binaries, allowed via babashka.process;
  the rule bars authoring LOGIC in .sh, not invoking installed tools)."
  (:require [etzhayyim.vitals :as vitals]
            [babashka.process :as p]))

(def ^:private worker-dir "50-infra/etzhayyim-did-web")

(defn -publish
  "Regenerate pulse (and, with --full, also joucho + trajectory) from the kotoba
  Datom log, then publish to etzhayyim.com via `npm run deploy` in the did-web
  worker dir. Assumes cwd = repo root (the LaunchAgent sets WorkingDirectory)."
  [& args]
  (let [full? (boolean (some #{"--full"} args))]
    (println "[organism] regenerating live feeds…")
    (vitals/-pulse)
    (when full?
      (vitals/-joucho)
      (try (vitals/-trajectory)
           (catch Throwable e (println "[organism] trajectory skipped:" (ex-message e)))))
    (println "[organism] publishing to etzhayyim.com (npm run deploy)…")
    (let [{:keys [exit]} (p/shell {:dir worker-dir :continue true :inherit true}
                                  "npm" "run" "deploy")]
      (if (zero? exit)
        (println "[organism] live → https://etzhayyim.com/organism/")
        (do (println "[organism] deploy FAILED (exit" exit ")")
            (System/exit exit))))))
