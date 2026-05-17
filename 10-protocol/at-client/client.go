// Package atclient provides an AT Protocol XRPC client for PDS operations,
// DID resolution, and Firehose event streaming.
package atclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// Client is an authenticated AT Protocol XRPC client bound to a PDS host.
type Client struct {
	host       string
	httpClient *http.Client

	mu         sync.RWMutex
	accessJWT  string
	refreshJWT string
	did        string
	handle     string
}

// NewClient creates an unauthenticated client for the given PDS host (e.g. "https://bsky.social").
func NewClient(host string) *Client {
	return &Client{
		host:       strings.TrimRight(host, "/"),
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// NewClientWithJWT creates a pre-authenticated client.
func NewClientWithJWT(host, did, accessJWT, refreshJWT string) *Client {
	c := NewClient(host)
	c.did = did
	c.accessJWT = accessJWT
	c.refreshJWT = refreshJWT
	return c
}

// DID returns the authenticated DID, empty if unauthenticated.
func (c *Client) DID() string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.did
}

// CreateSession authenticates with identifier (handle or DID) and password.
func (c *Client) CreateSession(ctx context.Context, identifier, password string) error {
	req := map[string]string{"identifier": identifier, "password": password}
	var resp struct {
		AccessJwt  string `json:"accessJwt"`
		RefreshJwt string `json:"refreshJwt"`
		DID        string `json:"did"`
		Handle     string `json:"handle"`
	}
	if err := c.Procedure(ctx, "com.atproto.server.createSession", req, &resp); err != nil {
		return err
	}
	c.mu.Lock()
	c.accessJWT = resp.AccessJwt
	c.refreshJWT = resp.RefreshJwt
	c.did = resp.DID
	c.handle = resp.Handle
	c.mu.Unlock()
	return nil
}

// RefreshSession refreshes the access JWT using the refresh JWT.
func (c *Client) RefreshSession(ctx context.Context) error {
	c.mu.RLock()
	refreshJWT := c.refreshJWT
	c.mu.RUnlock()
	if refreshJWT == "" {
		return fmt.Errorf("atclient: no refresh token")
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.host+"/xrpc/com.atproto.server.refreshSession", nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+refreshJWT)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return c.parseError(resp)
	}
	var result struct {
		AccessJwt  string `json:"accessJwt"`
		RefreshJwt string `json:"refreshJwt"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return err
	}
	c.mu.Lock()
	c.accessJWT = result.AccessJwt
	c.refreshJWT = result.RefreshJwt
	c.mu.Unlock()
	return nil
}

// Query executes an XRPC query (GET /xrpc/{nsid}) with optional params and decodes the response.
func (c *Client) Query(ctx context.Context, nsid string, params map[string]string, out any) error {
	u, err := url.Parse(c.host + "/xrpc/" + nsid)
	if err != nil {
		return err
	}
	if len(params) > 0 {
		q := u.Query()
		for k, v := range params {
			q.Set(k, v)
		}
		u.RawQuery = q.Encode()
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)
	if err != nil {
		return err
	}
	c.setAuth(req)
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return c.parseError(resp)
	}
	if out != nil {
		return json.NewDecoder(resp.Body).Decode(out)
	}
	return nil
}

// Procedure executes an XRPC procedure (POST /xrpc/{nsid}) with a JSON body.
func (c *Client) Procedure(ctx context.Context, nsid string, body any, out any) error {
	var bodyReader io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return err
		}
		bodyReader = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.host+"/xrpc/"+nsid, bodyReader)
	if err != nil {
		return err
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	c.setAuth(req)
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return c.parseError(resp)
	}
	if out != nil {
		return json.NewDecoder(resp.Body).Decode(out)
	}
	return nil
}

func (c *Client) setAuth(req *http.Request) {
	c.mu.RLock()
	jwt := c.accessJWT
	c.mu.RUnlock()
	if jwt != "" {
		req.Header.Set("Authorization", "Bearer "+jwt)
	}
}

// XRPCError is an AT Protocol XRPC error response.
type XRPCError struct {
	StatusCode int
	Code       string `json:"error"`
	Message    string `json:"message"`
}

func (e *XRPCError) Error() string {
	return fmt.Sprintf("atclient: xrpc error %d %s: %s", e.StatusCode, e.Code, e.Message)
}

func (c *Client) parseError(resp *http.Response) error {
	xe := &XRPCError{StatusCode: resp.StatusCode}
	body, err := io.ReadAll(resp.Body)
	if err == nil {
		_ = json.Unmarshal(body, xe)
	}
	return xe
}
