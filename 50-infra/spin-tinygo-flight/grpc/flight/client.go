package flight

import (
	"context"
	"encoding/base64"
	"errors"
	"io"
	"strings"
	"time"

	grpc "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc"
)

const (
	ServiceName            = "arrow.flight.protocol.FlightService"
	HandshakeProcedure     = "/" + ServiceName + "/Handshake"
	GetFlightInfoProcedure = "/" + ServiceName + "/GetFlightInfo"
	DoActionProcedure      = "/" + ServiceName + "/DoAction"
	DoGetProcedure         = "/" + ServiceName + "/DoGet"
	DoPutProcedure         = "/" + ServiceName + "/DoPut"
)

// Client is a minimal Arrow Flight client backed by the TinyGo gRPC transport.
type Client struct {
	Endpoint  string
	Headers   map[string]string
	Timeout   time.Duration
	BearerTok string
}

type DescriptorType uint64

const (
	DescriptorUnknown DescriptorType = 0
	DescriptorPath    DescriptorType = 1
	DescriptorCmd     DescriptorType = 2
)

// HandshakeRequest is the minimal protobuf shape for Flight handshake.
type HandshakeRequest struct {
	ProtocolVersion uint64
	Payload         []byte
}

// HandshakeResponse is the minimal protobuf shape for Flight handshake.
type HandshakeResponse struct {
	ProtocolVersion uint64
	Payload         []byte
}

type FlightDescriptor struct {
	Type DescriptorType
	Cmd  []byte
	Path []string
}

type FlightInfo struct {
	Schema           []byte
	FlightDescriptor *FlightDescriptor
	Endpoint         []FlightEndpoint
	TotalRecords     int64
	TotalBytes       int64
	Ordered          bool
	AppMetadata      []byte
}

type FlightEndpoint struct {
	Ticket      Ticket
	Location    []Location
	AppMetadata []byte
}

type Location struct {
	URI string
}

type Ticket struct {
	Ticket []byte
}

type Action struct {
	Type string
	Body []byte
}

type ActionResult struct {
	Body []byte
}

type CreatePreparedStatementResult struct {
	PreparedStatementHandle []byte
	DatasetSchema           []byte
	ParameterSchema         []byte
}

type PutResult struct {
	AppMetadata []byte
}

type FlightData struct {
	FlightDescriptor *FlightDescriptor
	DataHeader       []byte
	AppMetadata      []byte
	DataBody         []byte
}

// NewClient returns a Flight client for the given endpoint.
func NewClient(endpoint string) *Client {
	return &Client{Endpoint: endpoint}
}

// Handshake performs a single-message handshake exchange.
func (c *Client) Handshake(ctx context.Context, req HandshakeRequest) (*HandshakeResponse, *grpc.Response, error) {
	resp, meta, err := grpc.InvokeUnaryTyped(
		ctx,
		c.request(HandshakeProcedure),
		req,
		marshalHandshakeRequest,
		unmarshalHandshakeResponse,
	)
	if err != nil {
		return nil, meta, err
	}
	return &resp, meta, nil
}

// AuthenticateBasicToken performs Flight's basic-auth handshake and returns the
// authorization token echoed by the server.
func (c *Client) AuthenticateBasicToken(ctx context.Context, username, password string) (string, *grpc.Response, error) {
	req := c.request(HandshakeProcedure)
	if req.Headers == nil {
		req.Headers = make(map[string]string, 1)
	}
	req.Headers["authorization"] = "Basic " + base64.RawStdEncoding.EncodeToString([]byte(username+":"+password))
	req.Message = nil

	resp, err := grpc.InvokeUnary(ctx, req)
	if err != nil {
		return "", resp, err
	}
	token := firstHeader(resp.Trailers, "authorization")
	if token == "" {
		token = firstHeader(resp.Headers, "authorization")
	}
	if token == "" {
		return "", resp, errors.New("flight: no authorization header on the response")
	}
	c.BearerTok = token
	return token, resp, nil
}

func (c *Client) GetFlightInfo(ctx context.Context, desc FlightDescriptor) (*FlightInfo, *grpc.Response, error) {
	resp, meta, err := grpc.InvokeUnaryTyped(
		ctx,
		c.request(GetFlightInfoProcedure),
		desc,
		marshalFlightDescriptor,
		unmarshalFlightInfo,
	)
	if err != nil {
		return nil, meta, err
	}
	return &resp, meta, nil
}

func (c *Client) ExecuteQuery(ctx context.Context, query string) (*FlightInfo, *grpc.Response, error) {
	cmd, err := marshalCommandStatementQuery(query)
	if err != nil {
		return nil, nil, err
	}
	return c.GetFlightInfo(ctx, FlightDescriptor{Type: DescriptorCmd, Cmd: marshalAny(commandStatementQueryTypeURL, cmd)})
}

