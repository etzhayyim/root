package signalclient

import (
	"crypto/sha256"
	"fmt"
	"io"

	"golang.org/x/crypto/hkdf"
)

// x3dhInfo is the HKDF info string used for key derivation.
const x3dhInfo = "etzhayyim Signal X3DH v1"

// InitialMessage is the message sent by the initiator to establish an X3DH session.
// The recipient needs this to derive the same shared secret.
type InitialMessage struct {
	RegistrationID    uint32
	SenderIdentityKey [32]byte // IK_A public (X25519)
	SenderSignKey     []byte   // IK_A signing public (Ed25519, 32 bytes)
	EphemeralKey      [32]byte // EK_A public
	RecipientSPKID    uint32
	RecipientOPKID    *uint32 // nil if no OPK used
}

// X3DHSharedSecret is the output of a successful X3DH key agreement.
type X3DHSharedSecret struct {
	SharedSecret [32]byte
	AD           []byte // associated data: IK_A || IK_B
}

// InitiateX3DH performs X3DH as the initiator (Alice).
// Returns the shared secret and the InitialMessage to send to the recipient.
func InitiateX3DH(
	senderIK *IdentityKeyPair,
	recipientBundle *PreKeyBundle,
) (*X3DHSharedSecret, *InitialMessage, error) {
	// Validate recipient bundle
	if !VerifyPreKey(recipientBundle.IdentitySignKey, recipientBundle.SignedPreKey.PublicKey, recipientBundle.SignedPreKey.Signature) {
		return nil, nil, fmt.Errorf("signal: signed prekey signature verification failed")
	}

	// Generate ephemeral key pair
	ek, err := GenerateDHKeyPair()
	if err != nil {
		return nil, nil, err
	}

	// Compute DH outputs
	// DH1 = DH(IK_A, SPK_B)
	dh1, err := DH(senderIK.PrivateKey, recipientBundle.SignedPreKey.PublicKey)
	if err != nil {
		return nil, nil, fmt.Errorf("signal: x3dh dh1: %w", err)
	}
	// DH2 = DH(EK_A, IK_B)
	dh2, err := DH(ek.PrivateKey, recipientBundle.IdentityKey)
	if err != nil {
		return nil, nil, fmt.Errorf("signal: x3dh dh2: %w", err)
	}
	// DH3 = DH(EK_A, SPK_B)
	dh3, err := DH(ek.PrivateKey, recipientBundle.SignedPreKey.PublicKey)
	if err != nil {
		return nil, nil, fmt.Errorf("signal: x3dh dh3: %w", err)
	}

	// Concatenate DH material
	dhMaterial := make([]byte, 0, 128)
	dhMaterial = append(dhMaterial, dh1[:]...)
	dhMaterial = append(dhMaterial, dh2[:]...)
	dhMaterial = append(dhMaterial, dh3[:]...)

	var recipientOPKID *uint32
	if recipientBundle.OneTimePreKey != nil {
		// DH4 = DH(EK_A, OPK_B)
		dh4, err := DH(ek.PrivateKey, recipientBundle.OneTimePreKey.PublicKey)
		if err != nil {
			return nil, nil, fmt.Errorf("signal: x3dh dh4: %w", err)
		}
		dhMaterial = append(dhMaterial, dh4[:]...)
		id := recipientBundle.OneTimePreKey.KeyID
		recipientOPKID = &id
	}

	// AD = IK_A_pub || IK_B_pub
	ad := make([]byte, 64)
	copy(ad[:32], senderIK.PublicKey[:])
	copy(ad[32:], recipientBundle.IdentityKey[:])

	// Derive shared secret via HKDF-SHA256
	secret, err := x3dhKDF(dhMaterial, ad)
	if err != nil {
		return nil, nil, err
	}

	msg := &InitialMessage{
		RegistrationID:    RegistrationID(senderIK.PublicKey),
		SenderIdentityKey: senderIK.PublicKey,
		SenderSignKey:     []byte(senderIK.SignPublic),
		EphemeralKey:      ek.PublicKey,
		RecipientSPKID:    recipientBundle.SignedPreKey.KeyID,
		RecipientOPKID:    recipientOPKID,
	}
	return &X3DHSharedSecret{SharedSecret: secret, AD: ad}, msg, nil
}

// RespondX3DH performs X3DH as the recipient (Bob).
// recipientSignedPreKey must correspond to msg.RecipientSPKID.
// recipientOPK must correspond to msg.RecipientOPKID (nil if not used).
func RespondX3DH(
	recipientIK *IdentityKeyPair,
	recipientSPK *SignedPreKey,
	recipientOPK *OneTimePreKey,
	msg *InitialMessage,
) (*X3DHSharedSecret, error) {
	if recipientSPK.KeyID != msg.RecipientSPKID {
		return nil, fmt.Errorf("signal: signed prekey ID mismatch: got %d want %d",
			recipientSPK.KeyID, msg.RecipientSPKID)
	}

	// DH1 = DH(SPK_B, IK_A)
	dh1, err := DH(recipientSPK.KeyPair.PrivateKey, msg.SenderIdentityKey)
	if err != nil {
		return nil, fmt.Errorf("signal: x3dh respond dh1: %w", err)
	}
	// DH2 = DH(IK_B, EK_A)
	dh2, err := DH(recipientIK.PrivateKey, msg.EphemeralKey)
	if err != nil {
		return nil, fmt.Errorf("signal: x3dh respond dh2: %w", err)
	}
	// DH3 = DH(SPK_B, EK_A)
	dh3, err := DH(recipientSPK.KeyPair.PrivateKey, msg.EphemeralKey)
	if err != nil {
		return nil, fmt.Errorf("signal: x3dh respond dh3: %w", err)
	}

	dhMaterial := make([]byte, 0, 128)
	dhMaterial = append(dhMaterial, dh1[:]...)
	dhMaterial = append(dhMaterial, dh2[:]...)
	dhMaterial = append(dhMaterial, dh3[:]...)

	if msg.RecipientOPKID != nil {
		if recipientOPK == nil {
			return nil, fmt.Errorf("signal: one-time prekey required but not provided")
		}
		if recipientOPK.KeyID != *msg.RecipientOPKID {
			return nil, fmt.Errorf("signal: OPK ID mismatch")
		}
		// DH4 = DH(OPK_B, EK_A)
		dh4, err := DH(recipientOPK.KeyPair.PrivateKey, msg.EphemeralKey)
		if err != nil {
			return nil, fmt.Errorf("signal: x3dh respond dh4: %w", err)
		}
		dhMaterial = append(dhMaterial, dh4[:]...)
	}

	// AD = IK_A_pub || IK_B_pub
	ad := make([]byte, 64)
	copy(ad[:32], msg.SenderIdentityKey[:])
	copy(ad[32:], recipientIK.PublicKey[:])

	secret, err := x3dhKDF(dhMaterial, ad)
	if err != nil {
		return nil, err
	}
	return &X3DHSharedSecret{SharedSecret: secret, AD: ad}, nil
}

// x3dhKDF derives a 32-byte key from DH material using HKDF-SHA256.
// salt = AD (associated data), info = x3dhInfo
func x3dhKDF(dhMaterial, salt []byte) ([32]byte, error) {
	r := hkdf.New(sha256.New, dhMaterial, salt, []byte(x3dhInfo))
	var out [32]byte
	if _, err := io.ReadFull(r, out[:]); err != nil {
		return [32]byte{}, fmt.Errorf("signal: x3dh kdf: %w", err)
	}
	return out, nil
}
