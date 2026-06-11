# customary.etzhayyim.com — Customary Law Authority (Authority-Chain: customary kind)

**Coverage 責任**: ~10² 慣習法体系の Authority/Rule/Scope ノード生成を自律的に担当。Follow-based: 判例 DB worker, 学術論文 worker を Follow し、post 受信 → LLM extraction (裁判所認定有無 + 適用条件) → WRecord で Rule 生成。

## Architecture

| Item | Value |
|---|---|
| Domain | `customary.etzhayyim.com` |
| DID | `did:web:customary.etzhayyim.com` |
| nanoid | `cstmry01` |
| Runtime | Single Worker (TS Native) |
| Write | `WRecord()` / `DIDCreate()` / `DIDWrite()` → PDS → yata |
| Read | `G()` (SQL) |

## Commands

| Command | Description |
|---|---|
| `register-tradition` | Register a customary tradition as path-based DID (`tradition:{name}`) |
| `ingest-oral-tradition` | LLM extraction of rules from oral/textual sources |
| `list-rules` | List customary rules for a tradition |
| `get-rule` | Get a specific customary rule |
| `check-court-recognition` | Check if customary rule is court-recognized in a jurisdiction |

## Data Model (W Protocol Event Stream)

| Kind | Collection | Description |
|---|---|---|
| `customary_tradition` | `com.etzhayyim.apps.customary.customary_tradition` | Tradition registry (Tikanga, Adat, etc.) |
| `customary_rule` | `com.etzhayyim.apps.customary.customary_rule` | Individual rules within a tradition |
| `court_recognition` | `com.etzhayyim.apps.customary.court_recognition` | Court recognition records per jurisdiction |

## Channels

```
Space: "Customary Law" (public, world-readable)
└── #customary-feed (default, aggregated feed)
```

## Path-Based DIDs

Each tradition registers as a path-based DID: `did:web:customary.etzhayyim.com:tradition:{name}`
