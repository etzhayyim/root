package flightsql

import (
	"context"
	"errors"
	"io"
	"time"

	flight "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc/flight"
)

// Options configures a high-level Flight SQL query.
type Options struct {
	Endpoint string
	Username string
	Password string
	Headers  map[string]string
	Timeout  time.Duration
}

// Query executes a Flight SQL statement and materializes all rows.
func Query(ctx context.Context, sql string, opts Options) ([]map[string]any, error) {
	batches, err := QueryBatches(ctx, sql, opts)
	if err != nil {
		return nil, err
	}
	var rows []map[string]any
	for _, batch := range batches {
		rows = append(rows, batch.Rows()...)
	}
	return rows, nil
}

// QueryBatches executes a Flight SQL statement and returns decoded record batches.
func QueryBatches(ctx context.Context, sql string, opts Options) ([]*flight.RecordBatch, error) {
	client, err := NewClient(ctx, opts)
	if err != nil {
		return nil, err
	}
	return client.QueryBatches(ctx, sql)
}

// Client is a high-level Flight SQL wrapper over the lower-level Flight client.
type Client struct {
	flight *flight.Client
}

// PreparedStatement is a high-level wrapper around a Flight SQL prepared handle.
type PreparedStatement struct {
	client *Client
	handle []byte
}

// NewClient builds a client and performs basic-auth handshake if configured.
func NewClient(ctx context.Context, opts Options) (*Client, error) {
	if opts.Endpoint == "" {
		return nil, errors.New("flightsql endpoint is required")
	}
	fc := flight.NewClient(opts.Endpoint)
	fc.Headers = cloneHeaders(opts.Headers)
	fc.Timeout = opts.Timeout
	if opts.Username != "" || opts.Password != "" {
		if _, _, err := fc.AuthenticateBasicToken(ctx, opts.Username, opts.Password); err != nil {
			return nil, err
		}
	}
	return &Client{flight: fc}, nil
}

// Query executes a statement and materializes all rows.
func (c *Client) Query(ctx context.Context, sql string) ([]map[string]any, error) {
	batches, err := c.QueryBatches(ctx, sql)
	if err != nil {
		return nil, err
	}
	var rows []map[string]any
	for _, batch := range batches {
		rows = append(rows, batch.Rows()...)
	}
	return rows, nil
}

// QueryBatches executes a statement and returns all decoded record batches.
func (c *Client) QueryBatches(ctx context.Context, sql string) ([]*flight.RecordBatch, error) {
	if c == nil || c.flight == nil {
		return nil, errors.New("flightsql client is nil")
	}
	info, _, err := c.flight.ExecuteQuery(ctx, sql)
	if err != nil {
		return nil, err
	}
	if len(info.Endpoint) == 0 {
		return nil, errors.New("flight info returned no endpoints")
	}
	stream, err := c.flight.DoGet(ctx, info.Endpoint[0].Ticket)
	if err != nil {
		return nil, err
	}
	defer stream.Close()

	batches, err := stream.DrainBatches()
	if err != nil && !errors.Is(err, io.EOF) {
		return nil, err
	}
	return batches, nil
}

// Prepare creates a server-side prepared statement for the given SQL query.
func (c *Client) Prepare(ctx context.Context, sql string) (*PreparedStatement, error) {
	if c == nil || c.flight == nil {
		return nil, errors.New("flightsql client is nil")
	}
	prepared, err := c.flight.PrepareQuery(ctx, sql)
	if err != nil {
		return nil, err
	}
	if len(prepared.PreparedStatementHandle) == 0 {
		return nil, errors.New("prepared statement returned empty handle")
	}
	return &PreparedStatement{
		client: c,
		handle: append([]byte(nil), prepared.PreparedStatementHandle...),
	}, nil
}

// Query executes the prepared statement and materializes all rows.
func (p *PreparedStatement) Query(ctx context.Context) ([]map[string]any, error) {
	batches, err := p.QueryBatches(ctx)
	if err != nil {
		return nil, err
	}
	var rows []map[string]any
	for _, batch := range batches {
		rows = append(rows, batch.Rows()...)
	}
	return rows, nil
}

// QueryBatches executes the prepared statement and returns decoded batches.
func (p *PreparedStatement) QueryBatches(ctx context.Context) ([]*flight.RecordBatch, error) {
	if p == nil || p.client == nil || p.client.flight == nil {
		return nil, errors.New("prepared statement is nil")
	}
	info, _, err := p.client.flight.ExecutePreparedQuery(ctx, p.handle)
	if err != nil {
		return nil, err
	}
	if len(info.Endpoint) == 0 {
		return nil, errors.New("prepared statement returned no endpoints")
	}
	stream, err := p.client.flight.DoGet(ctx, info.Endpoint[0].Ticket)
	if err != nil {
		return nil, err
	}
	defer stream.Close()
	batches, err := stream.DrainBatches()
	if err != nil && !errors.Is(err, io.EOF) {
		return nil, err
	}
	return batches, nil
}

// Close releases the server-side prepared statement handle.
func (p *PreparedStatement) Close(ctx context.Context) error {
	if p == nil || p.client == nil || p.client.flight == nil {
		return errors.New("prepared statement is nil")
	}
	return p.client.flight.ClosePreparedStatement(ctx, p.handle)
}

func cloneHeaders(in map[string]string) map[string]string {
	if len(in) == 0 {
		return nil
	}
	out := make(map[string]string, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}
