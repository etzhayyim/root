package main

import (
	"encoding/json"
	"os"
	"testing"
)

func TestBuildMetricsBiWritePayloadUsesKagamiSQLShape(t *testing.T) {
	payload, err := buildMetricsBiWritePayload(&biMetrics{
		Timestamp:     "2026-04-15T10:00:00Z",
		StatusBuckets: map[string]int{"2xx": 10},
	}, "metrics:bi:test", "bi-test")
	if err != nil {
		t.Fatalf("buildMetricsBiWritePayload: %v", err)
	}

	var decoded map[string]any
	if err := json.Unmarshal(payload, &decoded); err != nil {
		t.Fatalf("unmarshal payload: %v", err)
	}

	if _, ok := decoded["statement"]; !ok {
		t.Fatal("payload missing statement")
	}
	if _, ok := decoded["sql"]; ok {
		t.Fatal("payload should not use legacy sql key")
	}

	params, ok := decoded["parameters"].(map[string]any)
	if !ok {
		t.Fatalf("parameters type: got %T", decoded["parameters"])
	}
	if params["vertex_id"] != "metrics:bi:test" {
		t.Fatalf("vertex_id: got %v", params["vertex_id"])
	}
	if params["rkey"] != "bi-test" {
		t.Fatalf("rkey: got %v", params["rkey"])
	}
	if _, ok := params["val"].(string); !ok {
		t.Fatalf("val type: got %T", params["val"])
	}
}

func TestDefaultMetricsBiWriteEnabled(t *testing.T) {
	t.Setenv("HOME", t.TempDir())
	t.Setenv("GFTD_TOKEN", "")
	t.Setenv("DATABASE_URL", "")
	t.Setenv("GFTD_DATABASE_URL", "")
	t.Setenv("CLOUDFLARE_API_TOKEN", "")
	t.Setenv("CF_API_TOKEN", "")
	if got := defaultMetricsBiWriteEnabled(); got {
		t.Fatal("defaultMetricsBiWriteEnabled: got true without write credentials")
	}

	t.Setenv("GFTD_TOKEN", "sk_live_example")
	if got := defaultMetricsBiWriteEnabled(); !got {
		t.Fatal("defaultMetricsBiWriteEnabled: got false with GFTD_TOKEN")
	}

	_ = os.Unsetenv("GFTD_TOKEN")
	t.Setenv("DATABASE_URL", "postgres://example")
	if got := defaultMetricsBiWriteEnabled(); !got {
		t.Fatal("defaultMetricsBiWriteEnabled: got false with DATABASE_URL")
	}
}
