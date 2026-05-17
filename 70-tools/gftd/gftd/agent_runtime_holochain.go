package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const holochainAgentRuntimePlanSchema = "https://etzhayyim.com/schemas/holochain-agent-runtime-plan/v1.json"

type holochainRuntimePlan struct {
	Schema           string                   `json:"schema"`
	RuntimeKind      string                   `json:"runtimeKind"`
	Status           string                   `json:"status"`
	Layer            string                   `json:"layer"`
	AgentDID         string                   `json:"agentDid"`
	Conductor        holochainConductorRef    `json:"conductor"`
	HApp             holochainHAppRef         `json:"happ"`
	Bindings         holochainRuntimeBindings `json:"bindings"`
	Lifecycle        []string                 `json:"lifecycle"`
	Verification     holochainRuntimeSmoke    `json:"verification"`
	Registration     map[string]string        `json:"registration"`
	OperationalGates []string                 `json:"operationalGates"`
}

type holochainConductorRef struct {
	Image     string `json:"image"`
	Cluster   string `json:"cluster"`
	Namespace string `json:"namespace"`
	Workload  string `json:"workload"`
}

type holochainHAppRef struct {
	Name       string `json:"name"`
	HAppURI    string `json:"happUri"`
	HAppSHA256 string `json:"happSha256,omitempty"`
	DNAHash    string `json:"dnaHash"`
	RoleName   string `json:"roleName"`
	ZomeName   string `json:"zomeName"`
}

type holochainRuntimeBindings struct {
	ActorEventEntry string `json:"actorEventEntry"`
	CommandFunction string `json:"commandFunction"`
	SignalFunction  string `json:"signalFunction"`
	SourceChain     string `json:"sourceChain"`
	DHT             string `json:"dht"`
	RisingWaveSink  string `json:"risingWaveSink"`
}

type holochainRuntimeSmoke struct {
	Mode        string                       `json:"mode"`
	HCAvailable bool                         `json:"hcAvailable"`
	CheckedAt   string                       `json:"checkedAt"`
	Checks      []holochainRuntimeSmokeCheck `json:"checks"`
}

type holochainRuntimeSmokeCheck struct {
	Name   string `json:"name"`
	OK     bool   `json:"ok"`
	Detail string `json:"detail"`
}

