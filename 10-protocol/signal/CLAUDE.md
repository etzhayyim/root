# `@gftd/signal`

Signal Protocol E2E primitives — **SSoT for the CRITICAL `Signal Protocol E2E`
convention** per ADR-2604261110 (2026-04-26).

## Scope

- X3DH key agreement
- Double Ratchet (1:1)
- Sender Keys (group)
- Field-level AES-GCM (`signal:v1:` envelope)
- IndexedDB key storage (`gftd-signal-v1`)

## Out of scope

- XRPC dispatch — caller injects via `setSignalTransport(...)`
- Lexicon definitions — live at `00-contracts/lexicons/ai/gftd/signal/`
- Auth / session bootstrap — caller's `@atproto/api` AtpAgent

## Transport injection

```ts
import { AtpAgent } from '@atproto/api';
import { setSignalTransport, atpAgentTransport, ensureSignalIdentity } from '@gftd/signal';

const agent = new AtpAgent({ service: 'https://pds.etzhayyim.com' });
await agent.login({ identifier: '...', password: '...' });

setSignalTransport(atpAgentTransport(() => agent));

await ensureSignalIdentity(agent.session!.did, 'device-1');
```

## Migration from `@gftd/wproto`

Per `[[migrations]] signal-extract-from-wproto` (deps.toml):

| Old | New |
|---|---|
| `import { ... } from '@gftd/wproto/signal'` | `import { ... } from '@gftd/signal'` |
| Implicit XRPC via wproto's global `atProcedure` | Explicit `setSignalTransport(...)` at app startup |

`10-protocol/wproto/src/signal.ts` will remain as a deprecated re-export
during the consumer migration window, then be removed alongside wproto
(`[[migrations]] wproto-retirement`).

## Wire-format note

`ai.gftd.signal.getPrekeyBundle` is declared as `query` (GET) in its Lexicon
but the original wproto implementation called it via POST. The port preserves
POST for behavioral parity. Switching to GET is a follow-up once server
acceptance is verified.
