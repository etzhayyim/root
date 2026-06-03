// Package lexicons defines AT Protocol Lexicon record types for the etzhayyim SpinApp platform.
// Namespace: com.etzhayyim.*
package lexicons

import "time"

// Lexicon collection IDs
const (
	LexiconChannel          = "com.etzhayyim.conversation.channel"
	LexiconMessage          = "com.etzhayyim.conversation.message"
	LexiconMembership       = "com.etzhayyim.conversation.membership"
	LexiconAppService       = "com.etzhayyim.app.service"
	LexiconBotUser          = "com.etzhayyim.app.botUser"
	LexiconPreKeyBundle     = "com.etzhayyim.signal.preKeyBundle"
	LexiconDeviceState      = "com.etzhayyim.signal.deviceState"
	LexiconCommand          = "com.etzhayyim.command"
	LexiconCommandResult    = "com.etzhayyim.command.result"
	LexiconShinshiImagePost = "com.etzhayyim.shinshi.imagePost"
)

// ShinshiImagePost is the AT Lexicon record for a shinshi image post.
// Created in the model's DID repo when an image is uploaded or generated.
// The blob ref points to data stored via com.atproto.repo.uploadBlob.
// rkey assigned by PDS.
type ShinshiImagePost struct {
	Type        string         `json:"$type"`
	Blob        map[string]any `json:"blob"`      // {$type:"blob", ref:{$link:cid}, mimeType, size}
	Title       string         `json:"title,omitempty"`
	Prompt      string         `json:"prompt,omitempty"`
	ModelID     string         `json:"modelId,omitempty"`
	Source      string         `json:"source"`    // "upload"|"local-llm"|"huggingface"|"external-api"
	UploaderDID string         `json:"uploaderDid,omitempty"`
	Tags        []string       `json:"tags,omitempty"`
	Width       int            `json:"width,omitempty"`
	Height      int            `json:"height,omitempty"`
	CreatedAt   time.Time      `json:"createdAt"`
}

// VisibilityPublic, VisibilityPrivate, VisibilitySecret are channel visibility levels.
const (
	VisibilityPublic  = "public"
	VisibilityPrivate = "private"
	VisibilitySecret  = "secret"
)

// Channel is the AT Lexicon record for a SpinApp conversation channel.
// Replaces Matrix room. rkey = nanoid.
type Channel struct {
	Type              string    `json:"$type"`
	Name              string    `json:"name"`
	Description       string    `json:"description,omitempty"`
	Visibility        string    `json:"visibility"` // public|private|secret
	AppID             string    `json:"appId"`
	CreatedBy         string    `json:"createdBy"` // DID
	EncryptionEnabled bool      `json:"encryptionEnabled"`
	CreatedAt         time.Time `json:"createdAt"`
}

// NewChannel creates a Channel record.
func NewChannel(name, appID, createdBy, visibility string, encrypted bool) *Channel {
	return &Channel{
		Type:              LexiconChannel,
		Name:              name,
		Visibility:        visibility,
		AppID:             appID,
		CreatedBy:         createdBy,
		EncryptionEnabled: encrypted,
		CreatedAt:         time.Now().UTC(),
	}
}

// Message is the AT Lexicon record for a SpinApp message.
// Replaces Matrix m.room.message. rkey = TID (timestamp-based).
type Message struct {
	Type          string    `json:"$type"`
	ChannelID     string    `json:"channelId"`     // CID of channel record
	Body          string    `json:"body,omitempty"`
	BodyFormat    string    `json:"bodyFormat"`    // plain|markdown
	EncryptedBody []byte    `json:"encryptedBody,omitempty"` // Signal ciphertext
	ReplyTo       string    `json:"replyTo,omitempty"`       // rkey
	ThreadRoot    string    `json:"threadRoot,omitempty"`    // rkey
	CreatedAt     time.Time `json:"createdAt"`
}

// NewPlaintextMessage creates a plaintext Message record.
func NewPlaintextMessage(channelID, body, replyTo, threadRoot string) *Message {
	return &Message{
		Type:       LexiconMessage,
		ChannelID:  channelID,
		Body:       body,
		BodyFormat: "plain",
		ReplyTo:    replyTo,
		ThreadRoot: threadRoot,
		CreatedAt:  time.Now().UTC(),
	}
}

