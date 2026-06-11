package signalclient

import (
	"crypto/sha512"
	"encoding/binary"
	"fmt"
	"strings"
)

// SafetyNumbers computes Signal-style safety numbers for a pair of identity keys.
// Returns a 60-digit string formatted in groups of 5.
// Both parties must compare these out-of-band to verify identity (no MITM).
func SafetyNumbers(localDID string, localIK [32]byte, remoteDID string, remoteIK [32]byte) string {
	a := safetyChunk(localDID, localIK)
	b := safetyChunk(remoteDID, remoteIK)

	// Combine in lexicographic order for determinism
	if localDID < remoteDID {
		return formatSafetyNumbers(a) + " " + formatSafetyNumbers(b)
	}
	return formatSafetyNumbers(b) + " " + formatSafetyNumbers(a)
}

// safetyChunk computes a 30-digit safety number chunk for one party.
// Algorithm: 5120 iterations of SHA-512 over (public_key || did)
func safetyChunk(did string, ik [32]byte) []byte {
	h := sha512.New()
	chunk := make([]byte, 32+len(did))
	copy(chunk[:32], ik[:])
	copy(chunk[32:], did)

	data := chunk
	for i := 0; i < 5120; i++ {
		h.Reset()
		h.Write(data)
		data = h.Sum(nil)
	}
	// Take first 30 bytes, convert to 5-digit groups
	return data[:30]
}

// formatSafetyNumbers converts 30 bytes to a 30-digit string in 5-digit groups.
func formatSafetyNumbers(data []byte) string {
	// Each 5 bytes → one 5-digit decimal number (0-99999)
	groups := make([]string, 6)
	for i := 0; i < 6; i++ {
		chunk := data[i*5 : i*5+5]
		n := binary.BigEndian.Uint64(append(make([]byte, 3), chunk...))
		n = n % 100000
		groups[i] = fmt.Sprintf("%05d", n)
	}
	return strings.Join(groups, " ")
}

// ErrKeyNotFound is returned when a key is not found in the store.
var ErrKeyNotFound = fmt.Errorf("signal: key not found")
