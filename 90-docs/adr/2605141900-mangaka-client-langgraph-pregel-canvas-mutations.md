---
id: adr-2605141900-mangaka-client-langgraph-pregel-canvas-mutations
title: "mangaka client-side LangGraph TS Pregel for canvas mutations"
status: active
doc_type: adr
topic: mangaka-client-pregel
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - mangaka client-side canvas mutation dispatcher (`canvas-pregel.ts`)
  - 12 op kinds → compiled LangGraph TS `StateGraph` graphs
  - `runCanvasOp(op, ctx)` unified mutation entry point
  - per-op audit `emit_op` step (suppressed with `quiet: true` on per-frame ticks)
  - cloudflared tunnel ingress using ClusterIPs to bypass cluster-DNS resolver flake
priority: 7.5
axis: orchestration
weight: 0.7
priority_note: "Single client-side mutation entry point unifies the canvas behaviour; pairs with pod-side LangGraph (`lg-mangaka` 6 Pregel graphs) using the same StateGraph shape. Cloudflared cluster-IP workaround unblocks tunnel routing under DNS resolver flake."
depends_on:
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605141200-mangaka-3d-scene-pregel-kami-sdk
  - adr-2605141600-mangaka-phase-c-activation-and-emotion-loop
related:
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2605080600-langgraph-server-granian-l3-runtime
supersedes: []
superseded_by: []
---

# Context

mangaka.etzhayyim.com's Genko canvas had ~15 imperative mutation paths scattered
across `Canvas.svelte` (resize, drag, image_offset, tail_drag, face_add,
tail_anchor, …) and `Genko.svelte` (add_node, add_nodes, delete, update_props,
face_clear, tail_clear). Each path duplicated:

1. pixel → mm-unit conversion (`_unit === 'mm' && f.sc > 0`)
2. snapshot the before-state for undo / opLog
3. apply the mutation
4. clamp invariants (`x1 < x2`, `y1 < y2`)
5. cascade to children (panel-only)
6. `requestRedraw()` + `scheduleAutoSave()`
7. `recordOp(...)` (XRPC → `lg-mangaka.record_op_log` Pregel graph)

The resize handler had a leaking cascade for **all non-`ai-image` types**,
which meant resizing a fukidashi pulled the underlying ai-image with it.
Hand-fixing that bug exposed how much of the same boilerplate was scattered
across handlers — a single missed `if` could re-introduce the leak.

Pod-side already runs `lg-mangaka` with 6 Pregel graphs (load_document,
save_document, list_documents, record_op_log, debug_canvas_state,
detect_faces, score_emotion, compose_scene_3d) using
`langgraph.graph.StateGraph` per ADR-2605082000. Mirroring that idiom on the
client closes the impedance mismatch between pod-side and client-side
mutation logic.

Separately, the cloudflared sidecar (tunnel `be2cc0b0-...`) routing
`dispatcher.etzhayyim.com/*` to the bpmn-dispatcher Service was failing with
`dial tcp: lookup *.svc.cluster.local: i/o timeout` from inside the
cloudflared pods, while fresh `kubectl run` pods on the same node resolved
cluster DNS fine. Symptom: every external XRPC call to mangaka.etzhayyim.com
returned 502 (CF edge wraps tunnel origin error). The Go-internal DNS
resolver inside cloudflared was failing to use kube-dns reliably on the
Calico mesh.

# Decision

1. **Client-side canvas mutations move through a single Pregel dispatcher.**
   `40-engine/kami-engine/kami-engine-sdk/src/lib/genko/canvas-pregel.ts`
   uses `@langchain/langgraph` 1.3 (TS) — the same StateGraph API as the
   Python pod-side graphs. 12 op kinds, each with its own compiled graph:

   | op.kind        | super-steps |
   |----------------|---|
   | `resize`       | snapshot_before → compute_delta → gather_cascade → apply_rect → apply_cascade → clamp → redraw_save → emit_op |
   | `drag`         | snapshot_before → compute_delta → apply_drag → redraw_save → emit_op |
   | `image_offset` | snapshot_before → compute_delta → apply_offset → redraw_save → emit_op |
   | `tail_drag`    | snapshot_before → compute_delta → apply_tail_drag → redraw_save → emit_op |
   | `tail_anchor`  | snapshot_before → apply → redraw_save → emit_op |
   | `tail_clear`   | snapshot_before → apply → redraw_save → emit_op |
   | `face_add`     | snapshot_before → apply → redraw_save → emit_op |
   | `face_clear`   | snapshot_before → apply → redraw_save → emit_op |
   | `add_node`     | apply → undo_push → redraw_save → emit_op |
   | `add_nodes`    | apply (batch) → undo_push → redraw_save → emit_op |
   | `delete`       | snapshot_before → apply → undo_push → redraw_save → emit_op |
   | `update_props` | snapshot_before → apply → undo_push → redraw_save → emit_op |

   Channels: `Annotation.Root({op, ctx, dx, dy, before, after, children, emitted})`.
   `quiet: true` on per-frame pointer-move ticks suppresses the `emit_op`
   step; the final pointer-up records a single before/after delta via the
   existing `ondragend` path.

   **Resize cascade is now scoped to `type === 'panel'` only**. Fukidashi
   resize no longer drags the underlying ai-image. This was the bug that
   triggered the refactor.

2. **`@langchain/langgraph` 1.3 + `@langchain/core` 1.1.46** are added to
   the svelte app's package.json AND as optional peerDependencies on the
   shared `@etzhayyim/kami-engine-sdk` (else rolldown can't resolve the
   import from the SDK file). `@langchain/langgraph/web` subpath doesn't
   resolve under rolldown — the main entry (`@langchain/langgraph`) works
   because the package's `exports` field maps `.` → browser-compatible
   build.

