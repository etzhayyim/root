---
id: adr-2604291630
title: YORO guest actor chat uses browser-local Gemma E2B
status: active
doc_type: adr
topic: yoro-projector-guest-chat
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - yoro actor profile guest chat
  - browser-local projector fallback
  - gemma-e2b web inference surface
related:
  - adr-2604271600-projector-l7-langgraph-integration
  - adr-2604282100
---

# Context

YORO actor profile pages need to let unauthenticated visitors send a message to
actors such as `uqpel6i6.etzhayyim.com`. The existing authenticated flow uses
`com.etzhayyim.projector.newProjectConvo` and `com.etzhayyim.projector.sendProjectMessage`,
but the public PDS handler intentionally rejects projector write methods
without a session.

Allowing anonymous writes directly into projector storage would change the PDS
auth model and spam boundary. The product requirement is weaker: a logged-out
visitor should still be able to converse with the visible actor in the profile
surface.

# Decision

Keep unauthenticated projector writes blocked at the PDS boundary. For logged
out visitors, YORO profile chat runs in the browser with the Web inference model
`gemma4-e2b` (`Gemma E2B / Web推論`) and does not persist messages to projector
convo storage.

Authenticated users continue to use the persisted projector path:

1. `createProjectConvo(actorDid)`
2. `sendProjectMessage(convoId, text)`
3. projector history/SSE surfaces where available

Unauthenticated users use the local path:

1. Show the same profile message affordance without a login CTA.
2. Initialize `useLocalLLM().init('gemma4-e2b')` on first send.
3. Stream a browser-local reply with a short actor system prompt containing the
   profile name and DID.
4. Keep conversation memory in component state only.

The LiveStage hero includes this behavior directly. Non-LiveStage profile
heroes render a compact projector chat panel below the hero so service/iframe
actors such as `uqpel6i6.etzhayyim.com` are also covered.

# Consequences

- Public PDS projector write auth remains unchanged.
- Guest chat has no cross-device history, audit trail, notifications, or actor
  side effects.
- First guest response may trigger a browser model download and WebGPU startup.
- Browsers without compatible Web inference show the local model error in the
  chat panel instead of silently failing.
- Integration coverage asserts that a logged-out profile page exposes the Gemma
  E2B chat input for the `uqpel6i6.etzhayyim.com` actor path.

# References

- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/LiveStage.svelte`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/ProjectorGuestChat.svelte`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/atproto-agent.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/tests/guest-projector-chat.spec.ts`
