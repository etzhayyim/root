;; etzhayyim.agent-token — Agent token pure helpers (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/agent_token.py
;;
;; TRIAGE RESULT: agent_token.py is ENTIRELY IO.
;;
;; The module is a single Click command that:
;;   1. Calls resolve_pds() (env read)
;;   2. Computes exp = int(time.time()) + ttl  — integer arithmetic
;;   3. Builds a payload dict                   — the only pure logic
;;   4. Fires an httpx POST to the PDS
;;   5. Prints the returned token
;;
;; Pure logic extracted:
;;   build-agent-token-payload  — assemble the POST payload map (lxm / exp / aud / sub)
;;
;; IO LEGS DEFERRED (not ported — httpx POST / time.time / Click):
;;   agent_token (Click command) — httpx POST getServiceAuth → bb leg
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.agent-token :as at])
;;   (at/build-agent-token-payload "com.etzhayyim.myLex" 1750000000)
;;   ;=> {"lxm" "com.etzhayyim.myLex" "exp" 1750000000}
;;   (at/build-agent-token-payload "com.etzhayyim.myLex" 1750000000
;;                                  "did:web:atproto.etzhayyim.com" nil)
;;   ;=> {"lxm" "..." "exp" ... "aud" "did:web:..."}

(ns etzhayyim.agent-token
  (:require [clojure.string :as str]
            [cheshire.core  :as json]))

;; ── pure helpers ─────────────────────────────────────────────────────────────

(defn build-agent-token-payload
  "Assemble the POST payload map for com.atproto.server.getServiceAuth.
   lxm     — Lexicon method NSID (required)
   exp     — expiry unix timestamp int (required)
   aud     — audience DID string or nil (optional, omitted when nil/empty)
   sub-did — subject DID override or nil (optional; sets X-Active-DID header, not payload)

   Returns a string-keyed map (JSON-safe).
   Mirrors Python: payload = {'lxm': lxm, 'exp': exp}; if aud: payload['aud'] = aud."
  ([lxm exp]
   (build-agent-token-payload lxm exp nil nil))
  ([lxm exp aud]
   (build-agent-token-payload lxm exp aud nil))
  ([lxm exp aud _sub-did]
   (cond-> {"lxm" lxm "exp" exp}
     (some-> aud not-empty) (assoc "aud" aud))))

(defn agent-token-xrpc-url
  "Build the full XRPC URL for getServiceAuth.
   pds-base — PDS URL (trailing slashes stripped).
   Returns the full endpoint URL."
  [pds-base]
  (str (clojure.string/replace (or pds-base "") #"/+$" "")
       "/xrpc/com.atproto.server.getServiceAuth"))

;; ── CLI -main ──────────────────────────────────────────────────────────────────
;; Mirrors the python `agent-token` click COMMAND (not a group) argv contract:
;;   e7m agent-token --lxm NSID [--aud DID] [--pds URL] [--ttl SECS] [--sub DID] [-v]
;; The twin ports the PURE payload + URL builders; the actual
;; httpx POST getServiceAuth (which returns the token) is the un-ported IO leg.
;; -main computes exp, builds the payload + endpoint URL, and prints them.
;; It does NOT perform the network fetch (no token is minted here).

(defn- at-parse
  [args bool-flags]
  (loop [a (seq args) pos [] flags {}]
    (if-not a
      [pos flags]
      (let [t (first a)]
        (cond
          (and (str/starts-with? t "--") (contains? bool-flags (subs t 2)))
          (recur (next a) pos (assoc flags (subs t 2) true))
          (or (= t "-v") (= t "--verbose"))
          (recur (next a) pos (assoc flags "verbose" true))
          (str/starts-with? t "--")
          (recur (nnext a) pos (assoc flags (subs t 2) (fnext a)))
          :else
          (recur (next a) (conj pos t) flags))))))

(defn -main [& args]
  (let [[_ flags] (at-parse args #{"verbose" "json"})
        lxm (get flags "lxm")
        aud (get flags "aud")
        ttl (try (Long/parseLong (or (get flags "ttl") "60")) (catch Exception _ 60))
        pds (or (get flags "pds")
                (System/getenv "etzhayyim_PDS_URL")
                "https://etzhayyim-pds-2603241700.etzhayyim.com")]
    (if-not lxm
      (println "usage: agent-token --lxm NSID [--aud DID] [--pds URL] [--ttl SECS] [--sub DID] [-v]")
      (let [exp     (+ (quot (System/currentTimeMillis) 1000) ttl)
            payload (build-agent-token-payload lxm exp aud (get flags "sub"))
            url     (agent-token-xrpc-url pds)]
        (if (get flags "json")
          (println (json/generate-string {:url url :payload payload} {:pretty true}))
          (do (println (str "POST " url))
              (println (str "  payload: " (json/generate-string payload)))
              (println "  (token fetch is the un-ported httpx IO leg; not executed here)")))))))
