/** Actor module facade — AT Protocol actor-based app architecture. */
export {
	ActorFrame,
	ActorHero,
	ActorFeedList,
	ActorEmbed,
	ActorGame,
	fetchActorProfileView,
	getCachedActorProfileView,
	invalidateActorProfile,
} from './actor/index.js';
export type {
	ActorPerformerType,
	ActorContentMode,
	ActorProfileView,
	ActorContext,
	ActorLoadState,
	ActorGameConfig,
} from './actor/index.js';
