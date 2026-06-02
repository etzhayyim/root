# ethics.etzhayyim.com — Professional/Academic Ethics Authority (Authority-Chain: professional + academic kind)

**Coverage 責任**: ~10² 倫理綱領の Authority/Rule/Scope ノード生成を自律的に担当。Follow-based: 職能団体 worker, 学術誌 worker を Follow し、post 受信 → LLM extraction (義務種類分類: prohibit/consent/disclose/license-check) → WRecord で Rule 生成。

## Architecture

| 項目 | 値 |
|---|---|
| **nanoid** | `eth1cs01` |
| **Domain** | `ethics.etzhayyim.com` |
| **DID** | `did:web:ethics.etzhayyim.com` |
| **Runtime** | Single Worker (`eth1cs01`) |
| **UI** | appview (Protocol Canvas card UI) |
| **W Protocol Event Stream** | WRecord kinds: `professional_code`, `academic_code`, `ethics_rule`. Write: `WRecord(kind, payload)`, Read: `G("Label").Match(Eq{...}).Query()` + `Q("table").Where(Eq{...}).Query()` |
| **Channels** | `ethics-feed`, `ethics-alerts` |
| **WIT export** | `etzhayyim:ethics-component/capability@1.0.0` |

## Commands

| Command | Type | Description |
|---|---|---|
| `register-profession` | Mutating | DIDCreate for profession paths (e.g. `medical:hippocratic`, `legal:aba_model_rules`, `engineering:ieee`) |
| `register-code` | Mutating | Create ethics code record for a profession |
| `ingest-code-text` | Mutating | LLM extraction of rules from ethics code text |
| `list-rules` | Query | List ethics rules by profession |
| `get-rule` | Query | Get single ethics rule by ID |
| `check-license-status` | Query | Check if person DID holds active professional license |

## Data Model

| WRecord kind | SQL Label | Description |
|---|---|---|
| `professional_code` | `:ProfessionalCode` | Professional ethics code (e.g. Hippocratic Oath, ABA Model Rules) |
| `academic_code` | `:AcademicCode` | Academic ethics code (e.g. COPE, ICMJE) |
| `ethics_rule` | `:EthicsRule` | Individual rule extracted from a code |

## Path-Based DIDs

Professions are managed as path-based DIDs under the primary DID:

- `did:web:ethics.etzhayyim.com:medical:hippocratic`
- `did:web:ethics.etzhayyim.com:legal:aba_model_rules`
- `did:web:ethics.etzhayyim.com:engineering:ieee`
- `did:web:ethics.etzhayyim.com:accounting:ifac`
- `did:web:ethics.etzhayyim.com:journalism:spj`
- `did:web:ethics.etzhayyim.com:academic:cope`
- `did:web:ethics.etzhayyim.com:academic:icmje`
