//go:build !tinygo

package grpc

import "context"

func invokeUnary(_ context.Context, _ Request) (*Response, error) {
	return nil, ErrUnsupported
}

func openServerStream(_ context.Context, _ Request) (ServerStream, error) {
	return nil, ErrUnsupported
}
