//! W Protocol Signal session management.
//!
//! Directly integrates yata-signal crypto operations via `SignalStorage`.
//! No intermediate trait — SessionManager owns crypto + persistence.

use std::sync::Arc;

use yata_signal::store::SignalStorage;
use yata_signal::{GroupSession, IdentityKeyPair, RatchetSession};

use crate::crypto::CryptoDecision;
use crate::error::{Result, WProtoError};
use crate::types::{EncryptionState, WChannel, WPreKeyBundle};

/// Encrypted payload result.
pub struct EncryptedPayload {
    pub ciphertext: Vec<u8>,
    pub sender_device_id: String,
    pub encryption: EncryptionState,
}

/// Decrypted payload result.
pub struct DecryptedPayload {
    pub plaintext: Vec<u8>,
}

const RATCHET_SESSIONS: &str = "signal.ratchet_sessions";
const GROUP_SESSIONS: &str = "signal.group_sessions";
const PREKEY_BUNDLES: &str = "signal.prekey_bundles";

/// W Protocol session manager — directly uses yata-signal crypto + SignalStorage.
pub struct SessionManager {
    storage: Arc<dyn SignalStorage>,
    identity: IdentityKeyPair,
    bot_did: String,
}

impl SessionManager {
    pub fn new(storage: Arc<dyn SignalStorage>, identity: IdentityKeyPair, bot_did: String) -> Self {
        Self {
            storage,
            identity,
            bot_did,
        }
    }

    pub fn bot_did(&self) -> &str {
        &self.bot_did
    }

    pub fn identity(&self) -> &IdentityKeyPair {
        &self.identity
    }

    /// Execute encryption based on AutoCrypto decision.
    pub async fn encrypt(
        &self,
        decision: &CryptoDecision,
        plaintext: &[u8],
        _channel: &WChannel,
    ) -> Result<EncryptedPayload> {
        match decision {
            CryptoDecision::Passthrough => Ok(EncryptedPayload {
                ciphertext: plaintext.to_vec(),
                sender_device_id: String::new(),
                encryption: EncryptionState::Plaintext,
            }),
            CryptoDecision::ClientEncrypted => Ok(EncryptedPayload {
                ciphertext: plaintext.to_vec(),
                sender_device_id: String::new(),
                encryption: EncryptionState::ClientEncrypted,
            }),
            CryptoDecision::HostEncrypt1to1 { peer_did } => {
                if peer_did.is_empty() {
                    return Err(WProtoError::Signal(
                        "peer_did must be pre-resolved for 1:1 encryption".into(),
                    ));
                }
                let ct = self.encrypt_1to1(peer_did, plaintext).await?;
                Ok(EncryptedPayload {
                    ciphertext: ct,
                    sender_device_id: format!("{}.0", self.bot_did),
                    encryption: EncryptionState::Signal1to1,
                })
            }
            CryptoDecision::HostEncryptGroup { group_id } => {
                let ct = self.encrypt_group(group_id, plaintext).await?;
                Ok(EncryptedPayload {
                    ciphertext: ct,
                    sender_device_id: format!("{}.0", self.bot_did),
                    encryption: EncryptionState::SignalGroup,
                })
            }
        }
    }

    /// Execute decryption based on AutoCrypto decision.
    pub async fn decrypt(
        &self,
        decision: &CryptoDecision,
        ciphertext: &[u8],
        sender_did: &str,
        _channel: &WChannel,
    ) -> Result<DecryptedPayload> {
        match decision {
            CryptoDecision::Passthrough | CryptoDecision::ClientEncrypted => {
                Ok(DecryptedPayload {
                    plaintext: ciphertext.to_vec(),
                })
            }
            CryptoDecision::HostEncrypt1to1 { .. } => {
                let pt = self.decrypt_1to1(sender_did, ciphertext).await?;
                Ok(DecryptedPayload { plaintext: pt })
            }
            CryptoDecision::HostEncryptGroup { group_id } => {
                let pt = self.decrypt_group(group_id, sender_did, ciphertext).await?;
                Ok(DecryptedPayload { plaintext: pt })
            }
        }
    }

    /// Store a PreKey bundle.
    pub async fn store_prekey_bundle(&self, bundle: &WPreKeyBundle) -> Result<()> {
        let bytes = yata_cbor::encode(bundle).map_err(|e| WProtoError::Cbor(e.to_string()))?;
        self.storage
            .save(PREKEY_BUNDLES, &bundle.did, bytes)
            .await
            .map_err(WProtoError::Signal)
    }

    /// Get a PreKey bundle.
    pub async fn get_prekey_bundle(&self, did: &str) -> Result<Option<WPreKeyBundle>> {
        match self
            .storage
            .load(PREKEY_BUNDLES, did)
            .await
            .map_err(WProtoError::Signal)?
        {
            Some(bytes) => {
                let b = yata_cbor::decode(&bytes).map_err(|e| WProtoError::Cbor(e.to_string()))?;
                Ok(Some(b))
            }
            None => Ok(None),
        }
    }

