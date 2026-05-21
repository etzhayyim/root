# ai-gftd-project-fm

Investment fund domain baseline for `fund.gftd.ai`.

- Public domains covered by this seed:
  - `sovereign_fund`
  - `mutual_fund`
  - `pension_fund`
  - `private_fund`
  - `government_fund`
  - `investor_fund`
- Seeded collections:
  - `ai.gftd.apps.fund.fund`
  - `ai.gftd.apps.fund.manager`
  - `ai.gftd.apps.fund.investor`
  - `ai.gftd.apps.fund.investee`
  - `ai.gftd.apps.fund.metric`
  - `ai.gftd.apps.fund.commitment`

## Why this exists

`public_fund` is a separate crowdfunding / budget-disbursement domain on
`public-fund.gftd.ai`. Investment-fund coverage should be bootstrapped from
`fund.gftd.ai` records, not only from `public_fund`.

## Seed

Authoritative path:

```bash
gftd seed --app fund
```

Direct PDS seed script:

```bash
export GFTD_TOKEN="$(gftd authn token)"
npx tsx 60-apps/ai-gftd-project-fm/seed.ts
```

After seeding, re-check:

```bash
gftd coverage world --domain sovereign_fund,mutual_fund,pension_fund,private_fund,government_fund,investor_fund
```
