;; etzhayyim.agent-runtime — ERC-8004 manifest + runtime pure helpers (cljc port, wave 5a).
;;
;; Port of 70-tools/etzhayyim-py/src/etzhayyim/agent_runtime.py
;;
;; PURE LOGIC PORTED:
;;   agent-runtime-schema    — constant schema URL
;;   default-registry        — constant default contract address
;;   default-rpc             — constant default RPC URL
;;   default-chain-id        — constant default chain ID
;;   default-ipfs            — constant default IPFS gateway
;;   build-runtime-doc       — fallback JSON document assembly (when render script absent)
;;   build-publish-result    — assemble the publish dry-run result map
;;   build-register-result   — assemble the register dry-run result map
;;   build-publish-agent-result — assemble the combined publish+register result map
;;   build-holochain-plan    — assemble the Holochain conductor k8s runtime plan map
;;
;; IO LEGS DEFERRED (not ported — subprocess / httpx / filesystem):
;;   _find_git_root          — subprocess git rev-parse → bb leg
;;   _render_runtime_public  — subprocess render script or file reads → bb leg
;;   _auth_headers           — reads auth file → bb leg
;;   ar_status / ar_list / ar_logs — httpx GET → bb leg
;;   ar_restart              — sys.exit → bb leg
;;   ar_render               — delegates to _render_runtime_public → bb leg
;;   ar_publish (live)       — IPFS HMAC keychain → Go binary leg
;;   ar_register (live)      — EVM signing → Go binary leg
;;   ar_publish_agent (live) — IPFS + EVM → Go binary leg
;;
;; NOTE: The dry-run legs of publish/register/publish-agent/holochain-plan
;;       are PURE JSON assembly — no I/O — and are fully ported here.
;;
;; bb usage (classpath 70-tools/src):
;;   (require '[etzhayyim.agent-runtime :as ar])
;;   (ar/build-publish-result "prod" "0xabc123" 512 true)
;;   ;=> {"ok" true "dryRun" true "sha256" "0xabc123" ...}
;;   (ar/build-holochain-plan "did:web:etzhayyim.com" "myapp" "ipfs://baf..." "bafy..." ...)

(ns etzhayyim.agent-runtime
  (:require [clojure.string :as str]
            [cheshire.core  :as json]))

;; ── constants ─────────────────────────────────────────────────────────────────

(def agent-runtime-schema
  "https://etzhayyim.com/schemas/k8s-runtime-public/v1.json")

(def default-registry
  "0x0000000000000000000000000000000000000001")

(def default-rpc
  "http://10.0.0.1:8545")

(def default-chain-id
  "1337")

(def default-ipfs
  "https://ipfs.etzhayyim.com")

;; ── pure document builders ───────────────────────────────────────────────────

(defn build-runtime-doc
  "Build a minimal k8s-runtime JSON document from manifest entries.
   manifests — seq of {:path string :content string} maps.
   cluster   — public cluster label string.

   Mirrors Python: fallback branch of _render_runtime_public."
  [cluster manifests]
  {"$schema"   agent-runtime-schema
   "cluster"   cluster
   "kind"      "k8s-runtime"
   "manifests" (vec manifests)})

(defn build-publish-result
  "Assemble the publish dry-run result map.
   cluster   — public cluster label
   sha256    — '0x' + hex digest of rendered bytes
   n-bytes   — byte count of rendered content
   dry-run?  — boolean
   ipfs-base — IPFS gateway base URL

   Mirrors Python: result dict in ar_publish."
  [cluster sha256 n-bytes dry-run? ipfs-base]
  {"ok"        true
   "dryRun"    dry-run?
   "sha256"    sha256
   "bytes"     n-bytes
   "schema"    agent-runtime-schema
   "kind"      "k8s-runtime"
   "cluster"   cluster
   "ipfsBase"  (str/replace (or ipfs-base default-ipfs) #"/+$" "")
   "published" false})

(defn build-register-result
  "Assemble the register dry-run result map.
   agent-uri    — published ERC-8004 URI (ipfs://...)
   root-did     — ERC-725 root DID
   agent-owner  — owner address
   metadata-hash — bytes32 hex metadata hash
   registry     — contract address
   rpc-url      — RPC endpoint
   chain-id     — chain ID string
   dry-run?     — boolean

   Mirrors Python: result dict in ar_register."
  [agent-uri root-did agent-owner metadata-hash registry rpc-url chain-id dry-run?]
  {"ok"           true
   "dryRun"       dry-run?
   "chainId"      chain-id
   "rpcUrl"       rpc-url
   "registry"     registry
   "rootDid"      root-did
   "owner"        agent-owner
   "agentURI"     agent-uri
   "metadataHash" metadata-hash
   "submitted"    false})

(defn build-publish-agent-result
  "Assemble the combined publish+register dry-run result map.
   Mirrors Python: result dict in ar_publish_agent."
  [cluster render-sha256 n-bytes metadata-hash root-did agent-owner registry ipfs-base]
  {"ok"          true
   "dryRun"      true
   "cluster"     cluster
   "renderSha256" render-sha256
   "renderBytes" n-bytes
   "metadataHash" metadata-hash
   "rootDid"     root-did
   "owner"       agent-owner
   "registry"    registry
   "ipfsBase"    (str/replace (or ipfs-base default-ipfs) #"/+$" "")
   "published"   false
   "submitted"   false})

(defn build-holochain-plan
  "Assemble the Holochain conductor k8s runtime plan map.
   Mirrors Python: plan dict in ar_holochain_plan.

   Required: agent-did, happ-name, happ-uri, dna-hash
   Optional (have defaults): role-name, zome-name, conductor-image, cluster, namespace, workload"
  [{:keys [agent-did happ-name happ-uri happ-sha256 dna-hash
           role-name zome-name conductor-image cluster namespace workload]
    :or   {happ-name       "etzhayyim-agent-actor-runtime"
           happ-sha256     ""
           role-name       "agent_actor_runtime"
           zome-name       "actor_runtime"
           conductor-image "ghcr.io/etzhayyim/holochain-agent-runtime:experimental"
           cluster         "local-dev"
           namespace       "agent-runtime-holochain"
           workload        "holochain-agent-runtime"}}]
  {"schema"   "https://etzhayyim.com/schemas/holochain-runtime-plan/v1.json"
   "agentDid" agent-did
   "cluster"  cluster
   "hApp"     {"name"     happ-name
               "uri"      happ-uri
               "sha256"   happ-sha256
               "roleName" role-name
               "zomeName" zome-name
               "dnaHash"  dna-hash}
   "k8s"      {"namespace"       namespace
               "workload"        workload
               "conductorImage"  conductor-image
               "env"             [{"name"  "AGENT_DID"  "value" agent-did}
                                  {"name"  "HAPP_URI"   "value" happ-uri}
                                  {"name"  "DNA_HASH"   "value" dna-hash}
                                  {"name"  "ROLE_NAME"  "value" role-name}
                                  {"name"  "ZOME_NAME"  "value" zome-name}]}})

;; ── CLI -main ──────────────────────────────────────────────────────────────────
;; Mirrors the python `agent-runtime` click group argv contract:
;;   e7m agent-runtime <status|list|logs|restart|render|publish|register|
;;                      publish-agent|holochain-plan> [args] [--opts]
;; SAFETY: status/list/logs need the httpx IO leg (not ported → message).
;; restart + live (--no-dry-run) publish/register/publish-agent require the Go
;; binary (mirror python ClickException). The dry-run result builders + the
;; holochain plan are PURE and run for real here. --dry-run is the default.

(defn- sha256-hex
  "'0x' + sha256 hex of a UTF-8 string. Mirrors python hashlib.sha256(...).hexdigest()."
  [s]
  (let [md (java.security.MessageDigest/getInstance "SHA-256")]
    (.update md (.getBytes (str s) "UTF-8"))
    (str "0x" (apply str (map #(format "%02x" (bit-and % 0xff)) (seq (.digest md)))))))

(defn- ar-parse
  [args bool-flags]
  (loop [a (seq args) pos [] flags {}]
    (if-not a
      [pos flags]
      (let [t (first a)]
        (cond
          (and (str/starts-with? t "--") (contains? bool-flags (subs t 2)))
          (recur (next a) pos (assoc flags (subs t 2) true))
          (str/starts-with? t "--")
          (recur (nnext a) pos (assoc flags (subs t 2) (fnext a)))
          :else
          (recur (next a) (conj pos t) flags))))))

(defn- ar-emit [data] (println (json/generate-string data {:pretty true})))

(defn -main [& args]
  (let [[pos flags] (ar-parse args #{"dry-run" "no-dry-run" "json"})
        sub      (first pos)
        live?    (boolean (get flags "no-dry-run"))]
    (case sub
      ("status" "list" "logs")
      (println (str "agent-runtime " sub " needs the bb httpx IO leg (XRPC GET, not "
                    "ported in this twin — only the pure dry-run builders are). "
                    "Use the Go/py CLI."))

      "restart"
      (println "agent-runtime restart requires the Go binary or kubectl.")

      "render"
      (let [cluster   (or (get flags "cluster") "")
            manifests (mapv (fn [p] {"path" p "content" ""}) (rest pos))]
        (ar-emit (build-runtime-doc cluster manifests)))

      "publish"
      (if live?
        (println "Live IPFS publish requires the Go binary (macOS Keychain IPFS_HMAC).")
        (let [cluster  (or (get flags "cluster") "")
              ipfs     (or (get flags "ipfs") default-ipfs)
              rendered (json/generate-string (build-runtime-doc cluster []))]
          (ar-emit (build-publish-result cluster (sha256-hex rendered)
                                         (count rendered) true ipfs))))

      "register"
      (if live?
        (println "Live on-chain registration requires the Go binary (EVM signing).")
        (let [root-did (or (get flags "root-did") "")
              owner    (or (get flags "owner") "")]
          (cond
            (empty? root-did) (println "error: --root-did is required (no --registration provided)")
            (empty? owner)    (println "error: --owner is required (no --registration provided)")
            :else
            (ar-emit (build-register-result
                      (or (get flags "agent-uri") "")
                      root-did owner
                      (or (get flags "metadata-hash") (str "0x" (apply str (repeat 64 "0"))))
                      (or (get flags "registry") default-registry)
                      (or (get flags "rpc-url") default-rpc)
                      (or (get flags "chain-id") default-chain-id)
                      true)))))

      "publish-agent"
      (if live?
        (println "Live publish-agent requires the Go binary.")
        (let [cluster  (or (get flags "cluster") "")
              rendered "{}"]
          (ar-emit (build-publish-agent-result
                    cluster (sha256-hex rendered) (count rendered)
                    (sha256-hex "{}")
                    (or (get flags "root-did") "") (or (get flags "owner") "")
                    (or (get flags "registry") default-registry)
                    (or (get flags "ipfs") default-ipfs)))))

      "holochain-plan"
      (let [agent-did (get flags "agent-did")
            happ-uri  (get flags "happ-uri")
            dna-hash  (get flags "dna-hash")]
        (cond
          (= (get flags "namespace") "default")
          (println "error: --namespace must not be default")
          (and agent-did happ-uri dna-hash)
          (ar-emit (build-holochain-plan
                    (cond-> {:agent-did agent-did :happ-uri happ-uri :dna-hash dna-hash}
                      (get flags "happ-name")       (assoc :happ-name (get flags "happ-name"))
                      (get flags "happ-sha256")     (assoc :happ-sha256 (get flags "happ-sha256"))
                      (get flags "role")            (assoc :role-name (get flags "role"))
                      (get flags "zome")            (assoc :zome-name (get flags "zome"))
                      (get flags "conductor-image") (assoc :conductor-image (get flags "conductor-image"))
                      (get flags "cluster")         (assoc :cluster (get flags "cluster"))
                      (get flags "namespace")       (assoc :namespace (get flags "namespace"))
                      (get flags "workload")        (assoc :workload (get flags "workload")))))
          :else
          (println "usage: agent-runtime holochain-plan --agent-did DID --happ-uri URI --dna-hash HASH [--opts]")))

      (println (str "usage: agent-runtime <status|list|logs|restart|render|publish|"
                    "register|publish-agent|holochain-plan> [args] [--opts]")))))
