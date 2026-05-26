# ai-gftd-project-fm

Investment fund domain baseline for `fund.etzhayyim.com`.

- Public domains covered by this seed:
  - `sovereign_fund`
  - `mutual_fund`
  - `pension_fund`
  - `private_fund`
  - `government_fund`
  - `investor_fund`
- Seeded collections:
  - `app.etzhayyim.apps.fund.fund`
  - `app.etzhayyim.apps.fund.manager`
  - `app.etzhayyim.apps.fund.investor`
  - `app.etzhayyim.apps.fund.investee`
  - `app.etzhayyim.apps.fund.metric`
  - `app.etzhayyim.apps.fund.commitment`

## Why this exists

`public_fund` is a separate crowdfunding / budget-disbursement domain on
`public-fund.etzhayyim.com`. Investment-fund coverage should be bootstrapped from
`fund.etzhayyim.com` records, not only from `public_fund`.

## Seed

Authoritative path:

```bash
gftd seed --app fund
```

Direct PDS seed script:

```bash
export etzhayyim_TOKEN="$(gftd authn token)"
npx tsx 60-apps/ai-gftd-project-fm/seed.ts
```

After seeding, re-check:

```bash
gftd coverage world --domain sovereign_fund,mutual_fund,pension_fund,private_fund,government_fund,investor_fund
```
