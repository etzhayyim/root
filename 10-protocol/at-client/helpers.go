package atclient

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
)

// buildBlobHTTPRequest builds an HTTP request for blob upload.
func buildBlobHTTPRequest(ctx context.Context, host, mimeType string, data []byte) (*http.Request, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		host+"/xrpc/com.atproto.repo.uploadBlob", bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", mimeType)
	return req, nil
}

// decodeJSON decodes JSON from a reader into v.
func decodeJSON(r io.Reader, v any) error {
	return json.NewDecoder(r).Decode(v)
}
