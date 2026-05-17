//go:build tinygo

package lancedbrest

import "net/http"

func defaultHTTPTransport() http.RoundTripper {
	return &http.Transport{}
}
