package grpc

import (
	"encoding/binary"
	"errors"
	"fmt"
)

func encodeUnaryPayload(message []byte) []byte {
	frame := make([]byte, 5+len(message))
	binary.BigEndian.PutUint32(frame[1:5], uint32(len(message)))
	copy(frame[5:], message)
	return frame
}

func encodeRequestPayloads(req Request) [][]byte {
	if len(req.Messages) == 0 {
		return [][]byte{encodeUnaryPayload(req.Message)}
	}
	frames := make([][]byte, 0, len(req.Messages))
	for _, message := range req.Messages {
		frames = append(frames, encodeUnaryPayload(message))
	}
	return frames
}

func decodeUnaryPayload(frame []byte) ([]byte, error) {
	if len(frame) == 0 {
		return nil, nil
	}
	if len(frame) < 5 {
		return nil, errors.New("grpc response frame too short")
	}
	if frame[0] != 0 {
		return nil, fmt.Errorf("compressed grpc responses are unsupported: flag=%d", frame[0])
	}
	size := binary.BigEndian.Uint32(frame[1:5])
	if len(frame) != int(5+size) {
		return nil, fmt.Errorf("grpc response frame length mismatch: got=%d want=%d", len(frame), 5+size)
	}
	return append([]byte(nil), frame[5:]...), nil
}
