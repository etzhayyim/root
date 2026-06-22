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

(ns etzhayyim.agent-token)

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
