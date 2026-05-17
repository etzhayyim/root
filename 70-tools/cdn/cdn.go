package cdn

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"sort"
	"strings"
	"time"
)

// Config holds S3-compatible storage credentials and endpoint info.
type Config struct {
	Endpoint  string
	Bucket    string
	Region    string
	AccessKey string
	SecretKey string
}

// HTTPSender is a function type for sending HTTP requests.
// It can be overridden for TinyGo WASI environments.
type HTTPSender func(*http.Request) (*http.Response, error)

// defaultSender is the package-level HTTP sender, set by transport.go init().
var defaultSender HTTPSender

// SetHTTPSender sets the package-level default HTTP sender.
// Call this in TinyGo WASI builds to inject a custom transport.
func SetHTTPSender(fn HTTPSender) {
	defaultSender = fn
}

// Client is a TinyGo-compatible S3/CDN client using SigV4 signing.
type Client struct {
	cfg  Config
	send HTTPSender
}

// New creates a Client using the package-level defaultSender.
func New(cfg Config) *Client {
	return &Client{cfg: cfg, send: defaultSender}
}

// NewWithSender creates a Client with an explicit HTTPSender.
func NewWithSender(cfg Config, send HTTPSender) *Client {
	return &Client{cfg: cfg, send: send}
}

// URL returns the public URL for a given object key.
func (c *Client) URL(key string) string {
	return fmt.Sprintf("%s/%s/%s", c.cfg.Endpoint, c.cfg.Bucket, key)
}

