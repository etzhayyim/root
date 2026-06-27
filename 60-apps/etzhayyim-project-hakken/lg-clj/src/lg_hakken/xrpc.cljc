(ns lg-hakken.xrpc
  "Tiny babashka.http-client + cheshire JSON helpers — the `httpx` replacement
  for the hakken node default edges (ADR-2606280030).

  Loaded lazily (requiring-resolve) so namespaces that merely *define* a default
  edge still load offline under bb; the resolve only happens when a default edge
  actually fires (tests rebind the edges and never hit the network)."
  (:require [clojure.string :as str]))

(defn get-json
  "HTTP GET url with query params → parsed JSON (keyword keys). Throws on >=400."
  ([url] (get-json url nil))
  ([url query]
   (let [get* (requiring-resolve 'babashka.http-client/get)
         parse (requiring-resolve 'cheshire.core/parse-string)
         resp (get* url (cond-> {:timeout 30000 :throw false}
                          (seq query) (assoc :query-params query)))]
     (if (>= (:status resp) 400)
       (throw (ex-info (str "GET " url " " (:status resp)) {:status (:status resp)}))
       (parse (:body resp) true)))))

(defn post-json
  "HTTP POST url with a JSON body → {:status :body(parsed-or-raw) :ok bool}.
  Never throws on HTTP status; caller inspects :ok / :status (mirrors the
  Python `resp.is_success` checks)."
  ([url body] (post-json url body 30000))
  ([url body timeout-ms]
   (let [post (requiring-resolve 'babashka.http-client/post)
         gen  (requiring-resolve 'cheshire.core/generate-string)
         parse (requiring-resolve 'cheshire.core/parse-string)
         resp (post url {:headers {"Content-Type" "application/json"}
                         :timeout timeout-ms :throw false
                         :body (gen body)})
         status (:status resp)
         parsed (try (parse (:body resp) true) (catch Exception _ nil))]
     {:status status :ok (and (>= status 200) (< status 300)) :body parsed})))

(defn clip [s n] (let [s (str s)] (subs s 0 (min n (count s)))))
