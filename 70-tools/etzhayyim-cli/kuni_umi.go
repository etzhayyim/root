// kuni_umi.go — `etzhayyim kuni-umi <subcommand>` human entry point for the
// 6-phase robotic-deployment flow (ADR-2605201400).
//
// Each subcommand maps 1:1 to a Lexicon procedure under
// com.etzhayyim.apps.etzhayyim.kuniUmi.* and POSTs a JSON payload whose shape
// is dictated by the lexicon's defs.main.input.schema (canonical at
// 00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/kuniUmi/).
//
// The default --target points at the SiteSurveyCell loopback healthz
// port (13017) as a placeholder pending the kuni-umi/api gateway. Real
// production traffic will hit
//   https://etzhayyim.com/xrpc/com.etzhayyim.apps.etzhayyim.kuniUmi.<procedure>
// — the CLI is shape-agnostic and works against either endpoint via the
// --target flag.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// defaultKuniUmiTarget — kuni-umi HTTP API gateway (KuniUmiApiCell on
// naphtali, ADR-2605201400 §1). The gateway translates POSTs into cell
// graph invocations (dev mode) or AT MST records via PdsClient
// (production mode, ETZHAYYIM_ENV=production).
const defaultKuniUmiTarget = "http://127.0.0.1:13030/api/invoke"

const kuniUmiHTTPTimeout = 10 * time.Second

func runKuniUmi(args []string) error {
	if len(args) == 0 {
		printKuniUmiUsage()
		return nil
	}
	switch args[0] {
	case "define-site":
		return cmdKuniUmiDefineSite(args[1:])
	case "submit-survey":
		return cmdKuniUmiSubmitSurvey(args[1:])
	case "propose-plan":
		return cmdKuniUmiProposePlan(args[1:])
	case "record-progress":
		return cmdKuniUmiRecordProgress(args[1:])
	case "commission":
		return cmdKuniUmiCommission(args[1:])
	case "audit-event":
		return cmdKuniUmiAuditEvent(args[1:])
	case "help", "--help", "-h":
		printKuniUmiUsage()
		return nil
	default:
		return fmt.Errorf("unknown kuni-umi subcommand: %s\nRun 'etzhayyim kuni-umi help' for usage.", args[0])
	}
}

func printKuniUmiUsage() {
	fmt.Print(`etzhayyim kuni-umi — 6-phase robotic-deployment flow (ADR-2605201400)

USAGE:
  etzhayyim kuni-umi <subcommand> [flags]

SUBCOMMANDS:
  define-site       Phase 1: declare a planetary-infrastructure deployment site
                    (POST defineDeploymentSite). Runs jurisdiction-eligibility DMN.
  submit-survey     Phase 2: submit a Giemon scout fleet survey result
                    (POST submitSiteSurvey). N>=2 robot DID signatures required.
  propose-plan      Phase 3 entry: propose a deployment plan
                    (POST proposeDeploymentPlan). BoM / payment-plan are encrypted envelopes.
  record-progress   Phase 3 stream: 1-10 Hz checkpointer progress records
                    (POST recordConstructionProgress). N>=2 witness signatures.
  commission        Phase 4: commission completed deployment, register open-* assets
                    (POST commissionDeployment). Site state -> operational.
  audit-event       Phase 5/6: permanent robot-witnessed audit event
                    (POST recordPhysicalAuditEvent). Feeds Phenotype.effectiveMultiplier.

COMMON FLAGS (all subcommands):
  --target <url>    API endpoint. Defaults to ` + defaultKuniUmiTarget + `
                    (loopback placeholder pending kuni-umi/api gateway).
                    Production: https://etzhayyim.com/xrpc/<lexicon-id>
  --dry-run         Print payload to stdout; do not POST.

Run 'etzhayyim kuni-umi <subcommand> --help' for per-command flags.

SEE ALSO:
  ADR-2605201400                                       (6-phase flow)
  00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/kuniUmi (input schemas)
  20-actors/magatama/cells/{site_survey,deployment_planning,
    construction_orchestration,commissioning,audit_witness,decommission}
`)
}

