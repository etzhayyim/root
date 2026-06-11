package signalclient

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"io"

	"golang.org/x/crypto/chacha20poly1305"
	"golang.org/x/crypto/hkdf"
)

const (
	maxSkip        = 100  // maximum number of skipped message keys to store
	ratchetInfoStr = "etzhayyim Signal Ratchet v1"
)

// Session is a Double Ratchet session for 1:1 encrypted messaging.
type Session struct {
	dhs DHKeyPair  // our current DH ratchet key pair
	dhr *[32]byte  // their current DH ratchet public key (nil initially for receiver)
	rk  [32]byte   // root key
	cks *[32]byte  // sending chain key
	ckr *[32]byte  // receiving chain key
	ns  uint32     // message number (sending)
	nr  uint32     // message number (receiving)
	pn  uint32     // previous sending chain length
	// skipped[{dh_pub_hex, msg_num}] = message_key
	skipped map[skippedKey][32]byte
	ad      []byte // associated data from X3DH
}

type skippedKey struct {
	pubHex [32]byte
	n      uint32
}

// MessageHeader is prepended to every ratchet-encrypted message.
type MessageHeader struct {
	DHPublic [32]byte
	PN       uint32
	N        uint32
}

// InitSessionSender initializes a Double Ratchet session for the sender (Alice).
// sharedSecret is from X3DH. recipientRatchetKey is the recipient's signed prekey (SPK_B).
func InitSessionSender(sharedSecret *X3DHSharedSecret, recipientRatchetKey [32]byte) (*Session, error) {
	dhs, err := GenerateDHKeyPair()
	if err != nil {
		return nil, err
	}
	s := &Session{
		dhs:     *dhs,
		dhr:     &recipientRatchetKey,
		skipped: make(map[skippedKey][32]byte),
		ad:      sharedSecret.AD,
	}
	// Perform initial DH ratchet step
	rk, cks, err := kdfRK(sharedSecret.SharedSecret, *dhs, recipientRatchetKey)
	if err != nil {
		return nil, err
	}
	s.rk = rk
	s.cks = &cks
	return s, nil
}

// InitSessionReceiver initializes a Double Ratchet session for the receiver (Bob).
// sharedSecret is from X3DH. ourRatchetKey is the signed prekey (SPK_B) used in X3DH.
func InitSessionReceiver(sharedSecret *X3DHSharedSecret, ourRatchetKey *DHKeyPair) (*Session, error) {
	rk := sharedSecret.SharedSecret
	s := &Session{
		dhs:     *ourRatchetKey,
		rk:      rk,
		skipped: make(map[skippedKey][32]byte),
		ad:      sharedSecret.AD,
	}
	return s, nil
}

// Encrypt encrypts plaintext, advancing the sending chain.
func (s *Session) Encrypt(plaintext []byte) (header MessageHeader, ciphertext []byte, err error) {
	if s.cks == nil {
		// Need to perform a DH ratchet step first (receiver hasn't sent yet)
		if s.dhr == nil {
			return MessageHeader{}, nil, fmt.Errorf("signal: session not initialized")
		}
	}

	mk, nextCKs, err := kdfCK(*s.cks)
	if err != nil {
		return MessageHeader{}, nil, err
	}

	header = MessageHeader{
		DHPublic: s.dhs.PublicKey,
		PN:       s.pn,
		N:        s.ns,
	}
	s.ns++
	*s.cks = nextCKs

	aad := encodeHeaderAAD(header, s.ad)
	ct, err := aeadEncrypt(mk, plaintext, aad)
	if err != nil {
		return MessageHeader{}, nil, err
	}
	return header, ct, nil
}

