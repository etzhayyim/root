// Package grpc provides a minimal unary gRPC client for TinyGo Spin components.
//
// The implementation targets Spin's WASI HTTP 0.2 outbound handler so it can
// speak gRPC over HTTP/2 without depending on Rust-only transport helpers.
package grpc
