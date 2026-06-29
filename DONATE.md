# Support etzhayyim — 寄付 / sponsor

**etzhayyim is operated _only_ on donation.** It is a 宗教法人 (任意団体 / unincorporated
religious voluntary association) whose constitution forbids profit distribution, advertising,
and selling anything. There is no paywall, no ad, no subscription, no member cash stipend. The
only way the work continues is that people give — **money** (USDC, other crypto, or fiat),
**compute**, or by **paying one of the mission's bills**.

> **Giving earns you nothing.** No perks, no tiers, no priority, no governance weight, no
> recognition leaderboard. A donation is a pure gift (anti-class invariant, ADR-2606012100 §G4).
> We say this up front so the ask is honest: you give because the mission is worth it, not for
> a benefit.

This is the public-facing companion to the always-on declaration at
**<https://etzhayyim.com/donate>** (human page) and
**<https://etzhayyim.com/.well-known/donation.json>** (machine-readable policy — the
**single source of truth** for live on-chain addresses).

---

## Why only on-chain / in-kind — and why no GitHub Sponsors / Patreon / Stripe

etzhayyim's substrate is blockchain-self-contained (ADR-2605172100). The load-bearing rule is
**no money custodian can hold, freeze, or KYC-gate etzhayyim's funds** — not "the word fiat is
forbidden." Under that rule, value may flow in as: **USDC on Base L2**, a **curated crypto
allowlist** (held as-is), **fiat via a non-custodial USDC-settling on-ramp**, **in-kind compute**,
or **in-kind fiat** (paying a mission bill direct to the vendor) — all **donation purpose only**
(ADR-2606111800).

What stays prohibited: **custodial** fiat rails — **GitHub Sponsors (Stripe), Patreon, Open
Collective, Ko-fi, Liberapay** — that hold the balance / KYC etzhayyim / retain donor PII (`deps.toml`
`payment_prohibited`). The repo's **Sponsor button** (`.github/FUNDING.yml`) therefore points at
our own on-chain donation page, not at a fiat platform.

---

## 1. Give money — USDC on Base L2

Donations settle on-chain through **`TitheRouter.donate()`**: **90%** goes to the recipient
program, **10%** auto-splits to the **Public Fund** (the constitutional 10% tithe,
`tithe_to_public_fund_bps = 1000`, ADR-2605192130). No fiat processor, no middleman fee.

