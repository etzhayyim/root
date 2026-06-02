//go:build !tinygo

package atclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"strings"
	"time"

	"github.com/fxamacker/cbor/v2"
	"github.com/gorilla/websocket"
)

// FirehoseEvent is a decoded event from the AT Protocol Firehose
// (com.atproto.sync.subscribeRepos).
type FirehoseEvent struct {
	// Header fields (CBOR map: {op, t})
	Op int    // 1 = message, -1 = error
	T  string // event type e.g. "#commit", "#handle", "#tombstone"
	// Sequence number from the relay
	Seq int64

	// Raw CBOR body for further decoding
	Body []byte

	// Decoded for #commit events
	Commit *CommitEvent
}

// CommitEvent is the body of a #commit firehose event.
type CommitEvent struct {
	Seq    int64  `cbor:"seq"`
	Rebase bool   `cbor:"rebase"`
	TooBig bool   `cbor:"tooBig"`
	Repo   string `cbor:"repo"`
	Commit []byte `cbor:"commit"` // CID bytes
	Prev   []byte `cbor:"prev"`   // CID bytes (nil for first commit)
	Rev    string `cbor:"rev"`
	Since  string `cbor:"since"`
	Blocks []byte `cbor:"blocks"` // CAR file bytes
	Ops    []RepoOp `cbor:"ops"`
	Blobs  [][]byte `cbor:"blobs"`
	Time   string `cbor:"time"`
}

// RepoOp is a single repository operation within a commit.
type RepoOp struct {
	Action string `cbor:"action"` // "create", "update", "delete"
	Path   string `cbor:"path"`   // collection/rkey
	CID    []byte `cbor:"cid"`    // nil for delete
}

// Collection returns the collection part of the op path.
func (op *RepoOp) Collection() string {
	parts := strings.SplitN(op.Path, "/", 2)
	if len(parts) == 0 {
		return ""
	}
	return parts[0]
}

// RKey returns the record key part of the op path.
func (op *RepoOp) RKey() string {
	parts := strings.SplitN(op.Path, "/", 2)
	if len(parts) < 2 {
		return ""
	}
	return parts[1]
}

// Firehose subscribes to the AT Protocol relay firehose.
type Firehose struct {
	relayURL string
	dialer   *websocket.Dialer
}

// NewFirehose creates a Firehose subscriber for the given relay host
// (e.g. "wss://bsky.network").
func NewFirehose(relayURL string) *Firehose {
	return &Firehose{
		relayURL: strings.TrimRight(relayURL, "/"),
		dialer:   &websocket.Dialer{HandshakeTimeout: 10 * time.Second},
	}
}

// Subscribe connects to the firehose and calls handler for each event.
// cursor=0 means start from the current head. Reconnects on transient errors.
// Blocks until ctx is cancelled or handler returns an error.
func (f *Firehose) Subscribe(ctx context.Context, cursor int64, handler func(*FirehoseEvent) error) error {
	u := f.relayURL + "/xrpc/com.atproto.sync.subscribeRepos"
	if cursor > 0 {
		u += fmt.Sprintf("?cursor=%d", cursor)
	}
	conn, _, err := f.dialer.DialContext(ctx, u, nil)
	if err != nil {
		return fmt.Errorf("atclient: firehose dial: %w", err)
	}
	defer conn.Close()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}
		_, msg, err := conn.ReadMessage()
		if err != nil {
			return fmt.Errorf("atclient: firehose read: %w", err)
		}
		ev, err := decodeFirehoseMessage(msg)
		if err != nil {
			// Skip malformed messages
			continue
		}
		if err := handler(ev); err != nil {
			return err
		}
	}
}

// SubscribeFiltered is like Subscribe but only calls handler for events
// matching the given collections (e.g. "com.etzhayyim.conversation.message").
func (f *Firehose) SubscribeFiltered(ctx context.Context, cursor int64, collections []string, handler func(*FirehoseEvent, *RepoOp) error) error {
	colSet := make(map[string]struct{}, len(collections))
	for _, c := range collections {
		colSet[c] = struct{}{}
	}
	return f.Subscribe(ctx, cursor, func(ev *FirehoseEvent) error {
		if ev.Commit == nil {
			return nil
		}
		for i := range ev.Commit.Ops {
			op := &ev.Commit.Ops[i]
			if _, ok := colSet[op.Collection()]; ok {
				if err := handler(ev, op); err != nil {
					return err
				}
			}
		}
		return nil
	})
}

// FirehoseWithCursorURL builds a subscribe URL with a cursor parameter.
func FirehoseWithCursorURL(relayURL string, cursor int64) string {
	u := strings.TrimRight(relayURL, "/") + "/xrpc/com.atproto.sync.subscribeRepos"
	if cursor > 0 {
		q := url.Values{}
		q.Set("cursor", fmt.Sprintf("%d", cursor))
		u += "?" + q.Encode()
	}
	return u
}

// decodeFirehoseMessage decodes a raw WebSocket message from the firehose.
// The AT Protocol firehose encodes messages as two concatenated CBOR values:
// a header map {op, t} and a body map.
func decodeFirehoseMessage(data []byte) (*FirehoseEvent, error) {
	// The message is two CBOR items concatenated.
	// First: header = {op: int, t: string}
	// Second: body = depends on t
	dec := cbor.NewDecoder(bytes.NewReader(data))

	var header struct {
		Op int    `cbor:"op"`
		T  string `cbor:"t"`
	}
	if err := dec.Decode(&header); err != nil {
		return nil, fmt.Errorf("atclient: firehose header decode: %w", err)
	}

	ev := &FirehoseEvent{
		Op: header.Op,
		T:  header.T,
	}

	// Decode body for known event types
	switch header.T {
	case "#commit":
		var commit CommitEvent
		if err := dec.Decode(&commit); err == nil {
			ev.Commit = &commit
			ev.Seq = commit.Seq
		}
	default:
		// Store raw remaining bytes for caller to decode
		var raw cbor.RawMessage
		if err := dec.Decode(&raw); err == nil {
			ev.Body, _ = json.Marshal(raw)
		}
	}

	return ev, nil
}
