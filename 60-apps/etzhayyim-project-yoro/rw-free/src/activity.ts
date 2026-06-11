import type { Etzhayyim } from "@etzhayyim/sdk";

export interface ListActivitiesInput {
  limit?: number;
  cursor?: string;
  objectTypes?: string;
  actorDid?: string;
}

export interface ListActivitiesOutput {
  events: object[];
  cursor?: string;
}

export interface ActivityTraceInput {
  objectType: string;
  objectId: string;
}

export interface ActivityTraceOutput {
  trace: object[];
}

export interface MarkSeenInput {}

export interface MarkSeenOutput {
  rkey: string;
  uri: string;
  cid: string;
}

export async function listActivities(
  _e: Etzhayyim,
  input?: ListActivitiesInput
): Promise<ListActivitiesOutput> {
  return {
    events: [],
    cursor: input?.cursor,
  };
}

export async function getActivityTrace(
  _e: Etzhayyim,
  input: ActivityTraceInput
): Promise<ActivityTraceOutput> {
  return {
    trace: [],
  };
}

export async function markSeen(
  _e: Etzhayyim,
  _input: MarkSeenInput
): Promise<MarkSeenOutput> {
  const timestamp = Date.now();
  return {
    rkey: `seen-${timestamp}`,
    uri: `at://yoro.etzhayyim.com/com.etzhayyim.yoro.activitySeen/seen-${timestamp}`,
    cid: "bafyref",
  };
}