// ----- subcommand: define-site -------------------------------------------

func cmdKuniUmiDefineSite(args []string) error {
	fs := flag.NewFlagSet("kuni-umi define-site", flag.ContinueOnError)
	siteCode := fs.String("site-code", "", "unique uppercase site code (A-Z0-9-, 2..64) [required]")
	name := fs.String("name", "", "human-readable site name")
	utilityClass := fs.String("utility-class", "", "electric|gas|water|network|power|rail|airplane|port|multi [required]")
	domain := fs.String("domain", "", "terrestrial|ocean|river|atmosphere|orbit [required]")
	intendedUse := fs.String("intended-use", "", "free-form intended-use statement [required]")
	jurisdictionDid := fs.String("jurisdiction-did", "", "DID of stewardship registry entry [required]")
	stewardDid := fs.String("steward-did", "", "Steward (Lv5+) DID [required]")
	lifespanYears := fs.Int("lifespan-years", 30, "operational lifespan years")
	geo := fs.String("geo", "", "GeoJSON Feature: inline JSON or @path/to.geojson [required]")
	var beneficiaries multiString
	fs.Var(&beneficiaries, "intended-beneficiary-did", "Community DID benefiting from deployment (repeatable)")
	localLawCid := fs.String("local-law-attestation-cid", "", "IPFS CID of local-law compliance attestation (required for restricted utilities)")
	target := fs.String("target", defaultKuniUmiTarget, "API endpoint URL")
	dryRun := fs.Bool("dry-run", false, "print payload, do not POST")
	if err := fs.Parse(args); err != nil {
		return err
	}

	// Required fields per lexicon defs.main.input.schema
	if err := requireString("site-code", *siteCode); err != nil {
		return err
	}
	if err := requireString("utility-class", *utilityClass); err != nil {
		return err
	}
	if err := requireString("domain", *domain); err != nil {
		return err
	}
	if err := requireString("intended-use", *intendedUse); err != nil {
		return err
	}
	if err := requireString("jurisdiction-did", *jurisdictionDid); err != nil {
		return err
	}
	if err := requireString("steward-did", *stewardDid); err != nil {
		return err
	}
	if err := requireString("geo", *geo); err != nil {
		return err
	}

	geoStr, err := loadGeo(*geo)
	if err != nil {
		return fmt.Errorf("--geo: %w", err)
	}

	// intendedBeneficiaryDids is required by the lexicon; default to [] not null.
	beneficiaryList := []string(beneficiaries)
	if beneficiaryList == nil {
		beneficiaryList = []string{}
	}
	payload := map[string]interface{}{
		"siteCode":                *siteCode,
		"name":                    *name,
		"geo":                     geoStr,
		"utilityClass":            *utilityClass,
		"domain":                  *domain,
		"jurisdictionDid":         *jurisdictionDid,
		"stewardDid":              *stewardDid,
		"intendedUse":             *intendedUse,
		"intendedBeneficiaryDids": beneficiaryList,
		"lifespanYears":           *lifespanYears,
	}
	if *name == "" {
		// name is required by schema; default to siteCode if not supplied.
		payload["name"] = *siteCode
	}
	if *localLawCid != "" {
		payload["localLawAttestationCid"] = *localLawCid
	}

	return postKuniUmi(*target, "com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite", payload, *dryRun)
}

// ----- subcommand: submit-survey -----------------------------------------

