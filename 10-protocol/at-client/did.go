package atclient

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

// DIDDocument is a W3C DID document.
type DIDDocument struct {
	Context            []string               `json:"@context"`
	ID                 string                 `json:"id"`
	AlsoKnownAs        []string               `json:"alsoKnownAs"`
	VerificationMethod []VerificationMethod   `json:"verificationMethod"`
	Service            []DIDService           `json:"service"`
}

// VerificationMethod is a key entry in a DID document.
type VerificationMethod struct {
	ID                 string `json:"id"`
	Type               string `json:"type"`
	Controller         string `json:"controller"`
	PublicKeyMultibase string `json:"publicKeyMultibase,omitempty"`
	PublicKeyJwk       any    `json:"publicKeyJwk,omitempty"`
}

// DIDService is a service endpoint in a DID document.
type DIDService struct {
	ID              string `json:"id"`
	Type            string `json:"type"`
	ServiceEndpoint string `json:"serviceEndpoint"`
}

// PDSEndpoint extracts the PDS service endpoint from a DID document.
func (d *DIDDocument) PDSEndpoint() string {
	for _, svc := range d.Service {
		if svc.Type == "AtprotoPersonalDataServer" {
			return svc.ServiceEndpoint
		}
	}
	return ""
}

// Handle returns the AT Protocol handle from alsoKnownAs, e.g. "at://user.etzhayyim.com".
func (d *DIDDocument) Handle() string {
	for _, aka := range d.AlsoKnownAs {
		if strings.HasPrefix(aka, "at://") {
			return strings.TrimPrefix(aka, "at://")
		}
	}
	return ""
}

var didHTTPClient = &http.Client{Timeout: 10 * time.Second}

// ResolveDID resolves a DID document. Supports did:plc and did:web.
func ResolveDID(ctx context.Context, did string) (*DIDDocument, error) {
	var resolveURL string
	switch {
	case strings.HasPrefix(did, "did:plc:"):
		resolveURL = "https://plc.directory/" + did
	case strings.HasPrefix(did, "did:web:"):
		host := strings.TrimPrefix(did, "did:web:")
		resolveURL = "https://" + host + "/.well-known/did.json"
	default:
		return nil, fmt.Errorf("atclient: unsupported DID method: %s", did)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, resolveURL, nil)
	if err != nil {
		return nil, err
	}
	resp, err := didHTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("atclient: DID resolution failed for %s: %w", did, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("atclient: DID resolution HTTP %d for %s", resp.StatusCode, did)
	}
	var doc DIDDocument
	if err := json.NewDecoder(resp.Body).Decode(&doc); err != nil {
		return nil, fmt.Errorf("atclient: DID document decode: %w", err)
	}
	return &doc, nil
}

// ResolveHandle resolves an AT Protocol handle to a DID.
// pdsURL is the PDS host to query (e.g. "https://bsky.social").
func ResolveHandle(ctx context.Context, pdsURL, handle string) (string, error) {
	c := NewClient(pdsURL)
	var result struct {
		DID string `json:"did"`
	}
	if err := c.Query(ctx, "com.atproto.identity.resolveHandle",
		map[string]string{"handle": handle}, &result); err != nil {
		return "", err
	}
	if result.DID == "" {
		return "", fmt.Errorf("atclient: handle %q resolved to empty DID", handle)
	}
	return result.DID, nil
}

// ClientForDID resolves a DID to its PDS and returns an authenticated client.
// Requires that the DID document contains an AtprotoPersonalDataServer service.
func ClientForDID(ctx context.Context, did string) (*Client, error) {
	doc, err := ResolveDID(ctx, did)
	if err != nil {
		return nil, err
	}
	pds := doc.PDSEndpoint()
	if pds == "" {
		return nil, fmt.Errorf("atclient: no PDS endpoint in DID document for %s", did)
	}
	return NewClient(pds), nil
}