// Put uploads data to the given key with the specified content type.
func (c *Client) Put(key, contentType string, data []byte) error {
	if c.cfg.AccessKey == "" || c.cfg.SecretKey == "" || c.cfg.Bucket == "" {
		return fmt.Errorf("cdn: credentials not configured")
	}
	req, err := buildRequest(c.cfg, "PUT", key, contentType, data)
	if err != nil {
		return fmt.Errorf("cdn put sign: %w", err)
	}
	resp, err := c.send(req)
	if err != nil {
		return fmt.Errorf("cdn put: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		errBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("cdn put status %d: %s", resp.StatusCode, string(errBody))
	}
	return nil
}

// Get downloads an object and returns its data and content type.
func (c *Client) Get(key string) (data []byte, contentType string, err error) {
	if c.cfg.AccessKey == "" || c.cfg.SecretKey == "" || c.cfg.Bucket == "" {
		return nil, "", fmt.Errorf("cdn: credentials not configured")
	}
	req, err := buildRequest(c.cfg, "GET", key, "", nil)
	if err != nil {
		return nil, "", fmt.Errorf("cdn get sign: %w", err)
	}
	resp, err := c.send(req)
	if err != nil {
		return nil, "", fmt.Errorf("cdn get: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode == 404 {
		return nil, "", fmt.Errorf("cdn get: not found")
	}
	if resp.StatusCode >= 300 {
		return nil, "", fmt.Errorf("cdn get status %d", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, "", fmt.Errorf("cdn get read: %w", err)
	}
	ct := resp.Header.Get("Content-Type")
	return body, ct, nil
}

// GetRange downloads a byte range of an object.
func (c *Client) GetRange(key string, offset, length int64) ([]byte, error) {
	if c.cfg.AccessKey == "" || c.cfg.SecretKey == "" || c.cfg.Bucket == "" {
		return nil, fmt.Errorf("cdn: credentials not configured")
	}
	req, err := buildRequest(c.cfg, "GET", key, "", nil)
	if err != nil {
		return nil, fmt.Errorf("cdn getrange sign: %w", err)
	}
	req.Header.Set("Range", fmt.Sprintf("bytes=%d-%d", offset, offset+length-1))
	resp, err := c.send(req)
	if err != nil {
		return nil, fmt.Errorf("cdn getrange: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode == 404 {
		return nil, fmt.Errorf("cdn getrange: not found")
	}
	if resp.StatusCode != 206 && resp.StatusCode >= 300 {
		return nil, fmt.Errorf("cdn getrange status %d", resp.StatusCode)
	}
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("cdn getrange read: %w", err)
	}
	return data, nil
}

// Delete removes an object at the given key.
func (c *Client) Delete(key string) error {
	if c.cfg.AccessKey == "" || c.cfg.SecretKey == "" || c.cfg.Bucket == "" {
		return fmt.Errorf("cdn: credentials not configured")
	}
	req, err := buildRequest(c.cfg, "DELETE", key, "", nil)
	if err != nil {
		return fmt.Errorf("cdn delete sign: %w", err)
	}
	resp, err := c.send(req)
	if err != nil {
		return fmt.Errorf("cdn delete: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 && resp.StatusCode != 404 {
		errBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("cdn delete status %d: %s", resp.StatusCode, string(errBody))
	}
	return nil
}

// --- SigV4 signing helpers ---

// sigHMAC computes HMAC-SHA256 using sha256.Sum256 directly,
// avoiding crypto/hmac's hash.Hash interface for TinyGo wasip1 compatibility.
func sigHMAC(key, data []byte) []byte {
	// Shorten key if longer than SHA-256 block size (64 bytes).
	if len(key) > 64 {
		h := sha256.Sum256(key)
		k := make([]byte, 32)
		copy(k, h[:])
		key = k
	}
	ipad := make([]byte, 64+len(data))
	opad := make([]byte, 64+32)
	for i := 0; i < 64; i++ {
		k := byte(0)
		if i < len(key) {
			k = key[i]
		}
		ipad[i] = k ^ 0x36
		opad[i] = k ^ 0x5c
	}
	copy(ipad[64:], data)
	inner := sha256.Sum256(ipad)
	copy(opad[64:], inner[:])
	outer := sha256.Sum256(opad)
	result := make([]byte, 32)
	copy(result, outer[:])
	return result
}

// sigSHA256Hex returns the hex-encoded SHA-256 digest of data.
func sigSHA256Hex(data []byte) string {
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}

// buildRequest constructs and signs an S3 SigV4 HTTP request.
func buildRequest(cfg Config, method, objectKey, contentType string, body []byte) (*http.Request, error) {
	now := time.Now().UTC()
	dateStamp := now.Format("20060102")
	amzDate := now.Format("20060102T150405Z")

	urlStr := fmt.Sprintf("%s/%s/%s", cfg.Endpoint, cfg.Bucket, objectKey)
	host := strings.TrimPrefix(cfg.Endpoint, "https://")
	host = strings.TrimPrefix(host, "http://")

	if body == nil {
		body = []byte{}
	}
	bodyHash := sigSHA256Hex(body)

	hdrMap := map[string]string{
		"host":                 host,
		"x-amz-content-sha256": bodyHash,
		"x-amz-date":           amzDate,
	}
	if contentType != "" {
		hdrMap["content-type"] = contentType
	}

	keys := make([]string, 0, len(hdrMap))
	for k := range hdrMap {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var canonHdrs, signedHdrs strings.Builder
	for i, k := range keys {
		canonHdrs.WriteString(k)
		canonHdrs.WriteString(":")
		canonHdrs.WriteString(hdrMap[k])
		canonHdrs.WriteString("\n")
		if i > 0 {
			signedHdrs.WriteString(";")
		}
		signedHdrs.WriteString(k)
	}

	canonReq := strings.Join([]string{
		method,
		"/" + cfg.Bucket + "/" + objectKey,
		"",
		canonHdrs.String(),
		signedHdrs.String(),
		bodyHash,
	}, "\n")

	credScope := fmt.Sprintf("%s/%s/s3/aws4_request", dateStamp, cfg.Region)
	strToSign := strings.Join([]string{
		"AWS4-HMAC-SHA256",
		amzDate,
		credScope,
		sigSHA256Hex([]byte(canonReq)),
	}, "\n")

	sigKey := sigHMAC(
		sigHMAC(
			sigHMAC(
				sigHMAC([]byte("AWS4"+cfg.SecretKey), []byte(dateStamp)),
				[]byte(cfg.Region),
			),
			[]byte("s3"),
		),
		[]byte("aws4_request"),
	)
	sig := hex.EncodeToString(sigHMAC(sigKey, []byte(strToSign)))
	auth := fmt.Sprintf("AWS4-HMAC-SHA256 Credential=%s/%s,SignedHeaders=%s,Signature=%s",
		cfg.AccessKey, credScope, signedHdrs.String(), sig)

	req, err := http.NewRequest(method, urlStr, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Amz-Date", amzDate)
	req.Header.Set("X-Amz-Content-SHA256", bodyHash)
	req.Header.Set("Authorization", auth)
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	return req, nil
}
