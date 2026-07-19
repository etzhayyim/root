;; etzhayyim.dodaf — DoDAF DM2 architecture model pure logic (cljc port, wave 3a).
;;
;; Pure-logic port of the non-IO core of
;; 70-tools/etzhayyim-py/src/etzhayyim/dodaf.py
;;
;; Ported (pure logic, no IO):
;;   viewpoints               — DoDAF viewpoint id → description map
;;   skip-dirs                — set of dirs to ignore during filesystem scans
;;   find-viewpoints          — extract DoDAF viewpoint refs from a text string
;;   artifact-counts          — count artifacts by :type
;;   build-tag-cond           — SQL fragment for scope_tags list_contains filter
;;   build-path-cond          — SQL fragment for scope_folders LIKE filter
;;   build-where              — combine tag + path SQL WHERE clause
;;   extract-prose            — strip code blocks/bullets and return first prose paragraph
;;   extract-critical-sections — parse ## CRITICAL: sections from CLAUDE.md text
;;   dodaf-id-from-title      — derive a stable TV-1 entry ID from file+title
;;   dodaf-tags-for-file      — infer scope tags from a relative path
;;   deps-mv-name             — extract VIEW name from a CREATE MATERIALIZED VIEW stmt
;;   seed-tv1 / seed-av2 / seed-ov5   — static seed data builders (pure data, no IO)
;;
;; IO legs deferred (NOT ported):
;;   _scan_dodaf_artifacts  — rglob("*.md", "*.json", "kotodama.jsonld") → babashka.fs
;;   _require_duckdb        — shutil.which + subprocess → babashka.process
;;   _duckdb_query          — subprocess duckdb → babashka.process
;;   _duckdb_query_json     — tempfile + subprocess → babashka.process / babashka.fs
;;   _write_json_to_parquet — tempfile + subprocess → babashka.process
;;   All click CLI commands — wave 4+ (babashka.cli)
;;   dodaf seed (PDS HTTP push) — urllib.request → babashka.http-client
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.dodaf :as dodaf])
;;   (dodaf/find-viewpoints "This section covers AV-1 and OV-5 concerns.")
;;   ;=> ["AV-1" "OV-5"]
;;   (dodaf/dodaf-id-from-title "60-apps/CLAUDE.md" "Shannon Redundancy Prohibition")
;;   ;=> "etzhayyim-project-shannon-redundancy-prohibition"

(ns etzhayyim.dodaf
  (:require [clojure.string :as str]))

;; ── constants ────────────────────────────────────────────────────────────────────

(def viewpoints
  "DoDAF viewpoint id → description map.
   Mirrors Python _VIEWPOINTS dict."
  {"AV-1"   "Overview and Summary"
   "AV-2"   "Integrated Dictionary"
   "OV-1"   "High-Level Operational Concept"
   "OV-2"   "Operational Resource Flow"
   "OV-5"   "Operational Activity Model"
   "SV-1"   "Systems Interface"
   "SV-4"   "Systems Functionality"
   "SvcV-1" "Services Context"
   "SvcV-4" "Services Functionality"
   "DIV-1"  "Conceptual Data Model"
   "DIV-2"  "Logical Data Model"
   "DIV-3"  "Physical Data Model"})