// Decrypt decrypts a ciphertext using the session's receiving chain.
func (s *Session) Decrypt(header MessageHeader, ciphertext []byte) ([]byte, error) {
	// Check if this is a skipped message
	sk := skippedKey{pubHex: header.DHPublic, n: header.N}
	if mk, ok := s.skipped[sk]; ok {
		delete(s.skipped, sk)
		aad := encodeHeaderAAD(header, s.ad)
		return aeadDecrypt(mk, ciphertext, aad)
	}

	// DH ratchet step if new DH key
	if s.dhr == nil || header.DHPublic != *s.dhr {
		// Skip remaining messages in current receiving chain
		if err := s.skipMessageKeys(header.PN); err != nil {
			return nil, err
		}
		if err := s.dhRatchetStep(header.DHPublic); err != nil {
			return nil, err
		}
	}

	// Skip messages in new chain if needed
	if err := s.skipMessageKeys(header.N); err != nil {
		return nil, err
	}

	mk, nextCKr, err := kdfCK(*s.ckr)
	if err != nil {
		return nil, err
	}
	s.nr++
	*s.ckr = nextCKr

	aad := encodeHeaderAAD(header, s.ad)
	return aeadDecrypt(mk, ciphertext, aad)
}

func (s *Session) skipMessageKeys(until uint32) error {
	if s.ckr == nil {
		return nil
	}
	if until < s.nr {
		return nil
	}
	if until-s.nr > maxSkip {
		return fmt.Errorf("signal: too many skipped messages: %d", until-s.nr)
	}
	for s.nr < until {
		mk, nextCK, err := kdfCK(*s.ckr)
		if err != nil {
			return err
		}
		s.skipped[skippedKey{pubHex: *s.dhr, n: s.nr}] = mk
		*s.ckr = nextCK
		s.nr++
	}
	return nil
}

func (s *Session) dhRatchetStep(remotePub [32]byte) error {
	s.pn = s.ns
	s.ns = 0
	s.nr = 0
	s.dhr = &remotePub

	// Receiving chain: RK, CKr = KDF_RK(RK, DH(DHs, DHr))
	rk, ckr, err := kdfRK(s.rk, s.dhs, remotePub)
	if err != nil {
		return err
	}
	s.rk = rk
	s.ckr = &ckr

	// New sending key pair and chain: RK, CKs = KDF_RK(RK, DH(new_DHs, DHr))
	newDHs, err := GenerateDHKeyPair()
	if err != nil {
		return err
	}
	s.dhs = *newDHs
	rk2, cks, err := kdfRK(s.rk, s.dhs, remotePub)
	if err != nil {
		return err
	}
	s.rk = rk2
	s.cks = &cks
	return nil
}

// kdfRK derives a new root key and chain key from the current root key and DH output.
// Returns (newRK, newCK, error)
func kdfRK(rk [32]byte, dhs DHKeyPair, dhr [32]byte) ([32]byte, [32]byte, error) {
	dhOut, err := DH(dhs.PrivateKey, dhr)
	if err != nil {
		return [32]byte{}, [32]byte{}, err
	}
	r := hkdf.New(sha256.New, dhOut[:], rk[:], []byte(ratchetInfoStr))
	var newRK, newCK [32]byte
	if _, err := io.ReadFull(r, newRK[:]); err != nil {
		return [32]byte{}, [32]byte{}, err
	}
	if _, err := io.ReadFull(r, newCK[:]); err != nil {
		return [32]byte{}, [32]byte{}, err
	}
	return newRK, newCK, nil
}

// kdfCK derives a message key and next chain key from a chain key.
// Returns (messageKey, nextChainKey, error)
func kdfCK(ck [32]byte) ([32]byte, [32]byte, error) {
	mac := hmac.New(sha256.New, ck[:])
	mac.Write([]byte{0x01})
	mk := [32]byte(mac.Sum(nil)[:32])

	mac.Reset()
	mac.Write([]byte{0x02})
	nextCK := [32]byte(mac.Sum(nil)[:32])
	return mk, nextCK, nil
}

