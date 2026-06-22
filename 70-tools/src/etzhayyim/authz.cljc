;; etzhayyim.authz — Authorization pure helpers (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/authz.py
;;
;; TRIAGE RESULT: authz.py is almost entirely IO.
;;
;; Every command (create-api-key / list-api-keys / revoke-api-key / dids / switch)
;; makes an httpx call or writes to the auth file.  The only non-IO logic is:
;;
;;   controlled-dids   — deduplicate + prepend primary DID to the controlled list
;;                       (pure list-building; mirrors authz_dids command body)
;;   format-key-row    — format a single API-key entry as a display string
;;                       (mirrors the for-loop in authz_list_api_keys)
;;
;; IO LEGS DEFERRED (not ported — httpx XRPC / auth-file read-write):
;;   _token / _headers    — reads auth file + calls resolve_pds → bb leg
;;   authz_create_api_key — httpx POST createApiKey → bb leg
;;   authz_list_api_keys  — httpx GET listApiKeys → bb leg
;;   authz_revoke_api_key — httpx POST revokeApiKey → bb leg
;;   authz_dids           — reads auth file + displays → bb leg (list IO)
;;   authz_switch         — writes auth file → bb leg
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.authz :as authz])
;;   (authz/controlled-dids {"did" "did:plc:abc" "controlledDids" ["did:plc:xyz"]})
;;   ;=> ["did:plc:abc" "did:plc:xyz"]
;;   (authz/format-key-row {"id" "k1" "label" "main" "scopes" "read,write"})
;;   ;=> "  k1  main  read,write"

(ns etzhayyim.authz
  (:require [clojure.string :as str]))

;; ── pure helpers ─────────────────────────────────────────────────────────────

(defn controlled-dids
  "Return a deduplicated list of DIDs controlled by the current auth identity.
   Primary DID is prepended if not already present.
   Mirrors Python: dids = auth.get('controlledDids') or []; prepend primary.

   auth-map — string-keyed auth.json map."
  [auth-map]
  (let [dids    (vec (or (get auth-map "controlledDids") []))
        primary (str/trim (or (get auth-map "did" "") ""))]
    (if (and (not-empty primary) (not (some #{primary} dids)))
      (into [primary] dids)
      dids)))

(defn format-key-row
  "Format a single API-key entry as a display string.
   Mirrors Python: for k in keys: echo(f'  {id}  {label}  {scopes}').

   key-map — string-keyed map with 'id', 'label', 'scopes'."
  [key-map]
  (str "  "
       (or (get key-map "id") "")
       "  "
       (or (get key-map "label") "")
       "  "
       (or (get key-map "scopes") "")))

(defn format-did-row
  "Format a single DID entry as a display string, marking the active DID.
   Mirrors Python: for d in dids: echo(f'  {d}{ (active) if d == primary else }').

   did      — the DID string
   primary  — the active DID (or nil/'')"
  [did primary]
  (str "  " did
       (when (= did primary) " (active)")))
