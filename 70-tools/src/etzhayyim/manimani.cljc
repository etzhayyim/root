;; etzhayyim.manimani — manimani personal-knowledge-router CLI over the kotoba Datom log.
;;
;; 「随に / まにまに」: throw a fragment (text / url / file / email) at one ingest;
;; an LLM auto-routes it into an emergent *project*; a per-kind processor turns it
;; into an artifact (facts / todos / summary / deferred). Projects EMERGE from
;; accumulated intake rather than a pre-declared taxonomy.
;;
;; This is the bb/clj entrypoint mandated by repo-root CLAUDE.md ("operational code
;; = clj/bb over the kotoba Datom log") and designed in ADR-2606302038. It is a
;; SECOND MOUTH on ONE STOMACH: it writes the SAME intake/project/artifact/run/todo
;; datoms (ADR-2605291100 §D1) as the (future) XRPC backend, so CLI and edge converge
;; on identical EAVT state.
;;
;; Storage tiers (ADR-2606302038):
;;   local hot tier  → 80-data/manimani/intake.journal.edn (gitignored, PII tier-3)
;;     → kotoba QuadStore + E2E Vault (XChaCha20, CID-over-ciphertext)
;;        → kotobase.net (canonical remote pin — CIPHERTEXT BLOCKS ONLY)
;;           → B2 / DataLad (cold archival)
;; iCloud / Google Drive are NEVER in the persistence path. Gmail is read-only ingest.
;;
;; Inference: Murakumo LiteLLM gateway only (ADR-2605215000); model ids resolve via
;; MURAKUMO_DEFAULT_MODEL, never hardcoded; no-server-key for read-only ops.
;;
;; CLI:  bb e7m manimani ingest "<text>" [--kind knowledge|task|memo|unsorted]
;;       bb e7m manimani ingest-gmail [--backfill]      ; read-only OAuth2 (Phase-3 stub)
;;       bb e7m manimani ingest-fs <root>...            ; allowlist walk + secret-skip (Phase-4 stub)
;;       bb e7m manimani classify <intake-id> <project-slug>
;;       bb e7m manimani projects
;;       bb e7m manimani project <slug>
;;       bb e7m manimani coverage [--days N]
;;       bb e7m manimani pin [--all|<cid>]              ; kotobase.net ciphertext pin (Phase-5 stub)
;;       bb e7m manimani vault init|rotate              ; Keychain read-cap (Phase-2 stub)

(ns etzhayyim.manimani
  (:require [clojure.string :as str]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [etzhayyim.kotoba.engine :as kt])
  (:import [java.security MessageDigest]))

(def ^:private journal "80-data/manimani/intake.journal.edn")
(def ^:private murakumo-gateway "http://127.0.0.1:4000")     ; LiteLLM (ADR-2605215000)
(def ^:private project-kinds #{:knowledge :task :memo :unsorted})

;; secret-skip (hard policy, ADR-2605291100 §D5) — never ingest these from fs:
(def ^:private secret-skip-re
  #"(?i)(/\.ssh/|/\.env|\.pem$|\.key$|_history$|/\.aws/|1password|keychain|/secrets/|\.gnupg/|credentials)")

;; ── identity / time ──────────────────────────────────────────────────────────
(defn- now-ms [] (System/currentTimeMillis))

(defn- sha256-hex [^String s]
  (let [d (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))]
    (apply str (map #(format "%02x" %) d))))

(defn- intake-id
  "Content-addressed-ish intake subject. Phase-0 sha-256 stand-in for the blake3 CID
   (blake3(actor-did + ts + raw-hash)) of ADR-2605291100 §D1 — re-ingest is idempotent."
  [actor-did raw]
  (str "manimani-intake:" (subs (sha256-hex (str actor-did "|" raw)) 0 24)))

(defn- conn [] (kt/connect {:journal journal}))

;; ── read helpers (kqe over the journal) ──────────────────────────────────────
(defn- projects [c]
  (->> (kt/q c '{:find [?e ?slug ?kind ?status]
                 :where [[?e :manimani.project/slug ?slug]
                         [?e :manimani.project/kind ?kind]
                         [?e :manimani.project/status ?status]]})
       (map (fn [[e slug kind status]] {:id e :slug slug :kind kind :status status}))))

(defn- intakes [c]
  (->> (kt/q c '{:find [?e ?proj]
                 :where [[?e :manimani.intake/source-kind _]
                         [?e :manimani.intake/belongs-to ?proj]]})
       (map (fn [[e proj]] {:id e :project proj}))))

;; ── classify (Murakumo structured-output; Phase-0 heuristic fallback) ─────────
(defn murakumo-classify
  "PRODUCTION classifier: one Murakumo LiteLLM structured-output call returning
   {existing-project|new-project, confidence, rationale}; confidence<0.5 → :unsorted.
   Phase-2 seam — wires to murakumo-gateway. Not yet implemented."
  [_raw _existing]
  (throw (ex-info "murakumo-classify not wired (Phase-2)"
                  {:gateway murakumo-gateway :see "ADR-2606302038 §D1 / 2605215000"})))

(defn- heuristic-classify
  "Phase-0 deterministic classifier: keyword-overlap with an existing project slug,
   else :unsorted (confidence<0.5 honest fallback, never silent misclassification)."
  [raw existing]
  (let [low (str/lower-case raw)
        hit (some (fn [{:keys [slug]}]
                    (when (some #(str/includes? low %) (str/split slug #"[-_]")) slug))
                  existing)]
    (if hit
      {:project hit :confidence 0.6 :method :heuristic}
      {:project "unsorted" :confidence 0.3 :method :heuristic})))

;; ── commands ─────────────────────────────────────────────────────────────────
(defn ingest
  "Submit one text intake → classify → emit intake+belongs-to datoms. opts: {:kind :actor}."
  [raw {:keys [kind actor] :or {actor "jun784@gmail.com"}}]
  (let [c (conn)
        existing (projects c)
        {:keys [project confidence method]} (heuristic-classify raw existing)
        slug (or kind project)
        iid (intake-id actor raw)
        ts (now-ms)
        pid (str "manimani-project:" slug)]
    (kt/transact c
      [[pid :manimani.project/slug slug ts :add]
       [pid :manimani.project/kind (if (project-kinds (keyword slug)) (keyword slug) :task) ts :add]
       [pid :manimani.project/status :active ts :add]
       [iid :manimani.intake/source-kind :text ts :add]
       [iid :manimani.intake/raw-ref :deferred ts :add]
       [iid :manimani.intake/sensitivity-ord 2 ts :add]
       [iid :manimani.intake/summary (subs raw 0 (min 280 (count raw))) ts :add]
       [iid :manimani.intake/classify-confidence confidence ts :add]
       [iid :manimani.intake/classify-method method ts :add]
       [iid :manimani.intake/belongs-to pid ts :add]])
    (println (format "→ intake %s → project %s (conf %.2f, %s)" iid slug confidence (name method)))
    iid))

(defn classify
  "Re-route an intake into a different project (writes a fresh belongs-to datom)."
  [iid slug]
  (let [c (conn) ts (now-ms) pid (str "manimani-project:" slug)]
    (kt/transact c [[pid :manimani.project/slug slug ts :add]
                    [pid :manimani.project/status :active ts :add]
                    [iid :manimani.intake/belongs-to pid ts :add]])
    (println (format "→ %s reclassified → %s" iid slug))))

(defn list-projects []
  (let [c (conn) ps (projects c) is (group-by :project (intakes c))]
    (if (empty? ps)
      (println "(no projects yet — `bb e7m manimani ingest \"...\"`)")
      (doseq [{:keys [id slug kind status]} (sort-by :slug ps)]
        (println (format "%-28s %-10s %-8s  intakes:%d" slug (name kind) (name status)
                         (count (get is id))))))))

(defn coverage [days]
  (let [c (conn) ps (projects c) is (intakes c)
        unrouted (count (filter #(str/ends-with? (str (:project %)) "unsorted") is))]
    (println (format "projects:%d  intakes:%d  unrouted:%d  window:%dd" (count ps) (count is) unrouted days))))

;; ── ingest sources / storage ops — external-integration stubs ────────────────
(defn ingest-gmail [_opts]
  (println "ingest-gmail: Phase-3 stub. Plan (ADR-2606302038 §D1, 2605291100 §D4a):")
  (println "  read-only OAuth2 gmail.readonly (token in Keychain, never committed)")
  (println "  → RFC2822 parse → body E2E-encrypted into SecureVault blob")
  (println "  → intake datoms (source-kind :email, source-uri <msg-id>, raw-ref <vault-cid>)")
  (println "  NB: the 2026-06-30 session already hand-wrote 2 email intakes via Claude Code MCP."))

(defn ingest-fs [roots]
  (println "ingest-fs: Phase-4 stub. allowlist roots (read-only) + HARD secret-skip:")
  (doseq [r roots]
    (println (format "  root %s — would walk; skip-re=%s" r (str secret-skip-re))))
  (println "  → Vault chunk (Single/CDC/CodecAware) → BlobManifest CID → intake (source-kind :fs-file)"))

(defn pin [_target]
  (println "pin: Phase-5 stub. Push local CIPHERTEXT blocks → kotobase.net (Kubo-compatible).")
  (println "  secure-by-construction: CID-over-ciphertext; pin host sees only opaque blocks.")
  (println "  config: KOTOBA_IPFS_PIN_ENDPOINT (default https://kotobase.net), ADR-2606091500/2606041130."))

(defn vault [sub]
  (println (format "vault %s: Phase-2 stub. XChaCha20-Poly1305 read-cap in macOS Keychain;" sub))
  (println "  key + nonce NEVER leave the device, NEVER a datom, NEVER pinned (ADR-2605181100)."))

;; ── dispatch ─────────────────────────────────────────────────────────────────
(defn- parse-flags [args]
  (loop [a args m {} pos []]
    (if-let [x (first a)]
      (if (str/starts-with? x "--")
        (recur (drop 2 a) (assoc m (keyword (subs x 2)) (second a)) pos)
        (recur (rest a) m (conj pos x)))
      [pos m])))

(defn -main [& argv]
  (let [[cmd & rest] argv
        [pos flags] (parse-flags rest)]
    (case cmd
      "ingest"       (ingest (first pos) {:kind (:kind flags)})
      "ingest-gmail" (ingest-gmail flags)
      "ingest-fs"    (ingest-fs pos)
      "classify"     (classify (first pos) (second pos))
      "projects"     (list-projects)
      "project"      (list-projects)            ; Phase-0: project detail folds into list
      "coverage"     (coverage (Integer/parseInt (or (:days flags) "7")))
      "pin"          (pin (or (first pos) (:all flags)))
      "vault"        (vault (or (first pos) "status"))
      (do (println "usage: bb e7m manimani <ingest|ingest-gmail|ingest-fs|classify|projects|project|coverage|pin|vault> ...")
          (println "see ADR-2606302038 (CLI + storage tiers) / ADR-2605291100 (kotoba-native)")))))
