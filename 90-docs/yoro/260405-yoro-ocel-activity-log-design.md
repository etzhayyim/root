---
id: yoro-ocel-activity-log
title: "yoro.etzhayyim.com — OCEL v2 Activity Log Design"
status: active
doc_type: explanation
topic: yoro-activity-ocel
authoritative: true
last_verified: 2026-04-10
authoritative_for:
  - yoro activity log architecture
  - notifications to activities migration
  - project notification integration
related:
  - ocel-process-mining
  - yoro-superapp-oembed
supersedes: []
superseded_by: []
---

# yoro.etzhayyim.com — OCEL v2 Activity Log Design

## Goal

Replace the Bluesky-style flat notification list (`/notifications`) with an **OCEL v2 (IEEE 1849-2023) object-centric activity log** (`/activities`). Consolidate project-scoped notifications into `/projects` with unread badges.

This design now assumes a canonical OCEL record schema at `com.etzhayyim.ocel.event`. UI activity events are reconstructed from the `OcelEvent` graph label, whose `props` field stores the canonical OCEL payload.

## Scope

- `/notifications` → `/activities` route migration (301 redirect)
- OCEL v2 event aggregation from 3 sources
- Project notification XRPC endpoints + badge UI
- Navigation update (layout, drawer, tab routing)

## Executive Summary

Notifications are **passive** (something happened to you). Activities are **observable events** (things happening in the system). OCEL v2 provides object-centric event semantics: each event has an `objectType`, `activity`, `phase`, and related objects — enabling process mining (DFG, variant analysis, conformance checking) on the same data that powers the UI.

### Before / After

| Before | After |
|---|---|
| `/notifications` — flat Bluesky notification list (like/repost/follow/mention) | `/activities` — OCEL v2 event timeline (All/Social/Deploy/Evolution/Records tabs) |
| `/projects` — project tree only | `/projects` — project tree + unread badge + notification panel |
| No OCEL integration in UI | Activity events feed OCEL process mining analyzers |

## Decision

### 1. Activity Data Model (OCEL v2 Event)

Each activity is an OCEL v2 event with the following structure:

```typescript
interface ActivityEvent {
  eventId: string;           // AT URI or canonical OCEL eventId
  specVersion: "ocel.v2";   // IEEE 1849-2023
  activity: string;          // namespace:action (e.g., "social:like", "deploy:build")
  objectType: string;        // OCEL object type (notification, deploy, app, record, actor)
  objectId: string;          // object identifier
  actorDid: string;          // DID of performer
  actorHandle: string;
  actorDisplayName: string;
  actorAvatar: string;
  timestamp: string;         // ISO 8601 or epoch ms
  phase: "start" | "success" | "error";
  subjectUri?: string;       // AT URI of subject (for social events)
  relatedObjects?: Array<{ objectType: string; objectId: string; qualifier: string }>;
}
```

### 2. Three Event Sources

| Source | Object Types | Activities | Graph Label |
|---|---|---|---|
| **Bluesky notifications** | `notification` | `social:like`, `social:repost`, `social:follow`, `social:mention`, `social:reply`, `social:quote` | `Like`, `Follow`, `Repost` (existing) |
| **OCEL collector events** | `deploy`, `worker`, `record`, `actor` | `deploy:*`, `record:*`, `profile:*`, `auth:*` | `OcelEvent` (`collection = com.etzhayyim.ocel.event`) |
| **Shinka evolution records** | `app` | `evolution:heartbeat`, `evolution:knowledge` | `shinkaEvolution`, `shinkaKnowledge` (collection filter) |

### 2.1 Canonical OCEL Record

The canonical persisted OCEL schema is the record lexicon `com.etzhayyim.ocel.event`.

- Storage collection: `com.etzhayyim.ocel.event`
- Graph label: `OcelEvent`
- Row projection: `graphar.vertex_ocel_event`
- Canonical payload location: `props`

The activity feed does not depend on legacy synthetic collection names such as `com.etzhayyim.apps.ocel.ocelEvent`.

### 3. XRPC Endpoints

#### Activity Log

| NSID | Type | Purpose |
|---|---|---|
| `com.etzhayyim.yoro.activity.listActivities` | query | List OCEL v2 activity events with object type / activity filter |
| `com.etzhayyim.yoro.activity.getActivityTrace` | query | Get all events for a specific object (trace view) |
| `com.etzhayyim.yoro.activity.markSeen` | procedure | Record activity seen timestamp |

**`listActivities` params**: `{ limit, cursor, objectTypes[]?, activities[]?, actorDid? }`

#### Project Notifications

