# wproto — W Protocol

AT Protocol + Signal Protocol over Bytecode Alliance wRPC/WIT + MDAG content-addressed sync.

## Protocol Coverage

### Summary

| Protocol | Coverage | Status |
|---|---|---|
| **AT Protocol** | **78%** | WIT + types + record mapping complete. wRPC dispatch / XRPC host pending |
| **Signal Protocol** | **45%** → **65%** | Decision engine + session manager + PreKey types. Crypto via yata-signal |
| **Matrix Protocol** | **0%** (by design) | W Protocol replaces Matrix with AT + Signal |

### AT Protocol

| Feature | Status | Implementation |
|---|---|---|
| **Identity** | | |
| DID identifier (did:plc / did:web) | ✅ | `WEnvelope.sender_did`, `WChannel.creator_did` |
| DID Document resolution | ⬜ | Delegated to yata-at / at-client |
| DID generation / registration | ⬜ | Delegated to at-provisioning WIT |
| **Repository** | | |
| Record CRUD (create/get/list/delete) | ✅ | WIT `w-command` (17 functions) |
| Collection NSID mapping | ✅ | `RecordMapper::kind_to_collection` |
| AT URI generation | ✅ | `RecordMapper::at_uri` |
| Record rkey (TID) | ✅ | `WEnvelope.rkey` |
| Record CID (content hash) | ✅ | MDAG Blake3 CID |
| Lexicon JSON output | ✅ | `RecordMapper::kind_to_collection` (derived) |
| CBOR (dag-cbor) encoding | ✅ | `RecordMapper::envelope_to_cbor` (primary) |
| Blob upload | ✅ | WIT IPFS interface |
| **Event Stream** | | |
| Inbound event subscription | ✅ | WIT `w-handler.handle` + yata-log subscription |
| Event commit receive | ✅ | `handleEnvelope()` callback |
| Outbound event broadcast | ✅ | yata-log append on commit (yata-native, not AT Firehose) |
| Collection filter | ✅ | `RecordMapper::builtin_collections()` (8 collections) |
| **Federation** | | |
| Cross-instance sync | ✅ | WIT `w-federation` (5 functions) |
| MDAG Merkle diff | ✅ | `w_diff()` — O(changed kinds) |
| CAS block transfer | ✅ | `BlockTransfer`, `fetch-blocks` |
| State announce (broadcast) | ✅ | `NatsSubjects::federation_announce()` |
| wRPC QUIC transport | 🔶 | Design only (`Target::Federation`) |
| **Provisioning** | | |
| EnsureATService | ⬜ | Delegated to at-provisioning WIT |
| EnsureATBotUser | ⬜ | Delegated to at-provisioning WIT |
| EnsureATChannel | ✅ | `w-command.create-channel` (host auto-provision) |
| Clerk service user binding | ⬜ | Delegated to authn WIT |

### Signal Protocol

| Feature | Status | Implementation |
|---|---|---|
| **Key Exchange (X3DH)** | | |
| PreKey Bundle type | ✅ | `WPreKeyBundle` (8 fields: IK, SPK, SPK_sig, OPK) |
| PreKey registration | ✅ | WIT `register-prekeys` |
| PreKey query (single) | ✅ | WIT `get-prekey-bundle` |
| PreKey batch query | ✅ | WIT `get-prekey-bundles` |
| OPK replenishment | ✅ | WIT `replenish-otpks` |
| X3DH initiate (DH1‖DH2‖DH3‖DH4) | ✅ | `SessionManager::encrypt_1to1` → `yata_signal::x3dh_initiate` |
| X3DH respond | ✅ | `SessionManager::decrypt_1to1` via yata-signal |
| **Double Ratchet (1:1)** | | |
| Session init (sender) | ✅ | `SessionManager::encrypt_1to1` → `yata_signal::ratchet_init_sender` |
| Session init (receiver) | ✅ | `SessionManager::decrypt_1to1` |
| Ratchet encrypt | ✅ | `SessionManager::encrypt` → `yata_signal::ratchet_encrypt` |
| Ratchet decrypt | ✅ | `SessionManager::decrypt` → `yata_signal::ratchet_decrypt` |
| Session state persistence | ✅ | yata-kv bucket `_w_signal_sessions` |
| **Sender Keys (group)** | | |
| Group session init | ✅ | `SessionManager::encrypt_group` → `yata_signal::group_init_sender` |
| SenderKey distribution | 🔶 | Via 1:1 session (design, not wired) |
| Group encrypt | ✅ | `SessionManager::encrypt_group` → `yata_signal::group_encrypt` |
| Group decrypt | ✅ | `SessionManager::decrypt_group` → `yata_signal::group_decrypt` |
| Group key rotation | ✅ | `SessionManager::rotate_group_key` + WIT `rotate-group-key` |
| **Encryption Routing** | | |
| Auto-encrypt decision | ✅ | `AutoCrypto::decide_encrypt` (4 paths) |
| Auto-decrypt decision | ✅ | `AutoCrypto::decide_decrypt` |
| Channel default encryption | ✅ | `ChannelKind::default_encryption` |
| Bot vs Human detection | ✅ | `sender_is_bot` / `receiver_is_bot` |
| contentType detection | ✅ | `application/x-signal-envelope` |
| **Identity & Device** | | |
| Bot identity key generation | ✅ | `SessionManager::get_or_create_identity` (yata-kv) |
| Device ID tracking | 🔶 | `WPreKeyBundle.device_id` (type only) |
| Multi-device session | ⬜ | Not implemented |

