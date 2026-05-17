package signalclient

// SignalStore is the interface for persisting Signal Protocol key material.
// Implementations must be goroutine-safe.
type SignalStore interface {
	IdentityStore
	PreKeyStore
	SignedPreKeyStore
	SessionStore
	GroupSessionStore
}

// IdentityStore manages identity keys.
type IdentityStore interface {
	// GetIdentityKeyPair returns the local device identity key pair.
	GetIdentityKeyPair() (*IdentityKeyPair, error)

	// SaveIdentity persists a remote identity public key for a DID.
	// Returns true if the identity changed (possible key change attack warning).
	SaveIdentity(did string, identityKey [32]byte) (bool, error)

	// GetIdentity retrieves a saved remote identity public key.
	GetIdentity(did string) ([32]byte, bool, error)

	// IsTrustedIdentity returns true if the identity key is trusted for the given DID.
	IsTrustedIdentity(did string, identityKey [32]byte) (bool, error)
}

// PreKeyStore manages one-time prekeys.
type PreKeyStore interface {
	// StorePreKey persists a one-time prekey.
	StorePreKey(keyID uint32, kp *OneTimePreKey) error

	// LoadPreKey retrieves a one-time prekey by ID.
	LoadPreKey(keyID uint32) (*OneTimePreKey, error)

	// RemovePreKey deletes a one-time prekey (after use).
	RemovePreKey(keyID uint32) error

	// AvailablePreKeyCount returns the count of remaining one-time prekeys.
	AvailablePreKeyCount() (int, error)
}

// SignedPreKeyStore manages signed prekeys.
type SignedPreKeyStore interface {
	// StoreSignedPreKey persists a signed prekey.
	StoreSignedPreKey(keyID uint32, spk *SignedPreKey) error

	// LoadSignedPreKey retrieves a signed prekey by ID.
	LoadSignedPreKey(keyID uint32) (*SignedPreKey, error)

	// CurrentSignedPreKeyID returns the ID of the active signed prekey.
	CurrentSignedPreKeyID() (uint32, error)
}

// SessionStore manages Double Ratchet sessions.
type SessionStore interface {
	// LoadSession retrieves a Double Ratchet session for a remote DID + device.
	LoadSession(did string, deviceID uint32) (*Session, error)

	// StoreSession persists a Double Ratchet session.
	StoreSession(did string, deviceID uint32, session *Session) error

	// DeleteSession removes a session.
	DeleteSession(did string, deviceID uint32) error

	// GetSubDeviceIDs returns all device IDs with active sessions for a DID.
	GetSubDeviceIDs(did string) ([]uint32, error)
}

// GroupSessionStore manages Sender Key group sessions.
type GroupSessionStore interface {
	// StoreGroupSession persists a GroupSession.
	StoreGroupSession(groupID string, session *GroupSession) error

	// LoadGroupSession retrieves a GroupSession by group ID.
	LoadGroupSession(groupID string) (*GroupSession, error)

	// StoreSenderKeyDistribution persists a received distribution message.
	StoreSenderKeyDistribution(groupID, senderDID string, msg *SenderKeyDistributionMessage) error

	// LoadSenderKeyDistributions retrieves all known distributions for a group.
	LoadSenderKeyDistributions(groupID string) (map[string]*SenderKeyDistributionMessage, error)
}

// InMemorySignalStore is a non-persistent in-memory implementation for testing.
type InMemorySignalStore struct {
	identityKP   *IdentityKeyPair
	identities   map[string][32]byte
	preKeys      map[uint32]*OneTimePreKey
	signedPreKeys map[uint32]*SignedPreKey
	currentSPKID uint32
	sessions     map[string]*Session
	groupSessions map[string]*GroupSession
	distributions map[string]map[string]*SenderKeyDistributionMessage
}

// NewInMemorySignalStore creates an in-memory store with a fresh identity key.
func NewInMemorySignalStore() (*InMemorySignalStore, error) {
	ik, err := GenerateIdentityKeyPair()
	if err != nil {
		return nil, err
	}
	return &InMemorySignalStore{
		identityKP:    ik,
		identities:    make(map[string][32]byte),
		preKeys:       make(map[uint32]*OneTimePreKey),
		signedPreKeys: make(map[uint32]*SignedPreKey),
		sessions:      make(map[string]*Session),
		groupSessions: make(map[string]*GroupSession),
		distributions: make(map[string]map[string]*SenderKeyDistributionMessage),
	}, nil
}

