package flightsql

import (
	"context"
	"testing"
	"time"
)

func TestNewClientRequiresEndpoint(t *testing.T) {
	if _, err := NewClient(context.Background(), Options{}); err == nil {
		t.Fatal("expected endpoint error")
	}
}

func TestCloneHeaders(t *testing.T) {
	opts := Options{
		Endpoint: "https://example.invalid",
		Headers:  map[string]string{"x-test": "1"},
		Timeout:  5 * time.Second,
	}
	client, err := NewClient(context.Background(), opts)
	if err != nil {
		t.Fatalf("new client: %v", err)
	}
	opts.Headers["x-test"] = "2"
	if client.flight.Headers["x-test"] != "1" {
		t.Fatalf("headers mutated: %#v", client.flight.Headers)
	}
	if client.flight.Timeout != 5*time.Second {
		t.Fatalf("timeout=%s", client.flight.Timeout)
	}
}

func TestPreparedStatementGuards(t *testing.T) {
	var stmt *PreparedStatement
	if err := stmt.Close(context.Background()); err == nil {
		t.Fatal("expected nil prepared statement close error")
	}
	if _, err := stmt.Query(context.Background()); err == nil {
		t.Fatal("expected nil prepared statement query error")
	}
}
