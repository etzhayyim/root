# industry-standard.etzhayyim.com — Industry Standard Authority (Authority-Chain: industry kind)

**Coverage 責任**: ~10³ 業界標準の Authority/Rule/Scope ノード生成を自律的に担当。Follow-based: ISO/NIST/PCI worker, 認証機関 worker を Follow し、post 受信 → LLM extraction (要件構造化: control→requirement→evidence) → WRecord で Rule 生成。

## Architecture

| 項目 | 値 |
|---|---|
| **nanoid** | `indstd01` |
| **Domain** | `industry-standard.etzhayyim.com` |
| **DID** | `did:web:industry-standard.etzhayyim.com` |
| **Runtime** | Single Worker (`indstd01`) |
| **UI** | appview (Protocol Canvas card UI) |
| **W Protocol Event Stream** | WRecord kinds: `industry_body`, `industry_standard`, `standard_requirement`, `certification_status`. Write: `WRecord(kind, payload)`, Read: `G("Label").Match(Eq{...}).Query()` + `Q("table").Where(Eq{...}).Query()` |
| **Channels** | `industry-feed`, `industry-alerts` |
| **WIT export** | `etzhayyim:industry-standard-component/capability@1.0.0` |

## Commands

| Command | Type | Description |
|---|---|---|
| `register-body` | Mutating | DIDCreate for industry body paths (e.g. `finance:pci_dss`, `food:haccp`, `esg:gri`) |
| `register-standard` | Mutating | Create standard record for a body |
| `ingest-standard-text` | Mutating | LLM extraction of requirements from standard text |
| `list-standards` | Query | List standards by sector |
| `get-standard` | Query | Get single standard by ID |
| `check-certification` | Query | Check if app/org DID holds active certification for a standard |

## Data Model

| WRecord kind | SQL Label | Description |
|---|---|---|
| `industry_body` | `:IndustryBody` | Standards body (e.g. PCI SSC, Codex Alimentarius, GRI) |
| `industry_standard` | `:IndustryStandard` | Standard document (e.g. PCI-DSS v4.0, HACCP Codex) |
| `standard_requirement` | `:StandardRequirement` | Individual requirement extracted from a standard |
| `certification_status` | `:CertificationStatus` | Certification status of an org/app against a standard |

## Path-Based DIDs

Industry bodies are managed as path-based DIDs:

- `did:web:industry-standard.etzhayyim.com:finance:pci_dss`
- `did:web:industry-standard.etzhayyim.com:finance:swift_csp`
- `did:web:industry-standard.etzhayyim.com:food:haccp`
- `did:web:industry-standard.etzhayyim.com:esg:gri`
- `did:web:industry-standard.etzhayyim.com:esg:tcfd`
- `did:web:industry-standard.etzhayyim.com:cyber:nist_csf`
- `did:web:industry-standard.etzhayyim.com:cyber:cis_controls`
- `did:web:industry-standard.etzhayyim.com:aviation:icao`
- `did:web:industry-standard.etzhayyim.com:maritime:imo`
- `did:web:industry-standard.etzhayyim.com:nuclear:iaea`
