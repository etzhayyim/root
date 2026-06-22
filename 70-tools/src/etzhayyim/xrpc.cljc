;; etzhayyim.xrpc — IO-REWRITE of 70-tools/etzhayyim-py/src/etzhayyim/xrpc.py
;; (ADR-2605151500, xrpc.go port).
;;
;; Invoke any XRPC endpoint on an App or PDS.
;; Auto-routes com.etzhayyim.apps.{slug}.* NSIDs to the correct nanoid worker.
;; Scoped-JWT auto-wrap stub: scoped-auth-headers is injectable (tested offline).
;;
;; The .py is KEPT (additive port — both co-exist).
;;
;; PURE-vs-IO split:
;;   PURE (parity-verifiable, unit-tested offline):
;;     known-apps               — slug → nanoid constant map
;;     app-host-template        — URL template constant
;;     resolve-base             — derive base URL from nsid/app/url options
;;     build-xrpc-url           — build full XRPC URL (base + /xrpc/ + nsid)
;;     build-xrpc-request       — assemble the full request map (method/url/headers/body)
;;     parse-xrpc-response-body — extract / pretty-print JSON from response body text
;;
;;   IO (request-shaping verified via injectable :http-fn, no live calls in tests):
;;     default-http-fn          — real babashka.http-client dispatch
;;     call-xrpc                — execute an XRPC call with injectable http-fn
;;
;; INJECTABLE HTTP CLIENT:
;;   call-xrpc accepts :http-fn in opts.  Default = real babashka.http-client.
;;   Tests inject a fake that records calls WITHOUT touching the network.
;;   build-xrpc-request is pure and fully testable offline.
;;
;; SECURITY:
;;   No secrets at load-time.  Auth headers read env only when call-xrpc is invoked.
;;
;; bb load check:
;;   bb --classpath 70-tools/src -e "(require 'etzhayyim.xrpc)(println :ok)"

