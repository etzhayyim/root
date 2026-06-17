(ns ibuki.methods.perception
  "perception — R2: the live perception membrane. ADR-2606101200 §R2.
  Clojure port of `methods/perception.py`.

  What the organism PERCEIVES each beat. Two sources, one closed vocabulary (joucho):

    - `representative-events` — the bounded deterministic R0/R1 stimulus pattern
      (idle every beat, a follower every 3rd, inbox pressure every 5th). The default, and
      the fail-open fallback: offline, no I/O, replay-safe.
    - `observe` (the LivePerception path) — READ-ONLY public XRPC observation (substrate
      boundary: \"read-only RPC / firehose subscribe\" is in the Allowed column; the
      organism only *looks*). It fetches the actor's public profile from an ALLOWLISTED
      AppView host (GET only — a non-allowlisted host or a non-GET shape raises before
      any I/O), compares follower count against the last `:perception/*` snapshot on the
      Datom log, and maps the delta into closed joucho events. Any failure falls back to
      the representative pattern — the organism keeps living offline.

  Live mode is enabled by `IBUKI_PERCEPTION_LIVE=1` (operator env, per the Council-gate-as-
  PR-merge direction of 2026-06-10: the code path is complete; *turning it on* is an explicit
  runtime act). Offline beats emit NO perception datoms, so offline head CIDs are unchanged
  from R1 — determinism tests stay byte-identical.

  HTTP is an INJECTABLE fn (`*http-get*` dynamic var or the `:fetch` option key,
  the ibuki.methods.infer pattern) defaulting to a babashka/JVM implementation
  (`babashka.http-client` via requiring-resolve); the default fetch enforces the
  allowlist BEFORE any I/O. No credential is ever read here: public endpoints only,
  the platform signs nothing (G7)."
  (:require [clojure.string :as str]
            [ibuki.methods.datoms :as datoms]))

