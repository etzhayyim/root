//! W Protocol: AT Protocol + Signal Protocol over Bytecode Alliance wRPC.
//!
//! # Modules
//!
//! | Module | Purpose |
//! |--------|---------|
//! | `pipeline` | Core orchestrator: send → crypto → MDAG → KV → broadcast |
//! | `channel` | Channel/member/envelope state: MDAG + KV backed |
//! | `session` | Signal session management: bridges AutoCrypto → yata-signal |
//! | `crypto` | Encryption decision engine (no crypto ops, stateless) |
//! | `blocks` | MDAG CBOR blocks (EnvelopeBlock, WRootBlock, etc.) |
//! | `commit` | Channel-scoped MDAG commit chain (time-travel, history) |
//! | `diff` | Merkle diff O(changed kinds) between commits |
//! | `record` | CBOR primary + Lexicon JSON derived. kind → AT NSID |
//! | `types` | WEnvelope, WChannel, WMember, EncryptionState |
//! | `serve` | wRPC Serve routing constants |
//! | `invoke` | wRPC Invoke federation helpers |
//! | `at` | AT Protocol re-exports (AtClient, AtFirehose, etc.) |
//! | `signal` | Signal Protocol re-exports (X3DH, Ratchet, SenderKey, host_api) |
//! | `firehose` | WFirehoseBridge — AT Firehose → W Protocol ingest |
//! | `transport` | NATS subject mapping, Target enum |

pub mod at;
pub mod blocks;
pub mod channel;
pub mod commit;
pub mod crypto;
pub mod diff;
pub mod error;
pub mod firehose;
pub mod invoke;
pub mod pipeline;
pub mod record;
pub mod serve;
pub mod session;
pub mod signal;
pub mod transport;
pub mod types;

pub use blocks::{
    ChannelRootBlock, EnvelopeBlock, EnvelopeGroupBlock, MemberBlock, WRootBlock,
};
pub use channel::{ChannelStore, CypherExecutor};
pub use commit::WCommitLog;
pub use crypto::{AutoCrypto, CryptoDecision};
pub use diff::{w_diff, WDiff};
pub use error::{Result, WProtoError};
pub use invoke::{BlockTransfer, FederationInvoke, SyncRequest, SyncResult};
pub use pipeline::WPipeline;
pub use record::RecordMapper;
pub use serve::{WrpcContext, WrpcRouter};
pub use session::{SessionManager, EncryptedPayload, DecryptedPayload};
pub use transport::{NatsSubjects, Target};
pub use types::*;
