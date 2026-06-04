# atproto PDS — Bun container build (ADR-2605111300, Phase P1)
#
# Builds the existing TS PDS Worker (50-infra/cloudflare/workers/atproto/src/)
# as a single-file Bun bundle. Workspace deps (@etzhayyim/*) are resolved via
# pnpm install, then bundled into one JS file with `bun build`.
#
# Build context = repo root. Invoke via 50-infra/k8s/atproto-pds/build.sh.

FROM oven/bun:1.1-alpine AS deps
WORKDIR /repo

# Workspace boundary files first (cache layer).
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./

# Workspace packages the PDS depends on (transitively).
COPY 10-protocol/did-etzhayyim/            10-protocol/did-etzhayyim/
COPY 10-protocol/xrpc/                10-protocol/xrpc/
COPY 10-protocol/lexicons-bundle/     10-protocol/lexicons-bundle/
COPY 10-protocol/signal/              10-protocol/signal/
COPY 00-contracts/                    00-contracts/
COPY 30-graph/graph-schema/           30-graph/graph-schema/
COPY 20-actors/magatama/sdk/magatama-host-sdk/  20-actors/magatama/sdk/magatama-host-sdk/
COPY 50-infra/cloudflare/workers/atproto/  50-infra/cloudflare/workers/atproto/

# pnpm install with workspace resolution.
RUN apk add --no-cache git nodejs npm \
 && npm install -g pnpm@9 \
 && pnpm install --frozen-lockfile --filter "etzhayyim-pds-2603241700..."

# ── build stage ──
FROM deps AS build
WORKDIR /repo

# Bun entrypoint shim (wraps CF Worker fetch() in Bun.serve).
COPY 50-infra/k8s/atproto-pds/bun-entry.ts \
     50-infra/cloudflare/workers/atproto/src/bun-entry.ts

WORKDIR /repo/50-infra/cloudflare/workers/atproto
RUN bun build src/bun-entry.ts \
    --target=bun \
    --outfile=/repo/dist/server.js \
    --define process.env.NODE_ENV='"production"'

# ── runtime ──
FROM oven/bun:1.1-alpine AS runtime
WORKDIR /app
RUN apk add --no-cache ca-certificates tini
COPY --from=build /repo/dist /app/dist

EXPOSE 8787
ENV PORT=8787
ENV NODE_ENV=production
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["bun", "/app/dist/server.js"]
