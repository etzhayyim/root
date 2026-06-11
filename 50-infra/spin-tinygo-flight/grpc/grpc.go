package grpc

import (
	"context"
	"errors"
	"time"
)

var ErrUnsupported = errors.New("spin grpc package supports operations only under tinygo")

// Request describes a single unary gRPC call using protobuf wire bytes.
type Request struct {
	Endpoint  string
	Procedure string
	Message   []byte
	Messages  [][]byte
	Headers   map[string]string
	Timeout   time.Duration
}

// Response contains the decoded unary payload and response metadata.
type Response struct {
	Message     []byte
	Headers     map[string][]string
	Trailers    map[string][]string
	HTTPStatus  uint16
	GRPCStatus  string
	GRPCMessage string
}

// ServerStream reads protobuf messages from a server-streaming gRPC response.
type ServerStream interface {
	Response() *Response
	Next() ([]byte, error)
	Close() error
}

// MarshalFunc encodes a request value into protobuf wire bytes.
type MarshalFunc[T any] func(T) ([]byte, error)

// UnmarshalFunc decodes protobuf wire bytes into a response value.
type UnmarshalFunc[T any] func([]byte) (T, error)

// InvokeUnaryTyped executes one unary gRPC call and decodes the response using
// caller-provided protobuf codecs.
func InvokeUnaryTyped[TReq, TResp any](
	ctx context.Context,
	req Request,
	message TReq,
	marshal MarshalFunc[TReq],
	unmarshal UnmarshalFunc[TResp],
) (TResp, *Response, error) {
	var zero TResp
	if marshal == nil {
		return zero, nil, errors.New("grpc marshal func is required")
	}
	if unmarshal == nil {
		return zero, nil, errors.New("grpc unmarshal func is required")
	}

	payload, err := marshal(message)
	if err != nil {
		return zero, nil, err
	}
	req.Message = payload

	resp, err := InvokeUnary(ctx, req)
	if err != nil {
		return zero, nil, err
	}
	decoded, err := unmarshal(resp.Message)
	if err != nil {
		return zero, resp, err
	}
	return decoded, resp, nil
}

// InvokeUnary executes one protobuf unary gRPC call.
func InvokeUnary(ctx context.Context, req Request) (*Response, error) {
	return invokeUnary(ctx, req)
}

// OpenServerStream opens a server-streaming gRPC call.
func OpenServerStream(ctx context.Context, req Request) (ServerStream, error) {
	return openServerStream(ctx, req)
}
