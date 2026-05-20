import type { Etzhayyim } from "@etzhayyim/sdk";

export interface ProfileViewDetailed {
  did: string;
  handle: string;
  displayName?: string;
  description?: string;
  avatar?: string;
  banner?: string;
  followersCount?: number;
  followsCount?: number;
  postsCount?: number;
  indexedAt?: string;
  labels?: string[];
  sensitivity?: string;
  viewerFollowing?: boolean;
  performerType?: string;
  contentMode?: string;
  nanoid?: string;
  uiType?: string;
  embedUrl?: string;
  service?: object;
  system?: object;
}

export interface PostView {
  uri: string;
  cid: string;
  author: ProfileViewDetailed;
  record: unknown;
  indexedAt: string;
  likeCount?: number;
  repostCount?: number;
  replyCount?: number;
  viewCount?: number;
}

export interface FeedViewPost {
  post: PostView;
}

export interface GetTimelineInput {
  limit?: number;
  cursor?: string;
}

export interface GetTimelineOutput {
  feed: FeedViewPost[];
  cursor?: string;
}

export interface GetAuthorFeedInput {
  actor: string;
  limit?: number;
  cursor?: string;
}

export interface GetAuthorFeedOutput {
  feed: FeedViewPost[];
  cursor?: string;
}

export interface GetPostThreadInput {
  uri: string;
  depth?: number;
  parentHeight?: number;
}

export interface GetPostThreadOutput {
  thread: unknown;
}

export interface GetRankedFeedInput {
  limit?: number;
  cursor?: string;
  debug?: boolean;
  echoPersistence?: number;
  sessionDwellMs?: number;
  sessionDistinctTopics?: number;
}

export interface RankedFeedDebug {
  eta?: number;
  candidateCount?: number;
  hardGateDropped?: number;
  personalizeOff?: boolean;
  nightMode?: boolean;
  botSuspect?: boolean;
}

export interface GetRankedFeedOutput {
  feed: FeedViewPost[];
  cursor?: string;
  debug?: RankedFeedDebug;
}

export interface GetDiscoverFeedInput {
  limit?: number;
  cursor?: string;
}

export interface GetDiscoverFeedOutput {
  feed: FeedViewPost[];
  cursor?: string;
}

export interface GetFollowersInput {
  actor: string;
  limit?: number;
  cursor?: string;
}

export interface GetFollowersOutput {
  subject?: ProfileViewDetailed;
  followers: ProfileViewDetailed[];
  cursor?: string;
}

export interface GetFollowsInput {
  actor: string;
  limit?: number;
  cursor?: string;
}

export interface GetFollowsOutput {
  subject?: ProfileViewDetailed;
  follows: ProfileViewDetailed[];
  cursor?: string;
}

export interface GetProfileInput {
  actor: string;
}

export interface GetProfileOutput {
  profile?: ProfileViewDetailed;
  error?: string;
}

export interface SearchActorsInput {
  q?: string;
  limit?: number;
  cursor?: string;
}

export interface SearchActorsOutput {
  actors: ProfileViewDetailed[];
  cursor?: string;
}

export async function getTimeline(
  _e: Etzhayyim,
  _input?: GetTimelineInput
): Promise<GetTimelineOutput> {
  return {
    feed: [],
    cursor: undefined,
  };
}

export async function getAuthorFeed(
  _e: Etzhayyim,
  _input: GetAuthorFeedInput
): Promise<GetAuthorFeedOutput> {
  return {
    feed: [],
    cursor: undefined,
  };
}

export async function getPostThread(
  _e: Etzhayyim,
  _input: GetPostThreadInput
): Promise<GetPostThreadOutput> {
  return {
    thread: {},
  };
}

export async function getRankedFeed(
  _e: Etzhayyim,
  input?: GetRankedFeedInput
): Promise<GetRankedFeedOutput> {
  const result: GetRankedFeedOutput = {
    feed: [],
    cursor: undefined,
  };
  if (input?.debug) {
    result.debug = {
      eta: 0,
      candidateCount: 0,
      hardGateDropped: 0,
      personalizeOff: false,
      nightMode: false,
      botSuspect: false,
    };
  }
  return result;
}

export async function getDiscoverFeed(
  _e: Etzhayyim,
  _input?: GetDiscoverFeedInput
): Promise<GetDiscoverFeedOutput> {
  return {
    feed: [],
    cursor: undefined,
  };
}

export async function getFollowers(
  _e: Etzhayyim,
  _input: GetFollowersInput
): Promise<GetFollowersOutput> {
  return {
    followers: [],
    cursor: undefined,
  };
}

export async function getFollows(
  _e: Etzhayyim,
  _input: GetFollowsInput
): Promise<GetFollowsOutput> {
  return {
    follows: [],
    cursor: undefined,
  };
}

export async function getProfile(
  _e: Etzhayyim,
  _input: GetProfileInput
): Promise<GetProfileOutput> {
  return {
    profile: undefined,
    error: "not found",
  };
}

export async function searchActors(
  _e: Etzhayyim,
  _input?: SearchActorsInput
): Promise<SearchActorsOutput> {
  return {
    actors: [],
    cursor: undefined,
  };
}
