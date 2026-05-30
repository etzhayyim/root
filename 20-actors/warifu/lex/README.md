# warifu lexicons

Wire-level AT-Proto lexicons live in **`10-protocol/warifu/`** under the `app.etzhayyim.card.*`
namespace:

| Lexicon | Purpose |
|---|---|
| `app.etzhayyim.card.issue` | issue a soulbound card (WarifuCard, ERC-5192) bound to a holder smart account |
| `app.etzhayyim.card.authorize` | authorize (debit hold / credit reserve) |
| `app.etzhayyim.card.capture` | capture an authorized hold |
| `app.etzhayyim.card.settle` | on-chain settlement (T+0, fee 0) |
| `app.etzhayyim.card.refund` | reverse transfer (purpose `escrow-refund`) |
| `app.etzhayyim.card.dispute` | chargeback / dispute record → chigiri procedure |

Per-cell I/O contracts (`warifu.authorize`, `warifu.settle`, …) live in `../cells/lex/`.
