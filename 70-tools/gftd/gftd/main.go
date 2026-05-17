// gftd — magatama build/deploy CLI (Cloudflare Workers)
package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
)

// version is set at build time via -ldflags "-X main.version=$(git describe --tags --always --dirty)"
var version = "dev"

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	var err error
	switch os.Args[1] {
	case "build":
		err = withOcelLog("gftd.build", func() error { return runBuild(os.Args[2:]) })
	case "deploy":
		err = withOcelLog("gftd.deploy", func() error { return runDeploy(os.Args[2:]) })
	case "workspace":
		err = runWorkspace(os.Args[2:])
	case "plugin":
		err = runPlugin(os.Args[2:])
	case "code":
		err = withOcelLog("gftd.code", func() error { return runCode(os.Args[2:]) })
	case "hinshitsu":
		err = withOcelLog("gftd.hinshitsu", func() error { return runHinshitsu(os.Args[2:]) })
	case "code-quality":
		err = withOcelLog("gftd.codeQuality", func() error { return runCodeQuality(os.Args[2:]) })
	case "lint":
		err = withOcelLog("gftd.lint", func() error { return runLint(os.Args[2:]) })
	case "deps":
		err = withOcelLog("gftd.deps", func() error { return runDeps(os.Args[2:]) })
	case "docs":
		err = runDocs(os.Args[2:])
	case "docs-gen":
		err = withOcelLog("gftd.docsGen", func() error { return runDocsGen(os.Args[2:]) })
	case "monitor":
		subArgs := os.Args[2:]
		if len(subArgs) > 0 && subArgs[0] == "shinka" {
			err = withOcelLog("gftd.monitor.shinka", func() error { return runMonitorShinka(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "did" {
			err = withOcelLog("gftd.monitor.did", func() error { return runMonitorDID(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "vote" {
			err = withOcelLog("gftd.monitor.vote", func() error { return runMonitorVote(subArgs[1:]) })
		} else {
			err = withOcelLog("gftd.monitor", func() error { return runMonitor(subArgs) })
		}
	case "apps":
		err = withOcelLog("gftd.apps", func() error { return runApps(os.Args[2:]) })
	case "actors":
		subArgs := os.Args[2:]
		if len(subArgs) > 0 && subArgs[0] == "jokyo" {
			err = withOcelLog("gftd.actors.jokyo", func() error { return runActorsJokyo(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "shinka" {
			err = withOcelLog("gftd.actors.shinka", func() error { return runActorsShinka(subArgs[1:]) })
		} else if len(subArgs) > 0 && (subArgs[0] == "common-crawler-coverage" || subArgs[0] == "cc-coverage") {
			err = withOcelLog("gftd.actors.ccCoverage", func() error { return runActorsCCCoverage(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "migrate-to-plc" {
			err = withOcelLog("gftd.actors.migrateToPLC", func() error { return runActorMigratePLC(subArgs[1:]) })
		} else {
			err = fmt.Errorf("unknown actors subcommand. Available: jokyo, shinka, common-crawler-coverage, migrate-to-plc")
		}
	case "set-profiles":
		err = withOcelLog("gftd.setProfiles", func() error { return runSetProfiles(os.Args[2:]) })
	case "authn":
		err = runAuthn(os.Args[2:])
	case "authz":
		err = runAuthz(os.Args[2:])
	case "agent-token":
		err = withOcelLog("gftd.agentToken", func() error { return runAgentToken(os.Args[2:]) })
	case "agent":
		err = withOcelLog("gftd.agent", func() error { return runAgent(os.Args[2:]) })
	case "agent-runtime":
		err = withOcelLog("gftd.agentRuntime", func() error { return runAgentRuntime(os.Args[2:]) })
	case "cohort":
		err = withOcelLog("gftd.cohort", func() error { return runCohort(os.Args[2:]) })
	case "projector":
		err = withOcelLog("gftd.projector", func() error { return runProjector(os.Args[2:]) })
	case "vertex":
		err = withOcelLog("gftd.vertex", func() error { return runVertex(os.Args[2:]) })
	case "migrate-manifest":
		err = runMigrateManifest(os.Args[2:])
	case "database", "db":
		subArgs := os.Args[2:]
		if len(subArgs) > 0 && subArgs[0] == "up" {
			err = withOcelLog("gftd.database.up", func() error { return runDatabaseUp(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "migrate" {
			err = withOcelLog("gftd.database.migrate", func() error { return runDatabaseMigrate(subArgs[1:]) })
		} else if len(subArgs) > 0 && (subArgs[0] == "repair-order" || subArgs[0] == "repair") {
			err = withOcelLog("gftd.database.repairOrder", func() error { return runDatabaseRepairOrder(subArgs[1:]) })
		} else if len(subArgs) > 0 && (subArgs[0] == "status" || subArgs[0] == "list") {
			err = withOcelLog("gftd.database.status", func() error { return runDatabaseMigrate([]string{"list"}) })
		} else {
			err = fmt.Errorf("unknown database subcommand. Available: up, migrate [latest|up|down|to <name>|list], repair-order, status")
		}
	case "coverage":
		// Subcommand routing: gftd coverage [world|test|domain|logicalactors|actors|oil]
		// Default (no subcommand) = world coverage
		subArgs := os.Args[2:]
		if len(subArgs) > 0 && subArgs[0] == "test" {
			err = withOcelLog("gftd.coverage.test", func() error { return runCoverage(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "domain" {
			err = withOcelLog("gftd.coverage.domain", func() error { return runDomainCoverage(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "actors" {
			err = withOcelLog("gftd.coverage.actors", func() error { return runCoverageActors(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "oil" {
			err = withOcelLog("gftd.coverage.oil", func() error { return runCoverageOil(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "infer" {
			err = withOcelLog("gftd.coverage.infer", func() error { return runCoverageInfer(subArgs[1:]) })
		} else if len(subArgs) > 0 && subArgs[0] == "hospitality" {
			err = withOcelLog("gftd.coverage.hospitality", func() error {
				return runHospitalityCoverage(context.Background(), subArgs[1:])
			})
		} else if len(subArgs) > 0 && subArgs[0] == "world" {
			err = withOcelLog("gftd.coverage.world", func() error { return runWorldCoverage(subArgs[1:]) })
		} else {
			err = withOcelLog("gftd.coverage.world", func() error { return runWorldCoverage(subArgs) })
		}
	case "coverage-test":
		err = withOcelLog("gftd.coverage.test", func() error { return runCoverage(os.Args[2:]) })
	case "source-graph":
		err = withOcelLog("gftd.sourceGraph", func() error { return runSourceGraph(os.Args[2:]) })
	case "haisen":
		err = withOcelLog("gftd.haisen", func() error { return runHaisen(os.Args[2:]) })
	case "kashika":
		err = withOcelLog("gftd.kashika", func() error { return runKashika(os.Args[2:]) })
	case "systemofsystem":
		err = withOcelLog("gftd.systemOfSystem", func() error { return runSystemOfSystem(os.Args[2:]) })
	// doc-audit subcommand removed 2026-04-13 (F-Plan F2): its only backing data source was
	// packages/contract/wit/deps/magatama-* which was archived to _archive/00-contracts/wit/.
	// doc_audit.go + wit_gen.go archived to _archive/70-tools/gftd/gftd-wit-260413/.
	case "shannon":
		err = withOcelLog("gftd.shannon", func() error { return runShannon(os.Args[2:]) })
	case "performance-test":
		err = withOcelLog("gftd.performanceTest", func() error { return runPerformanceTest(os.Args[2:]) })
	case "kaizen":
		err = withOcelLog("gftd.kaizen", func() error { return runKaizen(os.Args[2:]) })
	case "process-mining":
		err = withOcelLog("gftd.processMining", func() error { return runProcessMining(os.Args[2:]) })
	case "xrpc":
		err = runXRPC(os.Args[2:])
	case "seed":
		err = withOcelLog("gftd.seed", func() error { return runSeed(os.Args[2:]) })
	case "domain-ingest":
		err = withOcelLog("gftd.domainIngest", func() error { return runDomainIngest(os.Args[2:]) })
	case "collect":
		err = withOcelLog("gftd.collect", func() error { return runCollect(os.Args[2:]) })
	case "pds":
		subArgs := os.Args[2:]
		if len(subArgs) > 0 && subArgs[0] == "qa" {
			err = withOcelLog("gftd.pds.qa", func() error { return runPDSQA(subArgs[1:]) })
		} else {
			err = fmt.Errorf("unknown pds subcommand. Available: qa")
		}
	case "bunseki":
		err = withOcelLog("gftd.bunseki", func() error { return runBunseki(os.Args[2:]) })
	case "logs":
		err = runLogs(os.Args[2:])
	case "common-crawler":
		err = withOcelLog("gftd.commonCrawler", func() error { return runCommonCrawler(os.Args[2:]) })
	case "murakumo":
		err = withOcelLog("gftd.murakumo", func() error { return runMurakumo(os.Args[2:]) })
	case "yoroshiku":
		err = withOcelLog("gftd.yoroshiku", func() error { return runYoroshiku(os.Args[2:]) })
	case "mitama":
		err = withOcelLog("gftd.mitama", func() error { return runMitama(os.Args[2:]) })
	case "nono":
		err = withOcelLog("gftd.nono", func() error { return runNono(os.Args[2:]) })
	case "mokuteki":
		err = withOcelLog("gftd.mokuteki", func() error { return runMokuteki(os.Args[2:]) })
	case "kosei":
		err = withOcelLog("gftd.kosei", func() error { return runKosei(os.Args[2:]) })
	case "dodaf":
		err = withOcelLog("gftd.dodaf", func() error { return runDodaf(os.Args[2:]) })
	case "metrics":
		err = withOcelLog("gftd.metrics", func() error { return runMetrics(os.Args[2:]) })
	case "identifier-audit":
		err = withOcelLog("gftd.identifierAudit", func() error { return runIdentifierAudit(os.Args[2:]) })
	case "identity":
		subArgs := os.Args[2:]
		if len(subArgs) > 0 && subArgs[0] == "migrate-paths" {
			err = withOcelLog("gftd.identity.migratePaths", func() error { return runIdentityMigratePaths(subArgs[1:]) })
		} else {
			err = fmt.Errorf("unknown identity subcommand. Available: migrate-paths")
		}
	case "dns-sync":
		err = withOcelLog("gftd.dnsSync", func() error { return runDNSSync(os.Args[2:]) })
	case "bonsai":
		err = withOcelLog("gftd.bonsai", func() error { return runBonsai(os.Args[2:]) })
	case "training":
		err = withOcelLog("gftd.training", func() error { return runTraining(os.Args[2:]) })
	case "yukkuri":
		err = withOcelLog("gftd.yukkuri", func() error { return runYukkuri(os.Args[2:]) })
	case "version", "--version", "-v":
		fmt.Printf("gftd %s\n", version)
	case "help", "--help", "-h":
		printUsage()
	default:
		fatalf("unknown command: %s\n\nRun '%s help' for usage.", os.Args[1], filepath.Base(os.Args[0]))
	}
	if err != nil {
		fatalf("%v", err)
	}
}

func printUsage() {
	fmt.Printf(`gftd %s — magatama component build/deploy CLI (Cloudflare Workers)

USAGE:
  gftd <command> [flags]

COMMANDS:
  build              Build TS native component (magatama WIT)
                     magatama.jsonld hooks[event=post_build] are dispatched after a successful build
                     --extension: build as W Protocol extension (world: gftd:w/w-extension)
  deploy             Cloudflare deploy from source dir (magatama.jsonld → wrangler deploy + smoke test)
                     magatama.jsonld hooks[event=post_deploy] are dispatched after a successful deploy
  code-quality       Run code quality tools and produce a unified score report
  lint               Unified lint entrypoint (TS/JS/Go-adjacent checks via gftd)
  workspace          Workspace-level commands such as rsync-based sync
  plugin        Manage build tools (wasm-tools, tinygo adapters)
  code               Launch aider with LM Studio local API defaults (includes 'code exec' for non-interactive agents)
                     code agent: launch OpenRouter + RunPod ComfyUI terminal agent (LangGraph REPL)
                     code agent server: start LangGraph Server (langgraph dev)
  hinshitsu          Evaluate DID profile information quality and propose improvements via LM Studio OpenAI API
  deps               Evaluate deps.etzhayyim.com linker status and scoring
                     Subcommands: audit, export, score, governance-wit, sql, mv, graph
  docs               Docs registry and relation-graph commands
  docs-gen           Auto-generate factual schema docs from Parquet/local sources
                     Subcommands: schema (magatama.jsonld + G() scan → JSON or schema.auto.md)
  monitor            Monitor deployed app health, profile status, and send wave greetings
                     Subcommands: shinka (joucho cadence + kyumei-koji health analysis)
  apps               Per-app KPI dashboard, coverage evaluation, kyumei-koji analysis
                     Subcommands: status (default), coverage, kyumei-koji
  auth               Authenticate with etzhayyim.com (OAuth2 PKCE via Clerk)
  agent-token        Mint a short-lived service-auth JWT scoped to one NSID (com.atproto.server.getServiceAuth)
                     Usage: gftd agent-token --lxm <nsid> [--aud <did>] [--ttl 60] [-v]
                     Example: AT_TOKEN=$(gftd agent-token --lxm com.atproto.repo.applyWrites --ttl 60)
  agent              Local artificial-organism agent commands
                     Usage: gftd agent organism status [--json] [--web]
                            gftd agent organism publish [--no-dry-run --submit-chain]
                            gftd agent verify --did did:web:kami-agent.etzhayyim.com
  agent-runtime      Render/publish ERC-8004 public runtime manifests for k8s workers
                     Subcommands: render, publish, register, publish-agent
  set-profiles       Set AT Protocol profiles on mod.etzhayyim.com for all deployed workers
  coverage           World coverage analysis (DIDs/records vs real-world totals)
                     Subcommands: world (default), test (Rust/Go/TS test coverage), domain (authority-chain), logicalactors, actors, oil
  coverage-test      Alias for 'coverage test'
  source-graph       Source-level @gftd: annotation graph + policy enforcement
  haisen             App-level wiring diagram (配線図: invoke/write/read/subscribe edges)
  kashika            Visualization renderer (可視化: terminal/dot/mermaid/html)
  systemofsystem     System-of-Systems overview (DoDAF SV-1: layers/interfaces/health)
  doc-audit          Verify WIT @status annotations against code reality (intent vs implementation)
  shannon            Shannon redundancy scoring (8 checks: CLAUDE.md/code/WIT/config/dead-code/drift)
  kaizen             Kaizen toolbox (domain coverage + logs analysis; 'kaizen logs --fix' runs gftd code exec)
  pds                PDS subcommands (qa: API stability evaluation)
  performance-test   PDS XRPC endpoint performance measurement (latency, RPS, grading)
  process-mining     PDS handler static analysis + performance bottleneck detection
  bunseki            OCEL v2 runtime process mining + architecture analysis
                     Subcommands: scan, dfg, variants, conformance, performance, recommendations, arch
  logs               OCEL v2 event log viewer (Analytics Engine → PDS KV fallback)
                     Subcommands: arch (architecture event log from git history + deploy state)
  xrpc               Invoke any XRPC endpoint on an App or PDS (designed for Claude Code agents)
                     Usage: gftd xrpc <nsid> [-d <json>] [--app <nanoid>] [--url <base>] [--json] [-v]
                     Examples:
                       gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{"step":"platforms"}' --app a7m8oocs
                       gftd xrpc ai.gftd.apps.media_gamers.catalog.seedGames -d '{"offset":0,"limit":10}' --app a7m8oocs
                       gftd xrpc ai.gftd.apps.media_gamers.catalog.generateAll -d '{"slug":"elden-ring"}' --app a7m8oocs
  seed               Seed domain data + register DIDs for apps (DID + records → PDS → yata)
  domain-ingest      Canonical domain write path (normalize/enrich/local+CC imports → PDS)
  murakumo           Hayate V6 graph/train/inference pipeline commands
  yoroshiku          Validate/patch App obligations + KPI baseline
  kosei              Project Configuration (構成) Management — execution tier T1/T2/T3
                     Subcommands: list, show, set, promote, demote, suggest, snapshot, query, history, diff, kashika
  metrics            Business Intelligence dashboard (CF Analytics + Stripe + graph → MetricsBi vertex)
                     Subcommands: bi (default)
  identifier-audit   ADR-0019 atproto-native identifier topology validator
                     Flags: --json --severity {critical|high|medium|low} --deps <path>
                     Detects: mnemonic-nanoid, did-web-grandfathered, missing-legacy, handles-missing, orphan-legacy
  dns-sync           ADR-0013 Phase 3 DNS sync to Cloudflare (TXT + CNAME + A records)
                     Flags: --apply --json --no-cf --zone-name <name> --include-nanoid --include-txt --deps <path>
                     Auto-generates: _atproto.{handle} TXT (AT Protocol handle verify) + {nanoid}.etzhayyim.com CNAME (Phase 3 grace)
  dodaf              DoDAF v2-aligned Rule Registry (Parquet + DuckDB + MCP)
                     Subcommands: init, tv1 query, av2 get, rules context, add, validate, seed
  migrate-manifest   Migrate gftd.json → magatama.jsonld (--batch for bulk, --dry-run)
  database           RisingWave schema management via Kysely (@gftd/graph-schema SSoT)
                     Subcommands:
                       up                             Bootstrap: run all pending migrations (migrateToLatest)
                       migrate [latest|up|down|to|list]  Incremental migration control
                       status                         Show applied vs pending migrations
                     Flags: --env local|prod  --url <postgres-url>  (or $DATABASE_URL)
  projector     Project lifecycle + blocker tracking (MCP-backed)
                  create    Create new project
                  status    Get project status (with optional LLM summary)
                  update    Update progress/lifecycle_state
                  blocker   add / resolve blockers (Pregel BSP propagation)
                  list      List projects (filter by state/org)
  yukkuri       Yukkuri video generation CLI
                  compose   Compose a new video (--topic required, --outline, --owner-did, --json)
                  list      List videos (--owner-did, --status, --offset, --limit, --json)
                  get       Get a video by ID (--video-id or positional arg, --json)
                  health    Check yukkuri server health (--json)
                Base URL: $YUKKURI_URL or https://yukkuri.etzhayyim.com
  version       Print version

Run 'gftd <command> --help' for command-specific flags.
`, version)
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "gftd: "+format+"\n", args...)
	os.Exit(1)
}