func cmdKuniUmiSubmitSurvey(args []string) error {
	fs := flag.NewFlagSet("kuni-umi submit-survey", flag.ContinueOnError)
	siteDid := fs.String("site-did", "", "site DID [required]")
	var surveyCids multiString
	fs.Var(&surveyCids, "survey-blob-cid", "IPFS CID of survey sensor blob (repeatable, >=1) [required]")
	impactScore := fs.Int("impact-score", -1, "ecology impact 0..100 [required]")
	protectedSpecies := fs.Bool("protected-species", false, "protected species detected")
	culturalHeritage := fs.Bool("cultural-heritage", false, "cultural heritage detected")
	notesCid := fs.String("notes-cid", "", "optional IPFS CID for ecologist notes")
	populationImpacted := fs.Int("population-impacted", -1, "estimated population impacted (optional)")
	reversibilityScore := fs.Int("reversibility-score", -1, "0..100 reversibility score (optional)")
	var witnesses multiString
	fs.Var(&witnesses, "witness", "robotDid:blobHash:signature (repeatable, >=2 required)")
	target := fs.String("target", defaultKuniUmiTarget, "API endpoint URL")
	dryRun := fs.Bool("dry-run", false, "print payload, do not POST")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if err := requireString("site-did", *siteDid); err != nil {
		return err
	}
	if len(surveyCids) == 0 {
		return fmt.Errorf("--survey-blob-cid is required (>=1)")
	}
	if *impactScore < 0 || *impactScore > 100 {
		return fmt.Errorf("--impact-score must be in 0..100 (got %d)", *impactScore)
	}
	witnessAtt, err := parseWitnessAttestations(witnesses, "blobHash")
	if err != nil {
		return err
	}
	if len(witnessAtt) < 2 {
		return fmt.Errorf("--witness requires >=2 attestations (got %d)", len(witnessAtt))
	}

	ecology := map[string]interface{}{
		"impactScore":              *impactScore,
		"protectedSpeciesDetected": *protectedSpecies,
		"culturalHeritageDetected": *culturalHeritage,
	}
	if *notesCid != "" {
		ecology["notesCid"] = *notesCid
	}

	payload := map[string]interface{}{
		"siteDid":             *siteDid,
		"surveyBlobCids":      []string(surveyCids),
		"witnessAttestations": witnessAtt,
		"ecologyBaseline":     ecology,
	}
	if *populationImpacted >= 0 {
		payload["populationImpacted"] = *populationImpacted
	}
	if *reversibilityScore >= 0 {
		payload["reversibilityScore"] = *reversibilityScore
	}

	return postKuniUmi(*target, "com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey", payload, *dryRun)
}

// ----- subcommand: propose-plan ------------------------------------------

