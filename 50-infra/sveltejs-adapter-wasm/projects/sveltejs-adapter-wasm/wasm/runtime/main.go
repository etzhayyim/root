package main

import (
	"embed"
	"encoding/json"
	"io"
	"net/http"
	"path/filepath"
	"strings"

	jsruntime "github.com/etzhayyim/root/50-infra/sveltejs-adapter-wasm/wasm/runtime/gen/etzhayyimcojp/svelte-adapter/js-runtime"
	"go.wasmcloud.dev/component/log/wasilog"
	"go.wasmcloud.dev/component/net/wasihttp"
)

// SvelteKit artifacts (client/, prerendered/, index.js)
//go:embed build
var buildFS embed.FS

// SSR Bundle (index.js)
//go:embed build/index.js
var bundleJS string

type JsRequest struct {
	Method  string            `json:"method"`
	URL     string            `json:"url"`
	Headers map[string]string `json:"headers"`
	Body    string            `json:"body,omitempty"`
}

type JsResponse struct {
	Status  int               `json:"status"`
	Headers map[string]string `json:"headers"`
	Body    string            `json:"body"`
}

var mimeTypes = map[string]string{
	".html": "text/html",
	".js":   "application/javascript",
	".css":  "text/css",
	".png":  "image/png",
	".jpg":  "image/jpeg",
	".gif":  "image/gif",
	".svg":  "image/svg+xml",
	".wasm": "application/wasm",
	".json": "application/json",
	".ico":  "image/x-icon",
}

func getContentType(path string) string {
	ext := filepath.Ext(path)
	if mime, ok := mimeTypes[ext]; ok {
		return mime
	}
	return "application/octet-stream"
}

func tryServeStatic(w http.ResponseWriter, r *http.Request) bool {
	path := r.URL.Path
	if path == "" || path == "/" {
		path = "/index.html"
	}

	// 1. Try serving from client directory (assets like JS/CSS)
	clientPath := "build/client" + path
	if content, err := buildFS.ReadFile(clientPath); err == nil {
		w.Header().Set("Content-Type", getContentType(clientPath))
		w.Write(content)
		return true
	}

	// 2. Try serving from prerendered directory (SSG)
	prerenderedPath := "build/prerendered" + path
	
	// Try the exact path
	if content, err := buildFS.ReadFile(prerenderedPath); err == nil {
		w.Header().Set("Content-Type", "text/html")
		w.Write(content)
		return true
	}

	// Try with .html extension (SvelteKit default for many routes)
	if content, err := buildFS.ReadFile(prerenderedPath + ".html"); err == nil {
		w.Header().Set("Content-Type", "text/html")
		w.Write(content)
		return true
	}

	// If it's a directory (or looks like one), look for index.html
	if !strings.HasSuffix(prerenderedPath, ".html") {
		indexPath := prerenderedPath
		if !strings.HasSuffix(indexPath, "/") {
			indexPath += "/"
		}
		indexPath += "index.html"
		if content, err := buildFS.ReadFile(indexPath); err == nil {
			w.Header().Set("Content-Type", "text/html")
			w.Write(content)
			return true
		}
	}

	return false
}

func init() {
	logger := wasilog.ContextLogger("svelte-performer")

	wasihttp.HandleFunc(func(w http.ResponseWriter, r *http.Request) {
		logger.Info("Incoming request", "method", r.Method, "path", r.URL.Path)

		// Check for static files (Assets, SSG)
		if r.Method == "GET" && tryServeStatic(w, r) {
			logger.Info("Static asset served", "path", r.URL.Path)
			return
		}

		// Fallback: SvelteKit SSR (SSR)
		logger.Info("Falling back to SSR", "path", r.URL.Path)
		
		body, _ := io.ReadAll(r.Body)
		jsReq := JsRequest{
			Method:  r.Method,
			URL:     r.URL.String(),
			Headers: make(map[string]string),
			Body:    string(body),
		}
		for k, v := range r.Header {
			jsReq.Headers[k] = v[0]
		}
		reqJson, _ := json.Marshal(jsReq)

		// Call the JS engine (QuickJS/Boa) via WIT import to execute SSR
		logger.Info("Calling js-runtime.evaluate", "bundleSize", len(bundleJS), "request", string(reqJson))
		resultJSON := jsruntime.Evaluate(bundleJS, string(reqJson))

		var jsResp JsResponse
		if err := json.Unmarshal([]byte(resultJSON), &jsResp); err != nil {
			logger.Error("Failed to parse JS response", "error", err.Error(), "raw", resultJSON)
			w.Header().Set("Content-Type", "text/html")
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("<!DOCTYPE html><html><body><h1>SSR Error</h1><pre>Failed to parse JS engine response</pre></body></html>"))
			return
		}

		// Write response headers from JS engine
		for k, v := range jsResp.Headers {
			w.Header().Set(k, v)
		}
		w.Header().Set("X-Powered-By", "wasmCloud-Svelte-Performer")

		status := jsResp.Status
		if status == 0 {
			status = http.StatusOK
		}
		w.WriteHeader(status)
		w.Write([]byte(jsResp.Body))
	})
}

func main() {}
