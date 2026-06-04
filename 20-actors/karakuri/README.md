# karakuri 絡繰 — web-service-to-CLI

karakuri gives a member a uniform **command-line / programmatic handle over GUI-only web services**
(Squarespace, Wix, Notion, Shopify, …) — the charter-clean answer to the `clianything.org`-shaped
request *「squarespace のような webservice も CLI にする actor を設計して」*. 絡繰 = the *karakuri*
mechanism that drives a manual service by command — in the Toyota karakuri-kaizen sense: clever,
low-cost automation that removes manual clicking toil.

It is deliberately **not** a `clianything.org` clone. A generic "drive any website" SaaS imports four
violations; karakuri inverts each:

- **Own account only.** karakuri operates **only the member's OWN authenticated account** — never
  harvests third-party data, never a "scrape this site" product (G1, himotoki prior art).
- **Official API first, ToS-honest.** It prefers the service's **official API** (T1); uses
  headless-browser automation (T2) **only where the ToS permits**; and **never evades bot-detection**
  (no captcha-farming, no proxy/IP cloaking, no rate-limit circumvention) (G2).
- **No server-held keys.** The member's credentials/sessions stay with the member-operator,
  encrypted; the member **signs every mutating action** and a server signature is refused (G3,
  ADR-2605231525).
- **Auditable + portable.** Every planned/executed op is a **kotoba Datom** (`as-of`, replayable),
  and the **export round-trip** (T3) makes the member's data portable — the inverse of lock-in (G7/G9).

## The uniform vocabulary — `ServiceOp`

A CLI string parses into exactly one normalized op:

```
karakuri <service> <noun>.<verb> [--flag value ...]
```

…carrying a classified `safety` (`read`/`create`/`update`/`delete`), a `destructive` flag, and the
selected adapter `tier` (T1 official-API > T2 ToS-permitted headless > T3 export).

## Status

R0 (design + working ServiceOp parser/planner + session_broker state machine + `:representative`
service registry). **No live execution** — every adapter call is Council Lv6+ + operator gated (G6);
R0 is parse / plan / dry-run only. See `90-docs/adr/2606039200-*` and `CLAUDE.md` for gates G1–G9 and
non-goals N1–N6.

## Try the planner (offline, no network)

```
python3 methods/command.py karakuri squarespace pages.list
python3 methods/command.py karakuri shopify products.delete --id 42      # destructive → awaiting-member-sig
python3 methods/command.py karakuri notion database.update --title Hello # mutate → awaiting-member-sig
python3 methods/command.py karakuri totally-unknown widgets.list         # unknown service → honest degrade
```
