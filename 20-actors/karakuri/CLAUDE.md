# karakuri (絡繰) — web-service-to-CLI actor

**DID**: `did:web:etzhayyim.com:actor:karakuri` · **Tier**: B · **Status**: R0 · **ADR**: 2606039200

## What this is

The actor that **turns a GUI-only web service into a CLI** — the charter-clean answer to the
`clianything.org`-shaped request (*「squarespace のような webservice も CLI にする actor」*). 絡繰 =
the karakuri mechanism that drives a manual service by command (the Toyota karakuri-kaizen sense:
clever automation that removes manual toil; ties to the labor-liberation mission + KaizenObserverCell).

It is the **charter-clean inverse of clianything.org**, the way okaimono inverts Amazon and yadori
inverts GoDaddy: **own-account-only · official-API-first · ToS-honest (no detection-evasion) ·
no-server-key · member-signed mutate · data-portability over lock-in**. The uniform vocabulary is a
normalized **`ServiceOp`** (`service · noun · verb · safety · destructive · adapter-tier`), one vocab
across the TS/py runtimes (the sumitsubo `ModelOp` pattern). Three adapter tiers, safest-first:
**T1 official-API** > **T2 ToS-permitted headless-browser** > **T3 structured export**.

ISIC J6201 · ISCO 2512/3514 · UNSPSC 81112 (computer programming / web automation).

## Cells (langgraph→WASM; Murakumo-only; `.solve()` raises at R0)

service_resolve (reuben) · command_plan (simeon) · **session_broker** (levi — coded reference cell) ·
adapter_invoke (judah) · export_roundtrip (zebulun).

## Gates (immutable R0→R3)

**G1 member-principal / own-account-only** (drives only the member's OWN authenticated account; no
third-party access; no scrape-this-site product) · **G2 official-API-preferred / ToS-honest** (prefer
T1; T2 headless only where ToS permits; **no detection-evasion** — no captcha-farm / proxy-cloaking /
rate-limit circumvention; `:automation-prohibited` refuses T2 by construction) · **G3 no-server-key**
(member creds/sessions member-held + encrypted; mutate authorized by member signature; server
signature refused, ADR-2605231525) · G4 Murakumo-only · **G5 read-default / mutate-gated** (read +
export ship at R0; create/update/**delete** require member-sig + explicit dry-run confirm) ·
**G6 outward-gated** (ANY live third-party network call Council Lv6+ + operator gated; R0 =
parse/plan/dry-run only) · **G7 kotoba-EAVT audit** (every planned + executed ServiceOp = a Datom;
member can audit what touched their account) · G8 sourcing-honesty (`:representative` registry;
unknown service/op degrades honestly) · G9 PII / portability-consent (export = member's OWN data only,
encrypted).

## Non-goals

N1 not a scraper/surveillance/third-party-harvesting tool · N2 no detection-evasion / anti-bot
circumvention / captcha-farming / proxy-cloaking · N3 no credential-stuffing / account-takeover /
shared-account abuse · N4 no paywall/license/DRM circumvention or content piracy (portability =
member's OWN data) · N5 not a bot-farm / mass-automation / spam / fake-engagement engine · N6 no
driving of prohibited-content or third-party ad/affiliate systems (Charter-Rider §2(a)–(h)).

## Build / test

```
cd methods && python3 -m pytest                 # ServiceOp parser/planner (21 tests)
cd cells   && python3 -m pytest                 # session_broker state machine G1/G3/G5 (8 tests)
python3 methods/command.py karakuri squarespace pages.list   # offline planner demo
```

(If a global pytest plugin errors on pydantic, prefix `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` — the
karakuri code is stdlib-only.)

R0 = design + ServiceOp parser/planner + session_broker state-machine + `:representative` service
registry only. **No live execution** of any adapter (T1/T2/T3); all gated Council Lv6+ + operator (G6).

## Do not

- Do not operate any account that is not the member's OWN, and do not build a third-party scraper /
  surveillance / data-harvesting feature — G1 / N1.
- Do not use the T2 headless-browser adapter on a service whose ToS prohibits automation, and never
  add detection-evasion (captcha-solving-as-evasion, proxy/IP rotation, rate-limit circumvention) —
  G2 / N2 (`command.py tos_gate()` refuses; `select_tier()` is official-API-first).
- Do not store member service credentials/sessions server-side or let karakuri sign a mutating op —
  G3 / ADR-2605231525. The grant carries only an encrypted-envelope ref; the member signs.
- Do not execute any create/update/delete without member-sig + dry-run confirm, and never run a live
  adapter call without operator + Council — G5 / G6.
- Do not call any cell's `.solve()` — R0 scaffolds raise `RuntimeError` by design.
- Do not drive prohibited-content or third-party ad/affiliate systems — N6 / Charter-Rider §2.