func (s *InMemorySignalStore) GetIdentityKeyPair() (*IdentityKeyPair, error) {
	return s.identityKP, nil
}

func (s *InMemorySignalStore) SaveIdentity(did string, ik [32]byte) (bool, error) {
	old, ok := s.identities[did]
	changed := ok && old != ik
	s.identities[did] = ik
	return changed, nil
}

func (s *InMemorySignalStore) GetIdentity(did string) ([32]byte, bool, error) {
	ik, ok := s.identities[did]
	return ik, ok, nil
}

func (s *InMemorySignalStore) IsTrustedIdentity(did string, ik [32]byte) (bool, error) {
	stored, ok := s.identities[did]
	if !ok {
		return true, nil // first time: trust on first use
	}
	return stored == ik, nil
}

func (s *InMemorySignalStore) StorePreKey(keyID uint32, kp *OneTimePreKey) error {
	s.preKeys[keyID] = kp
	return nil
}

func (s *InMemorySignalStore) LoadPreKey(keyID uint32) (*OneTimePreKey, error) {
	kp, ok := s.preKeys[keyID]
	if !ok {
		return nil, ErrKeyNotFound
	}
	return kp, nil
}

func (s *InMemorySignalStore) RemovePreKey(keyID uint32) error {
	delete(s.preKeys, keyID)
	return nil
}

func (s *InMemorySignalStore) AvailablePreKeyCount() (int, error) {
	return len(s.preKeys), nil
}

func (s *InMemorySignalStore) StoreSignedPreKey(keyID uint32, spk *SignedPreKey) error {
	s.signedPreKeys[keyID] = spk
	s.currentSPKID = keyID
	return nil
}

func (s *InMemorySignalStore) LoadSignedPreKey(keyID uint32) (*SignedPreKey, error) {
	spk, ok := s.signedPreKeys[keyID]
	if !ok {
		return nil, ErrKeyNotFound
	}
	return spk, nil
}

func (s *InMemorySignalStore) CurrentSignedPreKeyID() (uint32, error) {
	return s.currentSPKID, nil
}

func (s *InMemorySignalStore) LoadSession(did string, deviceID uint32) (*Session, error) {
	sess, ok := s.sessions[sessionKey(did, deviceID)]
	if !ok {
		return nil, ErrKeyNotFound
	}
	return sess, nil
}

func (s *InMemorySignalStore) StoreSession(did string, deviceID uint32, sess *Session) error {
	s.sessions[sessionKey(did, deviceID)] = sess
	return nil
}

func (s *InMemorySignalStore) DeleteSession(did string, deviceID uint32) error {
	delete(s.sessions, sessionKey(did, deviceID))
	return nil
}

func (s *InMemorySignalStore) GetSubDeviceIDs(did string) ([]uint32, error) {
	prefix := did + ":"
	var ids []uint32
	for k := range s.sessions {
		if len(k) > len(prefix) && k[:len(prefix)] == prefix {
			var id uint32
			_, _ = parseDeviceID(k[len(prefix):], &id)
			ids = append(ids, id)
		}
	}
	return ids, nil
}

func (s *InMemorySignalStore) StoreGroupSession(groupID string, sess *GroupSession) error {
	s.groupSessions[groupID] = sess
	return nil
}

func (s *InMemorySignalStore) LoadGroupSession(groupID string) (*GroupSession, error) {
	sess, ok := s.groupSessions[groupID]
	if !ok {
		return nil, ErrKeyNotFound
	}
	return sess, nil
}

func (s *InMemorySignalStore) StoreSenderKeyDistribution(groupID, senderDID string, msg *SenderKeyDistributionMessage) error {
	if s.distributions[groupID] == nil {
		s.distributions[groupID] = make(map[string]*SenderKeyDistributionMessage)
	}
	s.distributions[groupID][senderDID] = msg
	return nil
}

func (s *InMemorySignalStore) LoadSenderKeyDistributions(groupID string) (map[string]*SenderKeyDistributionMessage, error) {
	return s.distributions[groupID], nil
}

func sessionKey(did string, deviceID uint32) string {
	return did + ":" + uint32str(deviceID)
}

func uint32str(n uint32) string {
	b := make([]byte, 0, 10)
	if n == 0 {
		return "0"
	}
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	return string(b)
}

func parseDeviceID(s string, out *uint32) (bool, error) {
	var n uint32
	for _, c := range s {
		if c < '0' || c > '9' {
			return false, nil
		}
		n = n*10 + uint32(c-'0')
	}
	*out = n
	return true, nil
}