### Matrix Protocol (Functional Equivalence)

W Protocol does NOT implement Matrix wire protocol. It provides functional equivalence via AT + Signal.

| Matrix Feature | W Protocol Equivalent | Notes |
|---|---|---|
| Room | `WChannel` | AT DID binding, MDAG commit chain |
| m.room.message | `WEnvelope { kind: "message" }` | Content-addressed (Blake3 CID) |
| m.room.create | `w-command.create-channel` | |
| m.room.name / m.room.topic | `WChannel.name` / `.description` | |
| m.room.member | `WMember` + `join/leave/invite` | AT Record backed |
| m.room.redaction | `w-command.redact` | AT Record tombstone |
| m.reaction | `w-command.react/unreact` | Separate envelope kind |
| m.read (receipts) | `w-command.mark-read` | Per-channel last-rkey |
| m.presence | `WPresence` + `w-command.update-presence` | |
| m.room.encryption | `EncryptionState` per channel | Signal (not Olm/Megolm) |
| Power levels | `MemberRole` (Owner/Admin/Member) | |
| /sync | yata-log subscription (push) | Not long-poll |
| Timeline pagination | `w-query.list-envelopes(before/after)` | |
| State resolution | MDAG commit chain | Time-travel, Merkle diff |
| Olm (1:1) | Signal X3DH + Double Ratchet | Forward secrecy |
| Megolm (group) | Signal Sender Keys | |
| Key sharing | Signal PreKey exchange | |
| Server federation | wRPC `w-federation` + MDAG | O(changed) delta |
| Homeserver discovery | AT Protocol DID resolution | |
| Event signing | MDAG Blake3 CID | Deterministic |
| m.typing | ⬜ **Not implemented** | Candidate: `w-command.typing` |
| Voice/Video (VoIP) | ⬜ **Not implemented** | Candidate: `w-command.call-*` |
| Spaces (hierarchy) | ⬜ **Not implemented** | Candidate: channel hierarchy |
| Threads (MSC3440) | ✅ `thread_id` + `reply_to` | REPLY_TO graph edge |

### Implementation Status

| Module | Lines | Status | Tests |
|---|---|---|---|
| `types.rs` | 169 | ✅ Complete | — |
| `blocks.rs` | 206 | ✅ Complete | 5 |
| `crypto.rs` | 182 | ✅ Complete | 7 |
| `record.rs` | 272 | ✅ Complete | 8 |
| `commit.rs` | 378 | ✅ Complete | 4 |
| `diff.rs` | 277 | ✅ Complete | 4 |
| `session.rs` | 260 | ✅ Complete | — |
| `pipeline.rs` | ~300 | ✅ Complete | — |
| `channel.rs` | ~200 | ✅ Complete | — |
| `serve.rs` | 136 | 🔶 Routing only | 4 |
| `invoke.rs` | 82 | 🔶 Types only | 2 |
| `transport.rs` | 123 | 🔶 Subjects only | 5 |
| `w.wit` | 232 | ✅ Complete | — |
| **Total** | **~2,800** | | **40+** |

## Architecture

```
Layer 5: App          — WSend / WQuery (1 call)
Layer 4: W Protocol   — Pipeline (crypto → MDAG → KV → broadcast)
Layer 3: Identity     — DID + Clerk
Layer 2: Encryption   — Signal (yata-signal) via SessionManager
Layer 1: Transport    — yata-wrpc (embedded, 583µs) / wRPC QUIC (federation)
Layer 0: Storage      — yata broker (CAS + KV + Log + Lance + Raft)
```

## Wire Format (3 layers)

| Layer | Format | Purpose |
|---|---|---|
| wRPC wire | Component Model binary | RPC dispatch (Invoke/Serve) |
| MDAG CAS | CBOR (Blake3 CID) | Content-addressed storage, federation diff |
| AT Lexicon | JSON (camelCase) | AT Protocol federation surface (derived only) |
