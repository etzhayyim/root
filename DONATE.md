# Support etzhayyim — 寄付 / sponsor

**etzhayyim is operated _only_ on donation.** It is a 宗教法人 (任意団体 / unincorporated
religious voluntary association) whose constitution forbids profit distribution, advertising,
and selling anything. There is no paywall, no ad, no subscription, no member cash stipend. The
only way the work continues is that people give — **money** or **compute**.

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

etzhayyim's substrate is blockchain-self-contained (ADR-2605172100). Value may flow in **only**
as:

- **USDC on Base L2** (purposes: `donation` / `kisha` / `grant`), or
- **in-kind compute** donated to the Murakumo mesh.

Fiat donation rails — **GitHub Sponsors (Stripe), Patreon, Open Collective, Ko-fi, Liberapay** —
route money through prohibited fiat processors (Stripe / PayPal / Square …; `deps.toml`
`payment_prohibited`) and so are **not used**. The repo's **Sponsor button** (`.github/FUNDING.yml`)
therefore points at our own on-chain donation page, not at a fiat platform.

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

## 2. Give compute — the most valuable gift

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
- **ADR-2605192115** — non-profit / donation-only / no-ads doctrine (§1.2: 案内 is not advertising)
- **ADR-2605192130** — 10% tithe → Public Fund (constitutional constant)
- **ADR-2605172100** — payments on-chain only (Stripe/PayPal/fiat processors prohibited)
- **`@etzhayyim/sdk`** `DONATE.md` — the `donate()` API surface