func cmdKuniUmiProposePlan(args []string) error {
	fs := flag.NewFlagSet("kuni-umi propose-plan", flag.ContinueOnError)
	siteDid := fs.String("site-did", "", "site DID [required]")
	surveyDid := fs.String("survey-did", "", "survey DID [required]")
	planCode := fs.String("plan-code", "", "plan code (A-Z0-9-, 2..64) [required]")
	var targetTopologies multiString
	fs.Var(&targetTopologies, "target-topology-did", "open-* utility record DID (repeatable, >=1) [required]")
	bomEnvelopeCid := fs.String("bom-envelope-cid", "", "IPFS CID of XChaCha20-Poly1305 BoM envelope [required]")
	paymentPlanCid := fs.String("payment-plan-cid", "", "IPFS CID of payment schedule envelope [required]")
	robotCount := fs.Int("robot-count", 0, "Giemon units required [required, >0]")
	estimatedRobotHours := fs.Int("estimated-robot-hours", 0, "estimated robot-hours [required, >0]")
	fleetDid := fs.String("fleet-did", "", "pre-allocated fleet DID (optional)")
	lifespanYears := fs.Int("lifespan-years", 30, "operational lifespan years")
	startISO := fs.String("start-iso", "", "RFC3339 start (optional)")
	endISO := fs.String("end-iso", "", "RFC3339 end (optional)")
	slackDays := fs.Int("slack-days", -1, "schedule slack days (optional)")
	requiresGov := fs.Bool("requires-governance", false, "from proportionality-check DMN")
	govProposalUri := fs.String("governance-proposal-uri", "", "URI of governance proposal record")
	thirdPartyReviewCid := fs.String("council-third-party-review-cid", "", "ecologist review CID (req when ecologyImpactScore>30)")
	target := fs.String("target", defaultKuniUmiTarget, "API endpoint URL")
	dryRun := fs.Bool("dry-run", false, "print payload, do not POST")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if err := requireString("site-did", *siteDid); err != nil {
		return err
	}
	if err := requireString("survey-did", *surveyDid); err != nil {
		return err
	}
	if err := requireString("plan-code", *planCode); err != nil {
		return err
	}
	if len(targetTopologies) == 0 {
		return fmt.Errorf("--target-topology-did is required (>=1)")
	}
	if err := requireString("bom-envelope-cid", *bomEnvelopeCid); err != nil {
		return err
	}
	if err := requireString("payment-plan-cid", *paymentPlanCid); err != nil {
		return err
	}
	if *robotCount <= 0 {
		return fmt.Errorf("--robot-count must be > 0")
	}
	if *estimatedRobotHours <= 0 {
		return fmt.Errorf("--estimated-robot-hours must be > 0")
	}

	fleet := map[string]interface{}{
		"robotCount":          *robotCount,
		"estimatedRobotHours": *estimatedRobotHours,
	}
	if *fleetDid != "" {
		fleet["fleetDid"] = *fleetDid
	}

	payload := map[string]interface{}{
		"siteDid":            *siteDid,
		"surveyDid":          *surveyDid,
		"planCode":           *planCode,
		"targetTopologyDids": []string(targetTopologies),
		"bomEnvelopeCid":     *bomEnvelopeCid,
		"fleetAllocation":    fleet,
		"paymentPlanCid":     *paymentPlanCid,
		"lifespanYears":      *lifespanYears,
		"requiresGovernance": *requiresGov,
	}

	if *startISO != "" || *endISO != "" || *slackDays >= 0 {
		timeline := map[string]interface{}{}
		if *startISO != "" {
			timeline["startISO"] = *startISO
		}
		if *endISO != "" {
			timeline["endISO"] = *endISO
		}
		if *slackDays >= 0 {
			timeline["slackDays"] = *slackDays
		}
		payload["timeline"] = timeline
	}
	if *govProposalUri != "" {
		payload["governanceProposalUri"] = *govProposalUri
	}
	if *thirdPartyReviewCid != "" {
		payload["councilThirdPartyReviewCid"] = *thirdPartyReviewCid
	}

	return postKuniUmi(*target, "com.etzhayyim.apps.etzhayyim.kuniUmi.proposeDeploymentPlan", payload, *dryRun)
}

// ----- subcommand: record-progress ---------------------------------------

func cmdKuniUmiRecordProgress(args []string) error {
	fs := flag.NewFlagSet("kuni-umi record-progress", flag.ContinueOnError)
	planDid := fs.String("plan-did", "", "plan DID [required]")
	siteDid := fs.String("site-did", "", "site DID [required]")
	superStepIndex := fs.Int("super-step-index", -1, "Pregel super-step counter (>=0) [required]")
	cellId := fs.String("cell-id", "", "construction cell identifier [required]")
	phase := fs.String("phase", "", "queued|in-progress|complete|halted|handoff-ready [required]")
	completionPct := fs.Float64("completion-pct", -1, "0..100 percent complete (optional)")
	robotDid := fs.String("robot-did", "", "primary actor robot DID")
	var sensorCids multiString
	fs.Var(&sensorCids, "sensor-blob-cid", "IPFS CID of sensor blob (repeatable)")
	var anomalyFlags multiString
	fs.Var(&anomalyFlags, "anomaly-flag", "anomaly tag (repeatable)")
	var witnesses multiString
	fs.Var(&witnesses, "witness", "robotDid:blobHash:signature (repeatable, >=2 required)")
	target := fs.String("target", defaultKuniUmiTarget, "API endpoint URL")
	dryRun := fs.Bool("dry-run", false, "print payload, do not POST")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if err := requireString("plan-did", *planDid); err != nil {
		return err
	}
	if err := requireString("site-did", *siteDid); err != nil {
		return err
	}
	if *superStepIndex < 0 {
		return fmt.Errorf("--super-step-index must be >= 0")
	}
	if err := requireString("cell-id", *cellId); err != nil {
		return err
	}
	if err := requireString("phase", *phase); err != nil {
		return err
	}
	witnessAtt, err := parseWitnessAttestations(witnesses, "blobHash")
	if err != nil {
		return err
	}
	if len(witnessAtt) < 2 {
		return fmt.Errorf("--witness requires >=2 attestations (got %d)", len(witnessAtt))
	}

	payload := map[string]interface{}{
		"planDid":             *planDid,
		"siteDid":             *siteDid,
		"superStepIndex":      *superStepIndex,
		"cellId":              *cellId,
		"phase":               *phase,
		"witnessAttestations": witnessAtt,
	}
	if *completionPct >= 0 {
		payload["completionPct"] = *completionPct
	}
	if *robotDid != "" {
		payload["robotDid"] = *robotDid
	}
	if len(sensorCids) > 0 {
		payload["sensorBlobCids"] = []string(sensorCids)
	}
	if len(anomalyFlags) > 0 {
		payload["anomalyFlags"] = []string(anomalyFlags)
	}

	return postKuniUmi(*target, "com.etzhayyim.apps.etzhayyim.kuniUmi.recordConstructionProgress", payload, *dryRun)
}

