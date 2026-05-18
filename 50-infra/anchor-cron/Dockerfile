# anchor-cron — Stage 5b of ADR-2605171800.
# Submits sidecar-flagged MST roots to EtzhayyimAnchor on Base L2 and
# writes the receipts back to the sidecar's index.
#
# Build context: repo root.
#
#   docker build -f 50-infra/anchor-cron/Dockerfile \
#     -t ghcr.io/etzhayyim/anchor-cron:$(git rev-parse --short HEAD) .

# ── Build stage ───────────────────────────────────────────────────────────────

FROM node:22-alpine AS builder

WORKDIR /build

RUN corepack enable && corepack prepare pnpm@9 --activate

COPY 50-infra/anchor-cron/package.json 50-infra/anchor-cron/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.pnpm-store \
    pnpm install --frozen-lockfile --ignore-scripts

COPY 50-infra/anchor-cron/tsconfig.json ./
COPY 50-infra/anchor-cron/src ./src
RUN pnpm build

RUN --mount=type=cache,target=/root/.pnpm-store \
    pnpm install --prod --frozen-lockfile --ignore-scripts

# ── Runtime stage ─────────────────────────────────────────────────────────────

FROM node:22-alpine AS runtime

RUN apk add --no-cache tini

WORKDIR /anchor-cron

COPY --from=builder /build/node_modules ./node_modules
COPY --from=builder /build/dist ./dist
COPY 50-infra/anchor-cron/package.json ./

# Same uid as the sidecar / langserver containers so it can mount the
# checkpointer-socket emptyDir without group acrobatics.
USER node:node

ENTRYPOINT ["/sbin/tini", "--", "node", "dist/index.js"]
