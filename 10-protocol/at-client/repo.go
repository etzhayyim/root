package atclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

// CreateRecordResult is the response from com.atproto.repo.createRecord.
type CreateRecordResult struct {
	URI string `json:"uri"`
	CID string `json:"cid"`
}

// PutRecordResult is the response from com.atproto.repo.putRecord.
type PutRecordResult struct {
	URI string `json:"uri"`
	CID string `json:"cid"`
}

// GetRecordResult is the response from com.atproto.repo.getRecord.
type GetRecordResult struct {
	URI   string         `json:"uri"`
	CID   string         `json:"cid"`
	Value map[string]any `json:"value"`
}

// ListRecordsResult is the response from com.atproto.repo.listRecords.
type ListRecordsResult struct {
	Cursor  string       `json:"cursor"`
	Records []RecordEntry `json:"records"`
}

// RecordEntry is a single record in a listRecords response.
type RecordEntry struct {
	URI   string         `json:"uri"`
	CID   string         `json:"cid"`
	Value map[string]any `json:"value"`
}

// CreateRecord creates a new record in the given collection.
// If rkey is empty, the PDS assigns one.
func (c *Client) CreateRecord(ctx context.Context, repo, collection, rkey string, record any) (*CreateRecordResult, error) {
	body := map[string]any{
		"repo":       repo,
		"collection": collection,
		"record":     record,
	}
	if rkey != "" {
		body["rkey"] = rkey
	}
	var result CreateRecordResult
	if err := c.Procedure(ctx, "com.atproto.repo.createRecord", body, &result); err != nil {
		return nil, err
	}
	return &result, nil
}

// PutRecord creates or replaces a record at the given rkey.
func (c *Client) PutRecord(ctx context.Context, repo, collection, rkey string, record any) (*PutRecordResult, error) {
	body := map[string]any{
		"repo":       repo,
		"collection": collection,
		"rkey":       rkey,
		"record":     record,
	}
	var result PutRecordResult
	if err := c.Procedure(ctx, "com.atproto.repo.putRecord", body, &result); err != nil {
		return nil, err
	}
	return &result, nil
}

// GetRecord fetches a record by repo, collection, and rkey.
func (c *Client) GetRecord(ctx context.Context, repo, collection, rkey string) (*GetRecordResult, error) {
	var result GetRecordResult
	err := c.Query(ctx, "com.atproto.repo.getRecord", map[string]string{
		"repo":       repo,
		"collection": collection,
		"rkey":       rkey,
	}, &result)
	if err != nil {
		return nil, err
	}
	return &result, nil
}

// DeleteRecord deletes a record.
func (c *Client) DeleteRecord(ctx context.Context, repo, collection, rkey string) error {
	return c.Procedure(ctx, "com.atproto.repo.deleteRecord", map[string]any{
		"repo":       repo,
		"collection": collection,
		"rkey":       rkey,
	}, nil)
}

// ListRecords lists records in a collection with optional cursor-based pagination.
func (c *Client) ListRecords(ctx context.Context, repo, collection string, limit int, cursor string) (*ListRecordsResult, error) {
	params := map[string]string{
		"repo":       repo,
		"collection": collection,
	}
	if limit > 0 {
		params["limit"] = fmt.Sprintf("%d", limit)
	}
	if cursor != "" {
		params["cursor"] = cursor
	}
	var result ListRecordsResult
	if err := c.Query(ctx, "com.atproto.repo.listRecords", params, &result); err != nil {
		return nil, err
	}
	return &result, nil
}

// UploadBlob uploads a binary blob to the PDS. Returns the blob reference CID map.
func (c *Client) UploadBlob(ctx context.Context, mimeType string, data []byte) (map[string]any, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.host+"/xrpc/com.atproto.repo.uploadBlob", bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", mimeType)
	c.setAuth(req)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, c.parseError(resp)
	}
	var result struct {
		Blob map[string]any `json:"blob"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Blob, nil
}