func (c *Client) PrepareQuery(ctx context.Context, query string) (*CreatePreparedStatementResult, error) {
	req, err := marshalCreatePreparedStatementRequest(query)
	if err != nil {
		return nil, err
	}
	stream, err := c.DoAction(ctx, Action{
		Type: createPreparedStatementActionType,
		Body: req,
	})
	if err != nil {
		return nil, err
	}
	defer stream.Close()
	result, err := stream.Next()
	if err != nil {
		return nil, err
	}
	decoded, err := unmarshalCreatePreparedStatementResult(result.Body)
	if err != nil {
		return nil, err
	}
	return &decoded, nil
}

func (c *Client) ExecutePreparedQuery(ctx context.Context, handle []byte) (*FlightInfo, *grpc.Response, error) {
	cmd, err := marshalCommandPreparedStatementQuery(handle)
	if err != nil {
		return nil, nil, err
	}
	return c.GetFlightInfo(ctx, FlightDescriptor{Type: DescriptorCmd, Cmd: marshalAny(commandPreparedStatementQueryTypeURL, cmd)})
}

func (c *Client) ClosePreparedStatement(ctx context.Context, handle []byte) error {
	req, err := marshalClosePreparedStatementRequest(handle)
	if err != nil {
		return err
	}
	stream, err := c.DoAction(ctx, Action{
		Type: closePreparedStatementActionType,
		Body: req,
	})
	if err != nil {
		return err
	}
	defer stream.Close()
	_, err = stream.Next()
	if err != nil && !errors.Is(err, io.EOF) {
		return err
	}
	return nil
}

func (c *Client) DoGet(ctx context.Context, ticket Ticket) (*DataStream, error) {
	body, err := marshalTicket(ticket)
	if err != nil {
		return nil, err
	}
	req := c.request(DoGetProcedure)
	req.Message = body
	stream, err := grpc.OpenServerStream(ctx, req)
	if err != nil {
		return nil, err
	}
	return &DataStream{stream: stream}, nil
}

func (c *Client) DoPut(ctx context.Context, messages []FlightData) (*PutResultStream, error) {
	encoded := make([][]byte, 0, len(messages))
	for _, msg := range messages {
		raw, err := marshalFlightData(msg)
		if err != nil {
			return nil, err
		}
		encoded = append(encoded, raw)
	}
	req := c.request(DoPutProcedure)
	req.Messages = encoded
	stream, err := grpc.OpenServerStream(ctx, req)
	if err != nil {
		return nil, err
	}
	return &PutResultStream{stream: stream}, nil
}

func (c *Client) DoAction(ctx context.Context, action Action) (*ActionStream, error) {
	body, err := marshalAction(action)
	if err != nil {
		return nil, err
	}
	req := c.request(DoActionProcedure)
	req.Message = body
	stream, err := grpc.OpenServerStream(ctx, req)
	if err != nil {
		return nil, err
	}
	return &ActionStream{stream: stream}, nil
}

type DataStream struct {
	stream grpc.ServerStream
	schema *Schema
	dicts  map[int64]Column
}

type ActionStream struct {
	stream grpc.ServerStream
}

type PutResultStream struct {
	stream grpc.ServerStream
}

func (s *ActionStream) Response() *grpc.Response {
	return s.stream.Response()
}

func (s *ActionStream) Next() (*ActionResult, error) {
	raw, err := s.stream.Next()
	if err != nil {
		return nil, err
	}
	msg, err := unmarshalActionResult(raw)
	if err != nil {
		return nil, err
	}
	return &msg, nil
}

func (s *ActionStream) Close() error {
	return s.stream.Close()
}

func (s *PutResultStream) Response() *grpc.Response {
	return s.stream.Response()
}

func (s *PutResultStream) Next() (*PutResult, error) {
	raw, err := s.stream.Next()
	if err != nil {
		return nil, err
	}
	msg, err := unmarshalPutResult(raw)
	if err != nil {
		return nil, err
	}
	return &msg, nil
}

func (s *PutResultStream) Close() error {
	return s.stream.Close()
}

func (s *DataStream) Response() *grpc.Response {
	return s.stream.Response()
}

func (s *DataStream) Next() (*FlightData, error) {
	raw, err := s.stream.Next()
	if err != nil {
		return nil, err
	}
	msg, err := unmarshalFlightData(raw)
	if err != nil {
		return nil, err
	}
	return &msg, nil
}

func (s *DataStream) Close() error {
	return s.stream.Close()
}

func (c *Client) request(procedure string) grpc.Request {
	headers := make(map[string]string, len(c.Headers)+1)
	for k, v := range c.Headers {
		headers[k] = v
	}
	if strings.TrimSpace(c.BearerTok) != "" {
		headers["authorization"] = c.BearerTok
	}
	return grpc.Request{
		Endpoint:  c.Endpoint,
		Procedure: procedure,
		Headers:   headers,
		Timeout:   c.Timeout,
	}
}

func firstHeader(headers map[string][]string, key string) string {
	values := headers[strings.ToLower(key)]
	if len(values) == 0 {
		return ""
	}
	return values[0]
}
