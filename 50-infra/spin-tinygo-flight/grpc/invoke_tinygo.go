//go:build tinygo

package grpc

import (
	"context"
	"encoding/base64"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"net/url"
	"strconv"
	"strings"
	"time"

	"go.bytecodealliance.org/cm"

	outgoinghandler "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc/internal/gen/wasi/http/outgoing-handler"
	types "github.com/etzhayyim/root/50-infra/spin-tinygo-flight/grpc/internal/gen/wasi/http/types"
)

const (
	defaultReadChunkSize = 64 * 1024
	headerContentType    = "content-type"
	headerTE             = "te"
	headerGrpcStatus     = "grpc-status"
	headerGrpcMessage    = "grpc-message"
	headerGrpcTimeout    = "grpc-timeout"
)

func invokeUnary(ctx context.Context, req Request) (*Response, error) {
	if req.Endpoint == "" {
		return nil, errors.New("grpc endpoint is required")
	}
	if req.Procedure == "" || !strings.HasPrefix(req.Procedure, "/") {
		return nil, errors.New("grpc procedure must start with '/'")
	}

	parsed, err := url.Parse(req.Endpoint)
	if err != nil {
		return nil, fmt.Errorf("parse endpoint: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return nil, fmt.Errorf("unsupported endpoint scheme: %s", parsed.Scheme)
	}
	if parsed.Host == "" {
		return nil, errors.New("grpc endpoint host is required")
	}

	headers, err := newFields(baseHeaders(req, ctx))
	if err != nil {
		return nil, err
	}

	outReq := types.NewOutgoingRequest(headers)
	defer outReq.ResourceDrop()

	if outReq.SetMethod(types.MethodPost()) == cm.ResultErr {
		return nil, errors.New("set grpc method")
	}
	if outReq.SetScheme(cm.Some(schemeForURL(parsed))) == cm.ResultErr {
		return nil, errors.New("set grpc scheme")
	}
	if outReq.SetAuthority(cm.Some(parsed.Host)) == cm.ResultErr {
		return nil, errors.New("set grpc authority")
	}
	if outReq.SetPathWithQuery(cm.Some(req.Procedure)) == cm.ResultErr {
		return nil, errors.New("set grpc procedure")
	}

	if err := writeRequestBody(outReq, req); err != nil {
		return nil, err
	}

	options := requestOptions(req, ctx)
	callResult := outgoinghandler.Handle(outReq, options)
	if callResult.IsErr() {
		return nil, fmt.Errorf("outbound grpc request: %s", callResult.Err().String())
	}

	incoming, err := waitIncomingResponse(*callResult.OK())
	if err != nil {
		return nil, err
	}
	defer incoming.ResourceDrop()

	resp := &Response{
		HTTPStatus: uint16(incoming.Status()),
	}

	resp.Headers = fieldMap(incoming.Headers())

	bodyResult := incoming.Consume()
	if bodyResult.IsErr() {
		return nil, errors.New("consume grpc response body")
	}
	body := *bodyResult.OK()
	defer body.ResourceDrop()

	payload, trailers, err := readResponse(body)
	if err != nil {
		return nil, err
	}
	resp.Trailers = trailers

	message, err := decodeUnaryPayload(payload)
	if err != nil {
		return nil, err
	}
	resp.Message = message
	resp.GRPCStatus = firstHeader(resp.Trailers, headerGrpcStatus)
	if resp.GRPCStatus == "" {
		resp.GRPCStatus = firstHeader(resp.Headers, headerGrpcStatus)
	}
	resp.GRPCMessage = firstHeader(resp.Trailers, headerGrpcMessage)
	if resp.GRPCMessage == "" {
		resp.GRPCMessage = firstHeader(resp.Headers, headerGrpcMessage)
	}
	if resp.GRPCStatus == "" {
		resp.GRPCStatus = "0"
	}
	if resp.GRPCStatus != "0" {
		return nil, &StatusError{
			Code:       resp.GRPCStatus,
			Message:    resp.GRPCMessage,
			HTTPStatus: resp.HTTPStatus,
		}
	}

	return resp, nil
}

func openServerStream(ctx context.Context, req Request) (ServerStream, error) {
	if req.Endpoint == "" {
		return nil, errors.New("grpc endpoint is required")
	}
	if req.Procedure == "" || !strings.HasPrefix(req.Procedure, "/") {
		return nil, errors.New("grpc procedure must start with '/'")
	}

	parsed, err := url.Parse(req.Endpoint)
	if err != nil {
		return nil, fmt.Errorf("parse endpoint: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return nil, fmt.Errorf("unsupported endpoint scheme: %s", parsed.Scheme)
	}
	if parsed.Host == "" {
		return nil, errors.New("grpc endpoint host is required")
	}

	headers, err := newFields(baseHeaders(req, ctx))
	if err != nil {
		return nil, err
	}
	outReq := types.NewOutgoingRequest(headers)
	if outReq.SetMethod(types.MethodPost()) == cm.ResultErr {
		outReq.ResourceDrop()
		return nil, errors.New("set grpc method")
	}
	if outReq.SetScheme(cm.Some(schemeForURL(parsed))) == cm.ResultErr {
		outReq.ResourceDrop()
		return nil, errors.New("set grpc scheme")
	}
	if outReq.SetAuthority(cm.Some(parsed.Host)) == cm.ResultErr {
		outReq.ResourceDrop()
		return nil, errors.New("set grpc authority")
	}
	if outReq.SetPathWithQuery(cm.Some(req.Procedure)) == cm.ResultErr {
		outReq.ResourceDrop()
		return nil, errors.New("set grpc procedure")
	}

	if err := writeRequestBody(outReq, req); err != nil {
		outReq.ResourceDrop()
		return nil, err
	}

	options := requestOptions(req, ctx)
	callResult := outgoinghandler.Handle(outReq, options)
	outReq.ResourceDrop()
	if callResult.IsErr() {
		return nil, fmt.Errorf("outbound grpc request: %s", callResult.Err().String())
	}

	incoming, err := waitIncomingResponse(*callResult.OK())
	if err != nil {
		return nil, err
	}

	resp := &Response{
		HTTPStatus: uint16(incoming.Status()),
		Headers:    fieldMap(incoming.Headers()),
	}
	bodyResult := incoming.Consume()
	if bodyResult.IsErr() {
		incoming.ResourceDrop()
		return nil, errors.New("consume grpc response body")
	}
	body := *bodyResult.OK()
	streamResult := body.Stream()
	if streamResult.IsErr() {
		body.ResourceDrop()
		incoming.ResourceDrop()
		return nil, errors.New("open grpc response stream")
	}

	return &serverStream{
		resp:     resp,
		incoming: incoming,
		body:     body,
		stream:   *streamResult.OK(),
	}, nil
}

// StatusError reports a non-OK gRPC status returned by the server.
type StatusError struct {
	Code       string
	Message    string
	HTTPStatus uint16
}

type serverStream struct {
	resp      *Response
	incoming  types.IncomingResponse
	body      types.IncomingBody
	stream    types.InputStream
	buf       []byte
	finalized bool
	closed    bool
}

func (s *serverStream) Response() *Response {
	return s.resp
}

func (s *serverStream) Next() ([]byte, error) {
	if s.closed {
		return nil, io.EOF
	}
	header, err := s.readExactly(5)
	if err != nil {
		if errors.Is(err, io.EOF) {
			if err := s.finalize(); err != nil {
				return nil, err
			}
		}
		return nil, err
	}
	if header[0] != 0 {
		return nil, fmt.Errorf("compressed grpc responses are unsupported: flag=%d", header[0])
	}
	size := binary.BigEndian.Uint32(header[1:5])
	payload, err := s.readExactly(int(size))
	if err != nil {
		return nil, err
	}
	return payload, nil
}

func (s *serverStream) Close() error {
	if s.closed {
		return nil
	}
	s.closed = true
	s.stream.ResourceDrop()
	s.body.ResourceDrop()
	s.incoming.ResourceDrop()
	return nil
}

func (e *StatusError) Error() string {
	if e.Message == "" {
		return "grpc status " + e.Code
	}
	return "grpc status " + e.Code + ": " + e.Message
}

func baseHeaders(req Request, ctx context.Context) map[string]string {
	headers := map[string]string{
		headerContentType: "application/grpc+proto",
		headerTE:          "trailers",
		"user-agent":      "spin-go-sdk/tinygo-grpc",
	}
	for k, v := range req.Headers {
		headers[strings.ToLower(k)] = v
	}
	if timeout := requestTimeout(req, ctx); timeout > 0 {
		headers[headerGrpcTimeout] = encodeGRPCTimeout(timeout)
	}
	return headers
}

func requestTimeout(req Request, ctx context.Context) time.Duration {
	if req.Timeout > 0 {
		return req.Timeout
	}
	deadline, ok := ctx.Deadline()
	if !ok {
		return 0
	}
	timeout := time.Until(deadline)
	if timeout < 0 {
		return 0
	}
	return timeout
}

func requestOptions(req Request, ctx context.Context) cm.Option[types.RequestOptions] {
	timeout := requestTimeout(req, ctx)
	if timeout <= 0 {
		return cm.None[types.RequestOptions]()
	}

	opts := types.NewRequestOptions()
	micros := uint64(timeout / time.Microsecond)
	if micros == 0 {
		micros = 1
	}
	optDuration := cm.Some(types.Duration(micros))
	_ = opts.SetConnectTimeout(optDuration)
	_ = opts.SetFirstByteTimeout(optDuration)
	_ = opts.SetBetweenBytesTimeout(optDuration)
	return cm.Some(opts)
}

func schemeForURL(u *url.URL) types.Scheme {
	if u.Scheme == "https" {
		return types.SchemeHTTPS()
	}
	return types.SchemeHTTP()
}

func newFields(headers map[string]string) (types.Fields, error) {
	entries := make([]cm.Tuple[types.FieldKey, types.FieldValue], 0, len(headers))
	for k, v := range headers {
		entries = append(entries, cm.Tuple[types.FieldKey, types.FieldValue]{
			F0: types.FieldKey(k),
			F1: types.FieldValue(cm.ToList([]byte(v))),
		})
	}
	result := types.FieldsFromList(cm.ToList(entries))
	if result.IsErr() {
		return 0, fmt.Errorf("invalid grpc headers: %s", result.Err().String())
	}
	return *result.OK(), nil
}

func writeRequestBody(outReq types.OutgoingRequest, req Request) error {
	bodyResult := outReq.Body()
	if bodyResult.IsErr() {
		return errors.New("acquire grpc request body")
	}
	body := *bodyResult.OK()
	defer body.ResourceDrop()

	streamResult := body.Write()
	if streamResult.IsErr() {
		return errors.New("open grpc request stream")
	}
	stream := *streamResult.OK()
	defer stream.ResourceDrop()

	frames := encodeRequestPayloads(req)
	for _, frame := range frames {
		writeResult := stream.BlockingWriteAndFlush(cm.ToList(frame))
		if writeResult.IsErr() {
			return fmt.Errorf("write grpc request body: %s", writeResult.Err().String())
		}
	}
	finishResult := types.OutgoingBodyFinish(body, cm.None[types.Trailers]())
	if finishResult.IsErr() {
		return fmt.Errorf("finish grpc request body: %s", finishResult.Err().String())
	}
	return nil
}

func waitIncomingResponse(future types.FutureIncomingResponse) (types.IncomingResponse, error) {
	defer future.ResourceDrop()
	for {
		if ready := future.Get(); ready.Some() != nil {
			outer := *ready.Some()
			if outer.IsErr() {
				return 0, errors.New("grpc future response unresolved")
			}
			inner := *outer.OK()
			if inner.IsErr() {
				return 0, fmt.Errorf("grpc response error: %s", inner.Err().String())
			}
			return *inner.OK(), nil
		}
		pollable := future.Subscribe()
		pollable.Block()
		pollable.ResourceDrop()
	}
}

func readResponse(body types.IncomingBody) ([]byte, map[string][]string, error) {
	streamResult := body.Stream()
	if streamResult.IsErr() {
		return nil, nil, errors.New("open grpc response stream")
	}
	stream := *streamResult.OK()
	defer stream.ResourceDrop()

	var payload []byte
	for {
		chunkResult := stream.BlockingRead(defaultReadChunkSize)
		if chunkResult.IsErr() {
			streamErr := chunkResult.Err()
			if streamErr.Closed() {
				break
			}
			return nil, nil, fmt.Errorf("read grpc response stream: %s", streamErr.String())
		}
		chunk := append([]byte(nil), chunkResult.OK().Slice()...)
		if len(chunk) == 0 {
			break
		}
		payload = append(payload, chunk...)
	}

	trailersFuture := types.IncomingBodyFinish(body)
	trailers, err := waitTrailers(trailersFuture)
	if err != nil {
		return nil, nil, err
	}
	return payload, trailers, nil
}

func (s *serverStream) readExactly(n int) ([]byte, error) {
	for len(s.buf) < n {
		chunkResult := s.stream.BlockingRead(defaultReadChunkSize)
		if chunkResult.IsErr() {
			streamErr := chunkResult.Err()
			if streamErr.Closed() {
				if len(s.buf) == 0 {
					return nil, io.EOF
				}
				return nil, io.ErrUnexpectedEOF
			}
			return nil, fmt.Errorf("read grpc response stream: %s", streamErr.String())
		}
		chunk := append([]byte(nil), chunkResult.OK().Slice()...)
		if len(chunk) == 0 {
			if len(s.buf) == 0 {
				return nil, io.EOF
			}
			return nil, io.ErrUnexpectedEOF
		}
		s.buf = append(s.buf, chunk...)
	}
	out := append([]byte(nil), s.buf[:n]...)
	s.buf = s.buf[n:]
	return out, nil
}

func (s *serverStream) finalize() error {
	if s.finalized {
		s.closed = true
		return io.EOF
	}
	s.finalized = true
	trailers, err := waitTrailers(types.IncomingBodyFinish(s.body))
	if err != nil {
		_ = s.Close()
		return err
	}
	s.resp.Trailers = trailers
	s.resp.GRPCStatus = firstHeader(trailers, headerGrpcStatus)
	if s.resp.GRPCStatus == "" {
		s.resp.GRPCStatus = firstHeader(s.resp.Headers, headerGrpcStatus)
	}
	s.resp.GRPCMessage = firstHeader(trailers, headerGrpcMessage)
	if s.resp.GRPCMessage == "" {
		s.resp.GRPCMessage = firstHeader(s.resp.Headers, headerGrpcMessage)
	}
	if s.resp.GRPCStatus == "" {
		s.resp.GRPCStatus = "0"
	}
	_ = s.Close()
	if s.resp.GRPCStatus != "0" {
		return &StatusError{
			Code:       s.resp.GRPCStatus,
			Message:    s.resp.GRPCMessage,
			HTTPStatus: s.resp.HTTPStatus,
		}
	}
	return io.EOF
}

func waitTrailers(future types.FutureTrailers) (map[string][]string, error) {
	defer future.ResourceDrop()
	for {
		if ready := future.Get(); ready.Some() != nil {
			outer := *ready.Some()
			if outer.IsErr() {
				return nil, errors.New("grpc trailers future unresolved")
			}
			inner := *outer.OK()
			if inner.IsErr() {
				return nil, fmt.Errorf("grpc trailers error: %s", inner.Err().String())
			}
			opt := *inner.OK()
			if opt.None() {
				return map[string][]string{}, nil
			}
			return fieldMap(*opt.Some()), nil
		}
		pollable := future.Subscribe()
		pollable.Block()
		pollable.ResourceDrop()
	}
}

func fieldMap(fields types.Fields) map[string][]string {
	entries := fields.Entries().Slice()
	out := make(map[string][]string, len(entries))
	for _, entry := range entries {
		key := strings.ToLower(string(entry.F0))
		out[key] = append(out[key], string(entry.F1.Slice()))
	}
	return out
}

func firstHeader(headers map[string][]string, key string) string {
	values := headers[strings.ToLower(key)]
	if len(values) == 0 {
		return ""
	}
	return values[0]
}

func encodeGRPCTimeout(timeout time.Duration) string {
	// gRPC timeout units: H, M, S, m, u, n. Prefer the coarsest exact unit.
	type unit struct {
		suffix string
		value  time.Duration
	}
	units := []unit{
		{suffix: "H", value: time.Hour},
		{suffix: "M", value: time.Minute},
		{suffix: "S", value: time.Second},
		{suffix: "m", value: time.Millisecond},
		{suffix: "u", value: time.Microsecond},
		{suffix: "n", value: time.Nanosecond},
	}
	for _, u := range units {
		if timeout%u.value == 0 {
			n := timeout / u.value
			if n > 0 && n <= 99999999 {
				return strconv.FormatInt(int64(n), 10) + u.suffix
			}
		}
	}
	nanos := timeout / time.Nanosecond
	if nanos <= 0 {
		nanos = 1
	}
	if nanos > 99999999 {
		nanos = 99999999
	}
	return strconv.FormatInt(int64(nanos), 10) + "n"
}

// DebugFrame returns a base64 representation useful for logging raw protobuf bodies.
func DebugFrame(message []byte) string {
	return base64.StdEncoding.EncodeToString(message)
}