| | |
|---|---|
| Asset | **USDC** (Base L2 — `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, 6 decimals) |
| Rail | `TitheRouter.donate(recipient, grossAmount, purpose)` |
| Purposes | `donation` (unrestricted) · `kisha` (structured charitable, tithe-exempt) · `grant` (time-bound project) |
| Split | 90% recipient program / 10% Public Fund (1 SBT = 1 vote governance) |
| SDK | `import { donate } from "@etzhayyim/sdk/donate"` |

> **On-chain donation address — status: pending.** The TitheRouter / Public-Fund Safe addresses
> are **not deployed yet** (Base L2 testnet is pending Bootstrap-Council ratification; Council
> Seats 2–5 RFP closes 2026-06-19). **No donation address is published in this file by design** —
> the canonical address appears at **<https://etzhayyim.com/.well-known/donation.json>** the
> moment it is live, in exactly one place, so it can never drift. Do **not** send funds to any
> address claimed elsewhere.

### Other crypto assets (held as-is)

Beyond USDC we accept a **curated allowlist of liquid majors** — **ETH / WETH / USDC / USDT /
DAI** — **held in their native asset** (not auto-swapped), with the 10% tithe computed **per
asset** at receipt. No memecoins, no algorithmic stablecoins (issuer/peg risk). Adding an asset
is a Council Tier-2 governance parameter. (ADR-2606111800 §C; per-asset TitheRouter support is a
follow-up — until then non-USDC gifts are recorded and manually tithed.)

### Auspicious local presets

Donation amount buttons may use culturally local auspicious numbers — for example JP-facing
surfaces can prefer `5`, `8`, `88`, `108`, while Jewish-facing surfaces can prefer `18`/`36`,
Chinese-facing surfaces can prefer `8`/`88`/`168`, US/West-facing surfaces can prefer dozen-family
counts like `12`/`24`/`36`/`72`/`144`, and Indian-facing surfaces can prefer `11`/`21`/`51`/`108`.
These are only defaults: any amount is valid, no number creates a donor tier, and custom amount
entry must always remain visible. (ADR-2606290830.)

### Give in fiat — via a non-custodial on-ramp

Prefer your **card or bank**? You can give in fiat through a **non-custodial on-ramp** that
**settles immediately to USDC on-chain** at the donation address. The point of difference (and why
this is charter-clean): **etzhayyim never holds a fiat balance, retains _no_ donor PII** (any KYC
is strictly between you and the on-ramp), and **no processor can ever freeze etzhayyim's
treasury** — preserving the exact property the on-chain-only rule protects. A **custodial** fiat
processor (one that holds our balance / KYCs etzhayyim / keeps your data) stays **prohibited**.
(ADR-2606111800 §B — a Tier-1 amendment ratified by Council Lv7+ unanimity.)

## 2. Pay one of our bills — fiat, in-kind (how the founder already gives)

The most direct fiat gift needs **no on-ramp at all**: **pay one of the mission's real-world
costs** — a **server / cloud / domain / bandwidth / hardware** bill — **directly to the vendor**,
for the mission. **No money flows to etzhayyim** (exactly like donating compute), so no fiat
processor and no amendment is involved — it is already charter-clean. It is **imputed-valued for
transparency only** (toritate, aggregate, no per-donor leaderboard), **non-titheable**, and earns
you nothing.

This is, in fact, how the **founder already donates** — paying the servers in Japanese yen. The
new record **`com.etzhayyim.give.infrastructureDonationAttestation`** makes that (and any
supporter's bill) a visible, accountable in-kind donation for the first time. (ADR-2606111800 §A.)

## 3. Give compute — the most valuable gift

Our inference runs on the **Murakumo mesh only** — we deliberately do **not** rent commercial
GPUs (ADR-2605215000). So donated compute goes **directly** to the mission. It is an
**uncompensated, non-titheable gift** (no USDC moves, so nothing to split — 100% serves the
mission): it earns you nothing and is never required.

| Node class | How | Notes |
|---|---|---|
| **ameno** | Open a consent-gated browser tab → WebGPU/WebNN inference on frozen baien edge models | Zero install (WASM-32, iPhone 12+ / Android 4GB); honors a battery/thermal budget; runs only while opted-in |
| **e7m** | `e7m node join` (and `e7m node leave` to stop) — register a laptop/workstation as an Ollama (gemma3:4b) / WASM node | You hold your own key; etzhayyim holds none (no-server-key) |
| **kotoba** | Run a kotoba pod — IPFS block backend + Datom replication (optional Ollama) | Your hardware, your keys; best-effort, SLA-free |

Donated compute joins the Murakumo fleet as a **first-party node** — never a commercial cloud.
It is valued (imputed, for transparency only — aggregate, no per-donor leaderboard, via toritate
accounting) but no money moves to or from you and donating more grants no priority.

> Live external mesh-enrollment is being rolled out under Council oversight (ADR-2606012100 §G9,
> R0 design today).

---

## What your gift funds (and what it never funds)

- **Funds:** the mission — 人類の構造的労働解放, the open actor mesh, the kotoba substrate,
  Murakumo inference, the Public Fund (grants to charter-aligned programs).
- **Never funds:** profit distribution (there are no shareholders), advertising (none, ever),
  member cash stipends (`adherentCashStipend = 0`, Basic High Income is in-kind), or any
  commercial GPU rental.

## References

- **Live:** <https://etzhayyim.com/donate> · <https://etzhayyim.com/.well-known/donation.json>
- **ADR-2606012100** — donation-funded operation + compute-node donation (the design this implements)
- **ADR-2606111700** — public sponsor/donation solicitation surfaces (FUNDING.yml + this doc + /donate CTA)
- **ADR-2606111800** — donation-media expansion: fiat in-kind (§A) + non-custodial fiat on-ramp (§B, Tier-1 amendment) + curated crypto allowlist (§C)
- **ADR-2606290830** — culturally scoped auspicious-number defaults for donation and root surfaces
- **ADR-2605192115** — non-profit / donation-only / no-ads doctrine (§1.2: 案内 is not advertising)
- **ADR-2605192130** — 10% tithe → Public Fund (constitutional constant)
- **ADR-2605172100** — payments on-chain only (the rule §B narrows; custodial fiat stays prohibited)
- **`com.etzhayyim.give.infrastructureDonationAttestation`** — the in-kind fiat (infra-cost) donation record
- **`@etzhayyim/sdk`** `DONATE.md` — the `donate()` API surface