// aeadEncrypt encrypts plaintext with ChaCha20-Poly1305 using a 32-byte key.
func aeadEncrypt(key [32]byte, plaintext, aad []byte) ([]byte, error) {
	aead, err := chacha20poly1305.New(key[:])
	if err != nil {
		return nil, err
	}
	nonce := make([]byte, aead.NonceSize())
	if _, err := rand.Read(nonce); err != nil {
		return nil, err
	}
	ct := aead.Seal(nonce, nonce, plaintext, aad)
	return ct, nil
}

// aeadDecrypt decrypts ciphertext with ChaCha20-Poly1305.
func aeadDecrypt(key [32]byte, ciphertext, aad []byte) ([]byte, error) {
	aead, err := chacha20poly1305.New(key[:])
	if err != nil {
		return nil, err
	}
	ns := aead.NonceSize()
	if len(ciphertext) < ns {
		return nil, fmt.Errorf("signal: ciphertext too short")
	}
	nonce, ct := ciphertext[:ns], ciphertext[ns:]
	return aead.Open(nil, nonce, ct, aad)
}

// ─── Session persistence ──────────────────────────────────────────────────────

// SkippedKeyState is the serializable form of a skipped message key entry.
type SkippedKeyState struct {
	DHPublic   [32]byte `json:"dh_public"`
	N          uint32   `json:"n"`
	MessageKey [32]byte `json:"message_key"`
}

// SessionState is a fully serializable snapshot of a Double Ratchet Session.
// Use Session.State() to extract and RestoreSession() to reconstruct.
type SessionState struct {
	DHsPrivate [32]byte          `json:"dhs_private"`
	DHsPublic  [32]byte          `json:"dhs_public"`
	DHr        *[32]byte         `json:"dhr,omitempty"`
	RK         [32]byte          `json:"rk"`
	CKs        *[32]byte         `json:"cks,omitempty"`
	CKr        *[32]byte         `json:"ckr,omitempty"`
	Ns         uint32            `json:"ns"`
	Nr         uint32            `json:"nr"`
	Pn         uint32            `json:"pn"`
	Skipped    []SkippedKeyState `json:"skipped,omitempty"`
	AD         []byte            `json:"ad,omitempty"`
}

// State extracts the session into a serializable snapshot.
func (s *Session) State() SessionState {
	st := SessionState{
		DHsPrivate: s.dhs.PrivateKey,
		DHsPublic:  s.dhs.PublicKey,
		DHr:        s.dhr,
		RK:         s.rk,
		CKs:        s.cks,
		CKr:        s.ckr,
		Ns:         s.ns,
		Nr:         s.nr,
		Pn:         s.pn,
		AD:         s.ad,
	}
	for k, mk := range s.skipped {
		st.Skipped = append(st.Skipped, SkippedKeyState{
			DHPublic:   k.pubHex,
			N:          k.n,
			MessageKey: mk,
		})
	}
	return st
}

// RestoreSession reconstructs a Session from a persisted SessionState.
func RestoreSession(st SessionState) *Session {
	sess := &Session{
		dhs: DHKeyPair{
			PrivateKey: st.DHsPrivate,
			PublicKey:  st.DHsPublic,
		},
		dhr:     st.DHr,
		rk:      st.RK,
		cks:     st.CKs,
		ckr:     st.CKr,
		ns:      st.Ns,
		nr:      st.Nr,
		pn:      st.Pn,
		skipped: make(map[skippedKey][32]byte, len(st.Skipped)),
		ad:      st.AD,
	}
	for _, entry := range st.Skipped {
		sess.skipped[skippedKey{pubHex: entry.DHPublic, n: entry.N}] = entry.MessageKey
	}
	return sess
}

// encodeHeaderAAD serializes a message header + session AD for AEAD.
func encodeHeaderAAD(h MessageHeader, sessionAD []byte) []byte {
	out := make([]byte, 32+4+4+len(sessionAD))
	copy(out[:32], h.DHPublic[:])
	binary.BigEndian.PutUint32(out[32:], h.PN)
	binary.BigEndian.PutUint32(out[36:], h.N)
	copy(out[40:], sessionAD)
	return out
}
