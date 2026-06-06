export { default as AuthGate } from './AuthGate.svelte';
export { default as IamKeyVaultPanel } from './IamKeyVaultPanel.svelte';

export {
	DEFAULT_CLERK_PUBLISHABLE_KEY,
	initClerk,
	signIn,
	signUp,
	signUpWithUsername,
	signOut,
	getSessionToken,
	refreshSessionToken,
	openUserProfile,
	getClerk,
	loadOrganizations,
	switchOrganization,
	createOrganization,
	setOnOrgSwitch,
} from './passkey';

export {
	clerkLoaded,
	isSignedIn,
	clerkUser,
	sessionToken,
	onboardingCompleted,
	currentOrg,
	userOrganizations,
	orgLoading,
	displayName,
	userPlan,
	trustSummary,
	currentAgent,
	ownedAgents,
	moderatorInfo,
	isModerator,
	agentDisplayName,
} from './stores';

export {
	hasEthereumProvider,
	linkEthereumAddress,
	unlinkEthereumAddress,
} from './ethereum';
export type { EthereumLinkResult } from './ethereum';

export {
	linkAdditionalPasskey,
	unlinkAdditionalPasskey,
} from './passkey-additional';
export type { AdditionalPasskeyResult } from './passkey-additional';

export { deriveWrappingKey, parseZkV1Envelope } from './zk';
export { KeyBundleClient } from './key-bundles';
export { buildTrustSummary, trustVariantFromScore } from './trust';
export {
	generateSecretKey,
	enrollKeyBundle,
	fetchAndUnlockKeyBundle,
	buildEmergencyKitText,
	downloadEmergencyKit,
} from './key-bundle-flows';

export type {
	ClerkUserInfo,
	Organization,
	AuthMethod,
	ExternalAccountInfo,
	AuthConfig,
	TrustStep,
	TrustSummary,
	KeyDerivationParams,
	ZkEnvelopeV1,
	KeyBundleLookupInput,
	KeyBundleUpsertInput,
	KeyBundleRevokeInput,
	KeyBundleEnvelopeRecord,
	KeyBundleClientConfig,
	EnrollKeyBundleInput,
	EnrollKeyBundleResult,
	FetchAndUnlockKeyBundleInput,
	FetchAndUnlockKeyBundleResult,
	UsernameSignUpInput,
	AgentCapability,
	AgentInfo,
	CharacterAppearance,
	CreateAgentInput,
	ModeratorInfo,
} from './types';

export { randomCharacterAppearance } from './types';

// Same-origin /profile auth (ADR-2606060000): WebAuthn/passkey + SIWE → CACAO.
export { default as ProfileEditGate } from './ProfileEditGate.svelte';
export {
	buildProfileCacao,
	siweMessage,
	signCacaoEd25519,
	signCacaoSiwe,
	didPkhEip155,
	graphResource,
	CAP_DATOM_TRANSACT,
	CAP_DATOM_READ,
} from './cacao';
export type { Cacao, CacaoPayload, Eip1193Provider, BuildCacaoParams } from './cacao';
export { signInWithPasskey, signInWithWallet } from './profile-signin';
export type { VerifyCacaoResult, SignInDeps } from './profile-signin';

// Site-wide CACAO session (ADR-2606061500): the header login is JWT-free + same-origin.
export {
	signInWithPasskeyCacao,
	establishCacaoSession,
	mintSessionCacao,
	makeCacaoTokenProvider,
	signOutCacao,
	getCacaoSession,
	sessionKeyFromArk,
} from './cacao-session';
export type { CacaoSession, CacaoSessionDeps, EstablishOutcome } from './cacao-session';
