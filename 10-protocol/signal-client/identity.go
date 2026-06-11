// Package signalclient implements Signal Protocol cryptographic primitives:
// X3DH key agreement, Double Ratchet sessions, and Sender Key group encryption.
package signalclient

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"fmt"

	"golang.org/x/crypto/curve25519"
)

// IdentityKeyPair is the long-term identity key for a device.
// X25519 is used for Diffie-Hellman operations; Ed25519 for signing prekeys.
type IdentityKeyPair struct {
	PublicKey  [32]byte         // X25519 public key
	PrivateKey [32]byte         // X25519 private key
	SignPublic ed25519.PublicKey // Ed25519 signing key
	SignPrivate ed25519.PrivateKey
}

// GenerateIdentityKeyPair generates a new long-term identity key pair.
func GenerateIdentityKeyPair() (*IdentityKeyPair, error) {
	var priv [32]byte
	if _, err := rand.Read(priv[:]); err != nil {
		return nil, err
	}
	// Clamp for X25519
	priv[0] &= 248
	priv[31] &= 127
	priv[31] |= 64

	var pub [32]byte
	curve25519.ScalarBaseMult(&pub, &priv)

	signPub, signPriv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, err
	}
	return &IdentityKeyPair{
		PublicKey:   pub,
		PrivateKey:  priv,
		SignPublic:  signPub,
		SignPrivate: signPriv,
	}, nil
}

// DHKeyPair is a Curve25519 key pair used for ephemeral or prekey operations.
type DHKeyPair struct {
	PublicKey  [32]byte
	PrivateKey [32]byte
}

// GenerateDHKeyPair generates a random Curve25519 key pair.
func GenerateDHKeyPair() (*DHKeyPair, error) {
	var priv [32]byte
	if _, err := rand.Read(priv[:]); err != nil {
		return nil, err
	}
	priv[0] &= 248
	priv[31] &= 127
	priv[31] |= 64

	var pub [32]byte
	curve25519.ScalarBaseMult(&pub, &priv)
	return &DHKeyPair{PublicKey: pub, PrivateKey: priv}, nil
}

// DH performs an X25519 Diffie-Hellman operation.
func DH(priv, pub [32]byte) ([32]byte, error) {
	out, err := curve25519.X25519(priv[:], pub[:])
	if err != nil {
		return [32]byte{}, fmt.Errorf("signal: DH failed: %w", err)
	}
	var result [32]byte
	copy(result[:], out)
	return result, nil
}

// SignPreKey signs a prekey public key with the identity signing key.
// Returns a 64-byte Ed25519 signature.
func (ik *IdentityKeyPair) SignPreKey(preKeyPublic [32]byte) []byte {
	return ed25519.Sign(ik.SignPrivate, preKeyPublic[:])
}

// VerifyPreKey verifies a prekey signature against an identity signing public key.
func VerifyPreKey(signPub ed25519.PublicKey, preKeyPublic [32]byte, sig []byte) bool {
	return ed25519.Verify(signPub, preKeyPublic[:], sig)
}

// registrationID generates a deterministic 14-bit registration ID from identity public key.
func RegistrationID(pub [32]byte) uint32 {
	h := sha256.Sum256(pub[:])
	return uint32(binary.BigEndian.Uint16(h[:2])) & 0x3FFF
}