(def skip-dirs
  "Directory names to skip during filesystem scans.
   Mirrors Python _SKIP_DIRS."
  #{"node_modules" ".git" "__pycache__" ".venv" "dist" "build"})

;; ── viewpoint extraction ─────────────────────────────────────────────────────────

(def ^:private viewpoint-pattern
  "Regex matching DoDAF viewpoint codes.
   Mirrors Python _RE_VIEWPOINT."
  #"(?:AV-[12]|OV-[125]|SV-[14]|SvcV-[14]|DIV-[123])")

(defn find-viewpoints
  "Extract distinct DoDAF viewpoint references from a text string.
   Returns a vector of matched codes (e.g. [\"AV-1\" \"OV-5\"]).
   Mirrors Python: list(set(_RE_VIEWPOINT.findall(content)))."
  [text]
  (->> (re-seq viewpoint-pattern (or text ""))
       distinct
       vec))

;; ── artifact counting ─────────────────────────────────────────────────────────────

(defn artifact-counts
  "Count artifacts by :type key.
   Returns a map of type-string → count.
   artifacts = seq of maps with :type key."
  [artifacts]
  (frequencies (map :type artifacts)))

;; ── SQL WHERE clause builders ────────────────────────────────────────────────────

(defn build-tag-cond
  "Build a DuckDB SQL fragment that checks scope_tags contains any of the given tags.
   tag-col  = column name (e.g. \"scope_tags\")
   tag-list = seq of tag strings
   Returns a SQL fragment string, or empty string when tag-list is empty.
   Mirrors Python _build_tag_cond."
  [tag-col tag-list]
  (if (empty? tag-list)
    ""
    (let [parts (map (fn [t]
                       (str "list_contains(" tag-col ", '"
                            (str/replace t "'" "''")
                            "')"))
                     tag-list)]
      (str "(" (str/join " OR " parts) ")"))))

(defn build-path-cond
  "Build a DuckDB SQL fragment for scope_folders path-prefix matching.
   folder-col = column name (e.g. \"scope_folders\") — pass empty string to skip
   path-val   = file path to match against folder prefixes
   Returns a SQL fragment string, or empty string when disabled.
   Mirrors Python _build_path_cond."
  [folder-col path-val]
  (if (or (str/blank? folder-col) (str/blank? path-val))
    ""
    (let [escaped (str/replace path-val "'" "''")]
      (str "(len(" folder-col ") = 0 OR EXISTS "
           "(SELECT 1 FROM unnest(" folder-col ") AS t(f) WHERE '"
           escaped "' LIKE f || '%'))"))))

(defn build-where
  "Combine tag and path SQL conditions into a WHERE clause string.
   Returns \"WHERE a AND b\" or \"\" when no conditions apply.
   Mirrors Python _build_where."
  [tag-col folder-col tag-list path-val]
  (let [parts (remove str/blank?
                       [(build-tag-cond tag-col tag-list)
                        (build-path-cond folder-col path-val)])]
    (if (empty? parts)
      ""
      (str "WHERE " (str/join " AND " parts)))))

;; ── CLAUDE.md critical-section extraction ────────────────────────────────────────

(defn extract-prose
  "Strip code blocks and list markers, return the first prose paragraph (up to 800 chars).
   Mirrors Python _extract_prose(body)."
  [body]
  (let [lines    (str/split-lines (or body ""))
        [_ prose] (reduce (fn [[in-code acc] line]
                             (cond
                               (str/starts-with? line "```")
                               [(not in-code) acc]
                               in-code
                               [in-code acc]
                               (str/blank? line)
                               (if (empty? acc)
                                 [false acc]
                                 (reduced [false acc]))  ; first blank after text → stop
                               (or (str/starts-with? (str/trim line) "|")
                                   (str/starts-with? (str/trim line) "-"))
                               [false acc]
                               :else
                               [false (conj acc (str/trim line))]))
                           [false []]
                           lines)
        rule (str/join " " prose)]
    (if (> (count rule) 800)
      (str (subs rule 0 800) "...")
      rule)))

(defn extract-critical-sections
  "Parse ## CRITICAL: sections from CLAUDE.md text.
   rel-path = relative file path string (for :file metadata).
   Returns a vector of maps: {:file :title :body :rule-text}.
   Mirrors Python _extract_critical_sections(content, rel_path)."
  [text rel-path]
  (let [lines (str/split-lines (or text ""))]
    (loop [lines lines
           cur   nil
           acc   []]
      (if (empty? lines)
        (if cur
          (conj acc (assoc cur :rule-text (extract-prose (:body cur))))
          acc)
        (let [line (first lines)
              rest-lines (rest lines)]
          (cond
            (str/starts-with? line "## CRITICAL:")
            (let [saved (when cur
                          (assoc cur :rule-text (extract-prose (:body cur))))
                  title (str/trim (subs line (count "## CRITICAL:")))]
              (recur rest-lines
                     {:file rel-path :title title :body "" :rule-text ""}
                     (if saved (conj acc saved) acc)))
            (and cur (or (str/starts-with? line "## ")
                         (str/starts-with? line "# ")))
            (recur rest-lines
                   nil
                   (conj acc (assoc cur :rule-text (extract-prose (:body cur)))))
            cur
            (recur rest-lines
                   (update cur :body str line "\n")
                   acc)
            :else
            (recur rest-lines cur acc)))))))

;; ── ID and tag derivation ────────────────────────────────────────────────────────

(defn dodaf-id-from-title
  "Derive a stable TV-1 entry ID from a relative CLAUDE.md path and section title.
   Mirrors Python _dodaf_id_from_title(rel_path, title)."
  [rel-path title]
  (let [parts (str/split rel-path #"/")
        base  (let [b (if (>= (count parts) 2)
                        (nth parts (- (count parts) 2))
                        "root")]
                (if (str/blank? b) "root" b))
        slug  (-> (str/lower-case title)
                  (str/replace " " "-")
                  (str/replace "/" "-")
                  (str/replace "（" "")
                  (str/replace "）" "")
                  (str/replace "(" "")
                  (str/replace ")" "")
                  (str/replace "→" "")
                  (str/replace "`" "")
                  (str/replace "'" "")
                  (str/replace "\"" "")
                  (str/replace "." "-")
                  (str/replace ":" "")
                  (str/replace "　" "-")
                  (str/replace "—" "-")
                  (str/replace "・" "-"))
        ;; collapse repeated hyphens
        slug  (loop [s slug]
                (if (str/includes? s "--")
                  (recur (str/replace s "--" "-"))
                  s))
        slug  (-> slug (str/replace #"^-+|-+$" "") (subs 0 (min 50 (count slug))))
        slug  (str/replace slug #"^-+|-+$" "")
        id_   (str base "-" slug)
        id_   (subs id_ 0 (min 60 (count id_)))
        id_   (str/replace id_ #"^-+|-+$" "")]
    id_))

(defn dodaf-tags-for-file
  "Infer DoDAF scope tags from a relative CLAUDE.md path.
   Mirrors Python _dodaf_tags_for_file(rel_path)."
  [rel-path]
  (cond-> ["claude" "docs"]
    (str/includes? rel-path "60-apps/")    (into ["at-protocol" "kotodama" "typescript"])
    (str/includes? rel-path "50-infra/")   (into ["cloudflare" "infrastructure"])
    (re-find #"orgs/etzhayyim/com-etzhayyim-(svelte-|vite-plugin-safe-builder)" rel-path) (into ["svelte" "frontend"])
    (str/includes? rel-path "30-graph/")   (into ["graph-db" "duckdb"])
    (str/includes? rel-path "70-tools/")   (into ["etzhayyim-cli" "tooling"])
    (= rel-path "CLAUDE.md")              (into ["root-policy"])))

;; ── deps MV name extraction ───────────────────────────────────────────────────────

(defn deps-mv-name
  "Extract the VIEW name from a CREATE MATERIALIZED VIEW IF NOT EXISTS <name> AS ... SQL statement.
   Mirrors Python _deps_mv_name(stmt)."
  [stmt]
  (let [words (str/split stmt #"\s+")]
    (or (some (fn [[i w]]
                (when (= (str/upper-case w) "EXISTS")
                  (some-> (nth words (inc i) nil)
                          (str/replace #";$" "")
                          str/trim)))
              (map-indexed vector words))
        (some (fn [[i w]]
                (when (and (= (str/upper-case w) "VIEW")
                           (let [nxt (nth words (inc i) "")]
                             (not= (str/upper-case nxt) "IF")))
                  (some-> (nth words (inc i) nil)
                          (str/replace #";$" "")
                          str/trim)))
              (map-indexed vector words))
        "?")))

;; ── static seed data (pure data, no IO) ──────────────────────────────────────────

(defn seed-tv1
  "Return the TV-1 seed records as a vector of maps.
   now = ISO 8601 timestamp string (e.g. from (java.time.Instant/now)).
   Mirrors Python _dodaf_seed_tv1(now)."
  [now]
  [{:id "cf-wasm-no-dynamic-compile"
    :view "TV-1"
    :title "CF Workers: WebAssembly.compile() blocked at runtime"
    :standard-ref "Cloudflare Workers V8 embedder policy"
    :rule "WebAssembly.compile(bytes) called at request time returns CompileError: 'Wasm code generation disallowed by embedder'. Only static WASM imports via CompiledWasm wrangler rule are supported."
    :severity "critical"
    :permitted false
    :scope-folders ["60-apps/" "_archive/30-graph/kagami-live-260414/wasm/"]
    :scope-tags ["cloudflare" "wasm" "assemblyscript"]
    :scope-exts [".ts" ".wasm" ".jsonc"]
    :evidence "h0g3t3st.etzhayyim.com/xrpc/com.etzhayyim.apps.hoge.wasmEval — validated 2026-04-08"
    :status "[PRODUCTION]"
    :source "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts"
    :alternative ""
    :created-at now}
   {:id "cf-wasm-static-import-ok"
    :view "TV-1"
    :title "CF Workers: static WASM import via CompiledWasm rule works"
    :standard-ref "Cloudflare Workers CompiledWasm rule"
    :rule "Static WASM import with CompiledWasm wrangler rule works correctly. new WebAssembly.Instance(MODULE, imports) per-request instantiation is ~0ms."
    :severity "info"
    :permitted true
    :scope-folders ["60-apps/" "_archive/30-graph/kagami-live-260414/wasm/"]
    :scope-tags ["cloudflare" "wasm" "assemblyscript"]
    :scope-exts [".ts" ".jsonc"]
    :evidence "h0g3t3st.etzhayyim.com/xrpc/com.etzhayyim.apps.hoge.wasmTest — validated 2026-04-08"
    :status "[PRODUCTION]"
    :source "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts"
    :alternative ""
    :created-at now}
   {:id "xrpc-sole-api"
    :view "TV-1"
    :title "XRPC (/xrpc/{NSID}) is the sole external API surface"
    :standard-ref "AT Protocol XRPC standard"
    :rule "All public API endpoints must use /xrpc/{NSID} format (AT Protocol native). REST endpoints for business mutations are prohibited."
    :severity "critical"
    :permitted false
    :scope-folders ["60-apps/" "50-infra/"]
    :scope-tags ["at-protocol" "xrpc" "typescript"]
    :scope-exts [".ts"]
    :evidence "CLAUDE.md root §XRPC = sole API"
    :status "[PRODUCTION]"
    :source "CLAUDE.md"
    :alternative ""
    :created-at now}])

(defn seed-av2
  "Return the AV-2 integrated-dictionary seed records.
   Mirrors Python _dodaf_seed_av2(now)."
  [now]
  [{:id "compiled-wasm"
    :term "CompiledWasm"
    :definition "Wrangler rule that converts .wasm ESM imports into WebAssembly.Module at bundle time."
    :aliases ["CompiledWasm rule" "wasm static import"]
    :domain "cloudflare"
    :scope-tags ["cloudflare" "wasm"]
    :source "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/wrangler.jsonc"
    :status "[PRODUCTION]"
    :created-at now}
   {:id "xrpc"
    :term "XRPC"
    :definition "AT Protocol Remote Procedure Call format. All public APIs use /xrpc/{NSID} path."
    :aliases ["XRPC" "AT Protocol RPC" "/xrpc/"]
    :domain "at-protocol"
    :scope-tags ["at-protocol" "xrpc" "api"]
    :source "10-protocol/wproto/xrpc/"
    :status "[PRODUCTION]"
    :created-at now}])

(defn seed-ov5
  "Return the OV-5 operational-activities seed records.
   Mirrors Python _dodaf_seed_ov5(now)."
  [now]
  [{:id "ov5-wasm-static-import"
    :action "import MODULE from '*.wasm' (CompiledWasm rule)"
    :permitted true
    :reason "Bundled at deploy time by wrangler CompiledWasm rule. Works on CF Workers V8."
    :scope-tags ["cloudflare" "wasm"]
    :alternative ""
    :source "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts"
    :created-at now}
   {:id "ov5-wasm-dynamic-compile"
    :action "WebAssembly.compile(userBytes) at request time"
    :permitted false
    :reason "Blocked by CF Workers V8 embedder: 'Wasm code generation disallowed by embedder'."
    :scope-tags ["cloudflare" "wasm"]
    :alternative "Pre-bundle WASM at deploy time via CompiledWasm rule"
    :source "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts"
    :created-at now}
   {:id "ov5-synthetic-200"
    :action "Return fabricated data in 200 OK response"
    :permitted false
    :reason "No synthetic data principle: 200 OK must only contain data that exists in graph/DB."
    :scope-tags ["api" "data-integrity"]
    :alternative "Return empty array [] or 404 when data does not exist"
    :source "CLAUDE.md"
    :created-at now}])
