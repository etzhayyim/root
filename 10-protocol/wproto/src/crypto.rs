//! W Protocol auto-encryption: transparent Signal Protocol integration.
//!
//! App passes plaintext. Host encrypts based on channel's encryption_mode.
//! - Plaintext channels: passthrough
//! - Signal 1:1 (bot/A2A): host encrypts with bot's Double Ratchet session
//! - Signal group: host encrypts with Sender Key session
//! - Client-encrypted: passthrough (client pre-encrypted)
//!
//! This module decides *what* to do. Actual crypto calls go through yata-signal.

use crate::types::{ChannelKind, EncryptionState, WChannel};

/// Crypto decision: what the host should do with a payload.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CryptoDecision {
    /// No encryption needed. Payload passes through as-is.
    Passthrough,
    /// Host performs Signal 1:1 encryption (bot side of Double Ratchet).
    HostEncrypt1to1 { peer_did: String },
    /// Host performs Signal group encryption (Sender Key).
    HostEncryptGroup { group_id: String },
    /// Client already encrypted. Host stores ciphertext as-is.
    ClientEncrypted,
}

/// Auto-crypto engine: resolves encryption decision from channel state.
pub struct AutoCrypto;

impl AutoCrypto {
    /// Decide encryption action for an outbound envelope.
    ///
    /// Bot/A2A channels → host encrypts (server-assisted Signal).
    /// Human channels → client must pre-encrypt (host passes through).
    pub fn decide_encrypt(channel: &WChannel, sender_is_bot: bool) -> CryptoDecision {
        match channel.encryption_mode {
            EncryptionState::Plaintext => CryptoDecision::Passthrough,
            EncryptionState::ClientEncrypted => CryptoDecision::ClientEncrypted,
            EncryptionState::Signal1to1 => {
                if sender_is_bot || matches!(channel.kind, ChannelKind::Bot | ChannelKind::A2a) {
                    // Server-assisted: host encrypts on behalf of bot DID
                    CryptoDecision::HostEncrypt1to1 {
                        peer_did: String::new(), // resolved at dispatch time from channel members
                    }
                } else {
                    // Human sender: must be client-encrypted already
                    CryptoDecision::ClientEncrypted
                }
            }
            EncryptionState::SignalGroup => {
                if sender_is_bot || matches!(channel.kind, ChannelKind::Bot | ChannelKind::A2a) {
                    CryptoDecision::HostEncryptGroup {
                        group_id: channel.channel_id.clone(),
                    }
                } else {
                    CryptoDecision::ClientEncrypted
                }
            }
        }
    }

    /// Decide decryption action for an inbound envelope.
    ///
    /// Bot/A2A channels → host decrypts (server-assisted Signal).
    /// Human channels → host passes ciphertext through (client decrypts).
    pub fn decide_decrypt(
        channel: &WChannel,
        receiver_is_bot: bool,
        encryption: EncryptionState,
    ) -> CryptoDecision {
        match encryption {
            EncryptionState::Plaintext => CryptoDecision::Passthrough,
            EncryptionState::ClientEncrypted => CryptoDecision::ClientEncrypted,
            EncryptionState::Signal1to1 => {
                if receiver_is_bot || matches!(channel.kind, ChannelKind::Bot | ChannelKind::A2a) {
                    CryptoDecision::HostEncrypt1to1 {
                        peer_did: String::new(),
                    }
                } else {
                    CryptoDecision::ClientEncrypted
                }
            }
            EncryptionState::SignalGroup => {
                if receiver_is_bot || matches!(channel.kind, ChannelKind::Bot | ChannelKind::A2a) {
                    CryptoDecision::HostEncryptGroup {
                        group_id: channel.channel_id.clone(),
                    }
                } else {
                    CryptoDecision::ClientEncrypted
                }
            }
        }
    }

    /// Determine the effective encryption state for a new channel.
    pub fn resolve_channel_encryption(
        kind: ChannelKind,
        requested: Option<EncryptionState>,
    ) -> EncryptionState {
        match requested {
            Some(enc) => enc,
            None => kind.default_encryption(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;

    fn channel(kind: ChannelKind, enc: EncryptionState) -> WChannel {
        WChannel {
            channel_id: "ch1".into(),
            org_id: "org1".into(),
            name: "test".into(),
            description: "".into(),
            kind,
            encryption_mode: enc,
            creator_did: "did:plc:x".into(),
            member_count: 2,
            at_uri: "".into(),
            created_at: "".into(),
            mdag_root_cid: None,
        }
    }

    #[test]
    fn test_plaintext_passthrough() {
        let ch = channel(ChannelKind::Public, EncryptionState::Plaintext);
        assert_eq!(AutoCrypto::decide_encrypt(&ch, false), CryptoDecision::Passthrough);
        assert_eq!(AutoCrypto::decide_encrypt(&ch, true), CryptoDecision::Passthrough);
    }

    #[test]
    fn test_bot_channel_host_encrypts() {
        let ch = channel(ChannelKind::Bot, EncryptionState::Signal1to1);
        let decision = AutoCrypto::decide_encrypt(&ch, true);
        assert!(matches!(decision, CryptoDecision::HostEncrypt1to1 { .. }));
    }

    #[test]
    fn test_human_dm_client_encrypts() {
        let ch = channel(ChannelKind::Direct, EncryptionState::Signal1to1);
        let decision = AutoCrypto::decide_encrypt(&ch, false);
        assert_eq!(decision, CryptoDecision::ClientEncrypted);
    }

    #[test]
    fn test_a2a_group_host_encrypts() {
        let ch = channel(ChannelKind::A2a, EncryptionState::SignalGroup);
        let decision = AutoCrypto::decide_encrypt(&ch, true);
        assert!(matches!(decision, CryptoDecision::HostEncryptGroup { .. }));
    }

    #[test]
    fn test_default_encryption_direct_is_signal() {
        assert_eq!(
            AutoCrypto::resolve_channel_encryption(ChannelKind::Direct, None),
            EncryptionState::Signal1to1
        );
    }

    #[test]
    fn test_default_encryption_public_is_plaintext() {
        assert_eq!(
            AutoCrypto::resolve_channel_encryption(ChannelKind::Public, None),
            EncryptionState::Plaintext
        );
    }

    #[test]
    fn test_override_encryption() {
        assert_eq!(
            AutoCrypto::resolve_channel_encryption(
                ChannelKind::Public,
                Some(EncryptionState::SignalGroup)
            ),
            EncryptionState::SignalGroup
        );
    }
}
