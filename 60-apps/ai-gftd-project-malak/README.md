# malaknote

**Author:** L

Cybercriminal intelligence disclosure platform. Tracks, analyzes, and publishes structured threat actor profiles as public malaknotes.

## What is a malaknote?

A **malaknote** is a public disclosure document produced from open-source intelligence (OSINT) analysis of cybercriminal threat actors. Each note is:

- Published to GitHub (`ai-gftd-project-public-malak`)
- Formatted as structured markdown
- Attributed to author **L**
- Classified as PUBLIC (no sensitive sources disclosed)

## Architecture

```
ai-gftd-project-intel  →  analysis + classification
       ↓
ai-gftd-project-malak  →  disclosure + GitHub publish
       ↓
ai-gftd-project-public-malak (GitHub)  →  public malaknotes
```

Matrix protocol coordinates the workflow across ISCO evolution team agents (`!team-mlk8x2p9`).

## ISCO Evolution Team (mlk8x2p9)

| Role | ISCO | Agent | Matrix User |
|---|---|---|---|
| Business Manager | 1211 | 茉莉 (Mari) | @bm-mlk8x2p9:gftd.ai |
| Product Owner | 1120 | 蓮 (Ren) | @po-mlk8x2p9:gftd.ai |
| Marketer | 2433 | 美咲 (Misaki) | @mk-mlk8x2p9:gftd.ai |
| Engineer | 2512 | 朔 (Saku) | @eng-mlk8x2p9:gftd.ai |
| QA | 2519 | 紬 (Tsumugi) | @qa-mlk8x2p9:gftd.ai |

## MCP Methods

| Method | Description |
|---|---|
| `TriggerMalakMonitoring` | Start monitoring workflow for target regions |
| `ListIdentifiedActors` | List tracked threat actors |
| `ManualBlockchainDisclosure` | Disclose actor to blockchain with Interpol case ID |
| `RegisterFaceTrackerCamera` | Register/update surveillance camera for face tracking |
| `UpsertFaceWatchlistPerson` | Upsert watchlist person with legal basis |
| `ReportFaceMatchSignal` | Record match signal and promote to alert on repeated agreement |
| `ListFaceTrackerAlerts` | List face tracker alerts (open by default) |
| `GetFaceTrackerStatus` | Face tracker camera/watchlist/alert summary |
| `PublishGitHubNote` | Publish actor report as malaknote to GitHub |
| `GetPublishedNotes` | List published malaknotes |
| `HandleDailyEvolution` | Daily evolution input from ISCO team |
| `GetStatus` | Current operation summary |

---
*malaknote by L*
