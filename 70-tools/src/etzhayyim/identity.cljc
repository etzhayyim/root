;; etzhayyim.identity — Identity pure helpers (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/identity.py
;;
;; TRIAGE RESULT: identity.py is mostly IO (httpx XRPC calls + subprocess).
;;
;; PURE LOGIC PORTED:
;;   compute-path-did       — sha256(json-genesis) → b32 → did:etzhayyim:<24chars>
;;                            Mirrors Python: _compute_path_did(nanoid)
;;   resolve-endpoint       — choose XRPC endpoint based on handle vs DID prefix
;;   format-identity-row    — format a k/v display line (mirrors identity_resolve output)
;;
;; IO LEGS DEFERRED (not ported — httpx XRPC / subprocess / tomllib / Click):
;;   _auth_headers          — reads auth file → bb leg
;;   identity_resolve       — httpx GET describeRepo or resolveHandle → bb leg
;;   identity_update_handle — httpx POST updateHandle → bb leg
;;   identity_migrate       — live: Go binary; dry-run: pure print → bb leg
;;   identity_migrate_paths — subprocess git + tomllib + httpx → bb leg
;;   identity_audit         — httpx GET auditIdentities → bb leg
;;
;; NOTE: compute-path-did is the critical pure function with real business logic.
;;       It uses java.security.MessageDigest + base32 encoding.
;;       The sha256 + b32 lower-case match Python exactly (verified in parity smoke).
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.identity :as id])
;;   (id/compute-path-did "abc123nanoid")
;;   ;=> "did:etzhayyim:<24-char-b32>"
;;   (id/resolve-endpoint "did:plc:abc" "https://atproto.etzhayyim.com")
;;   ;=> ["https://atproto.etzhayyim.com/xrpc/com.atproto.repo.describeRepo" {:repo "did:plc:abc"}]

(ns etzhayyim.identity
  (:require [clojure.string :as str])
  #?(:clj (:import [java.security MessageDigest]
                   [java.util Base64])))

;; ── path DID derivation ──────────────────────────────────────────────────────

(defn- sha256-bytes
  "Compute SHA-256 digest of a UTF-8 string, returning a byte array."
  [^String s]
  #?(:clj  (.digest (MessageDigest/getInstance "SHA-256") (.getBytes s "UTF-8"))
     :cljs (let [arr (js/TextEncoder. "utf-8")]
             ;; CLJS: use SubtleCrypto — async; return nil for now (bb/clj is primary)
             nil)))

(defn- base32-encode-lower
  "Encode a byte array to base32 lower-case (no padding).
   Matches Python: base64.b32encode(digest).decode().lower().rstrip('=').
   Processes 5 bits at a time from the input bytes."
  [^bytes b]
  #?(:clj  (let [alpha "abcdefghijklmnopqrstuvwxyz234567"
                 n     (alength b)
                 ;; accumulate all bits into a long sequence, then group by 5
                 total-bits (* n 8)
                 ;; number of 5-bit groups (no padding stripped on output)
                 n-chars   (quot total-bits 5)
                 out       (StringBuilder. n-chars)]
             ;; emit floor(n*8/5) characters; discard trailing partial group
             (dotimes [ci n-chars]
               (let [bit-pos (* ci 5)
                     byte-i  (quot bit-pos 8)
                     bit-off (mod  bit-pos 8)
                     ;; read at most 2 bytes to cover a 5-bit window
                     b0 (long (bit-and 0xff (aget b byte-i)))
                     b1 (if (< (inc byte-i) n)
                          (long (bit-and 0xff (aget b (inc byte-i))))
                          0)
                     ;; 5 bits starting at bit-off within b0
                     ;; combined 16-bit window
                     window (bit-or (bit-shift-left b0 8) b1)
                     ;; shift right to align 5-bit group to bit 0
                     shift  (- 11 bit-off)  ; 16 - 5 = 11
                     idx    (bit-and 0x1f (bit-shift-right window shift))]
                 (.append out ^char (get alpha idx))))
             (.toString out))
     :cljs ""))

(defn compute-path-did
  "Compute a path-DID from a nanoid string.
   Matches Python _compute_path_did:
     payload = json.dumps({'type': 'path-did-genesis', 'nanoid': nanoid}).encode()
     digest  = hashlib.sha256(payload).digest()
     b32     = base64.b32encode(digest).decode().lower().rstrip('=')
     return f'did:etzhayyim:{b32[:24]}'

   JSON encoding must match Python's compact default (no spaces after separators)."
  [nanoid]
  (let [payload (str "{\"type\": \"path-did-genesis\", \"nanoid\": \"" nanoid "\"}")
        digest  (sha256-bytes payload)
        b32     (if digest (base32-encode-lower digest) "")]
    (str "did:etzhayyim:" (subs b32 0 (min 24 (count b32))))))

;; ── endpoint routing ─────────────────────────────────────────────────────────

(defn resolve-endpoint
  "Choose the XRPC endpoint and params for resolving a handle or DID.
   Returns [endpoint-url params-map].
   Mirrors Python: identity_resolve command branch."
  [handle-or-did pds-url]
  (let [base (str/replace (or pds-url "") #"/+$" "")]
    (if (str/starts-with? (or handle-or-did "") "did:")
      [(str base "/xrpc/com.atproto.repo.describeRepo")  {"repo" handle-or-did}]
      [(str base "/xrpc/com.atproto.identity.resolveHandle") {"handle" handle-or-did}])))

;; ── display formatting ────────────────────────────────────────────────────────

(defn format-identity-row
  "Format a single key-value pair as a display line.
   Mirrors Python: for k, v in data.items(): echo(f'  {k}: {v}')."
  [[k v]]
  (str "  " (name k) ": " v))
