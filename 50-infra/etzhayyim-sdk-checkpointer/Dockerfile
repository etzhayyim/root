# etzhayyim-sdk-checkpointer — TS sidecar image for MstCheckpointSaver.
#
# Stage 2 of the LangGraph → MST → IPFS → L2 pipeline per ADR-2605171800.
# The Python langserver (lg-uhl-right-neural etc.) talks to this sidecar
# over a Unix-domain socket (default /run/etzhayyim/checkpointer.sock).
#
# Build context: repo root.
#
#   docker build -f 50-infra/etzhayyim-sdk-checkpointer/Dockerfile \
#     -t ghcr.io/etzhayyim/etzhayyim-sdk-checkpointer:$(git rev-parse --short HEAD) .
#
# This is an infra-side image. It contains only the @etzhayyim/sdk runtime
# (the checkpointer entrypoint + its prod deps). No app code lives here.
#
# Runtime env (see 20-actors/etzhayyim-sdk/dist/checkpointer.js#runFromEnv):
#   ETZ_CHECKPOINTER_SOCKET           default /run/etzhayyim/checkpointer.sock
#   ETZ_CHECKPOINTER_STATE_DIR        default <node-cwd>/state
#   ETZ_CHECKPOINTER_ALLOWED_DIDS     required, comma-separated DID allowlist
#   ETZ_IPFS_API_URL                  optional, enables Stage 3 pin
#   ETZ_ANCHOR_CHAIN_ID               optional, enables Stage 4 anchor

# ── Build stage ───────────────────────────────────────────────────────────────

FROM node:22-alpine AS builder

WORKDIR /build

# pnpm via corepack — matches the SDK's lockfile (pnpm-lock.yaml v9).
RUN corepack enable && corepack prepare pnpm@9 --activate

# Install prod deps only. We intentionally do not copy .npmrc — the
# SDK has only public registry dependencies (atproto, ipld, viem,
# msgpack, multiformats). Any future @etzhayyim/* dep would need an
# explicit build-time mount.
COPY 20-actors/etzhayyim-sdk/package.json 20-actors/etzhayyim-sdk/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.pnpm-store \
    pnpm install --prod --frozen-lockfile --ignore-scripts

# ── Runtime stage ─────────────────────────────────────────────────────────────

FROM node:22-alpine AS runtime

# tini for proper signal forwarding (SIGTERM → graceful sidecar.stop()).
RUN apk add --no-cache tini

WORKDIR /sidecar

# Drop in the prebuilt JS + prod node_modules. dist/ is already built;
# the langgraph repo's CI builds it via `pnpm --filter @etzhayyim/sdk build`
# before the docker context is assembled.
COPY --from=builder /build/node_modules ./node_modules
COPY 20-actors/etzhayyim-sdk/dist ./dist
COPY 20-actors/etzhayyim-sdk/package.json ./

# Pod runs all containers as uid 65532 (set via K8s securityContext);
# this Dockerfile USER directive is a sane local-docker default. K8s
# will override per spec.template.spec.securityContext.runAsUser.
USER node:node

# No exposed TCP port by default — Unix socket lives on a shared emptyDir.
# Tests that run the sidecar over TCP set ETZ_CHECKPOINTER_SOCKET to
# tcp://0.0.0.0:<port>; expose that port externally as needed.

ENTRYPOINT ["/sbin/tini", "--", "node", "dist/checkpointer-bin.js"]