    /// Rotate group key — deletes existing group session.
    pub async fn rotate_group_key(&self, channel_id: &str) -> Result<()> {
        // Save empty to effectively delete the session; next encrypt will re-init.
        self.storage
            .save(GROUP_SESSIONS, channel_id, vec![])
            .await
            .map_err(WProtoError::Signal)
    }

    // ── Internal crypto operations ────────────────────────────

    async fn encrypt_1to1(&self, peer_did: &str, plaintext: &[u8]) -> Result<Vec<u8>> {
        let key = format!("{}:{}", self.bot_did, peer_did);
        let mut session = self.load_ratchet_session(&key).await?;
        let encrypted = session
            .encrypt(plaintext)
            .map_err(|e| WProtoError::Signal(e.to_string()))?;
        self.save_ratchet_session(&key, &session).await?;
        serde_json::to_vec(&encrypted).map_err(|e| WProtoError::Signal(e.to_string()))
    }

    async fn decrypt_1to1(&self, sender_did: &str, ciphertext: &[u8]) -> Result<Vec<u8>> {
        let key = format!("{}:{}", sender_did, self.bot_did);
        let mut session = self.load_ratchet_session(&key).await?;
        let msg: yata_signal::EncryptedMessage =
            serde_json::from_slice(ciphertext).map_err(|e| WProtoError::Signal(e.to_string()))?;
        let plaintext = session
            .decrypt(&msg)
            .map_err(|e| WProtoError::Signal(e.to_string()))?;
        self.save_ratchet_session(&key, &session).await?;
        Ok(plaintext)
    }

    async fn encrypt_group(&self, group_id: &str, plaintext: &[u8]) -> Result<Vec<u8>> {
        let mut session = self.load_or_create_group_session(group_id).await?;
        let encrypted = session
            .encrypt(plaintext)
            .map_err(|e| WProtoError::Signal(e.to_string()))?;
        self.save_group_session(group_id, &session).await?;
        serde_json::to_vec(&encrypted).map_err(|e| WProtoError::Signal(e.to_string()))
    }

    async fn decrypt_group(
        &self,
        group_id: &str,
        _sender_did: &str,
        ciphertext: &[u8],
    ) -> Result<Vec<u8>> {
        let mut session = self.load_or_create_group_session(group_id).await?;
        let msg: yata_signal::SenderKeyMessage =
            serde_json::from_slice(ciphertext).map_err(|e| WProtoError::Signal(e.to_string()))?;
        let plaintext = session
            .decrypt(&msg)
            .map_err(|e| WProtoError::Signal(e.to_string()))?;
        self.save_group_session(group_id, &session).await?;
        Ok(plaintext)
    }

    // ── Session persistence ───────────────────────────────────

    async fn load_ratchet_session(&self, key: &str) -> Result<RatchetSession> {
        match self
            .storage
            .load(RATCHET_SESSIONS, key)
            .await
            .map_err(WProtoError::Signal)?
        {
            Some(bytes) if !bytes.is_empty() => RatchetSession::from_cbor(&bytes)
                .map_err(|e| WProtoError::Signal(e.to_string())),
            _ => Err(WProtoError::Signal(format!(
                "no ratchet session for key '{key}'"
            ))),
        }
    }

    async fn save_ratchet_session(&self, key: &str, session: &RatchetSession) -> Result<()> {
        let bytes = session
            .to_cbor()
            .map_err(|e| WProtoError::Signal(e.to_string()))?;
        self.storage
            .save(RATCHET_SESSIONS, key, bytes)
            .await
            .map_err(WProtoError::Signal)
    }

    async fn load_or_create_group_session(&self, group_id: &str) -> Result<GroupSession> {
        match self
            .storage
            .load(GROUP_SESSIONS, group_id)
            .await
            .map_err(WProtoError::Signal)?
        {
            Some(bytes) if !bytes.is_empty() => GroupSession::from_json(&bytes)
                .map_err(|e| WProtoError::Signal(e.to_string())),
            _ => {
                let mut session = GroupSession::new(group_id, &self.bot_did);
                let _dist = session
                    .init_sender()
                    .map_err(|e| WProtoError::Signal(e.to_string()))?;
                Ok(session)
            }
        }
    }

    async fn save_group_session(&self, group_id: &str, session: &GroupSession) -> Result<()> {
        let bytes = session
            .to_json()
            .map_err(|e| WProtoError::Signal(e.to_string()))?;
        self.storage
            .save(GROUP_SESSIONS, group_id, bytes)
            .await
            .map_err(WProtoError::Signal)
    }
}