// ----- subcommand: commission --------------------------------------------

func cmdKuniUmiCommission(args []string) error {
	fs := flag.NewFlagSet("kuni-umi commission", flag.ContinueOnError)
	planDid := fs.String("plan-did", "", "plan DID [required]")
	siteDid := fs.String("site-did", "", "site DID [required]")
	var utilityAssetDids multiString
	fs.Var(&utilityAssetDids, "utility-asset-did", "open-* utility record DID (repeatable, >=1) [required]")
	var openOtLoopDids multiString
	fs.Var(&openOtLoopDids, "open-ot-loop-did", "open-ot defineLoop DID (repeatable, >=1) [required]")
	acceptancePassed := fs.Bool("acceptance-passed", true, "acceptance test passed")
	testReportCid := fs.String("test-report-cid", "", "IPFS CID of acceptance test report [required]")
	var openOtCellFingerprints multiString
	fs.Var(&openOtCellFingerprints, "open-ot-cell-fingerprint", "WASM AOT module hash (repeatable)")
	stewardOperatorDid := fs.String("steward-operator-did", "", "Steward DID for day-to-day ops [required]")
	target := fs.String("target", defaultKuniUmiTarget, "API endpoint URL")
	dryRun := fs.Bool("dry-run", false, "print payload, do not POST")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if err := requireString("plan-did", *planDid); err != nil {
		return err
	}
	if err := requireString("site-did", *siteDid); err != nil {
		return err
	}
	if len(utilityAssetDids) == 0 {
		return fmt.Errorf("--utility-asset-did is required (>=1)")
	}
	if len(openOtLoopDids) == 0 {
		return fmt.Errorf("--open-ot-loop-did is required (>=1)")
	}
	if err := requireString("test-report-cid", *testReportCid); err != nil {
		return err
	}
	if err := requireString("steward-operator-did", *stewardOperatorDid); err != nil {
		return err
	}

	acceptanceTest := map[string]interface{}{
		"passed":        *acceptancePassed,
		"testReportCid": *testReportCid,
	}
	if len(openOtCellFingerprints) > 0 {
		acceptanceTest["openOtCellFingerprints"] = []string(openOtCellFingerprints)
	}

	payload := map[string]interface{}{
		"planDid":            *planDid,
		"siteDid":            *siteDid,
		"utilityAssetDids":   []string(utilityAssetDids),
		"openOtLoopDids":     []string(openOtLoopDids),
		"acceptanceTest":     acceptanceTest,
		"stewardOperatorDid": *stewardOperatorDid,
	}

	return postKuniUmi(*target, "com.etzhayyim.apps.etzhayyim.kuniUmi.commissionDeployment", payload, *dryRun)
}

