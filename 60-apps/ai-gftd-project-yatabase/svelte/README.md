# yatabase Studio (SvelteKit + @gftdcojp/design-system)

UI for `https://yatabase.gftd.ai/studio/*`. Static-prerendered SvelteKit
CSR (`adapter-static`, `fallback: index.html`), served by the yatabase
CF Worker's Workers Assets binding (`wrangler.jsonc → assets.directory =
./svelte/build`).

## Stack

- **Svelte 5** runes (`$state` / `$derived` / `$props`)
- **SvelteKit** (`adapter-static` + `single-page-application` fallback)
- **Tailwind 3** + `@gftdcojp/design-system/plugin` (gftdUIKit) + the
  AppShell v2 token set (`--gv2-*` CSS custom properties)
- **`@gftdcojp/design-system`** components only — no custom UI primitives
  (per `40-engine/svelte/CLAUDE.md` §"UIKit (design-system) 必須")

## Routes

| Route | Page | Description |
|---|---|---|
| `/` | `routes/+page.svelte` | Redirects to `/studio` |
| `/studio` | `routes/studio/+page.svelte` | Home: plan + identity + API key + quick wins |
| `/studio/cypher` | `routes/studio/cypher/+page.svelte` | Cypher query editor + result table + history |
| `/studio/storage` | `routes/studio/storage/+page.svelte` | S3-compat object browser (PUT/list/delete/sign) |
| `/studio/billing` | `routes/studio/billing/+page.svelte` | Plan + 24h/30d usage + Stripe portal link |

## Auth

The user pastes their `sk_live_yata_*` API key into `SignInPanel`. It's
persisted to `localStorage` (`yatabase-studio:apiKey`) and sent as a
Bearer token on every API call. `lib/stores.ts` validates via
`/auth/v1/whoami` and caches identity + plan.

No Passkey / AT JWT integration in this iteration — the Studio target
user is a developer who already has an API key from `/auth/v1/signup`.

## Develop

```bash
cd 60-apps/ai-gftd-project-yatabase/svelte
pnpm install
# Option 1: dev against the live yatabase.gftd.ai (fastest):
VITE_YATABASE_ORIGIN=https://yatabase.gftd.ai pnpm dev
# Option 2: dev against a local Worker (`wrangler dev` in the parent):
pnpm dev
```

`vite.config.ts` proxies `/xrpc`, `/storage`, `/auth`, `/api`,
`/cypher`, `/mcp` to `$VITE_YATABASE_ORIGIN` when set, so the dev
server can talk to production without CORS gymnastics.

## Build & deploy

```bash
cd 60-apps/ai-gftd-project-yatabase
pnpm deploy                     # vite build → gftd deploy
# or fast (skip svelte rebuild):
pnpm deploy:fast
```

`pnpm deploy` runs `cd svelte && pnpm build` → writes to
`svelte/build/` → `gftd deploy --no-svelte` uploads the parent
Worker (the Worker's `assets.directory` is already pointed at
`./svelte/build`).

## Rules followed

- **No custom CSS in `.svelte` files** — Tailwind utilities only,
  matching `40-engine/svelte/CLAUDE.md` §"Tailwind-Only" rule.
  `app.css` is the single home for `@tailwind` directives + html/body
  defaults.
- **Design tokens via `--gv2-*` CSS custom properties** with light/dark
  switch on `html[data-theme=…]`.
- **No SSR** (`ssr = false`, `prerender = true`). The Studio is fully
  client-rendered against the edge Worker.
- **Components imported from `@gftdcojp/design-system`** only:
  `Button`, `Input`, `Textarea`, `Card`, `Badge`, `NotificationBanner`,
  `EmptyState`, `ErrorText`, `Label`, `SupportText`, `Skeleton`.