;; READ-ONLY public AppView hosts the membrane may observe. HTTPS GET only.
(def allowed-xrpc-hosts
  #{"public.api.bsky.app"})

(def live-env "IBUKI_PERCEPTION_LIVE")

;; how many :event/follower-gained one beat may fold (a 10k-follower spike must not
;; saturate joy in a single beat — growth is a trajectory, not a step function)
(def follower-event-cap 3)

;; how many :event/reaction-received one beat may fold. Reactions (like/love/comment/
;; repost on the organism's OWN posts) are a REWARD INPUT (ADR-2606171800 — the organism
;; feels being seen), but the OBJECTIVE is wellbecoming, never the count: a viral post is
;; CAPPED here so engagement can never become the thing maximized. Felt, bounded, un-farmable.
(def reaction-event-cap 3)

;; ── PerceptionBoundaryViolation ───────────────────────────────────────────

(defn perception-boundary-violation
  "A perception fetch was requested outside the read-only allowlist."
  [msg url]
  (ex-info msg {:ibuki/perception-boundary-violation true :url url}))

(defn perception-boundary-violation? [e]
  (boolean (:ibuki/perception-boundary-violation (ex-data e))))

(defn- url-parts
  "Minimal portable urlsplit: {:scheme :host} (both lower-cased), nil parts when
  the url has no scheme://netloc shape."
  [url]
  (if-let [[_ scheme netloc]
           (re-find #"^([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)" (str url))]
    {:scheme (str/lower-case scheme) :host (str/lower-case netloc)}
    {:scheme nil :host nil}))

(defn assert-allowed
  "Refuse any perception endpoint outside the read-only https allowlist. Returns
  nil on the allowlist; throws PerceptionBoundaryViolation otherwise."
  [url]
  (let [{:keys [scheme host]} (url-parts url)]
    (when-not (and (= "https" scheme) (contains? allowed-xrpc-hosts host))
      (throw (perception-boundary-violation
              (str "perception endpoint " (pr-str url)
                   " is outside the read-only allowlist "
                   (vec (sort allowed-xrpc-hosts)))
              url)))
    nil))

;; ── the bounded deterministic stimulus pattern ────────────────────────────

(defn representative-events
  "The bounded deterministic stimulus pattern (R0/R1 default + live fallback)."
  [beat]
  (cond-> [":event/idle"]
    (zero? (mod beat 3)) (conj ":event/follower-gained")
    (zero? (mod beat 5)) (conj ":event/inbox-pressure")))

;; ── injectable HTTP edge (read-only GET, allowlist-guarded) ───────────────
;;
;; Contract: (fetch url) → the endpoint's JSON response parsed to a map with
;; STRING keys (Python json.loads parity — `followersCount` is wire schema,
;; not kebab-cased). ANY throw is treated as fail-open by `events-for-beat`.

#?(:clj
   (defn default-http-get
     "GET an allowlisted public XRPC endpoint and parse JSON (string keys). The
     ONLY I/O in this module — read-only, unauthenticated, allowlist-guarded.
     `babashka.http-client` + `cheshire` are loaded lazily via requiring-resolve."
     ([url] (default-http-get url 5.0))
     ([url timeout-s]
      (assert-allowed url)
      (let [get* (requiring-resolve 'babashka.http-client/get)
            parse (requiring-resolve 'cheshire.core/parse-string)
            resp (get* (str url)
                       {:headers {"Accept" "application/json"}
                        :timeout (long (* 1000 (double timeout-s)))})]
        (parse (:body resp))))))

(def ^:dynamic *http-get*
  "The injectable read-only fetch fn (see contract above). Rebind, or pass
  `:fetch` in the options map, to stub the AppView in hermetic tests."
  #?(:clj default-http-get :default nil))

(defn- url-quote
  "Python `urllib.parse.quote(s, safe='')` parity: percent-encode everything
  but ALPHA / DIGIT / `_.-~`."
  [s]
  #?(:clj (-> (java.net.URLEncoder/encode (str s) "UTF-8")
              (str/replace "+" "%20")
              (str/replace "*" "%2A")
              (str/replace "%7E" "~"))
     :default (throw (ex-info "url-quote: no host impl" {}))))

;; ── live observation (the LivePerception path) ────────────────────────────

(defn- feed-reactions
  "Total reactions across the organism's own recent posts (like + reply + repost counts).
  Public wire schema (getAuthorFeed). A SUM, fed as a capped delta — never a per-post rank."
  [feed]
  (reduce (fn [acc item]
            (let [p (get item "post")]
              (+ acc (long (get p "likeCount" 0))
                     (long (get p "replyCount" 0))
                     (long (get p "repostCount" 0)))))
          0 (get feed "feed" [])))

(defn observe
  "One observation of one actor (did or handle) — READ-ONLY public observation → closed
  joucho events. Two reward inputs (ADR-2606171800): follower growth and reactions on the
  organism's OWN posts (the organism feels being seen). Both CAPPED so engagement can never
  become the objective. `:fetch` is injectable for hermetic tests; the default enforces the
  allowlist. `prev` may be an int (legacy = prev followers) or a map {:followers :reactions}.
  The reaction sub-fetch is resilient: any failure → no reaction delta (the organism simply
  does not feel reactions that beat). Returns {:followers :reactions :events [closed kinds]}."
  ([actor prev] (observe actor prev {}))
  ([actor prev {:keys [fetch]}]
   (let [prev (if (map? prev) prev {:followers prev})
         f (or fetch *http-get*)
         profile (f (str "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile"
                         "?actor=" (url-quote actor)))
         followers (long (get profile "followersCount" 0))
         prev-f (:followers prev)
         gained (if (and (some? prev-f) (> followers prev-f))
                  (min (- followers prev-f) follower-event-cap) 0)
         prev-r (:reactions prev)
         reactions (try (feed-reactions
                         (f (str "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
                                 "?actor=" (url-quote actor) "&limit=30")))
                        (catch #?(:clj Exception :cljs :default) e
                          (when (perception-boundary-violation? e) (throw e))
                          (or prev-r 0)))   ;; resilient: no spurious reaction delta on failure
         received (if (and (some? prev-r) (> reactions prev-r))
                    (min (- reactions prev-r) reaction-event-cap) 0)]
     {:followers followers :reactions reactions
      :events (into [":event/idle"]
                    (concat (repeat gained ":event/follower-gained")
                            (repeat received ":event/reaction-received")))})))

(defn- env-live?
  "The IBUKI_PERCEPTION_LIVE=1 gate, read from the real process env."
  []
  #?(:clj (= "1" (System/getenv live-env))
     :default false))

;; ── the membrane's single entry point ─────────────────────────────────────

(defn events-for-beat
  "(events, snapshot|nil) for one organism-beat, returned as a 2-vector.

  snapshot is nil on every offline/representative beat — offline logs carry no
  perception datoms, so R1 head CIDs are unchanged. Live failures fall back to
  the representative pattern (fail-open); a boundary violation is a bug, never
  silently absorbed (rethrown).

  Options: :actor :prev-followers :prev-reactions :live :fetch."
  ([beat] (events-for-beat beat {}))
  ([beat {:keys [actor prev-followers prev-reactions live fetch] :or {actor ""}}]
   (let [is-live (if (some? live) (boolean live) (env-live?))]
     (if (or (not is-live) (str/blank? (str actor)))
       [(representative-events beat) nil]
       (try
         (let [obs (observe actor {:followers prev-followers :reactions prev-reactions} {:fetch fetch})]
           [(:events obs) {:followers (:followers obs) :reactions (:reactions obs)}])
         (catch #?(:clj Exception :cljs :default) e
           (if (perception-boundary-violation? e)
             (throw e)   ;; a boundary violation is a bug, never silently absorbed
             [(representative-events beat) nil])))))))

(defn perception-datoms
  "Checkpoint a live observation as `:perception/*` datoms (the durable prev-follower /
  prev-reaction snapshot the NEXT beat diffs against — perception history is as-of like
  everything). `reactions` may be nil (legacy callers); omitted when nil.
  Opts: :beat :as-of."
  ([of followers opts] (perception-datoms of followers nil opts))
  ([of followers reactions {:keys [beat as-of]}]
   (let [e (str "perc-" of "-" beat)]
     (cond-> [(datoms/add e ":perception/of" of)
              (datoms/add e ":perception/followers" followers)
              (datoms/add e ":perception/beat" beat)
              (datoms/add e ":perception/as-of" as-of)]
       (some? reactions) (conj (datoms/add e ":perception/reactions" reactions))))))