// ----- subcommand: audit-event -------------------------------------------

func cmdKuniUmiAuditEvent(args []string) error {
	fs := flag.NewFlagSet("kuni-umi audit-event", flag.ContinueOnError)
	siteDid := fs.String("site-did", "", "site DID [required]")
	planDid := fs.String("plan-did", "", "plan DID (optional, when during construction)")
	eventClass := fs.String("event-class", "", "anomaly|intrusion|injury|compliance-check|community-event [required]")
	subtype := fs.String("subtype", "", "class-specific subtype")
	occurredAt := fs.String("occurred-at", "", "RFC3339 timestamp [required]")
	evidenceCid := fs.String("evidence-cid", "", "IPFS CID of evidence [required]")
	var participantDids multiString
	fs.Var(&participantDids, "participant-did", "participant DID (repeatable)")
	var witnesses multiString
	fs.Var(&witnesses, "witness", "robotDid:evidenceHash:signature (repeatable, >=2 required)")
	phenotypeDeltaTargetDid := fs.String("phenotype-delta-target-did", "", "DID whose effectiveMultiplier updates (optional)")
	phenotypeDeltaBps := fs.Int("phenotype-delta-bps", 0, "signed basis-points delta")
	target := fs.String("target", defaultKuniUmiTarget, "API endpoint URL")
	dryRun := fs.Bool("dry-run", false, "print payload, do not POST")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if err := requireString("site-did", *siteDid); err != nil {
		return err
	}
	if err := requireString("event-class", *eventClass); err != nil {
		return err
	}
	if err := requireString("occurred-at", *occurredAt); err != nil {
		return err
	}
	if err := requireString("evidence-cid", *evidenceCid); err != nil {
		return err
	}
	witnessAtt, err := parseWitnessAttestations(witnesses, "evidenceHash")
	if err != nil {
		return err
	}
	if len(witnessAtt) < 2 {
		return fmt.Errorf("--witness requires >=2 attestations (got %d)", len(witnessAtt))
	}

	payload := map[string]interface{}{
		"siteDid":             *siteDid,
		"eventClass":          *eventClass,
		"occurredAt":          *occurredAt,
		"evidenceCid":         *evidenceCid,
		"witnessAttestations": witnessAtt,
	}
	if *planDid != "" {
		payload["planDid"] = *planDid
	}
	if *subtype != "" {
		payload["subtype"] = *subtype
	}
	if len(participantDids) > 0 {
		payload["participantDids"] = []string(participantDids)
	}
	if *phenotypeDeltaTargetDid != "" {
		payload["phenotypeDeltaTargetDid"] = *phenotypeDeltaTargetDid
	}
	if *phenotypeDeltaBps != 0 {
		payload["phenotypeDeltaBps"] = *phenotypeDeltaBps
	}

	return postKuniUmi(*target, "com.etzhayyim.apps.etzhayyim.kuniUmi.recordPhysicalAuditEvent", payload, *dryRun)
}

// ----- helpers -----------------------------------------------------------

// multiString is a repeatable string flag (e.g., --witness a --witness b).
type multiString []string

func (m *multiString) String() string {
	if m == nil {
		return ""
	}
	return strings.Join(*m, ",")
}

func (m *multiString) Set(v string) error {
	*m = append(*m, v)
	return nil
}

func requireString(flagName, v string) error {
	if strings.TrimSpace(v) == "" {
		return fmt.Errorf("--%s is required", flagName)
	}
	return nil
}

// loadGeo accepts either inline GeoJSON or @path/to/file. The lexicon stores
// the GeoJSON as an opaque string (geo: { "type": "string" }) so we preserve
// raw text rather than re-marshalling, but we validate it parses as JSON.
func loadGeo(raw string) (string, error) {
	var src string
	if strings.HasPrefix(raw, "@") {
		path := strings.TrimPrefix(raw, "@")
		b, err := os.ReadFile(path)
		if err != nil {
			return "", fmt.Errorf("read %s: %w", path, err)
		}
		src = string(b)
	} else {
		src = raw
	}
	var probe interface{}
	if err := json.Unmarshal([]byte(src), &probe); err != nil {
		return "", fmt.Errorf("not valid JSON: %w", err)
	}
	return src, nil
}

