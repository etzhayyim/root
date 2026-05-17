//go:build !tinygo

package lancedbrest

import (
	"net/http"
	"time"
)

func defaultHTTPTransport() http.RoundTripper {
	return &http.Transport{
		MaxIdleConnsPerHost:   100,
		MaxConnsPerHost:       200,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}
}
