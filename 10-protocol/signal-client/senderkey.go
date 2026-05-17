package signalclient

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"fmt"
)

// GroupSession manages Sender Key encryption for a group channel.
// Each sender has their own SenderKey, distributed to group members via X3DH-encrypted messages.
type GroupSession struct {
	groupID  string
	members  map[string]*senderState // keyed by sender DID
	ourDID   string
	ourState *senderState
}

type senderState struct {
	chainKey [32]byte
	iteration uint32
}

// SenderKeyDistributionMessage is sent (encrypted 1:1) to each group member
// to allow them to decrypt future group messages from this sender.
type SenderKeyDistributionMessage struct {
	GroupID   string   `json:"group_id"`
	SenderDID string   `json:"sender_did"`
	Iteration uint32   `json:"iteration"`
	ChainKey  [32]byte `json:"chain_key"`
}

// SenderKeyMessage is an encrypted group message.
type SenderKeyMessage struct {
	GroupID   string `json:"group_id"`
	SenderDID string `json:"sender_did"`
	Iteration uint32 `json:"iteration"`
	// ChaCha20-Poly1305 ciphertext; key derived from chain at Iteration
	Ciphertext []byte `json:"ciphertext"`
}

// NewGroupSession creates a new GroupSession for a group channel.
func NewGroupSession(groupID, ourDID string) *GroupSession {
	return &GroupSession{
		groupID: groupID,
		ourDID:  ourDID,
		members: make(map[string]*senderState),
	}
}

// InitSender generates a fresh sender key for this device and returns the
// distribution message to send (encrypted 1:1) to each group member.
func (g *GroupSession) InitSender() (*SenderKeyDistributionMessage, error) {
	var ck [32]byte
	if _, err := rand.Read(ck[:]); err != nil {
		return nil, fmt.Errorf("signal: group init sender: %w", err)
	}
	g.ourState = &senderState{chainKey: ck, iteration: 0}
	return &SenderKeyDistributionMessage{
		GroupID:   g.groupID,
		SenderDID: g.ourDID,
		Iteration: 0,
		ChainKey:  ck,
	}, nil
}

// ProcessDistribution registers a remote sender's key distribution message,
// enabling decryption of future messages from that sender.
func (g *GroupSession) ProcessDistribution(msg *SenderKeyDistributionMessage) error {
	if msg.GroupID != g.groupID {
		return fmt.Errorf("signal: group ID mismatch: got %q want %q", msg.GroupID, g.groupID)
	}
	g.members[msg.SenderDID] = &senderState{
		chainKey:  msg.ChainKey,
		iteration: msg.Iteration,
	}
	return nil
}

// Encrypt encrypts a plaintext message for the group using our sender key.
func (g *GroupSession) Encrypt(plaintext []byte) (*SenderKeyMessage, error) {
	if g.ourState == nil {
		return nil, fmt.Errorf("signal: group sender not initialized; call InitSender first")
	}
	mk, nextCK := senderKDFCK(g.ourState.chainKey)
	iteration := g.ourState.iteration
	g.ourState.chainKey = nextCK
	g.ourState.iteration++

	ct, err := aeadEncrypt(mk, plaintext, []byte(g.groupID))
	if err != nil {
		return nil, fmt.Errorf("signal: group encrypt: %w", err)
	}
	return &SenderKeyMessage{
		GroupID:    g.groupID,
		SenderDID:  g.ourDID,
		Iteration:  iteration,
		Ciphertext: ct,
	}, nil
}

// Decrypt decrypts a group message from the given sender.
func (g *GroupSession) Decrypt(msg *SenderKeyMessage) ([]byte, error) {
	if msg.GroupID != g.groupID {
		return nil, fmt.Errorf("signal: group ID mismatch")
	}
	state, ok := g.members[msg.SenderDID]
	if !ok {
		return nil, fmt.Errorf("signal: no sender key for %q; process distribution first", msg.SenderDID)
	}

	// Advance chain key to the message's iteration
	if msg.Iteration < state.iteration {
		return nil, fmt.Errorf("signal: group message iteration %d already passed (at %d)", msg.Iteration, state.iteration)
	}
	for state.iteration < msg.Iteration {
		_, next := senderKDFCK(state.chainKey)
		state.chainKey = next
		state.iteration++
	}

	mk, nextCK := senderKDFCK(state.chainKey)
	state.chainKey = nextCK
	state.iteration++

	return aeadDecrypt(mk, msg.Ciphertext, []byte(g.groupID))
}

// Distribution returns the current distribution message for re-sending to new members.
// Call after InitSender.
func (g *GroupSession) Distribution() (*SenderKeyDistributionMessage, error) {
	if g.ourState == nil {
		return nil, fmt.Errorf("signal: group sender not initialized")
	}
	return &SenderKeyDistributionMessage{
		GroupID:   g.groupID,
		SenderDID: g.ourDID,
		Iteration: g.ourState.iteration,
		ChainKey:  g.ourState.chainKey,
	}, nil
}

// SenderState returns the current chain key and iteration for the given senderDID.
// Used to persist group session state between requests (e.g., to a database).
// Returns ok=false if no state has been registered for that sender.
func (g *GroupSession) SenderState(senderDID string) (chainKey [32]byte, iteration uint32, ok bool) {
	state, found := g.members[senderDID]
	if !found {
		return
	}
	return state.chainKey, state.iteration, true
}

// RestoreGroupSession reconstructs a GroupSession from persisted sender state entries.
// Each entry should be a SenderKeyDistributionMessage reflecting the current (not initial)
// chain key and iteration for that sender — i.e., the value returned by SenderState after
// the last successful Decrypt call.
func RestoreGroupSession(groupID, ourDID string, states []SenderKeyDistributionMessage) *GroupSession {
	g := &GroupSession{
		groupID: groupID,
		ourDID:  ourDID,
		members: make(map[string]*senderState),
	}
	for _, dist := range states {
		g.members[dist.SenderDID] = &senderState{
			chainKey:  dist.ChainKey,
			iteration: dist.Iteration,
		}
	}
	return g
}

// senderKDFCK derives (messageKey, nextChainKey) from a sender chain key.
func senderKDFCK(ck [32]byte) ([32]byte, [32]byte) {
	mac := hmac.New(sha256.New, ck[:])
	mac.Write([]byte{0x01})
	var mk [32]byte
	copy(mk[:], mac.Sum(nil))

	mac.Reset()
	mac.Write([]byte{0x02})
	var nextCK [32]byte
	copy(nextCK[:], mac.Sum(nil))
	return mk, nextCK
}
