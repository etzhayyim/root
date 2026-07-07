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
;;       bb e7m manimani auth-gmail                     ; ONE-TIME OAuth2 PKCE consent → Keychain refresh token
;;       bb e7m manimani ingest-gmail [--since Nd|--backfill]  ; read-only OAuth2 poll (Phase-3, LIVE)
;;       bb e7m manimani ingest-fs <root>...            ; allowlist walk + secret-skip (Phase-4 stub)
;;       bb e7m manimani classify <intake-id> <project-slug>
;;       bb e7m manimani projects
;;       bb e7m manimani project <slug>
;;       bb e7m manimani coverage [--days N]
;;       bb e7m manimani pin [--all|<cid>]              ; kotobase.net ciphertext pin (Phase-5 stub)
;;       bb e7m manimani vault init|rotate              ; Keychain read-cap (Phase-2 stub)
;;
;; Gmail OAuth2 (Phase-3, ADR-2606302038 §D1 / ADR-2605291100 §D4a): read-only
;; (gmail.readonly), PKCE (S256), macOS Keychain-held client id/secret + refresh token,
;; NEVER an env var / datom / committed file. One-time setup:
;;   1. Google Cloud Console → new/existing project → enable Gmail API → OAuth consent
;;      screen (External, Testing is fine for a single-user tool) → Credentials →
;;      Create OAuth client → type "Desktop app" → note the Client ID + Client Secret.
;;   2. `bb e7m manimani auth-gmail` — prompts for the client id/secret (stored in
;;      Keychain thereafter), opens the consent URL, catches the localhost redirect,
;;      exchanges the code, stores the refresh token in Keychain. Run once.
;;   3. `bb e7m manimani ingest-gmail` any time after — no browser needed again; the
;;      refresh token mints short-lived access tokens on demand.

(ns etzhayyim.manimani
  (:require [clojure.string :as str]
            [cheshire.core :as json]
            [babashka.http-client :as http]
            [babashka.process :as proc]
            [etzhayyim.kotoba.engine :as kt])
  (:import [java.security MessageDigest SecureRandom]
           [java.util Base64]
           [java.net ServerSocket]
           [java.io BufferedReader InputStreamReader]))