// NewEncryptedMessage creates an encrypted Message record.
func NewEncryptedMessage(channelID string, ciphertext []byte, replyTo, threadRoot string) *Message {
	return &Message{
		Type:          LexiconMessage,
		ChannelID:     channelID,
		EncryptedBody: ciphertext,
		ReplyTo:       replyTo,
		ThreadRoot:    threadRoot,
		CreatedAt:     time.Now().UTC(),
	}
}

// Membership is the AT Lexicon record for channel membership.
// rkey = "{channelRKey}:{memberDID}" (URL-safe encoded)
type Membership struct {
	Type      string    `json:"$type"`
	ChannelID string    `json:"channelId"` // CID of channel
	Member    string    `json:"member"`    // DID
	Role      string    `json:"role"`      // admin|mod|member
	JoinedAt  time.Time `json:"joinedAt"`
}

// RoleAdmin, RoleMod, RoleMember are membership roles.
const (
	RoleAdmin  = "admin"
	RoleMod    = "mod"
	RoleMember = "member"
)

// NewMembership creates a Membership record.
func NewMembership(channelID, memberDID, role string) *Membership {
	return &Membership{
		Type:      LexiconMembership,
		ChannelID: channelID,
		Member:    memberDID,
		Role:      role,
		JoinedAt:  time.Now().UTC(),
	}
}

// AppService is the AT Lexicon record for a SpinApp bot service registration.
// Replaces Matrix Application Service. rkey = appId.
type AppService struct {
	Type      string `json:"$type"`
	AppID     string `json:"appId"`
	Handle    string `json:"handle"`
	BotDID    string `json:"botDid"`
	Namespace string `json:"namespace"` // AT Lexicon namespace prefix
	PDSUrl    string `json:"pdsUrl"`
}

// BotUser is the AT Lexicon record for a SpinApp agent identity.
// Replaces Matrix bot user. rkey = agentId.
type BotUser struct {
	Type          string `json:"$type"`
	AgentID       string `json:"agentId"`
	ActorID       string `json:"actorId"`
	AppID         string `json:"appId"`
	DID           string `json:"did"`
	DisplayName   string `json:"displayName"`
	ClerkUserID   string `json:"clerkUserId"` // service_user_id binding (CRITICAL)
}

// PreKeyBundle is the AT Lexicon record for a Signal Protocol PreKey Bundle.
// Published by each device so senders can establish X3DH sessions.
// rkey = "{did}:{deviceId}"
type PreKeyBundle struct {
	Type           string              `json:"$type"`
	RegistrationID uint32              `json:"registrationId"`
	DeviceID       uint32              `json:"deviceId"`
	IdentityKey    []byte              `json:"identityKey"`  // X25519 public key (32 bytes)
	IdentitySignKey []byte             `json:"identitySignKey"` // Ed25519 public key (32 bytes)
	SignedPreKey   SignedPreKeyRecord   `json:"signedPreKey"`
	OneTimePreKeys []OneTimePreKeyRecord `json:"oneTimePreKeys"`
	PublishedAt    time.Time           `json:"publishedAt"`
}

// SignedPreKeyRecord is the public portion of a signed prekey.
type SignedPreKeyRecord struct {
	KeyID     uint32 `json:"keyId"`
	PublicKey []byte `json:"publicKey"`  // X25519 public (32 bytes)
	Signature []byte `json:"signature"`  // Ed25519 signature (64 bytes)
}

// OneTimePreKeyRecord is the public portion of a one-time prekey.
type OneTimePreKeyRecord struct {
	KeyID     uint32 `json:"keyId"`
	PublicKey []byte `json:"publicKey"`  // X25519 public (32 bytes)
}

// Command is the AT Lexicon record for a SpinApp command event.
// Replaces Matrix org.etzhayyim.command.* event. rkey = commandId.
type Command struct {
	Type          string    `json:"$type"`
	LexiconID     string    `json:"lexiconId"`     // e.g. "com.etzhayyim.command.updateProfile"
	CommandID     string    `json:"commandId"`
	AggregateID   string    `json:"aggregateId"`
	CausationID   string    `json:"causationId,omitempty"`
	CorrelationID string    `json:"correlationId,omitempty"`
	ChannelID     string    `json:"channelId"`     // channel CID
	ThreadRKey    string    `json:"threadRKey,omitempty"`
	ConversationID string   `json:"conversationId,omitempty"`
	Payload       []byte    `json:"payload"`       // JSON-encoded command payload
	CreatedAt     time.Time `json:"createdAt"`
}
