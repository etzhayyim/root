import type { Etzhayyim } from "@etzhayyim/sdk";

export const YORO_DID_PREFIX = "did:web:yoro.etzhayyim.com:" as const;

export function projectEntityDid(projectId: string): string {
  return `${YORO_DID_PREFIX}project:${projectId}`;
}

export function projectEntityRkey(projectId: string, entityId: string): string {
  return `entity-${projectId}-${entityId}`;
}

export function productResearchDid(jobId: string): string {
  return `${YORO_DID_PREFIX}research:${jobId}`;
}

export function productResearchRkey(jobId: string): string {
  return `research-${jobId}`;
}

export function activitySeenDid(objectId: string): string {
  return `${YORO_DID_PREFIX}seen:${objectId}`;
}

export function activitySeenRkey(objectId: string): string {
  return `seen-${objectId}`;
}

export function appDid(appId: string): string {
  return `${YORO_DID_PREFIX}app:${appId}`;
}

export function appRkey(appId: string): string {
  return `app-${appId}`;
}

export function shinkaEvolutionDid(nanoid: string): string {
  return `${YORO_DID_PREFIX}evolution:${nanoid}`;
}

export function shinkaEvolutionRkey(nanoid: string): string {
  return `evo-${nanoid}`;
}

export function shinkaKnowledgeDid(nanoid: string): string {
  return `${YORO_DID_PREFIX}knowledge:${nanoid}`;
}

export function shinkaKnowledgeRkey(nanoid: string): string {
  return `know-${nanoid}`;
}

export function productCategoryDid(category: string): string {
  return `${YORO_DID_PREFIX}category:${category}`;
}

export function productCategoryRkey(category: string): string {
  return `cat-${category}`;
}

export function postDid(postId: string): string {
  return `${YORO_DID_PREFIX}post:${postId}`;
}

export function postRkey(postId: string): string {
  return `post-${postId}`;
}

export interface ProjectEntityRecord {
  projectId: string;
  entityType: string;
  entityId: string;
}

export interface ProductResearchRecord {
  query: string;
  category?: string;
  retailers: string[];
  totalOffers: number;
  offersByRetailer?: unknown;
  topOfferDids?: string[];
  minPriceJpy?: number;
  maxPriceJpy?: number;
  medianPriceJpy?: number;
  capturedAt: string;
  jobId: string;
}

export interface ActivitySeenRecord {
  seenAt: string;
}

export interface AppItem {
  id: string;
  name: string;
  shortName?: string;
  href: string;
  icon: string;
  category: string;
  description?: string;
}

export interface ShinkaEvolutionRecord {
  nanoid: string;
  evolutionData: unknown;
}

export interface ShinkaKnowledgeRecord {
  nanoid: string;
  knowledgeData: unknown;
}

export interface ProductCategoryRecord {
  category: string;
  description?: string;
}

export interface PostRecord {
  uri: string;
  cid: string;
  authorDid: string;
  createdAt: string;
}

export interface HealthOutput {
  ok?: boolean;
  app?: string;
  ts?: string;
}

export interface StatsOutput {
  posts?: number;
  profiles?: number;
  ts?: string;
}

export interface ListAppsOutput {
  items?: AppItem[];
  total?: number;
}

export interface ListPostsOutput {
  items?: string[];
  count?: number;
}

export interface ListProductResearchOutput {
  items: unknown[];
  total: number;
  offset: number;
  limit: number;
}

export interface IngestProductCategoryInput {
  query: string;
  category?: string;
  retailers?: string[];
  maxItemsPerRetailer?: number;
  actorPath?: string;
}

export interface IngestProductCategoryOutput {
  jobId: string;
  status: string;
  researchVertexId?: string;
}