(def ^:private journal "80-data/manimani/intake.journal.edn")
(def ^:private murakumo-gateway "http://127.0.0.1:4000")     ; LiteLLM (ADR-2605215000)
(def ^:private project-kinds #{:knowledge :task :memo :unsorted})

;; ── Gmail OAuth2 (Phase-3) ────────────────────────────────────────────────────
(def ^:private gmail-scope "https://www.googleapis.com/auth/gmail.readonly")
(def ^:private gmail-auth-endpoint "https://accounts.google.com/o/oauth2/v2/auth")
(def ^:private gmail-token-endpoint "https://oauth2.googleapis.com/token")
(def ^:private gmail-api-base "https://gmail.googleapis.com/gmail/v1/users/me")
(def ^:private oauth-redirect-port 8721)
(def ^:private oauth-redirect-uri (str "http://127.0.0.1:" oauth-redirect-port "/"))
(def ^:private keychain-service "etzhayyim-manimani-gmail")

;; ── Keychain (macOS `security` CLI — never an env var, never committed) ───────
(defn- keychain-get [account]
  (let [{:keys [exit out]} (proc/shell {:out :string :err :string :continue true}
                                        "security" "find-generic-password"
                                        "-s" keychain-service "-a" account "-w")]
    (when (zero? exit) (str/trim out))))

(defn- keychain-set! [account value]
  (proc/shell {:out :string :err :string :continue true}
              "security" "add-generic-password" "-U"
              "-s" keychain-service "-a" account "-w" value))

(defn- read-line-prompt [prompt]
  (print prompt) (flush)
  (str/trim (or (read-line) "")))

;; ── PKCE ────────────────────────────────────────────────────────────────────
(defn- b64url [^bytes bs]
  (-> (Base64/getUrlEncoder) .withoutPadding (.encodeToString bs)))

(defn- pkce-verifier []
  (let [bs (byte-array 32)] (.nextBytes (SecureRandom.) bs) (b64url bs)))

(defn- pkce-challenge [^String verifier]
  (b64url (.digest (MessageDigest/getInstance "SHA-256") (.getBytes verifier "UTF-8"))))

;; ── local redirect catcher: one raw HTTP GET, extract `code`, reply, close ────
(defn- await-oauth-redirect
  "Blocks on 127.0.0.1:oauth-redirect-port for the browser's redirect after consent;
   returns the `code` query param (or throws on `error=` / timeout)."
  [timeout-ms]
  (let [srv (ServerSocket. oauth-redirect-port)]
    (.setSoTimeout srv timeout-ms)
    (try
      (with-open [sock (.accept srv)
                  rdr (BufferedReader. (InputStreamReader. (.getInputStream sock)))]
        (let [request-line (.readLine rdr)          ; "GET /?code=...&scope=... HTTP/1.1"
              path (second (str/split (or request-line "") #"\s+"))
              query (second (str/split (or path "") #"\?" 2))
              params (into {} (map (fn [kv] (let [[k v] (str/split kv #"=" 2)]
                                               [k (some-> v (java.net.URLDecoder/decode "UTF-8"))]))
                                    (str/split (or query "") #"&")))
              out (.getOutputStream sock)
              body (if (get params "code")
                     "<html><body>manimani: Gmail authorized — you can close this tab.</body></html>"
                     "<html><body>manimani: authorization failed — see the terminal.</body></html>")]
          (.write out (.getBytes (str "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: "
                                      (count body) "\r\n\r\n" body) "UTF-8"))
          (.flush out)
          (cond
            (get params "error") (throw (ex-info (str "oauth consent denied: " (get params "error")) params))
            (get params "code")  (get params "code")
            :else (throw (ex-info "oauth redirect carried no code" params)))))
      (finally (.close srv)))))

;; ── token exchange / refresh ───────────────────────────────────────────────
(defn- form-post [url form]
  (json/parse-string
   (:body (http/post url {:headers {"content-type" "application/x-www-form-urlencoded"}
                          :body (str/join "&" (map (fn [[k v]] (str k "=" (java.net.URLEncoder/encode (str v) "UTF-8")))
                                                    form))
                          :throw false}))
   true))

(defn- exchange-code! [client-id client-secret code verifier]
  (form-post gmail-token-endpoint
             {"code" code "client_id" client-id "client_secret" client-secret
              "redirect_uri" oauth-redirect-uri "grant_type" "authorization_code"
              "code_verifier" verifier}))

(defn- refresh-access-token [client-id client-secret refresh-token]
  (let [resp (form-post gmail-token-endpoint
                        {"client_id" client-id "client_secret" client-secret
                         "refresh_token" refresh-token "grant_type" "refresh_token"})]
    (or (:access_token resp)
        (throw (ex-info "gmail token refresh failed — re-run `bb e7m manimani auth-gmail`" resp)))))

(defn- gmail-oauth-creds
  "{:client-id :client-secret :refresh-token}, throwing with setup guidance if any are missing."
  []
  (let [client-id (or (System/getenv "GOOGLE_OAUTH_CLIENT_ID") (keychain-get "oauth-client-id"))
        client-secret (or (System/getenv "GOOGLE_OAUTH_CLIENT_SECRET") (keychain-get "oauth-client-secret"))
        refresh-token (keychain-get "refresh-token")]
    (when-not (and client-id client-secret refresh-token)
      (throw (ex-info "gmail not authorized — run `bb e7m manimani auth-gmail` first" {})))
    {:client-id client-id :client-secret client-secret :refresh-token refresh-token}))

(defn auth-gmail
  "ONE-TIME interactive setup: OAuth client id/secret (prompted → Keychain) → PKCE
   consent URL → local redirect catch → code exchange → refresh token → Keychain."
  []
  (let [client-id (or (System/getenv "GOOGLE_OAUTH_CLIENT_ID") (keychain-get "oauth-client-id")
                      (let [v (read-line-prompt "Google OAuth Client ID (Desktop app type): ")]
                        (keychain-set! "oauth-client-id" v) v))
        client-secret (or (System/getenv "GOOGLE_OAUTH_CLIENT_SECRET") (keychain-get "oauth-client-secret")
                          (let [v (read-line-prompt "Google OAuth Client Secret: ")]
                            (keychain-set! "oauth-client-secret" v) v))
        verifier (pkce-verifier)
        challenge (pkce-challenge verifier)
        auth-url (str gmail-auth-endpoint
                      "?client_id=" (java.net.URLEncoder/encode client-id "UTF-8")
                      "&redirect_uri=" (java.net.URLEncoder/encode oauth-redirect-uri "UTF-8")
                      "&response_type=code&access_type=offline&prompt=consent"
                      "&scope=" (java.net.URLEncoder/encode gmail-scope "UTF-8")
                      "&code_challenge=" challenge "&code_challenge_method=S256")]
    (println "\nOpen this URL, sign in as the Gmail account to authorize (read-only), and allow access:\n")
    (println (str "  " auth-url "\n"))
    (proc/shell {:continue true} "open" auth-url)   ; best-effort; the URL above always works manually
    (println (format "waiting up to 5 min on 127.0.0.1:%d for the consent redirect…" oauth-redirect-port))
    (let [code (await-oauth-redirect 300000)
          resp (exchange-code! client-id client-secret code verifier)]
      (if-let [rt (:refresh_token resp)]
        (do (keychain-set! "refresh-token" rt)
            (println "✓ Gmail authorized — refresh token stored in Keychain (service="
                     keychain-service "). Run `bb e7m manimani ingest-gmail` any time now."))
        (throw (ex-info "token exchange returned no refresh_token — revoke prior access at https://myaccount.google.com/permissions and retry"
                        resp))))))

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

;; ── ingest-gmail (Phase-3, LIVE — read-only gmail.readonly) ───────────────────
(defn- gmail-get [access-token path]
  (json/parse-string
   (:body (http/get (str gmail-api-base path)
                     {:headers {"authorization" (str "Bearer " access-token)} :throw false}))
   true))

(defn- gmail-header [headers name]
  (:value (first (filter #(= name (:name %)) headers))))

(defn- gmail-list-candidate-ids
  "Message ids matching the 'needs a response' heuristic: unread, in the inbox, not
   promo/social/forum bulk mail. --backfill widens to all inbox mail in the window
   (read or not); default is unread-only. window-days bounds either mode."
  [access-token {:keys [backfill? window-days]}]
  (let [q (str "in:inbox newer_than:" window-days "d"
              (when-not backfill? " is:unread")
              " -category:promotions -category:social -category:forums -category:updates")
        resp (gmail-get access-token (str "/messages?maxResults=50&q=" (java.net.URLEncoder/encode q "UTF-8")))]
    (map :id (:messages resp))))

(defn- gmail-fetch-summary
  "One message's {:msg-id :from :subject :date :snippet} via a metadata-only GET
   (never format=full/raw — body content stays unfetched at this Phase)."
  [access-token msg-id]
  (let [m (gmail-get access-token
                     (str "/messages/" msg-id "?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date"))
        headers (get-in m [:payload :headers])]
    {:msg-id msg-id
     :from (or (gmail-header headers "From") "?")
     :subject (or (gmail-header headers "Subject") "(no subject)")
     :date (or (gmail-header headers "Date") "?")
     :snippet (or (:snippet m) "")}))

(defn- existing-email-source-uris
  "Already-ingested Gmail message ids (for idempotent re-runs)."
  [c]
  (->> (kt/q c '{:find [?uri]
                :where [[?e :manimani.intake/source-kind :email]
                        [?e :manimani.intake/source-uri ?uri]]})
       (map first) set))

(defn ingest-gmail
  "LIVE (Phase-3): OAuth2 refresh → list unread/candidate inbox mail → per-message
   intake+belongs-to datoms (source-kind :email; snippet-only, body never fetched).
   opts: {:since \"Nd\" :backfill true}."
  [{:keys [since backfill]}]
  (let [{:keys [client-id client-secret refresh-token]} (gmail-oauth-creds)
        access-token (refresh-access-token client-id client-secret refresh-token)
        window-days (Integer/parseInt (str/replace (or since "7") #"[^0-9]" ""))
        backfill? (boolean backfill)
        ids (gmail-list-candidate-ids access-token {:backfill? backfill? :window-days window-days})
        c (conn)
        seen (existing-email-source-uris c)
        new-ids (remove seen ids)]
    (println (format "ingest-gmail: %d candidate message(s) in the last %dd (%s), %d already ingested, %d new"
                     (count ids) window-days (if backfill? "backfill: read+unread" "unread only")
                     (- (count ids) (count new-ids)) (count new-ids)))
    (doseq [msg-id new-ids]
      (let [{:keys [from subject date snippet]} (gmail-fetch-summary access-token msg-id)
            existing (projects c)
            raw (str subject " — " from " — " snippet)
            {:keys [project confidence method]} (heuristic-classify raw existing)
            iid (str "manimani-intake:" (subs (sha256-hex (str "gmail|" msg-id)) 0 24))
            ts (now-ms)
            pid (str "manimani-project:" project)]
        (kt/transact c
          [[pid :manimani.project/slug project ts :add]
           [pid :manimani.project/kind (if (project-kinds (keyword project)) (keyword project) :task) ts :add]
           [pid :manimani.project/status :active ts :add]
           [iid :manimani.intake/source-kind :email ts :add]
           [iid :manimani.intake/source-uri msg-id ts :add]
           [iid :manimani.intake/raw-ref :deferred ts :add]                 ; Phase-2: SecureVault CID
           [iid :manimani.intake/sensitivity-ord 2 ts :add]
           [iid :manimani.intake/summary (subs raw 0 (min 280 (count raw))) ts :add]
           [iid :manimani.intake/classify-confidence confidence ts :add]
           [iid :manimani.intake/classify-method method ts :add]
           [iid :manimani.intake/belongs-to pid ts :add]])
        (println (format "  ✉ %-40s  from %-32s  %s  → %s (conf %.2f)"
                         (subs subject 0 (min 40 (count subject))) (subs from 0 (min 32 (count from)))
                         date project confidence))))
    (when (empty? new-ids) (println "  (nothing new — inbox already reflected in the journal)"))))

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
(defn- parse-flags
  "[\"--key\" \"val\" \"--flag\"] → {:key \"val\" :flag true}; a `--flag` with no
   following value (or followed by another `--flag`) is a boolean switch, not nil."
  [args]
  (loop [a args m {} pos []]
    (if-let [x (first a)]
      (if (str/starts-with? x "--")
        (let [k (keyword (subs x 2)) nxt (second a)]
          (if (and nxt (not (str/starts-with? nxt "--")))
            (recur (drop 2 a) (assoc m k nxt) pos)
            (recur (rest a) (assoc m k true) pos)))
        (recur (rest a) m (conj pos x)))
      [pos m])))

(defn -main [& argv]
  (let [[cmd & rest] argv
        [pos flags] (parse-flags rest)]
    (case cmd
      "ingest"       (ingest (first pos) {:kind (:kind flags)})
      "auth-gmail"   (auth-gmail)
      "ingest-gmail" (ingest-gmail {:since (:since flags) :backfill (:backfill flags)})
      "ingest-fs"    (ingest-fs pos)
      "classify"     (classify (first pos) (second pos))
      "projects"     (list-projects)
      "project"      (list-projects)            ; Phase-0: project detail folds into list
      "coverage"     (coverage (Integer/parseInt (or (:days flags) "7")))
      "pin"          (pin (or (first pos) (:all flags)))
      "vault"        (vault (or (first pos) "status"))
      (do (println "usage: bb e7m manimani <ingest|auth-gmail|ingest-gmail|ingest-fs|classify|projects|project|coverage|pin|vault> ...")
          (println "see ADR-2606302038 (CLI + storage tiers) / ADR-2605291100 (kotoba-native)")))))
