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
  (:require [clojure.string :as str]))

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
