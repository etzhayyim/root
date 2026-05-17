package grpc

import (
	"context"
	"errors"
	"testing"
)

func TestInvokeUnaryTypedRequiresCodecs(t *testing.T) {
	_, _, err := InvokeUnaryTyped[struct{}, struct{}](context.Background(), Request{}, struct{}{}, nil, func([]byte) (struct{}, error) {
		return struct{}{}, nil
	})
	if err == nil {
		t.Fatal("expected marshal error")
	}

	_, _, err = InvokeUnaryTyped[struct{}, struct{}](context.Background(), Request{}, struct{}{}, func(struct{}) ([]byte, error) {
		return nil, nil
	}, nil)
	if err == nil {
		t.Fatal("expected unmarshal error")
	}
}

func TestRequestMessagesOverrideSingleMessage(t *testing.T) {
	req := Request{
		Message:  []byte("single"),
		Messages: [][]byte{[]byte("one"), []byte("two")},
	}
	frames := encodeRequestPayloads(req)
	if len(frames) != 2 {
		t.Fatalf("frames=%d want 2", len(frames))
	}
	if got, err := decodeUnaryPayload(frames[0]); err != nil || string(got) != "one" {
		t.Fatalf("frame0=%q err=%v", got, err)
	}
	if got, err := decodeUnaryPayload(frames[1]); err != nil || string(got) != "two" {
		t.Fatalf("frame1=%q err=%v", got, err)
	}
}

func TestInvokeUnaryTypedPropagatesMarshalError(t *testing.T) {
	want := errors.New("marshal failed")
	_, _, err := InvokeUnaryTyped[struct{}, struct{}](context.Background(), Request{}, struct{}{}, func(struct{}) ([]byte, error) {
		return nil, want
	}, func([]byte) (struct{}, error) {
		return struct{}{}, nil
	})
	if !errors.Is(err, want) {
		t.Fatalf("expected %v, got %v", want, err)
	}
}
