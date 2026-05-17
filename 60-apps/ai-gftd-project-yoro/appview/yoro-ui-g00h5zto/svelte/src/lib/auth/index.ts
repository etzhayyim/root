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