3. **mangaka SvelteKit migration** keeps three custom routes under
   `routes/`:
   - `at/[...path]/+page.svelte` — AT URI deep-link catch-all (renders
     `App.svelte`; the SPA parses `location.pathname` and calls
     `loadDocument` XRPC).
   - `xrpc/[nsid]/+server.ts` — proxies `com.etzhayyim.mangaka.*` POSTs to
     `dispatcher.etzhayyim.com` with the `x-internal-trust` header from the CF
     Secrets Store binding.
   - `blob/[cid]/+server.ts` — direct B2 SigV4 GET for ai-image blobs
     (bypasses the PDS `com.atproto.sync.getBlob` POST-only endpoint).

4. **Cloudflared tunnel ingress uses ClusterIPs**, not cluster.local
   hostnames. Pushed via CF API `PUT /accounts/{acc}/cfd_tunnel/{id}/configurations`:

   ```
   ^/xrpc/ai\.etzhayyim\.apps\.shinshi\..*$  → http://10.109.101.123:8000  (lg-shinshi)
   ^/xrpc/ai\.etzhayyim\.apps\.animeka\..*$  → http://10.109.85.144:8000   (lg-animeka)
   ^/xrpc/ai\.etzhayyim\.apps\.recap\..*$    → http://10.103.208.59:8000   (lg-recap)
   ^/xrpc/ai\.etzhayyim\.apps\.mangaka\..*$  → http://10.103.112.21:8000   (lg-mangaka NEW)
   (default)                            → http://10.100.81.213:8080   (bpmn-dispatcher)
   404                                  → http_status:404
   ```

   mangaka NSIDs now go **direct to `lg-mangaka` pod**, bypassing
   bpmn-dispatcher entirely. Side effect: bpmn-dispatcher's
   `LG_MANGAKA_PROXY_NSIDS` allowlist is no longer in the request path for
   mangaka — pymagatama image churn (CI overwrites our allowlist edits)
   no longer breaks mangaka XRPC.

5. **Cluster-side actions** taken to stabilise:
   - `kubectl cordon edge-pool-0657e27d2dc7` — flapping NodeReady ↔
     NotReady was scheduling cloudflared pods on broken kubelet.
   - Helm chart `lg-mangaka-pool` upgraded to image
     `anime-faces-113949-amd64@sha256:9ed0f5...` (opencv-python-headless +
     facenet-pytorch + nagadomi/lbpcascade_animeface bundled).

# Consequences

**Positive**:
- Single mutation entry point: any new canvas op = add variant to
  `CanvasOp` + register graph in `OP_GRAPHS`. No more scattered
  imperative paths.
- Bug class extinct: resize cascade leak (fukidashi pulling ai-image)
  cannot reappear because cascade is gathered in a dedicated super-step
  gated on `type === 'panel'`.
- Audit completeness: `emit_op` is the **only** path to `recordOp`. If a
  graph doesn't end with `emit_op` (or `quiet: true` for intra-drag
  ticks), it's a build error.
- Pod-side / client-side share `StateGraph` idiom — engineers can move
  between layers without context switch.
- mangaka XRPC chain stable across pymagatama CI churn — dispatcher
  allowlist no longer matters for mangaka.

**Negative**:
- ~80 KB bundle weight from `@langchain/langgraph` + `@langchain/core`
  in the client. Acceptable for an authoring SPA; would be too heavy for
  a viewer-only app.
- Async dispatch (`graph.invoke` returns Promise). Callers use
  `void runCanvasOp(...)` since super-steps mutate the shared `ctx`
  synchronously — the Promise is just for graph completion. New
  contributors may try to `await` and slow the pointer-move loop.
- ClusterIPs in cloudflared config are brittle to ClusterIP changes
  (Service recreation reassigns IPs). Re-running the CF API config push
  is a one-line operation but it's not declarative — needs a script to
  reconcile against `kubectl get svc -o json`.

**Open follow-ups**:
- `kubectl drain edge-pool-0657e27d2dc7` and remove from autoscaler if
  Vultr node remains unstable (currently cordoned but not drained).
- CoreDNS HPA (single replica is a SPOF that triggered the cloudflared
  DNS flake under load).
- Flip cloudflared to local `config.yaml` (`config_src: local`) so
  ingress rules don't depend on CF API rate limits.
- Migrate the remaining 3 lg-* pods (shinshi / animeka / recap) tunnel
  config to ClusterIPs too — they have the same DNS flake risk.
- Optional: replace the per-call CF Secrets Store `binding.get()`
  fetch in `xrpc/[nsid]/+server.ts` with a Worker-local cache. Currently
  every XRPC POST awaits a secret read.

# Verification

- `cd 60-apps/.../mng4k4x1/svelte && pnpm build` succeeds with new
  StateGraph imports.
- Live: `mangaka.etzhayyim.com/xrpc/com.etzhayyim.mangaka.detectFaces` →
  HTTP 200, method=`anime-cascade`, 2 faces per ai-image,
  1.9s latency end-to-end.
- Live: `mangaka.etzhayyim.com/blob/{cid}?did=anonymous` → HTTP 200,
  image/jpeg, 3 MB stream, cache-control immutable.
- Hard-refresh test in browser: resize, drag, add fukidashi, delete,
  update props, face anchor — all dispatch through `runCanvasOp`,
  `recordOp` fires exactly once per gesture (verified via
  `vertex_mangaka kind='opLog'` rows after each action).