| NSID | Type | Purpose |
|---|---|---|
| `com.etzhayyim.projector.listProjectNotifications` | query | List notifications scoped to project convo(s) |
| `com.etzhayyim.projector.getProjectUnreadCounts` | query | Get unread count per project convoId |

### 4. UI Architecture

#### `/activities` — Activity Timeline

```
/activities
+-- Header: "Activities" + OCEL v2 badge
+-- Filter tabs: All | Social | Deploy | Evolution | Records
+-- Timeline list
|   +-- [icon] [avatar] [actor] [verb] [timestamp]
|   |   +-- [objectType chip] [phase dot]
|   |   +-- [subjectUri preview] (social events)
|   +-- Load more (cursor pagination)
```

#### `/projects` — Notification Integration

```
/projects
+-- Header: [back] "Projects" [bell badge] [new]
+-- Notification panel (slide-down, toggled by bell)
|   +-- Cross-project notification list
+-- Project list
    +-- [icon] [name] [unread badge] [kind] [email]
```

### 5. Route Migration

| Route | Behavior |
|---|---|
| `/activities` | OCEL v2 Activity Log (new) |
| `/activities?tab=social` | Social tab (equivalent to old notifications) |
| `/notifications` | Client-side redirect → `/activities?tab=social` |

Navigation references updated: layout header bell, AppDrawer, menu actions.

### 6. Bluesky Notification Preservation

The existing `app.bsky.notification.*` XRPC handlers remain unchanged for AT Protocol federation compatibility. The activity log **wraps** notifications as OCEL events via `notifToActivity()` conversion at query time — no data migration required.

## Data Flow

```
PDS Commit Stream (ComAtprotoSyncSubscribeRepos)
  |
  +---> OCEL Collector DIDs (existing ocel.etzhayyim.com)
  |     +-- ingest com.etzhayyim.ocel.event --> OcelEvent graph label
  |
  +---> Bluesky Notification (existing)
  |     +-- Like/Follow/Repost graph labels
  |
  +---> Shinka collections (existing)
        +-- shinkaEvolution / shinkaKnowledge records

Browser (/activities)
  +-- XRPC com.etzhayyim.yoro.activity.listActivities
      +-- Source 1: Like/Follow/Repost --> social:* events
      +-- Source 2: OcelEvent(props = canonical com.etzhayyim.ocel.event) --> deploy:*/record:* events
      +-- Source 3: shinkaEvolution/Knowledge --> evolution:* events
      +-- Merge + sort by timestamp --> paginated response

Browser (/projects)
  +-- XRPC com.etzhayyim.projector.getProjectUnreadCounts
  |   +-- convo.message records, grouped by convoId
  +-- XRPC com.etzhayyim.projector.listProjectNotifications
      +-- convo.message/member/project records, filtered by convoId
```

## Implementation Files

| File | Change |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/pds-handlers-etzhayyim.ts` | Activity XRPC handlers + project notification handlers |
| `50-infra/cloudflare/workers/atproto/src/pds-dispatch.ts` | Route registration for new NSID sets |
| `60-apps/etzhayyim-project-yoro/.../routes/activities/+page.svelte` | Activity timeline UI |
| `60-apps/etzhayyim-project-yoro/.../routes/notifications/+page.svelte` | Redirect to /activities |
| `60-apps/etzhayyim-project-yoro/.../routes/projects/+page.svelte` | Unread badges + notification panel |
| `60-apps/etzhayyim-project-yoro/.../lib/superapp/stores.ts` | pathToTab() update |
| `60-apps/etzhayyim-project-yoro/.../routes/+layout.svelte` | Navigation update |
| `60-apps/etzhayyim-project-yoro/.../lib/components/AppDrawer.svelte` | Drawer link update |

## Process Mining Connection

Activity events are compatible with OCEL v2 process mining at `ocel.etzhayyim.com`:

| Algorithm | Activity Log Usage |
|---|---|
| **DFG (Directly-Follows Graph)** | Toggle view in `/activities` (P5 future) |
| **Variant Analysis** | Group user traces by activity sequence |
| **Conformance Checking** | Compare observed deploy/evolution patterns vs expected |
| **Performance Analysis** | Measure transition latency between activities |

The same `OcelEvent` graph label is consumed by both the UI (`listActivities`) and the process mining WIT interface (`etzhayyim:ocel/process-mining`).

Canonical record URI form for persisted OCEL events:

`at://{repo}/com.etzhayyim.ocel.event/{rkey}`

## References

- IEEE 1849-2023 (OCEL v2 standard)
- `60-apps/etzhayyim-project-ocel/CLAUDE.md` — OCEL project architecture
- `60-apps/etzhayyim-project-ocel/wit/ocel/package.wit` — WIT interface
- `60-apps/etzhayyim-project-yoro/CLAUDE.md` — yoro routing table