func runAgentRuntimeHolochainPlan(args []string) error {
	fs := flag.NewFlagSet("agent-runtime holochain-plan", flag.ContinueOnError)
	agentDID := fs.String("agent-did", "", "agent DID bound to the Holochain cell (required)")
	happName := fs.String("happ-name", "gftd-agent-actor-runtime", "hApp name")
	happURI := fs.String("happ-uri", "", "published .happ URI, usually ipfs://... or https://... (required)")
	happSHA256 := fs.String("happ-sha256", "", "optional .happ sha256 bytes32 hex")
	dnaHash := fs.String("dna-hash", "", "Holochain DNA hash for the actor runtime network (required)")
	roleName := fs.String("role", "agent_actor_runtime", "hApp role name")
	zomeName := fs.String("zome", "actor_runtime", "coordinator zome name")
	conductorImage := fs.String("conductor-image", "ghcr.io/etzhayyim/holochain-agent-runtime:experimental", "conductor container image")
	cluster := fs.String("cluster", "local-dev", "public cluster label")
	namespace := fs.String("namespace", "agent-runtime-holochain", "k8s namespace")
	workload := fs.String("workload", "holochain-agent-runtime", "k8s workload name")
	out := fs.String("out", "", "optional output JSON path")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *agentDID == "" {
		return fmt.Errorf("--agent-did is required")
	}
	if *happURI == "" {
		return fmt.Errorf("--happ-uri is required")
	}
	if *dnaHash == "" {
		return fmt.Errorf("--dna-hash is required")
	}
	if *namespace == "default" {
		return fmt.Errorf("--namespace must not be default")
	}
	if *happSHA256 != "" && !isBytes32Hex(*happSHA256) {
		return fmt.Errorf("--happ-sha256 must be bytes32 hex")
	}

	plan := buildHolochainRuntimePlan(holochainRuntimePlanInput{
		AgentDID:       *agentDID,
		HAppName:       *happName,
		HAppURI:        *happURI,
		HAppSHA256:     *happSHA256,
		DNAHash:        *dnaHash,
		RoleName:       *roleName,
		ZomeName:       *zomeName,
		ConductorImage: *conductorImage,
		Cluster:        *cluster,
		Namespace:      *namespace,
		Workload:       *workload,
	})
	data, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	if *out != "" {
		if err := os.MkdirAll(filepath.Dir(*out), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(*out, data, 0o644); err != nil {
			return err
		}
	}
	fmt.Print(string(data))
	return nil
}

type holochainRuntimePlanInput struct {
	AgentDID       string
	HAppName       string
	HAppURI        string
	HAppSHA256     string
	DNAHash        string
	RoleName       string
	ZomeName       string
	ConductorImage string
	Cluster        string
	Namespace      string
	Workload       string
}

func buildHolochainRuntimePlan(in holochainRuntimePlanInput) holochainRuntimePlan {
	hcAvailable := false
	if _, err := exec.LookPath("hc"); err == nil {
		hcAvailable = true
	}
	artifactMaterial := strings.Join([]string{in.AgentDID, in.HAppURI, in.DNAHash, in.RoleName, in.ZomeName}, "\n")
	artifactSum := sha256.Sum256([]byte(artifactMaterial))
	artifactID := "0x" + hex.EncodeToString(artifactSum[:])
	checks := []holochainRuntimeSmokeCheck{
		{Name: "runtime-kind-contract", OK: true, Detail: "runtimeKind=holochain is admitted by the registration/public-runtime schemas"},
		{Name: "cell-binding", OK: in.AgentDID != "" && in.DNAHash != "", Detail: "cell identity is modeled as DNA hash + agent DID"},
		{Name: "zome-command-surface", OK: in.RoleName != "" && in.ZomeName != "", Detail: "actor commands bind to role/zome function calls"},
		{Name: "projection-boundary", OK: true, Detail: "Holochain source chain/DHT are event transport; RisingWave remains query projection SSoT"},
	}
	return holochainRuntimePlan{
		Schema:      holochainAgentRuntimePlanSchema,
		RuntimeKind: "holochain",
		Status:      "experimental",
		Layer:       "L3 virtual actor runtime experiment; L5 remains RisingWave",
		AgentDID:    in.AgentDID,
		Conductor: holochainConductorRef{
			Image:     in.ConductorImage,
			Cluster:   in.Cluster,
			Namespace: in.Namespace,
			Workload:  in.Workload,
		},
		HApp: holochainHAppRef{
			Name:       in.HAppName,
			HAppURI:    in.HAppURI,
			HAppSHA256: in.HAppSHA256,
			DNAHash:    in.DNAHash,
			RoleName:   in.RoleName,
			ZomeName:   in.ZomeName,
		},
		Bindings: holochainRuntimeBindings{
			ActorEventEntry: "ActorEvent { actor_did, command_id, lexicon_nsid, input_cid, output_cid, occurred_at }",
			CommandFunction: in.ZomeName + ".commit_actor_event",
			SignalFunction:  in.ZomeName + ".latest_actor_head",
			SourceChain:     "per-agent append-only command/outcome log",
			DHT:             "shared actor heads, capability grants, and validation receipts",
			RisingWaveSink:  "vertex_actor_event_holochain -> existing actor/runtime projections",
		},
		Lifecycle: []string{
			"install_app(happ)",
			"enable_app(agent_did)",
			"call_zome(commit_actor_event)",
			"emit_signal(latest_actor_head)",
			"project_to_risingwave(vertex_actor_event_holochain)",
		},
		Verification: holochainRuntimeSmoke{
			Mode:        "offline-contract-smoke",
			HCAvailable: hcAvailable,
			CheckedAt:   time.Now().UTC().Format(time.RFC3339),
			Checks:      checks,
		},
		Registration: map[string]string{
			"artifactId":   artifactID,
			"runtimeKind":  "holochain",
			"artifactUri":  in.HAppURI,
			"containerRef": in.ConductorImage,
		},
		OperationalGates: []string{
			"Do not use as production default runtime until conductor packaging is reproducible in CI.",
			"Do not store query SSoT in Holochain; project accepted events to RisingWave.",
			"Do not expose conductor admin API publicly; publish only MCP/XRPC facade endpoints.",
		},
	}
}
