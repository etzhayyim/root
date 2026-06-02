# etzhayyim-project-demining

Humanitarian Mine Action (HMA) platform — detection, survey, clearance, land release, EORE, victim assistance. **Design stage.** No Worker deployed yet.

## Scope = Humanitarian Mine Action ONLY

| In scope | Out of scope (hard prohibited) |
|---|---|
| Non-Technical Survey / Technical Survey | Manufacture, stockpile, transfer, deployment of APM |
| Manual / MDD / mechanical clearance | Offensive EOD, counter-mobility |
| Land Release (IMAS 07.11) | Real-time targeting, weaponization |
| EORE (IMAS 12.10) | |
| Victim assistance referral | |
| Detector / PPE / MDD / flail inventory | |

**Legal basis**: Anti-Personnel Mine Ban Convention (Ottawa, 1997) + 対人地雷の製造の禁止及び所持の規制等に関する法律 (平成10年法律第115号) + CCM + CCW Protocol V. Prohibits any actor/app that produces, holds, or transfers APM. This project implements the *counter* side (detection + clearance).

## Authoritative taxonomy: IMAS

The authoritative technical taxonomy for this domain is **IMAS (International Mine Action Standards)** maintained by UNMAS / GICHD — not UNSPSC/CPC. UNSPSC/CPC are included for procurement/statistics crosswalk only.

See `legalInstruments.jsonld` for global legal layer (3 multilateral treaties + 5 regional instruments + 34 national implementation statutes across 33 jurisdictions, incl. non-party heavy users US/RU/CN/IN/KR and heavily-contaminated states AF/CO/KH/LA/UA/IQ/BA/HR).

See `classifications.jsonld` for:
- IMAS series → activity mapping
- UNSPSC family 46101500 (Mine clearing equipment) + children → asset types
- CPC v2.1 crosswalk (no clean class; falls under 91290 public order services or 94900 n.e.c.)
- ISIC 8412 (public administration — defence, public order, safety) crosswalk
- EO item taxonomy: AP mine / AT mine / UXO / ERW / IED / cluster submunition

## Identity (TBD — not yet registered)

| Key | Value |
|---|---|
| nanoid | **TBD** — register via `etzhayyim actor register demining` |
| domain | `demining.etzhayyim.com` |
| AT bot DID | `did:web:demining.etzhayyim.com` |
| Execution tier | **T1 MCP-Compose** (see `20-actors/demining/actor-manifest.jsonld`) |
| Data store | RisingWave via Hyperdrive (read), PDS pipeline (write) |

## Sensitivity tiering (CRITICAL)

AT Protocol Repo = always public / federable. Publishing uncleared minefield coordinates endangers civilians (IMAS 05.10 information security). Therefore:

| Data | Tier | Storage |
|---|---|---|
| SHA / CHA polygon while uncleared | **Tier 3** | `Preferences()` server-side, not in Repo |
| Exact detector hit coordinates | **Tier 3** | `Preferences()` |
| Victim PII | **Tier 3** | `Preferences()` |
| Operator PII (deminer identity) | **Tier 3** | `Preferences()` |
| Detector / PPE / MDD inventory | Tier 2 | `ComAtprotoRepoCreateRecord("assetRecord")` |
| Task record (de-identified) | Tier 2 | `ComAtprotoRepoCreateRecord("clearanceTask")` |
| Released area polygon (post-clearance) | Tier 1 | `AppBskyFeedPost` + public record |
| EORE outreach summary | Tier 1 | `AppBskyFeedPost` |
| Aggregate statistics | Tier 1 | `AppBskyFeedPost` |

Tier demotion (3 → 1) happens only on Land Release decision per IMAS 07.11, recorded via `releaseArea` procedure.

## Planned actors (path-based Multi-DID)

| DID | Role | IMAS ref |
|---|---|---|
| `did:web:demining.etzhayyim.com` | Controller / coordinator | 07.10 |
| `did:web:demining.etzhayyim.com:actor:survey` | NTS + TS data capture | 08.10 / 08.20 |
| `did:web:demining.etzhayyim.com:actor:clearance` | Clearance task lifecycle | 09.10 |
| `did:web:demining.etzhayyim.com:actor:release` | Land Release decision record | 07.11 |
| `did:web:demining.etzhayyim.com:actor:eore` | EORE session + beneficiary | 12.10 |
| `did:web:demining.etzhayyim.com:actor:victim-assistance` | Victim referral (Tier 3 PII) | VA guidelines |
| `did:web:demining.etzhayyim.com:actor:assets` | Detector / PPE / MDD / flail inventory | UNSPSC 46101500 |
| `did:web:demining.etzhayyim.com:actor:imsma-sync` | IMSMA XML / NAA interop | 05.10 |

## Planned lexicons (`com.etzhayyim.apps.demining.*`)

Seed stubs committed in `00-contracts/lexicons/com/etzhayyim/apps/demining/`:

- `registerHazardArea` — create SHA/CHA (Tier 3 coords)
- `listHazardAreas` — list (polygon omitted unless caller has `demining.viewCoordinates` capability)
- `recordDetection` — detector hit (Tier 3 coords, Tier 2 item taxonomy)
- `recordClearanceTask` — NTS/TS/clearance task lifecycle
- `releaseArea` — Land Release decision → Tier 1 demotion
- `recordEoreSession` — EORE session + beneficiary count
- `recordVictim` — victim assistance referral (Tier 3)

Tighten schemas before wiring Worker.

## Graph schema (planned)

**Vertex labels**: `HazardArea`, `ExplosiveOrdnanceItem`, `ClearanceTask`, `SurveyRecord`, `LandReleaseDecision`, `DetectionEvent`, `DeminingAsset` (Detector/PPE/MDD/Flail), `EoreSession`, `Beneficiary`, `Victim`, `Operator`.

**Edge types**: `CONTAINS_EO`, `SURVEYED_BY`, `CLEARED_BY`, `RELEASED_BY`, `DETECTED_AT`, `ASSIGNED_ASSET`, `EORE_TARGETS_AREA`, `VICTIM_IN_AREA`, `SUPERSEDES`.

## Next steps (do not execute without review)

1. Review scaffold + sensitivity tiering with user
2. Register nanoid via `etzhayyim actor register`
3. Expand lexicon schemas (IMAS / IMSMA field parity)
4. Design Tier 3 `Preferences()` layout for SHA coords + PII
5. Scaffold T1 pipeline steps in `actor-manifest.jsonld`
6. Only then: consider T3 Worker fallback if needed