// parseWitnessAttestations parses --witness robotDid:hash:signature triples
// into the lexicon's witnessAttestations array shape. hashKey is "blobHash"
// for survey/progress and "evidenceHash" for audit-event (per each lexicon).
//
// Splitting: we split on the FIRST two colons only, so DIDs containing
// colons (e.g., did:web:etzhayyim.com:...) survive intact in robotDid.
// The hash is the substring between the last two colons; signature is the tail.
// Strategy used: SplitN from the end via index of last ':'.
func parseWitnessAttestations(raw []string, hashKey string) ([]map[string]string, error) {
	out := make([]map[string]string, 0, len(raw))
	for i, v := range raw {
		// Find the last two ':' so DIDs (which contain ':') stay in robotDid.
		lastColon := strings.LastIndex(v, ":")
		if lastColon < 0 {
			return nil, fmt.Errorf("--witness #%d %q: expected <robotDid>:<hash>:<signature>", i+1, v)
		}
		sig := v[lastColon+1:]
		rest := v[:lastColon]
		penultimate := strings.LastIndex(rest, ":")
		if penultimate < 0 {
			return nil, fmt.Errorf("--witness #%d %q: expected <robotDid>:<hash>:<signature>", i+1, v)
		}
		hash := rest[penultimate+1:]
		robotDid := rest[:penultimate]
		if robotDid == "" || hash == "" || sig == "" {
			return nil, fmt.Errorf("--witness #%d %q: robotDid/hash/signature must all be non-empty", i+1, v)
		}
		out = append(out, map[string]string{
			"robotDid":  robotDid,
			hashKey:     hash,
			"signature": sig,
		})
	}
	return out, nil
}

// resolveKuniUmiTarget resolves the per-subcommand POST URL.
//
// If target already contains "/xrpc/" it is used verbatim (caller is
// pointing at an explicit endpoint). Otherwise we treat target as a
// base URL (or strip a trailing "/api/invoke" if present) and append
// "/xrpc/<nsid>" — the canonical KuniUmiApiCell route.
func resolveKuniUmiTarget(target, nsid string) string {
	if strings.Contains(target, "/xrpc/") {
		return target
	}
	base := target
	if strings.HasSuffix(base, "/api/invoke") {
		base = strings.TrimSuffix(base, "/api/invoke")
	}
	base = strings.TrimRight(base, "/")
	return base + "/xrpc/" + nsid
}

// postKuniUmi marshals payload as JSON and either prints (dry-run) or
// POSTs to target with a 10s timeout. Response body is pretty-printed.
// nsid is the kuni-umi lexicon ID; the helper builds the canonical XRPC
// URL via resolveKuniUmiTarget so subcommands can pass the raw --target.
func postKuniUmi(target, nsid string, payload map[string]interface{}, dryRun bool) error {
	resolved := resolveKuniUmiTarget(target, nsid)
	body, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal payload: %w", err)
	}

	if dryRun {
		fmt.Printf("Would POST to %s:\n%s\n", resolved, string(body))
		return nil
	}

	req, err := http.NewRequest(http.MethodPost, resolved, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	client := &http.Client{Timeout: kuniUmiHTTPTimeout}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("POST %s: %w", resolved, err)
	}
	defer resp.Body.Close()

	respBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read response: %w", err)
	}

	// Try to pretty-print JSON; fall back to raw bytes.
	var parsed interface{}
	if jerr := json.Unmarshal(respBytes, &parsed); jerr == nil {
		pretty, perr := json.MarshalIndent(parsed, "", "  ")
		if perr == nil {
			fmt.Println(string(pretty))
		} else {
			fmt.Println(string(respBytes))
		}
	} else {
		fmt.Println(string(respBytes))
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d from %s", resp.StatusCode, target)
	}
	return nil
}
