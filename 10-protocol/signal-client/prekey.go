package signalclient

import (
	"crypto/rand"
	"encoding/binary"
)

// SignedPreKey is a medium-term DH key pair signed by the identity key.
type SignedPreKey struct {
	KeyID     uint32
	KeyPair   DHKeyPair
	Signature []byte // Ed25519 signature over KeyPair.PublicKey
}

// OneTimePreKey is a single-use DH key pair for X3DH.
type OneTimePreKey struct {
	KeyID   uint32
	KeyPair DHKeyPair
}

// PreKeyBundle is the public key material published by a recipient to a key server.
type PreKeyBundle struct {
	RegistrationID   uint32
	DeviceID         uint32
	IdentityKey      [32]byte // X25519 identity public key
	IdentitySignKey  []byte   // Ed25519 signing public key (32 bytes)
	SignedPreKey      SignedPreKeyPublic
	OneTimePreKey    *OneTimePreKeyPublic // nil if none available
}

// SignedPreKeyPublic is the public portion of a SignedPreKey.
type SignedPreKeyPublic struct {
	KeyID     uint32
	PublicKey [32]byte
	Signature []byte
}

// OneTimePreKeyPublic is the public portion of a OneTimePreKey.
type OneTimePreKeyPublic struct {
	KeyID     uint32
	PublicKey [32]byte
}

// GenerateSignedPreKey generates a new signed prekey and signs it with the identity key.
func GenerateSignedPreKey(ik *IdentityKeyPair, keyID uint32) (*SignedPreKey, error) {
	kp, err := GenerateDHKeyPair()
	if err != nil {
		return nil, err
	}
	sig := ik.SignPreKey(kp.PublicKey)
	return &SignedPreKey{
		KeyID:     keyID,
		KeyPair:   *kp,
		Signature: sig,
	}, nil
}

// PublicBundle returns the public portion of a SignedPreKey.
func (spk *SignedPreKey) Public() SignedPreKeyPublic {
	return SignedPreKeyPublic{
		KeyID:     spk.KeyID,
		PublicKey: spk.KeyPair.PublicKey,
		Signature: spk.Signature,
	}
}

// GenerateOneTimePreKeys generates n one-time prekeys starting at keyID.
func GenerateOneTimePreKeys(startKeyID uint32, n int) ([]OneTimePreKey, error) {
	opks := make([]OneTimePreKey, n)
	for i := 0; i < n; i++ {
		kp, err := GenerateDHKeyPair()
		if err != nil {
			return nil, err
		}
		opks[i] = OneTimePreKey{
			KeyID:   startKeyID + uint32(i),
			KeyPair: *kp,
		}
	}
	return opks, nil
}

// PublicKeys returns the public portions of a slice of one-time prekeys.
func OneTimePreKeyPublics(opks []OneTimePreKey) []OneTimePreKeyPublic {
	out := make([]OneTimePreKeyPublic, len(opks))
	for i, opk := range opks {
		out[i] = OneTimePreKeyPublic{
			KeyID:     opk.KeyID,
			PublicKey: opk.KeyPair.PublicKey,
		}
	}
	return out
}

// randomKeyID generates a random 24-bit key ID.
func randomKeyID() (uint32, error) {
	var b [4]byte
	if _, err := rand.Read(b[:]); err != nil {
		return 0, err
	}
	return binary.BigEndian.Uint32(b[:]) & 0x00FFFFFF, nil
}