(ns etzhayyim.xrpc
  (:require [clojure.string :as str]
            [cheshire.core  :as json]
            #?(:bb [babashka.http-client :as http])))

;; ---------------------------------------------------------------------------
;; Constants (pure)
;; ---------------------------------------------------------------------------

(def ^:private known-apps
  "Slug → nanoid mapping.  Mirrors Python _KNOWN_APPS."
  {"media_gamers" "a7m8oocs"
   "media_anime"  "animegr01"
   "autorace"     "q7v8yed1k"
   "keirin"       "k31r1njp"
   "kyotei"       "qv8yed1k"
   "handotai"     "dtyy44cr"
   "hanrei"       "h4nr31jp"
   "kakaku"       "k4k4kux1"
   "gtin"         "gt1n4k7m"})

(def ^:private app-host-template
  "https://{nanoid}.com.etzhayyim.com")

;; ---------------------------------------------------------------------------
;; Private helpers
;; ---------------------------------------------------------------------------

(defn- strip-trailing-slash
  "Remove a single trailing '/' from s, if present.
  Uses str/ends-with? + subs — avoids 2-arg str/trimr which is not available
  in bb/SCI (clojure.string/trimr takes only one argument in SCI)."
  [s]
  (if (str/ends-with? s "/")
    (subs s 0 (dec (count s)))
    s))

;; ---------------------------------------------------------------------------
;; Pure: URL / request construction
;; ---------------------------------------------------------------------------

(defn resolve-base
  "Derive the base URL for an XRPC call from options.
  Priority: explicit url > explicit app > NSID inference > PDS fallback.
  pds-url must be provided (no env reads here — callers supply it).
  Mirrors Python _resolve_base()."
  [nsid app url pds-url]
  (cond
    (and url (seq url))
    (strip-trailing-slash url)

    (and app (seq app))
    (str/replace app-host-template "{nanoid}" app)

    :else
    ;; NSID inference: com.etzhayyim.apps.<slug>.*
    (let [parts (str/split nsid #"\.")
          prefix ["com" "etzhayyim" "apps"]]
      (if (and (>= (count parts) 4)
               (= (vec (take 3 parts)) prefix))
        (let [slug   (nth parts 3)
              nanoid (get known-apps slug)]
          (if nanoid
            (str/replace app-host-template "{nanoid}" nanoid)
            (strip-trailing-slash (or pds-url ""))))
        (strip-trailing-slash (or pds-url ""))))))

(defn build-xrpc-url
  "Build the full XRPC endpoint URL.
  Mirrors Python: url = f'{base}/xrpc/{nsid}'"
  [base nsid]
  (str base "/xrpc/" nsid))

(defn build-xrpc-request
  "Build the full HTTP request map for an XRPC call WITHOUT executing it.
  Returns {:method :url :headers :body?} (body absent for GET with no payload).
  Mirrors Python xrpc() request construction.

  opts:
    :method       — :get or :post (default: :post if payload given, else :get)
    :payload      — parsed data map (nil = no body)
    :auth-headers — map of auth headers (injectable; default {})
    :pds-url      — PDS fallback URL (default \"\")
    :app          — explicit nanoid (overrides NSID inference)
    :url          — full base URL (overrides :app and inference)"
  [nsid opts]
  (let [{:keys [method payload auth-headers pds-url app url]
         :or   {auth-headers {}
                pds-url      ""}} opts
        base     (resolve-base nsid app url pds-url)
        xrpc-url (build-xrpc-url base nsid)
        method   (or method (if (some? payload) :post :get))
        hdrs     (merge {"Content-Type" "application/json"} auth-headers)]
    (cond-> {:method method :url xrpc-url :headers hdrs}
      (and (= method :post) (some? payload))
      (assoc :body payload)
      (and (= method :get) (map? payload))
      (assoc :params payload))))

(defn parse-xrpc-response-body
  "Extract and optionally pretty-print the response body text.
  Returns [body-str parsed-ok?].
  Mirrors Python xrpc() output formatting."
  [body-text pretty?]
  (if pretty?
    (try
      (let [parsed (json/parse-string body-text)]
        [(json/generate-string parsed {:pretty true}) true])
      (catch Exception _
        [body-text false]))
    [body-text false]))

;; ---------------------------------------------------------------------------
;; IO: HTTP dispatch — injectable for tests
;; ---------------------------------------------------------------------------

(defn- default-http-fn
  "Real babashka.http-client dispatch.
  Expects {:method :url :headers :body? :params?} and returns {:status :body}."
  [{:keys [method url headers body params]}]
  #?(:bb
     (let [base-opts (cond-> {:headers headers :timeout 30000}
                       params (assoc :query-params params)
                       body   (assoc :body (json/generate-string body)))
           resp      (case method
                       :get  (http/get  url base-opts)
                       :post (http/post url base-opts))]
       {:status (:status resp) :body (:body resp)})
     :default
     (throw (ex-info "babashka.http-client only available under bb"
                     {:method method :url url}))))

(defn call-xrpc
  "Execute an XRPC call.
  Returns {:status int :body str}.
  Raises ex-info on HTTP error (status >= 300).

  opts keys (all optional):
    :method       — :get or :post
    :payload      — data map (POST body or GET query params)
    :auth-headers — map of extra headers (auth etc.)
    :pds-url      — PDS fallback base URL
    :app          — explicit nanoid
    :url          — explicit full base URL
    :http-fn      — injectable HTTP fn (default = babashka.http-client)

  NEVER reads env at load time; auth-headers are caller-supplied."
  [nsid opts]
  (let [{:keys [http-fn] :or {http-fn default-http-fn}} opts
        req  (build-xrpc-request nsid opts)
        resp (http-fn req)]
    (when (>= (:status resp) 300)
      (throw (ex-info (str "XRPC " (:status resp) ": " (:body resp))
                      {:status (:status resp)
                       :body   (:body resp)
                       :nsid   nsid
                       :url    (:url req)})))
    resp))
