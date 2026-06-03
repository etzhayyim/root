/**
 * Actor types for AT Protocol actor-based app architecture.
 *
 * Each app = AT Protocol Actor (DID + Profile + Records).
 * performerType determines hero section layout.
 * contentMode determines frame content (timeline/interactive/game).
 */

import type {
	CardPersonPayload,
	CardOrganizationPayload,
	CardServicePayload,
	CardSystemPayload,
} from '$lib/atproto-agent';

/** AT Protocol actor performer type (DoDAF DM2). */
export type ActorPerformerType = 'service' | 'system' | 'person' | 'organization';

/** Actor frame content mode. */
export type ActorContentMode = 'timeline' | 'interactive' | 'game';

/** Legacy actor profile shape (used by ActorEmbed/ActorGame). */
export interface ActorProfile {
	nanoid: string;
	name: string;
	ui: string;
	accent?: string;
	icon?: string;
	customEntry?: string;
	fullUrl?: string;
	gameConfig?: ActorGameConfig;
}

/** Actor loading state. */
export type ActorLoadState = 'idle' | 'loading' | 'ready' | 'error';

/** Game mode configuration. */
export interface ActorGameConfig {
	runtime: 'godot' | 'html';
	entry: string;
	assetsBaseUrl: string;
}

/**
 * Actor profile view — AT Protocol profile + AT Protocol extensions.
 * Returned by getAuthorProfile with AT Protocol extension fields from PDS.
 */
export interface ActorProfileView {
	// AT Protocol standard (app.bsky.actor.defs#profileViewDetailed)
	did: string;
	handle: string;
	displayName: string;
	avatar?: string;
	description?: string;
	followersCount: number;
	followsCount: number;
	postsCount: number;
	viewerFollowing?: boolean;
	viewerFollowedBy?: boolean;
	viewerMuted?: boolean;
	viewerBlocked?: string;

	// AT Protocol extensions
	nanoid?: string;
	performerType?: ActorPerformerType;
	contentMode?: ActorContentMode;
	accent?: string;
	icon?: string;

	// Performer-specific payloads (discriminated by performerType)
	service?: CardServicePayload;
	system?: CardSystemPayload;
	person?: CardPersonPayload;
	organization?: CardOrganizationPayload;

	// contentMode=interactive
	embedUrl?: string;

	// contentMode=game
	gameConfig?: ActorGameConfig;

	// Cross-app scores (dojo, joucho, society6)
	scores?: ActorScores;
}

/** Cross-app scores for profile display. */
export interface ActorScores {
	dojo?: {
		drillsCompleted: number;
		avgScore: number;
	};
	joucho?: {
		reviewCount: number;
		avgScore: number;
		grade: string;
	};
}

/** Context injected into webcomponent-mode actor components. */
export interface ActorContext {
	nanoid: string;
	name: string;
	userId: string;
	actorId: string;
	orgId: string;
	wSend: (kind: string, payload: Record<string, unknown>) => Promise<void>;
	wQuery: (method: string, params: Record<string, unknown>) => Promise<unknown>;
	backend: {
		call: <T>(service: string, method: string, body?: Record<string, unknown>) => Promise<T>;
	};
	sql: {
		exec: (stmt: string, params?: Record<string, unknown>) => Promise<void>;
		query: (stmt: string, params?: Record<string, unknown>) => Promise<Record<string, unknown>[]>;
	};
	navigate: (path: string) => void;
	remoteCall: (pkg: string, iface: string, func: string, params: Uint8Array) => Promise<Uint8Array>;
}
