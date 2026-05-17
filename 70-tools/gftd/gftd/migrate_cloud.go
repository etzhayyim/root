package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// runMigrateCloud implements `gftd migrate --to cloud`.
//
// Provisions a new tenant on kyber.etzhayyim.com by calling
// ai.gftd.apps.kyber.provisionTenant, then prints a step-by-step
// migration checklist. Full data migration requires Hyperdrive read
// integration (ADR-0036) which is tracked in ADR-2605072300 Consequences.
func runMigrateCloud(args []string) error {
	fs := flag.NewFlagSet("migrate", flag.ContinueOnError)
	to := fs.String("to", "", "migration target: cloud (required)")
	orgDid := fs.String("org-did", "", "your org DID (e.g. did:web:yourcompany.etzhayyim.com)")
	orgName := fs.String("org-name", "", "your organisation name")
	email := fs.String("email", "", "billing contact email")
	planID := fs.String("plan", "free", "target plan: free|starter|growth|scale")
	cloudURL := fs.String("cloud-url", "https://kyber.etzhayyim.com", "gftd Cloud base URL")
	dir := fs.String("dir", ".", "self-hosted component directory (magatama.jsonld)")
	dryRun := fs.Bool("dry-run", false, "print plan without calling the cloud API")
	jsonOut := fs.Bool("json", false, "emit JSON result")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if *to == "" {
		return fmt.Errorf("--to is required (only supported value: cloud)")
	}
	if *to != "cloud" {
		return fmt.Errorf("unsupported migration target %q — only 'cloud' is supported", *to)
	}

	// Auto-detect orgDid from magatama.jsonld if not supplied.
	if *orgDid == "" {
		detected, err := detectOrgDid(*dir)
		if err == nil && detected != "" {
			*orgDid = detected
			fmt.Fprintf(os.Stderr, "detected org DID from magatama.jsonld: %s\n", *orgDid)
		}
	}
	if *orgDid == "" {
		return fmt.Errorf("--org-did is required (e.g. did:web:yourcompany.etzhayyim.com)")
	}
	if *orgName == "" {
		// Derive from DID as fallback.
		*orgName = deriveOrgName(*orgDid)
	}

	plan := cloudMigrationPlan{
		OrgDid:   *orgDid,
		OrgName:  *orgName,
		Email:    *email,
		PlanID:   *planID,
		CloudURL: *cloudURL,
	}

	if *dryRun {
		return printMigrationPlan(plan, *jsonOut)
	}

	result, err := provisionCloudTenant(plan)
	if err != nil {
		return fmt.Errorf("provisioning failed: %w", err)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(result)
	}

	printMigrationResult(plan, result)
	return nil
}

type cloudMigrationPlan struct {
	OrgDid   string
	OrgName  string
	Email    string
	PlanID   string
	CloudURL string
}

type provisionResult struct {
	TenantID         string `json:"tenantId"`
	PlanID           string `json:"planId"`
	Status           string `json:"status"`
	StripeCustomerID string `json:"stripeCustomerId,omitempty"`
	AlreadyExisted   bool   `json:"alreadyExisted"`
	Error            string `json:"error,omitempty"`
}

func provisionCloudTenant(p cloudMigrationPlan) (*provisionResult, error) {
	body := map[string]string{
		"orgDid":  p.OrgDid,
		"orgName": p.OrgName,
		"planId":  p.PlanID,
	}
	if p.Email != "" {
		body["email"] = p.Email
	}

	payload, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}

	url := strings.TrimRight(p.CloudURL, "/") + "/xrpc/ai.gftd.apps.kyber.provisionTenant"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTTP request failed: %w", err)
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result provisionResult
	if err := json.Unmarshal(raw, &result); err != nil {
		return nil, fmt.Errorf("unexpected response body: %s", string(raw))
	}
	if result.Error != "" {
		return nil, fmt.Errorf("provision error: %s", result.Error)
	}
	return &result, nil
}

func detectOrgDid(dir string) (string, error) {
	jsonldPath := filepath.Join(dir, "magatama.jsonld")
	data, err := os.ReadFile(jsonldPath)
	if err != nil {
		return "", err
	}
	var m map[string]interface{}
	if err := json.Unmarshal(data, &m); err != nil {
		return "", err
	}
	if did, ok := m["did"].(string); ok && did != "" {
		return did, nil
	}
	return "", nil
}

func deriveOrgName(did string) string {
	// did:web:company.etzhayyim.com → "company.etzhayyim.com"
	parts := strings.SplitN(did, ":", 3)
	if len(parts) == 3 {
		return parts[2]
	}
	return did
}

func printMigrationPlan(p cloudMigrationPlan, asJSON bool) error {
	if asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]interface{}{
			"dryRun":   true,
			"orgDid":   p.OrgDid,
			"orgName":  p.OrgName,
			"planId":   p.PlanID,
			"cloudUrl": p.CloudURL,
		})
	}

	fmt.Printf(`
gftd migrate --to cloud — dry run
──────────────────────────────────
  Org DID  : %s
  Org Name : %s
  Plan     : %s
  Cloud    : %s

Steps that will execute:
  1. POST %s/xrpc/ai.gftd.apps.kyber.provisionTenant
  2. Receive tenant ID + Stripe customer ID
  3. Print post-migration checklist

Run without --dry-run to proceed.
`, p.OrgDid, p.OrgName, p.PlanID, p.CloudURL, p.CloudURL)
	return nil
}

func printMigrationResult(p cloudMigrationPlan, r *provisionResult) {
	status := "✓ new tenant created"
	if r.AlreadyExisted {
		status = "✓ tenant already existed (idempotent)"
	}

	fmt.Printf(`
gftd migrate --to cloud — %s
──────────────────────────────────────────────
  Tenant ID : %s
  Org DID   : %s
  Plan      : %s
  Status    : %s
`, status, r.TenantID, p.OrgDid, r.PlanID, r.Status)

	if r.StripeCustomerID != "" {
		fmt.Printf("  Stripe ID : %s\n", r.StripeCustomerID)
	}

	fmt.Printf(`
Next steps
──────────
  1. Update your DNS / DID document to point at %s
     did:web redirect: add /.well-known/did.json → {"id":"%s","service":[{"id":"#kyber","type":"KyberErp","serviceEndpoint":"%s"}]}

  2. In your self-hosted wrangler.jsonc, add:
       "KYBER_CLOUD_TENANT": "%s"
     Deploy once to flush pending records, then decommission the self-hosted Worker.

  3. Verify at:
       curl '%s/xrpc/ai.gftd.apps.kyber.getTenantPlan?orgDid=%s'

  4. Optional — upgrade plan:
       curl -X POST '%s/xrpc/ai.gftd.apps.kyber.provisionTenant' \
            -H 'content-type: application/json' \
            -d '{"orgDid":"%s","orgName":"%s","planId":"starter"}'

  ADR reference: 90-docs/adr/2605072300-open-source-cloud-business-model.md
`, p.CloudURL, p.OrgDid, p.CloudURL,
		r.TenantID,
		p.CloudURL, p.OrgDid,
		p.CloudURL, p.OrgDid, p.OrgName)
}
