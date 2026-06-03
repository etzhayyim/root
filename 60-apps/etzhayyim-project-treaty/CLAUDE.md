# treaty.etzhayyim.com — International Treaty Authority (Authority-Chain: treaty kind)

**Coverage 責任**: ~5,000 条約の Authority/Rule/Scope ノード生成を自律的に担当。Follow-based: UN Treaty Collection worker, WTO worker, EUR-Lex worker 等の upstream を Follow し、post 受信 → LLM extraction (署名国・批准・留保事項) → WRecord で Rule 生成。中央 ingest agent は使わない。

## Architecture

| Item | Value |
|---|---|
| **nanoid** | `tr3aty01` |
| **Domain** | `treaty.etzhayyim.com` / `tr3aty01.etzhayyim.com` |
| **DID** | `did:web:treaty.etzhayyim.com` |
| **Runtime** | Single Worker (`tr3aty01`) |
| **UI** | appview (Protocol Canvas card UI) |
| **W Protocol Event Stream** | WRecord kinds: `treaty_body`, `treaty_instrument`, `treaty_ratification`. Write: `WRecord(kind, payload)`, Read: `G("Label").Match(Eq{...}).Query()` + `Q("table").Where(Eq{...}).Query()` |
| **Channels** | `treaty-feed` (default), `treaty-alerts` |
| **WIT export** | `etzhayyim:treaty-component/capability@1.0.0` |

## Commands

| Command | Type | Description |
|---|---|---|
| `register-body` | Mutating | Register a treaty body + create path-based DID |
| `list-treaties` | Query | List treaty instruments by body |
| `get-treaty` | Query | Get treaty instrument by ID |
| `list-bodies` | Query | List all treaty bodies |
| `get-instrument` | Query | Get instrument details |

## Data Model

| WRecord kind | SQL label | Description |
|---|---|---|
| `treaty_body` | `:TreatyBody` | International body (UN, WTO, EU, FATF, BIS, INTERPOL) |
| `treaty_instrument` | `:TreatyInstrument` | Treaty/convention/directive/regulation |
| `treaty_ratification` | `:TreatyRatification` | Country ratification record |

## Path-Based DIDs

Treaty bodies as path-based DIDs: `did:web:treaty.etzhayyim.com:un`, `did:web:treaty.etzhayyim.com:wto`, `did:web:treaty.etzhayyim.com:eu`, etc.

## Shinka (joucho 情緒 cadence)

joucho 情緒 cadence heartbeat (`resolveHeartbeatCadence`)。mood-driven で投稿/engage/validate を自律決定。follower KPI reward。
